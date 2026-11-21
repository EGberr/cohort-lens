"""Third pass: hand-written queries on StockSnap (modern CC0 photography) for picks that
failed visual review. Usage: uv run python -m scripts.curate_images"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from scripts.fetch_images import API, OUT, UA, credit, download

PRODUCTS: dict[str, str] = {}
CATEGORIES = {"skincare": "skincare", "haircare": "hairdresser", "video-streaming": "watching tv"}


def search(q: str) -> list[dict]:
    params = {"q": q, "license": "cc0,pdm,by,by-sa", "source": "stocksnap", "page_size": 20}
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    time.sleep(3.2)
    return [x for x in data.get("results", []) if x.get("width")]


def main() -> None:
    credits_path = OUT / "credits.json"
    credits = json.loads(credits_path.read_text())
    used = {c["url"] for c in credits.values()}
    jobs = [(f"products/{k}.webp", q, 900, False) for k, q in PRODUCTS.items()]
    jobs += [(f"categories/{k}.webp", q, 1600, True) for k, q in CATEGORIES.items()]
    for file, q, width, wide in jobs:
        results = [r for r in search(q) if r["foreign_landing_url"] not in used]
        if wide:
            results.sort(key=lambda r: r["width"] / r["height"] < 1.3)
        for r in results:
            if download(r["url"], width, OUT / file):
                credits[file] = credit(r, file)
                used.add(r["foreign_landing_url"])
                print(f"{file}: {r['title']}")
                break
        else:
            print(f"  ! nothing for {file} ({q})")
        credits_path.write_text(json.dumps(dict(sorted(credits.items())), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
