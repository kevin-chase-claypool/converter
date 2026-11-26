"""Transactional multi-program publishing."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from program_set_export import (  # noqa: E402
    ProgramSetExportError,
    program_set_paths,
    write_file_set_transaction,
)


class ProgramSetExportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(
            prefix="program-set-export-"
        )
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def test_commits_every_program_and_manifest_together(self):
        base = self.root / "portrait-cmyk.gcode"
        programs = program_set_paths(base, ("01-yellow", "02-black"))
        manifest = self.root / "portrait-cmyk-set.json"

        written = write_file_set_transaction(
            [
                (programs[0], "G1 X0 Y0\n"),
                (programs[1], "G1 X1 Y0\n"),
                (manifest, '{"kind":"cmyk-print-set"}\n'),
            ]
        )

        self.assertEqual(written, programs + [manifest])
        self.assertEqual(programs[0].read_text(encoding="utf-8"), "G1 X0 Y0\n")
        self.assertEqual(programs[1].read_text(encoding="utf-8"), "G1 X1 Y0\n")
        self.assertIn("cmyk-print-set", manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            list(self.root.glob(".*.tmp")),
            [],
        )
        self.assertEqual(
            list(self.root.glob(".*.backup")),
            [],
        )

    def test_staging_failure_leaves_existing_set_untouched(self):
        first = self.root / "first.gcode"
        second = self.root / "second.gcode"
        first.write_text("old first\n", encoding="utf-8")
        second.write_text("old second\n", encoding="utf-8")
        real_stage = __import__("program_set_export")._stage_file
        calls = 0

        def fail_second_stage(path, payload):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("disk full")
            return real_stage(path, payload)

        with (
            mock.patch(
                "program_set_export._stage_file",
                side_effect=fail_second_stage,
            ),
            self.assertRaises(ProgramSetExportError),
        ):
            write_file_set_transaction(
                [(first, "new first\n"), (second, "new second\n")]
            )

        self.assertEqual(first.read_text(encoding="utf-8"), "old first\n")
        self.assertEqual(second.read_text(encoding="utf-8"), "old second\n")
        self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_commit_failure_restores_every_previous_file(self):
        first = self.root / "first.gcode"
        second = self.root / "second.gcode"
        first.write_text("old first\n", encoding="utf-8")
        second.write_text("old second\n", encoding="utf-8")
        real_replace = os.replace

        def fail_second_publish(source, target):
            source_path = Path(source)
            target_path = Path(target)
            if (
                target_path.name == "second.gcode"
                and source_path.suffix == ".tmp"
            ):
                raise OSError("publish denied")
            return real_replace(source, target)

        with (
            mock.patch(
                "program_set_export.os.replace",
                side_effect=fail_second_publish,
            ),
            self.assertRaises(ProgramSetExportError),
        ):
            write_file_set_transaction(
                [(first, "new first\n"), (second, "new second\n")]
            )

        self.assertEqual(first.read_text(encoding="utf-8"), "old first\n")
        self.assertEqual(second.read_text(encoding="utf-8"), "old second\n")
        self.assertEqual(list(self.root.glob(".*.tmp")), [])
        self.assertEqual(list(self.root.glob(".*.backup")), [])

    def test_duplicate_or_unsafe_program_labels_are_rejected(self):
        with self.assertRaises(ValueError):
            program_set_paths(
                self.root / "art.gcode",
                ("yellow", "yellow"),
            )
        with self.assertRaises(ValueError):
            program_set_paths(
                self.root / "art.gcode",
                ("../yellow",),
            )


if __name__ == "__main__":
    unittest.main()
