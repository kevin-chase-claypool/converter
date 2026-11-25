"""Registered Y/M/C/K SVG export for Plotterfun Extended."""

import hashlib
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter
from generator_tabs._plotterfun_cmyk import (
    CmykSplitError,
    sanitize_base_name,
    split_cmyk_svg,
    write_cmyk_svg_set,
)


SVG_NS = "http://www.w3.org/2000/svg"


def _cmyk_svg(*, include_black=True):
    black = (
        '<g id="black"><path id="black-1" d="M 410,280 L 390,300" '
        'stroke="#000000" stroke-width="2" fill="none"/></g>'
        if include_black
        else ""
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="8in" '
        'height="6in" viewBox="0 0 800 600" style="background:#fff">'
        '<defs><clipPath id="crop"><rect width="800" height="600"/>'
        "</clipPath></defs>"
        '<g id="cyan" clip-path="url(#crop)">'
        '<path id="cyan-1" d="M 100,100 L 180,120" stroke="#00ffff" '
        'stroke-width="2" fill="none"/></g>'
        '<g id="magenta"><path id="magenta-1" d="M 200,140 L 280,180" '
        'stroke="#ff00ff" stroke-width="2" fill="none"/></g>'
        '<g id="yellow"><path id="yellow-1" d="M 300,220 L 380,240" '
        'stroke="#ffff00" stroke-width="2" fill="none"/></g>'
        f"{black}</svg>"
    )


def _groups(root):
    return {
        node.get("id"): node
        for node in root.iter()
        if node.tag == f"{{{SVG_NS}}}g" and node.get("id")
    }


class PlotterfunCmykSplitTests(unittest.TestCase):
    def test_base_name_removes_only_the_artwork_extension(self):
        self.assertEqual(
            sanitize_base_name(r"C:\art\portrait.v2.png"),
            "portrait.v2",
        )

    def test_split_preserves_page_and_keeps_only_one_ink_per_file(self):
        documents = split_cmyk_svg(_cmyk_svg())
        self.assertEqual(
            list(documents),
            ["yellow", "magenta", "cyan", "black"],
        )
        for ink, document in documents.items():
            root = ET.fromstring(document)
            self.assertEqual(root.get("width"), "8in")
            self.assertEqual(root.get("height"), "6in")
            self.assertEqual(root.get("viewBox"), "0 0 800 600")
            self.assertEqual(root.get("style"), "background:#fff")
            groups = _groups(root)
            self.assertIn(ink, groups)
            self.assertIn("crop", document)
            self.assertTrue(
                any(
                    node.get("id") == "crop"
                    and node.tag == f"{{{SVG_NS}}}clipPath"
                    for node in root.iter()
                )
            )
            registration = groups["theta-registration"]
            self.assertEqual(
                registration.get("data-theta-registration"),
                "true",
            )
            self.assertEqual(
                registration.get("data-theta-print-order"),
                str(
                    {
                        "yellow": 1,
                        "magenta": 2,
                        "cyan": 3,
                        "black": 4,
                    }[ink]
                ),
            )
            self.assertEqual(
                sum(
                    1
                    for child in registration
                    if child.tag == f"{{{SVG_NS}}}line"
                ),
                8,
            )
            channel_ids = {
                node.get("id")
                for node in groups.values()
                if node.get("id") in {"cyan", "magenta", "yellow", "black"}
            }
            self.assertEqual(channel_ids, {ink})

    def test_registration_makes_all_layer_bounds_identical(self):
        documents = split_cmyk_svg(_cmyk_svg())
        bounds = []
        with tempfile.TemporaryDirectory(prefix="plotterfun-bounds-") as folder:
            for index, document in enumerate(documents.values()):
                path = Path(folder) / f"{index}.svg"
                path.write_text(document, encoding="utf-8")
                contours = converter.parse_svg_geometry(
                    str(path),
                    0.01,
                    False,
                    expand_strokes=False,
                )
                bounds.append(converter.contour_bounds(contours))
        for observed in bounds[1:]:
            for got, expected in zip(observed, bounds[0]):
                self.assertAlmostEqual(got, expected, places=5)

    def test_missing_channel_becomes_registered_blank_layer(self):
        documents = split_cmyk_svg(_cmyk_svg(include_black=False))
        root = ET.fromstring(documents["black"])
        groups = _groups(root)
        self.assertNotIn("black", groups)
        self.assertIn("theta-registration", groups)

    def test_non_cmyk_svg_is_rejected_with_actionable_error(self):
        with self.assertRaisesRegex(CmykSplitError, "named CMYK"):
            split_cmyk_svg(
                '<svg xmlns="http://www.w3.org/2000/svg" width="8" '
                'height="6" viewBox="0 0 8 6">'
                '<path d="M0,0 L1,1"/></svg>'
            )

    def test_page_size_is_required(self):
        with self.assertRaisesRegex(CmykSplitError, "width, height"):
            split_cmyk_svg(
                '<svg xmlns="http://www.w3.org/2000/svg">'
                '<g id="yellow"><path d="M0,0 L1,1"/></g></svg>'
            )


