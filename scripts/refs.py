#!/usr/bin/env python3
"""Reference photos for modelling real objects (bedah look): search Wikimedia Commons, download thumbnails,
make one contact sheet per item. Look at the sheets before modelling, and write the spec (size, colours,
parts, how it is installed) into projects/<slug>/refs/SPEK.md.

Usage:
    python scripts/refs.py projects/<slug> "kwh_meter=prepaid electricity meter Indonesia;PLN prepaid meter" \
                                           "mcb=miniature circuit breaker" ...
    -> projects/<slug>/refs/<item>/NN.jpg (+ .txt with title and source URL), refs/sheet_<item>.png, refs/sources.txt

Each argument is item=query1;query2 (queries are tried in order until 8 images). Uses curl (Python's SSL store
may be outdated on Windows) and waits between requests (Commons rate-limits with HTTP 429). The photos are
for research only: do not publish them; note the source pages if you describe them.
"""
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
UA = "motion-shorts-reference-research/1.0"


def get(url):
    time.sleep(1.5)
    r = subprocess.run(["curl", "-sSfL", "--max-time", "40", "-A", UA, url], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors="ignore")[:160])
    return r.stdout


def fetch(item, queries, out, limit=8):
    d = out / item
    d.mkdir(parents=True, exist_ok=True)
    n = len(list(d.glob("*.jpg")))
    seen = set()
    for q in queries:
        if n >= limit:
            break
        params = {"action": "query", "generator": "search", "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": 10,
                  "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 900, "format": "json"}
        try:
            data = json.loads(get(API + "?" + urllib.parse.urlencode(params)))
        except Exception as e:
            print(f"  ! search '{q}': {e}")
            continue
        for pg in sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
            ii = (pg.get("imageinfo") or [{}])[0]
            if ii.get("mime") not in ("image/jpeg", "image/png") or pg["title"] in seen:
                continue
            seen.add(pg["title"])
            try:
                (d / f"{n:02d}.jpg").write_bytes(get(ii["thumburl"]))
                (d / f"{n:02d}.txt").write_text(pg["title"] + "\n" + ii.get("descriptionurl", ""), encoding="utf-8")
                n += 1
            except Exception as e:
                print(f"  ! download {pg['title']}: {e}")
            if n >= limit:
                break
    return n


def sheet(item, out):
    from PIL import Image, ImageDraw
    ims = []
    for f in sorted((out / item).glob("*.jpg")):
        try:
            im = Image.open(f).convert("RGB")
            im.thumbnail((330, 330))
            ims.append(im)
        except Exception:
            pass
    if not ims:
        return None
    W = Image.new("RGB", (4 * 340, 2 * 340), "white")
    dr = ImageDraw.Draw(W)
    for i, im in enumerate(ims[:8]):
        x, y = (i % 4) * 340 + 5, (i // 4) * 340 + 5
        W.paste(im, (x, y))
        dr.text((x + 4, y + 4), str(i), fill=(255, 0, 0))
    p = out / f"sheet_{item}.png"
    W.save(p)
    return p


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]) / "refs"
    out.mkdir(parents=True, exist_ok=True)
    for arg in sys.argv[2:]:
        item, _, qs = arg.partition("=")
        n = fetch(item.strip(), [q.strip() for q in qs.split(";") if q.strip()], out)
        p = sheet(item.strip(), out)
        print(json.dumps({"item": item, "images": n, "sheet": str(p) if p else None}))
    srcs = sorted({t.read_text(encoding="utf-8").splitlines()[-1] for t in out.glob("*/*.txt")})
    (out / "sources.txt").write_text("\n".join(srcs) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
