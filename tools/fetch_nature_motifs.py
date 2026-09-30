"""Download real public-domain nature silhouettes for the kaleidoscope motifs.

Pulls images from Wikimedia Commons (no API key needed), keeps only freely
licensed files, and converts each one into the plotter's format: a pure
black-on-white 1-bit PNG, trimmed to the subject and squared off with a margin.

It also writes ``manifest.json`` and ``CREDITS.md`` next to the images, because
public-domain and CC0 files are still worth crediting, and CC BY / CC BY-SA
files require it.

Usage::

    python tools\\fetch_nature_motifs.py --out motifs\\nature --limit 120
    python tools\\fetch_nature_motifs.py --out D:\\shapes --search "fern silhouette"

Notes:

- Photos of specimens on plain backgrounds work well too; the border colour
  decides the polarity, so white-on-black art is inverted automatically.
- Downloading needs network access. Nothing is written until a file passes the
  quality checks, so a bad candidate is skipped rather than saved.
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
from pathlib import Path

USER_AGENT = "converter-motif-tool/1.0 (personal pen-plotter project)"
API = "https://commons.wikimedia.org/w/api.php"
OUTPUT_PIXELS = 512
MARGIN = 26

# Searches are cheap and give a mixed, natural assortment; the categories hold
# curated specimen photography. Both are freely licensed or filtered out.
SEARCHES = (
    "Quercus silhouette",
    "Acer silhouette",
    "Fagus silhouette",
    "Betula silhouette",
    "Salix silhouette",
    "Pinus silhouette",
    "fern silhouette",
    "palm leaf silhouette",
    "monstera silhouette",
    "tree silhouette plain background",
    "leaf herbarium white background",
    "pressed leaf specimen",
)

CATEGORIES = (
    "Category:Silhouettes of plants",
    "Category:Leaves on white background",
    "Category:Silhouettes of birds",
    "Category:Silhouettes of animals",
    "Category:Herbarium specimens",
)

FREE_LICENCES = (
    "public domain",
    "cc0",
    "cc by 4.0",
    "cc by 3.0",
    "cc by 2.0",
    "cc by-sa 4.0",
    "cc by-sa 3.0",
    "cc by-sa 2.0",
)


def _api(params):
    params = dict(params)
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    url = API + "?" + urllib.parse.urlencode(params)
    last = 0.0
    for attempt in range(5):
        # Commons throttles hard: keep at least 1.5 s between calls and back
        # off properly on 429 instead of hammering it.
        global _LAST_CALL
        wait = 2.5 - (time.time() - _LAST_CALL)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                _LAST_CALL = time.time()
                return json.load(response)
        except Exception as exc:
            _LAST_CALL = time.time()
            if attempt == 4:
                raise
            delay = 5.0 * (attempt + 1)
            print("   (API %s - waiting %.0fs)" % (exc, delay))
            time.sleep(delay)
    return {}


_LAST_CALL = 0.0


def _strip_html(text):
    return re.sub(r"<[^>]+>", "", str(text or "")).strip()


def _entry(page):
    """Freely licensed image details for one API page, or None."""
    image_info = (page.get("imageinfo") or [{}])[0]
    meta = image_info.get("extmetadata", {})
    licence = _strip_html(meta.get("LicenseShortName", {}).get("value", ""))
    if licence.lower() not in FREE_LICENCES and "public domain" not in licence.lower():
        return None
    if not image_info.get("thumburl"):
        return None
    return {
        "title": page["title"],
        "url": image_info["thumburl"],
        "descriptionurl": image_info.get("descriptionurl", ""),
        "artist": _strip_html(meta.get("Artist", {}).get("value", "")),
        "licence": licence,
        "width": image_info.get("width", 0),
        "height": image_info.get("height", 0),
    }


def search_with_info(term, count=50):
    """Search one term and get each hit's image info in a single request."""
    try:
        data = _api(
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": term + " filetype:bitmap",
                "gsrnamespace": "6",
                "gsrlimit": str(count),
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": "1600",
            }
        )
    except Exception:
        return {}
    pages = data.get("query", {}).get("pages", [])
    if isinstance(pages, dict):
        pages = list(pages.values())
    return pages


