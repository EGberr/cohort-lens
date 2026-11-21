"""Second pass: re-search weak picks on modern stock-photo sources only, then reselect."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from app.corpus.catalog import PRODUCT_BY_SLUG
from scripts.fetch_images import API, CACHE, UA, acceptable

MODERN = "stocksnap,rawpixel"


def search_modern(query: str) -> list[dict]:
    params = {"q": query, "license": "cc0,pdm,by,by-sa", "source": MODERN, "page_size": 12, "mature": "false"}
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    return [
        {
            k: x.get(k)
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
        for x in data.get("results", [])
        if x.get("width") and x.get("height")
    ]


def main() -> None:
    cache = json.loads(CACHE.read_text())
    credits = json.loads((CACHE.parents[2] / "web/public/img/credits.json").read_text())
    weak = []
    for slug, cands in cache.items():
        chosen = credits.get(f"products/{slug}.webp", {}).get("url")
        sel = next((c for c in cands if c["foreign_landing_url"] == chosen), None)
        if not sel or not acceptable(sel):
            weak.append(slug)
    print(f"{len(weak)} weak picks")
    for slug in weak:
        p = PRODUCT_BY_SLUG[slug]
        query = p.name.lower().replace("/", " ")
        try:
            fresh = search_modern(query) or search_modern(p.query)
        except Exception as exc:  # rate limit or network: keep what we have
            print(f"  ! {slug}: {exc}")
            break
        seen = {c["id"] for c in fresh}
        cache[slug] = fresh + [c for c in cache[slug] if c["id"] not in seen]
        print(f"{slug}: +{len(fresh)}")
        CACHE.write_text(json.dumps(cache, indent=1))
        time.sleep(3.2)


if __name__ == "__main__":
    main()
