"""Fetch openly licensed photos for categories and products from Openverse.

Only CC0, Public Domain Mark, CC BY and CC BY-SA images are kept. Each image is resized,
converted to WebP and stored in web/public/img; attribution goes to web/public/img/credits.json
and is displayed in the app. Candidates are cached so a picture can be swapped without new
API calls (`--pick product-slug=N`).

Run: `uv run python -m scripts.fetch_images [--refresh] [--pick slug=index ...]`
"""

from __future__ import annotations

import argparse
import io
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

from app.corpus.catalog import BY_CATEGORY, PRODUCTS
from app.corpus.spec import CATEGORIES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "web" / "public" / "img"
CACHE = ROOT / "backend" / "scripts" / "image_candidates.json"
API = "https://api.openverse.org/v1/images/"
UA = "ZentrendPortfolio/1.0 (open-source demo; https://github.com/EGberr/zentrend)"
LICENSES = "cc0,pdm,by,by-sa"
SOURCES = "stocksnap,rawpixel,wikimedia,flickr"
SOURCE_RANK = {"stocksnap": 0, "rawpixel": 1, "flickr": 2, "wikimedia": 3}
# Reject archival artwork, clip art and visible brands: the catalogue shows generic product types.
BANNED = (
    "illustration",
    "vintage",
    "drawing",
    "engraving",
    "etching",
    "painting",
    "antique",
    "clipart",
    "clip art",
    "vector",
    "icon",
    "logo",
    "sticker",
    "poster",
    "lithograph",
    "museum",
    "century",
    "print",
    "cartoon",
    "png",
    "sketch",
    "portrait of",
    "carte de visite",
    "photograph of",
    "1880",
    "1890",
    "1900",
    "191",
    "192",
    "193",
    "194",
    "195",
    "monster",
    "chanel",
    "netflix",
    "nike",
    "apple",
    "samsung",
    "carabinieri",
    "police",
    "army",
    "soldier",
    "uniform",
    "xbox",
    "atari",
    "lou reed",
    "cartier",
)


def acceptable(c: dict) -> bool:
    title = (c.get("title") or "").lower()
    if any(b in title for b in BANNED):
        return False
    if c["source"] == "wikimedia":
        return False  # mostly archival or documentary shots; keep as a last resort only
    return c["width"] >= 800


def ranked(cands: list[dict]) -> list[dict]:
    good = [c for c in cands if acceptable(c)]
    rest = [c for c in cands if c not in good and c["source"] != "wikimedia"]
    return good + rest + [c for c in cands if c["source"] == "wikimedia"]


def search(query: str) -> list[dict]:
    params = {"q": query, "license": LICENSES, "source": SOURCES, "size": "large", "page_size": 12, "mature": "false"}
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            raise
    keep = []
    for r in data.get("results", []):
        if not r.get("width") or not r.get("height"):
            continue
        keep.append(
            {
                k: r.get(k)
                for k in (
                    "id",
                    "title",
                    "creator",
                    "license",
                    "license_version",
                    "license_url",
                    "source",
                    "url",
                    "foreign_landing_url",
                    "width",
                    "height",
                )
            }
        )
    keep.sort(key=lambda r: SOURCE_RANK.get(r["source"], 9))
    return keep


def download(url: str, max_w: int, dest: Path) -> bool:
    time.sleep(1.5 if "wikimedia" in url else 0.2)  # be polite to Wikimedia's bot limits
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:  # broken link, unsupported format
        print(f"  ! download failed {url[:80]}: {exc}")
        return False
    if img.width > max_w:
        img = img.resize((max_w, round(img.height * max_w / img.width)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "WEBP", quality=78, method=6)
    return True


def credit(c: dict, file: str) -> dict:
    lic = c["license"].upper() if c["license"] not in ("cc0", "pdm") else c["license"].upper()
    return {
        "file": file,
        "title": c["title"],
        "creator": c["creator"],
        "license": f"{lic} {c.get('license_version') or ''}".strip(),
        "license_url": c["license_url"],
        "source": c["source"],
        "url": c["foreign_landing_url"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="Ignore the candidate cache")
    ap.add_argument("--pick", nargs="*", default=[], help="Override candidate index: slug=N")
    ap.add_argument("--reselect", action="store_true", help="Re-run the quality ranking for every image")
    args = ap.parse_args()
    picks = dict(p.split("=") for p in args.pick)

    cache = {} if args.refresh or not CACHE.exists() else json.loads(CACHE.read_text())
    for p in PRODUCTS:
        if p.slug not in cache:
            print(f"search {p.slug}: {p.query}")
            cache[p.slug] = search(p.query)
            CACHE.write_text(json.dumps(cache, indent=1))
            time.sleep(3.3)  # stay under the anonymous burst limit

    credits_path = OUT / "credits.json"
    credits = json.loads(credits_path.read_text()) if credits_path.exists() else {}
    used: set[str] = set()
    chosen: dict[str, dict] = {}
    for p in PRODUCTS:
        file = f"products/{p.slug}.webp"
        prev = credits.get(file)
        if prev and (OUT / file).exists() and p.slug not in picks and not args.reselect:
            done = next((c for c in cache[p.slug] if c["foreign_landing_url"] == prev["url"]), None)
            if done:
                used.add(done["id"])
                continue
        cands = [c for c in ranked(cache[p.slug]) if c["id"] not in used]
        if p.slug in picks:
            cands = [cache[p.slug][int(picks[p.slug])]] + cands
        for c in cands:
            file = f"products/{p.slug}.webp"
            prev = credits.get(file)
            if prev and prev.get("url") == c["foreign_landing_url"] and (OUT / file).exists():
                chosen[p.slug] = c
                used.add(c["id"])
                break
            if download(c["url"], 900, OUT / file):
                chosen[p.slug] = c
                used.add(c["id"])
                credits[file] = credit(c, file)
                break
        else:
            print(f"  ! no image for {p.slug}")

    # Category hero: the widest unused candidate among its products' results.
    for cat in CATEGORIES:
        file = f"categories/{cat.slug}.webp"
        pool = [c for prod in BY_CATEGORY[cat.slug] for c in cache[prod.slug] if c["id"] not in used]
        pool.sort(
            key=lambda c: (not acceptable(c), -(c["width"] / c["height"] >= 1.35), SOURCE_RANK.get(c["source"], 9))
        )
        if cat.slug in picks:
            prod_slug, idx = picks[cat.slug].split(":")
            pool = [cache[f"{cat.slug}--{prod_slug}"][int(idx)]] + pool
        for c in pool:
            prev = credits.get(file)
            if prev and prev.get("url") == c["foreign_landing_url"] and (OUT / file).exists():
                used.add(c["id"])
                break
            if download(c["url"], 1600, OUT / file):
                used.add(c["id"])
                credits[file] = credit(c, file)
                break
        else:
            print(f"  ! no hero for {cat.slug}")

    credits_path.write_text(json.dumps(dict(sorted(credits.items())), indent=1, ensure_ascii=False))
    print(f"{len(credits)} images credited in {credits_path}")


if __name__ == "__main__":
    main()