def gather(limit):
    """Freely licensed candidates from searches and categories."""
    found = {}
    wanted = limit * 3
    for term in SEARCHES:
        if len(found) >= wanted:
            break
        for page in search_with_info(term):
            entry = _entry(page)
            if entry:
                found[page["title"]] = entry
        print("  search %-30s total %d" % (term, len(found)), flush=True)
    for category in CATEGORIES:
        if len(found) >= wanted:
            break
        try:
            data = _api(
                {
                    "action": "query",
                    "list": "categorymembers",
                    "cmtitle": category,
                    "cmtype": "file",
                    "cmlimit": "100",
                }
            )
        except Exception:
            continue
        titles = [m["title"] for m in data.get("query", {}).get("categorymembers", [])]
        for start in range(0, len(titles), 40):
            found.update(file_info(titles[start : start + 40]))
        print("  category %-28s total %d" % (category, len(found)), flush=True)
    return found


def file_info(titles):
    """Image URL plus licence metadata for a batch of titles."""
    info = {}
    for start in range(0, len(titles), 40):
        batch = titles[start : start + 40]
        data = _api(
            {
                "action": "query",
                "titles": "|".join(batch),
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": "1600",
            }
        )
        pages = data.get("query", {}).get("pages", [])
        if isinstance(pages, dict):
            pages = list(pages.values())
        for page in pages:
            entry = _entry(page)
            if entry:
                info[page["title"]] = entry
    return info


