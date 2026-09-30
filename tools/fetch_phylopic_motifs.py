"""Download realistic organism silhouettes from PhyloPic for the motif folder.

PhyloPic (https://www.phylopic.org) publishes scientist-made silhouettes of
living things under CC0, public domain and CC BY licences. They are vector
files, so they rasterise crisply and look like real animals and plants rather
than clip art - which is what the kaleidoscope motif mode wants.

Usage::

    python tools\\fetch_phylopic_motifs.py --out motifs\\nature --limit 140
    python tools\\fetch_phylopic_motifs.py --out D:\\shapes --pages 40

Files land as 512 px, 1-bit, black-on-white PNGs with a margin, plus
``manifest.json`` and ``CREDITS.md`` listing the taxon, contributor, licence and
source page. Needs network access and PySide6 (for SVG rasterising).
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import time
import urllib.request
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

API = "https://api.phylopic.org"
USER_AGENT = "converter-motif-tool/1.0 (personal pen-plotter project)"
OUTPUT_PIXELS = 512
MARGIN = 26

FREE = {
    "publicdomain/zero": "CC0",
    "publicdomain/mark": "Public domain",
    "licenses/by/": "CC BY",
    "licenses/by-sa/": "CC BY-SA",
}

_LAST_CALL = 0.0


def _throttle(seconds=0.6):
    global _LAST_CALL
    wait = seconds - (time.time() - _LAST_CALL)
    if wait > 0:
        time.sleep(wait)
    _LAST_CALL = time.time()


def api(path):
    _throttle()
    request = urllib.request.Request(
        API + path,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.api+json; version=2",
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3.0 * (attempt + 1))
    return {}


def download(url):
    _throttle(0.4)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3.0 * (attempt + 1))
    raise RuntimeError("unreachable")


def build_number():
    return api("/")["build"]


def index_page(build, page):
    """(image uuid, taxon name) pairs from one index page."""
    data = api("/images?build=%d&page=%d" % (build, page))
    out = []
    for item in data.get("_links", {}).get("items", []):
        match = re.search(r"/images/([0-9a-f-]{36})", item.get("href", ""))
        if match:
            out.append((match.group(1), item.get("title", "")))
    return out


def image_meta(uuid, build):
    """Licence and vector URL for one image."""
    data = api("/images/%s?build=%d" % (uuid, build))
    links = data.get("_links", {})
    licence_url = links.get("license", {}).get("href", "")
    licence = ""
    for needle, label in FREE.items():
        if needle in licence_url:
            licence = label
            break
    if not licence:
        return None
    vector = links.get("vectorFile", {}).get("href") or links.get(
        "sourceFile", {}
    ).get("href")
    if not vector:
        return None
    return {
        "uuid": uuid,
        "licence": licence,
        "licence_url": licence_url,
        "vector": vector,
        "contributor": links.get("contributor", {}).get("title", ""),
        "taxon": links.get("specificNode", {}).get("title", "")
        or links.get("generalNode", {}).get("title", ""),
        "source": "https://www.phylopic.org/images/%s" % uuid,
    }


def rasterise(svg_bytes, size=900):
    """Rasterise an SVG with Qt so strokes and fills keep their shape."""
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PIL import Image

    renderer = QSvgRenderer(QByteArray(svg_bytes))
    if not renderer.isValid():
        return None
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    buffer = image.constBits().tobytes()
    pil = Image.frombuffer(
        "RGBA", (image.width(), image.height()), buffer, "raw", "BGRA", 0, 1
    )
    return pil.copy()


def to_motif(pil_image):
    """Trim, square and threshold a rendered silhouette."""
    import numpy as np
    from PIL import Image

    if pil_image is None:
        return None, ""
    canvas = Image.new("RGBA", pil_image.size, (255, 255, 255, 255))
    canvas.alpha_composite(pil_image.convert("RGBA"))
    grey = canvas.convert("L")
    pixels = np.asarray(grey, dtype=np.uint8)
    mask = pixels < 160
    fraction = float(mask.mean())
    if fraction < 0.01 or fraction > 0.85:
        return None, ""
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any() or not cols.any():
        return None, ""
    top, bottom = int(np.argmax(rows)), int(len(rows) - np.argmax(rows[::-1]))
    left, right = int(np.argmax(cols)), int(len(cols) - np.argmax(cols[::-1]))
    subject = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").crop(
        (left, top, right, bottom)
    )
    inner = OUTPUT_PIXELS - 2 * MARGIN
    scale = min(inner / subject.width, inner / subject.height)
    target = (
        max(1, int(round(subject.width * scale))),
        max(1, int(round(subject.height * scale))),
    )
    subject = subject.resize(target, Image.LANCZOS)
    # Black subject on white, the way the plotter's tracer expects it.
    subject = subject.point(lambda value: 0 if value < 128 else 255, "L")
    square = Image.new("L", (OUTPUT_PIXELS, OUTPUT_PIXELS), 255)
    square.paste(
        subject,
        ((OUTPUT_PIXELS - target[0]) // 2, (OUTPUT_PIXELS - target[1]) // 2),
    )
    shape = "%dx%d" % (right - left, bottom - top)
    return square.convert("1"), shape


def safe_name(text):
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:46] or "organism"


def build(out_dir, limit, pages):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    build_id = build_number()
    print("PhyloPic build", build_id, flush=True)

    # Sample pages evenly across the index so the assortment is varied rather
    # than one taxonomic corner.
    total_pages = api("/images?build=%d" % build_id).get("totalPages", 1)
    step = max(1, total_pages // max(pages, 1))
    candidates = []
    for page in range(0, total_pages, step):
        if len(candidates) >= limit * 4:
            break
        try:
            candidates.extend(index_page(build_id, page))
        except Exception as exc:
            print("  page %d failed: %s" % (page, exc), flush=True)
    print("%d candidates from %d pages" % (len(candidates), pages), flush=True)

    saved = []
    for uuid, name in candidates:
        if len(saved) >= limit:
            break
        try:
            meta = image_meta(uuid, build_id)
            if not meta:
                continue
            svg = download(meta["vector"])
            motif, shape = to_motif(rasterise(svg))
        except Exception as exc:
            print("  skip %s (%s)" % (name[:32], str(exc)[:60]), flush=True)
            continue
        if motif is None:
            continue
        taxon = meta["taxon"] or name
        filename = "%03d-%s.png" % (len(saved) + 1, safe_name(taxon))
        motif.save(out_dir / filename, optimize=True)
        saved.append(
            {
                "file": filename,
                "taxon": taxon,
                "contributor": meta["contributor"],
                "licence": meta["licence"],
                "licence_url": meta["licence_url"],
                "source": meta["source"],
                "subject_pixels": shape,
            }
        )
        print("  %3d %-38s %s" % (len(saved), taxon[:38], meta["licence"]), flush=True)

    (out_dir / "manifest.json").write_text(
        json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Motif credits",
        "",
        "Organism silhouettes from [PhyloPic](https://www.phylopic.org),",
        "rasterised and converted to black-on-white by",
        "`tools/fetch_phylopic_motifs.py`.",
        "",
        "| File | Taxon | Contributor | Licence | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in saved:
        lines.append(
            "| %s | %s | %s | [%s](%s) | [PhyloPic](%s) |"
            % (
                row["file"],
                row["taxon"],
                row["contributor"] or "unknown",
                row["licence"],
                row["licence_url"],
                row["source"],
            )
        )
    (out_dir / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[1] / "motifs" / "nature"),
        help="folder to write the silhouettes into",
    )
    parser.add_argument("--limit", type=int, default=140)
    parser.add_argument("--pages", type=int, default=36, help="index pages to sample")
    args = parser.parse_args()
    saved = build(args.out, args.limit, args.pages)
    print("saved %d motifs to %s" % (len(saved), args.out))


if __name__ == "__main__":
    main()