class PlotterfunCmykWriteTests(unittest.TestCase):
    def test_writer_names_files_and_manifest_in_print_order(self):
        with tempfile.TemporaryDirectory(prefix="plotterfun-set-") as folder:
            exported = write_cmyk_svg_set(
                _cmyk_svg(),
                Path(folder),
                base_name="Golden Sunset",
                source_artwork=r"C:\art\Golden Sunset.png",
                algorithm="flowfield.js",
                created_utc="2026-11-25T12:00:00+00:00",
            )
            self.assertEqual(
                [layer.path.name for layer in exported.layers],
                [
                    "Golden Sunset-01-yellow.svg",
                    "Golden Sunset-02-magenta.svg",
                    "Golden Sunset-03-cyan.svg",
                    "Golden Sunset-04-black.svg",
                ],
            )
            self.assertEqual(
                [layer.order for layer in exported.layers],
                [1, 2, 3, 4],
            )
            self.assertEqual(
                [layer.ink for layer in exported.layers],
                ["yellow", "magenta", "cyan", "black"],
            )
            self.assertEqual(exported.missing_inks, ())
            manifest = json.loads(
                exported.manifest_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["kind"],
                "theta-plotterfun-cmyk-svg-set",
            )
            self.assertEqual(
                manifest["print_order"],
                ["yellow", "magenta", "cyan", "black"],
            )
            self.assertEqual(
                manifest["source_artwork"],
                r"C:\art\Golden Sunset.png",
            )
            self.assertEqual(manifest["algorithm"], "flowfield.js")
            self.assertIn("numeric order", manifest["print_instruction"])
            self.assertEqual(
                manifest["page"]["viewBox"],
                "0 0 800 600",
            )
            for layer, record in zip(exported.layers, manifest["layers"]):
                payload = layer.path.read_bytes()
                self.assertEqual(
                    record["sha256"],
                    hashlib.sha256(payload).hexdigest(),
                )
                self.assertEqual(record["file"], layer.path.name)
                self.assertEqual(record["order"], layer.order)
                self.assertEqual(record["ink"], layer.ink)
                self.assertEqual(record["drawing_elements"], 1)
                self.assertEqual(record["registration_elements"], 8)
                self.assertTrue(record["has_artwork"])

    def test_writer_reports_blank_missing_ink(self):
        with tempfile.TemporaryDirectory(prefix="plotterfun-empty-") as folder:
            exported = write_cmyk_svg_set(
                _cmyk_svg(include_black=False),
                Path(folder),
                base_name="portrait.png",
                created_utc="2026-11-25T12:00:00+00:00",
            )
        self.assertEqual(exported.missing_inks, ("Black",))
        black = next(layer for layer in exported.layers if layer.ink == "black")
        self.assertFalse(black.has_artwork)
        self.assertEqual(black.drawing_elements, 0)
        self.assertEqual(black.registration_elements, 8)


if __name__ == "__main__":
    unittest.main()