def _otsu_threshold(gray):
    import numpy as np

    values = np.asarray(gray, dtype=np.uint8)
    histogram = np.bincount(values.ravel(), minlength=256).astype(np.float64)
    total = histogram.sum()
    if total <= 0:
        return 128
    weight_background = np.cumsum(histogram)
    weight_foreground = total - weight_background
    levels = np.arange(256, dtype=np.float64)
    sum_background = np.cumsum(histogram * levels)
    sum_total = sum_background[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        mean_background = sum_background / np.maximum(weight_background, 1)
        mean_foreground = (sum_total - sum_background) / np.maximum(
            weight_foreground, 1
        )
    variance = (
        weight_background
        * weight_foreground
        * (mean_background - mean_foreground) ** 2
    )
    variance[~np.isfinite(variance)] = 0.0
    return int(np.argmax(variance))


def to_silhouette(data):
    """Convert image bytes into a trimmed black-on-white silhouette image.

    Only images with a clean, light background and one dominant subject get
    through: labels, rulers, dust, other specimens and photographs of scenes
    are rejected here rather than shipped as bad motifs.
    """
    import numpy as np
    from PIL import Image

    image = Image.open(io.BytesIO(data))
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        canvas = Image.new("RGBA", image.size, (255, 255, 255, 255))
        canvas.alpha_composite(image)
        image = canvas.convert("L")
    else:
        image = image.convert("L")
    if max(image.size) > 1600:
        scale = 1600 / max(image.size)
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.LANCZOS,
        )
    if min(image.size) < 200:
        return None

    width, height = image.size
    pixels = np.asarray(image, dtype=np.uint8)
    border = np.concatenate(
        [pixels[0, :], pixels[-1, :], pixels[:, 0], pixels[:, -1]]
    )
    if border.mean() < 200 or border.std() > 42:
        # Not a clean, light backdrop: a photograph of a scene, a shadowed
        # sheet, an inverted drawing. Skip rather than guess.
        return None

    threshold = _otsu_threshold(image)
    if threshold < 20 or threshold > 235:
        return None
    subject = pixels < threshold
    fraction = subject.mean()
    if fraction < 0.02 or fraction > 0.80:
        return None

    # Keep only the biggest connected shape. Everything else - labels, rules,
    # dust, a second specimen - is dropped.
    labels, areas = _label_components(subject)
    if not areas:
        return None
    largest = max(areas, key=areas.get)
    if areas[largest] < 0.55 * subject.sum():
        return None
    keep = labels == largest
    if keep.sum() < 0.02 * keep.size:
        return None
    rows = np.any(keep, axis=1)
    cols = np.any(keep, axis=0)
    top, bottom = int(np.argmax(rows)), int(len(rows) - np.argmax(rows[::-1]))
    left, right = int(np.argmax(cols)), int(len(cols) - np.argmax(cols[::-1]))
    if min(bottom - top, right - left) < 60:
        return None
    if max(bottom - top, right - left) < 0.14 * max(width, height):
        return None

    cropped = Image.fromarray(np.where(keep, 0, 255).astype(np.uint8), "L")
    cropped = cropped.crop((left, top, right, bottom))

    # Fit into a square with a margin, keeping the subject's proportions.
    inner = OUTPUT_PIXELS - 2 * MARGIN
    scale = min(inner / cropped.width, inner / cropped.height)
    target = (
        max(1, int(round(cropped.width * scale))),
        max(1, int(round(cropped.height * scale))),
    )
    cropped = cropped.resize(target, Image.LANCZOS)
    cropped = cropped.point(lambda value: 255 if value < 128 else 0, "L")
    canvas = Image.new("L", (OUTPUT_PIXELS, OUTPUT_PIXELS), 0)
    canvas.paste(
        cropped,
        ((OUTPUT_PIXELS - target[0]) // 2, (OUTPUT_PIXELS - target[1]) // 2),
    )
    return canvas.convert("1")


def _label_components(mask, max_side=480):
    """Label 4-connected components of a boolean mask.

    Returns ``(labels, areas)`` where labels is an int array the size of the
    mask and areas maps label -> pixel count. The mask is analysed at a reduced
    size, which is enough to spot a label or a second specimen.
    """
    import numpy as np
    from collections import deque

    height, width = mask.shape
    step = max(1, int(max(height, width) / max_side))
    small = mask[::step, ::step]
    labels = np.zeros(small.shape, dtype=np.int32)
    areas = {}
    current = 0
    rows, cols = small.shape
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
            areas[current] = count
    if step > 1:
        expanded = np.zeros(mask.shape, dtype=np.int32)
        for y in range(rows):
            for x in range(cols):
                if labels[y, x]:
                    expanded[
                        y * step : min((y + 1) * step, height),
                        x * step : min((x + 1) * step, width),
                    ] = labels[y, x]
        labels = expanded
        areas = {key: value * step * step for key, value in areas.items()}
    return labels, areas


def safe_name(title):
    name = title[5:] if title.startswith("File:") else title
    name = re.sub(r"\.(png|jpe?g|gif|tif?f|webp|svg)$", "", name, flags=re.I)
    name = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return name[:52] or "motif"


def fetch(url):
    global _LAST_DOWNLOAD
    for attempt in range(5):
        wait = 1.2 - (time.time() - _LAST_DOWNLOAD)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                _LAST_DOWNLOAD = time.time()
                return response.read()
        except Exception:
            _LAST_DOWNLOAD = time.time()
            if attempt == 4:
                raise
            time.sleep(6.0 * (attempt + 1))
    raise RuntimeError("unreachable")


_LAST_DOWNLOAD = 0.0


def _safe(text):
    """Console-safe text: the Windows console is not always UTF-8."""
    try:
        text.encode("cp1252")
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", "replace").decode("ascii")


def build(out_dir, limit, searches=None, max_candidates=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    global SEARCHES
    if searches:
        SEARCHES = tuple(searches)

    info = gather(limit)
    print("%d freely licensed candidates" % len(info), flush=True)

    saved = []
    budget = max_candidates or limit * 3
    for index, (title, meta) in enumerate(info.items()):
        if len(saved) >= limit:
            break
        if index >= budget:
            print("  stopped after %d candidates" % budget, flush=True)
            break
        try:
            data = fetch(meta["url"])
        except Exception as exc:
            print("  skip %s (%s)" % (_safe(title), _safe(str(exc))[:90]), flush=True)
            continue
        try:
            image = to_silhouette(data)
        except Exception as exc:
            print("  skip %s (convert: %s)" % (_safe(title), _safe(str(exc))[:90]), flush=True)
            continue
        if image is None:
            continue
        name = "%03d-%s.png" % (len(saved) + 1, safe_name(title))
        path = out_dir / name
        image.save(path, optimize=True)
        saved.append(
            {
                "file": name,
                "title": title,
                "artist": meta["artist"],
                "licence": meta["licence"],
                "source": meta["descriptionurl"] or meta["url"],
            }
        )
        print("  %3d saved %s" % (len(saved), name), flush=True)

    (out_dir / "manifest.json").write_text(
        json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Motif credits",
        "",
        "Downloaded from Wikimedia Commons and converted to black-on-white",
        "silhouettes by `tools/fetch_nature_motifs.py`.",
        "",
        "| File | Source | Author | Licence |",
        "| --- | --- | --- | --- |",
    ]
    for row in saved:
        lines.append(
            "| %s | [%s](%s) | %s | %s |"
            % (
                row["file"],
                row["title"],
                row["source"],
                row["artist"] or "unknown",
                row["licence"],
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
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="give up after this many downloaded candidates (default 3x limit)",
    )
    parser.add_argument(
        "--search",
        action="append",
        default=None,
        help="extra search term; repeatable (replaces the built-in list)",
    )
    args = parser.parse_args()
    saved = build(args.out, args.limit, args.search, args.max_candidates)
    print("saved %d motifs to %s" % (len(saved), args.out))


if __name__ == "__main__":
    main()
