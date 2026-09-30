"""Cut public-domain nature engravings into individual motifs.

The kaleidoscope's reference artwork is built from hand-drawn, hatched leaves
and creatures, so the best motif source is not a silhouette but an *engraving*:
black ink line work on white paper. Wikimedia Commons holds the classic
public-domain sets - Ernst Haeckel's "Kunstformen der Natur", botanical
engravings, zoological plates - as high-resolution scans, each page carrying
several organisms.

This tool downloads a page at a standard thumbnail size, keeps the ink, finds
the individual organisms on it, drops captions and rules, and writes each one
as a 512 px black-on-white 1-bit PNG. Credits and a manifest are written beside
the images.

Usage::

    python tools\\fetch_engraving_motifs.py --out motifs\\nature-engravings --plates 20
    python tools\\fetch_engraving_motifs.py --out some\\dir --limit 80

Wikimedia throttles bulk downloads, so the tool paces itself and backs off on
429 responses; expect a few minutes for a couple of dozen plates.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import time
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "converter-motif-tool/1.0 (personal pen-plotter project)"
OUTPUT_PIXELS = 512
MARGIN = 22
PLATE_BOX = 900

CATEGORIES = (
    "Category:Kunstformen der Natur",
    "Category:Engravings of plants",
    "Category:Botanical illustrations",
    "Category:Zoological illustrations",
)

FREE = ("public domain", "cc0", "cc by", "cc-by")

_LAST_CALL = 0.0


def _throttle(seconds=2.4):
    global _LAST_CALL
    wait = seconds - (time.time() - _LAST_CALL)
    if wait > 0:
        time.sleep(wait)
    _LAST_CALL = time.time()


def _request(url, accept=None, timeout=60):
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    return urllib.request.Request(url, headers=headers)


def api(params):
    params = dict(params)
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        _throttle()
        try:
            with urllib.request.urlopen(
                _request(url, "application/json"), timeout=45
            ) as response:
                return json.load(response)
        except Exception as exc:
            if attempt == 3:
                raise
            print("   (api %s - retrying)" % str(exc)[:60], flush=True)
            time.sleep(6.0 * (attempt + 1))
    return {}


def download(url):
    for attempt in range(4):
        _throttle()
        try:
            with urllib.request.urlopen(_request(url), timeout=90) as response:
                return response.read()
        except Exception as exc:
            if attempt == 3:
                raise
            print("   (download %s - retrying)" % str(exc)[:60], flush=True)
            time.sleep(8.0 * (attempt + 1))
    raise RuntimeError("unreachable")


def _strip_html(text):
    return re.sub(r"<[^>]+>", "", str(text or "")).strip()


def plates(category, wanted):
    """Freely licensed page scans from one category."""
    found = []
    data = api(
        {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": "file",
            "cmlimit": "100",
        }
    )
    titles = [
        member["title"]
        for member in data.get("query", {}).get("categorymembers", [])
        if member["title"].lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff"))
    ]
    for start in range(0, len(titles), 20):
        if len(found) >= wanted:
            break
        batch = titles[start : start + 20]
        info = api(
            {
                "action": "query",
                "titles": "|".join(batch),
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": "1280",
            }
        )
        pages = info.get("query", {}).get("pages", [])
        if isinstance(pages, dict):
            pages = list(pages.values())
        for page in pages:
            image = (page.get("imageinfo") or [{}])[0]
            meta = image.get("extmetadata", {})
            licence = _strip_html(meta.get("LicenseShortName", {}).get("value", ""))
            if not any(token in licence.lower() for token in FREE):
                continue
            if not image.get("thumburl"):
                continue
            found.append(
                {
                    "title": page["title"],
                    "url": image["thumburl"],
                    "source": image.get("descriptionurl", ""),
                    "artist": _strip_html(meta.get("Artist", {}).get("value", "")),
                    "licence": licence,
                }
            )
            if len(found) >= wanted:
                break
    return found


def _otsu(values):
    import numpy as np

    histogram = np.bincount(values.ravel(), minlength=256).astype(np.float64)
    total = histogram.sum()
    if total <= 0:
        return 128
    levels = np.arange(256, dtype=np.float64)
    weight_back = np.cumsum(histogram)
    weight_front = total - weight_back
    sum_back = np.cumsum(histogram * levels)
    sum_total = sum_back[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        mean_back = sum_back / np.maximum(weight_back, 1)
        mean_front = (sum_total - sum_back) / np.maximum(weight_front, 1)
    variance = weight_back * weight_front * (mean_back - mean_front) ** 2
    variance[~np.isfinite(variance)] = 0.0
    return int(np.argmax(variance))


def _components(mask, max_side=460):
    """Label 4-connected ink blobs; returns (labels, areas, step)."""
    import numpy as np

    height, width = mask.shape
    step = max(1, int(math.ceil(max(height, width) / max_side)))
    small = mask[::step, ::step]
    labels = np.zeros(small.shape, dtype=np.int32)
    areas = {}
    rows, cols = small.shape
    current = 0
    for y in range(rows):
        for x in range(cols):
            if not small[y, x] or labels[y, x]:
                continue
            current += 1
            queue = deque([(y, x)])
            labels[y, x] = current
            count = 0
            while queue:
                cy, cx = queue.popleft()
                count += 1
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < rows and 0 <= nx < cols:
                        if small[ny, nx] and not labels[ny, nx]:
                            labels[ny, nx] = current
                            queue.append((ny, nx))
            areas[current] = count * step * step
    return labels, areas, step


def extract(data, per_plate=6):
    """Ink crops of the organisms on one plate."""
    import numpy as np
    from PIL import Image

    image = Image.open(io.BytesIO(data)).convert("L")
    if max(image.size) > PLATE_BOX:
        scale = PLATE_BOX / max(image.size)
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.LANCZOS,
        )
    if min(image.size) < 300:
        return []
    # Scans keep a frame and a black page edge; trimming a few percent removes
    # both without touching the drawings.
    trim_x = int(image.width * 0.025)
    trim_y = int(image.height * 0.025)
    image = image.crop((trim_x, trim_y, image.width - trim_x, image.height - trim_y))
    pixels = np.asarray(image, dtype=np.uint8)
    border = np.concatenate(
        [pixels[0, :], pixels[-1, :], pixels[:, 0], pixels[:, -1]]
    )
    if border.mean() < 170 or border.std() > 70:
        return []
    threshold = _otsu(pixels)
    ink = pixels < threshold
    fraction = float(ink.mean())
    if fraction < 0.015 or fraction > 0.50:
        return []

    labels, areas, step = _components(ink)
    height, width = ink.shape
    if not areas:
        return []
    # Engravings are line work, so one organism is many unconnected strokes:
    # cutting on connected ink shatters it. Split the page on its own white
    # gutters instead, which is how the plates are laid out.
    for index in range(height):
        if ink[index].mean() > 0.9:
            ink[index] = False
    for index in range(width):
        if ink[:, index].mean() > 0.9:
            ink[:, index] = False

    def runs(has_ink, minimum):
        blocks = []
        start = None
        for index, value in enumerate(has_ink):
            if not value:
                if start is None:
                    start = index
            else:
                if start is not None:
                    if index - start >= minimum and blocks:
                        blocks.append(index)
                    start = None
        if start is not None and len(has_ink) - start >= minimum:
            blocks.append(len(has_ink))
        return blocks

    # First pass: the plate's drawing area, separated from the title band and
    # the captions by the widest white gutters.
    def region(box):
        left, top, right, bottom = box
        return ink[top:bottom, left:right]

    whole = (0, 0, width, height)
    columns = [0] + runs(ink.any(axis=0), max(6, int(0.02 * width))) + [width]
    best = whole
    best_area = 0
    for left, right in zip(columns, columns[1:]):
        rows = [0] + runs(ink[:, left:right].any(axis=1), max(6, int(0.02 * height))) + [height]
        for top, bottom in zip(rows, rows[1:]):
            area = (right - left) * (bottom - top)
            if area > best_area and region((left, top, right, bottom)).mean() > 0.02:
                best_area = area
                best = (left, top, right, bottom)
    left0, top0, right0, bottom0 = best
    area_ink = ink[top0:bottom0, left0:right0]
    area_h = bottom0 - top0
    area_w = right0 - left0

    # Second pass: the organisms are packed too tightly for gutter detection to
    # be reliable, so walk the drawing area on an overlapping grid and keep the
    # cells that hold a real drawing (enough ink, spread over the cell, not a
    # caption line).
    crops = []
    grid_x, grid_y, overlap = 3, 2, 0.18
    for row in range(grid_y):
        for column in range(grid_x):
            width_step = area_w / grid_x
            height_step = area_h / grid_y
            left = int(column * width_step - overlap * width_step)
            right = int((column + 1) * width_step + overlap * width_step)
            top = int(row * height_step - overlap * height_step)
            bottom = int((row + 1) * height_step + overlap * height_step)
            left, right = max(0, left), min(area_w, right)
            top, bottom = max(0, top), min(area_h, bottom)
            block = area_ink[top:bottom, left:right]
            if block.size == 0:
                continue
            density = float(block.mean())
            if density < 0.06 or density > 0.55:
                continue
            ys = np.nonzero(block.any(axis=1))[0]
            if len(ys) < 0.3 * block.shape[0]:
                continue  # a caption line
            pad = int(max(block.shape) * 0.04) + 3
            crops.append(
                (
                    max(0, left0 + left - pad),
                    max(0, top0 + top - pad),
                    min(width, left0 + right + pad),
                    min(height, top0 + bottom + pad),
                )
            )
            if len(crops) >= per_plate:
                break
        if len(crops) >= per_plate:
            break
    if len(crops) < 2:
        return []
    return crops[:per_plate], image


def to_motif(image, box):
    """Trim one crop into a square, black-on-white, 1-bit motif."""
    from PIL import Image

    crop = image.crop(box)
    if max(crop.size) < 80:
        return None
    inner = OUTPUT_PIXELS - 2 * MARGIN
    scale = min(inner / crop.width, inner / crop.height)
    target = (
        max(1, int(round(crop.width * scale))),
        max(1, int(round(crop.height * scale))),
    )
    crop = crop.resize(target, Image.LANCZOS)
    crop = crop.point(lambda value: 0 if value < 150 else 255, "L")
    square = Image.new("L", (OUTPUT_PIXELS, OUTPUT_PIXELS), 255)
    square.paste(
        crop, ((OUTPUT_PIXELS - target[0]) // 2, (OUTPUT_PIXELS - target[1]) // 2)
    )
    return square.convert("1")


def slug(text):
    text = re.sub(r"\.(jpe?g|png|tiff?)$", "", text, flags=re.I)
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:46] or "plate"


def _safe(text):
    try:
        text.encode("cp1252")
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", "replace").decode("ascii")


def build(out_dir, plate_target, motif_limit, per_plate):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plates_found = []
    for category in CATEGORIES:
        if len(plates_found) >= plate_target:
            break
        try:
            plates_found.extend(plates(category, plate_target - len(plates_found)))
        except Exception as exc:
            print("  %s failed: %s" % (category, str(exc)[:70]), flush=True)
        print("  %-34s plates so far %d" % (category, len(plates_found)), flush=True)

    saved = []
    for plate in plates_found:
        if len(saved) >= motif_limit:
            break
        try:
            data = download(plate["url"])
            result = extract(data, per_plate)
        except Exception as exc:
            print("  skip %s (%s)" % (_safe(plate["title"])[:40], str(exc)[:60]), flush=True)
            continue
        if not result:
            continue
        crops, image = result
        made = 0
        for left, top, right, bottom in crops:
            if len(saved) >= motif_limit:
                break
            motif = to_motif(image, (left, top, right, bottom))
            if motif is None:
                continue
            name = "%03d-%s-%d.png" % (len(saved) + 1, slug(plate["title"]), made + 1)
            motif.save(out_dir / name, optimize=True)
            saved.append(
                {
                    "file": name,
                    "plate": plate["title"],
                    "artist": plate["artist"],
                    "licence": plate["licence"],
                    "source": plate["source"],
                }
            )
            made += 1
        print(
            "  %-42s %d motifs (%d total)"
            % (_safe(plate["title"])[:42], made, len(saved)),
            flush=True,
        )

    (out_dir / "manifest.json").write_text(
        json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Motif credits",
        "",
        "Organisms cut from public-domain engraving plates on Wikimedia Commons",
        "(chiefly Ernst Haeckel's *Kunstformen der Natur*) by",
        "`tools/fetch_engraving_motifs.py`.",
        "",
        "| File | Plate | Artist | Licence | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in saved:
        lines.append(
            "| %s | %s | %s | %s | [Commons](%s) |"
            % (
                row["file"],
                row["plate"],
                row["artist"] or "unknown",
                row["licence"],
                row["source"],
            )
        )
    (out_dir / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[1] / "motifs" / "nature-engravings"),
        help="folder to write the motifs into",
    )
    parser.add_argument("--plates", type=int, default=18, help="plates to look at")
    parser.add_argument("--limit", type=int, default=140, help="motifs to save")
    parser.add_argument("--per-plate", type=int, default=6)
    args = parser.parse_args()
    saved = build(args.out, args.plates, args.limit, args.per_plate)
    print("saved %d engraving motifs to %s" % (len(saved), args.out))


if __name__ == "__main__":
    main()
