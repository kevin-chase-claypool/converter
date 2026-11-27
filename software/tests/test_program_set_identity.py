"""Cross-program identity checks for multi-ink G-code sets."""

import dataclasses
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


class ProgramSetIdentityTests(unittest.TestCase):
    def programs(self):
        settings = dataclasses.replace(
            converter.default_settings(),
            theta_mode="fixed",
            flip_y=False,
            frame_center_mm=(0.0, 0.0),
        )
        contours = [[(-20.0, 0.0), (20.0, 0.0)]]
        return {
            channel: converter.contours_to_gcode(contours, settings)
            for channel in converter.CHANNELS
        }

    def test_matching_program_set_identity_is_accepted(self):
        programs = self.programs()

        identity = converter.validate_program_set_identity(programs)

        self.assertEqual(identity["frame_center_mm"], (0.0, 0.0))
        self.assertEqual(identity["profile_fingerprint"], "f85ec410dbac")
        self.assertEqual(identity["machine_reach_radius_mm"], 180.0)
        self.assertEqual(identity["final_scale"], 1.0)
        self.assertEqual(
            identity["a_schedule_identity"],
            "per-contour",
        )

    def test_mismatched_frame_or_profile_is_rejected(self):
        programs = self.programs()
        programs["m"] = programs["m"].replace(
            "(frame center 0.000,0.000 mm",
            "(frame center 0.500,0.000 mm",
        )
        with self.assertRaisesRegex(ValueError, "frame center"):
            converter.validate_program_set_identity(programs)

        programs = self.programs()
        programs["k"] = programs["k"].replace(
            "f85ec410dbac",
            "deadbeefcafe",
        )
        with self.assertRaisesRegex(ValueError, "profile fingerprint"):
            converter.validate_program_set_identity(programs)

    def test_profile_must_match_the_configured_selection(self):
        with self.assertRaisesRegex(ValueError, "configured deadbeefcafe"):
            converter.validate_program_set_identity(
                self.programs(),
                expected_profile_fingerprint="deadbeefcafe",
            )

    def test_final_scale_and_a_schedule_identity_must_match(self):
        programs = self.programs()
        programs["y"] = programs["y"].replace(
            "(program scale 1.000000000, A schedule per-contour)",
            "(program scale 1.001000000, A schedule per-contour)",
        )
        with self.assertRaisesRegex(ValueError, "final scale"):
            converter.validate_program_set_identity(programs)

        programs = self.programs()
        programs["k"] = programs["k"].replace(
            "A schedule per-contour",
            "A schedule different-schedule",
        )
        with self.assertRaisesRegex(ValueError, "A schedule"):
            converter.validate_program_set_identity(programs)

    def test_expected_row_angles_are_checked_per_ink(self):
        settings = dataclasses.replace(
            converter.default_settings(),
            theta_mode="fixed",
            flip_y=False,
            frame_center_mm=(0.0, 0.0),
            row_locked_compensation=True,
        )
        profile = converter.load_bed_compensation(
            settings.bed_compensation_path
        )
        row_lock_set = converter.row_locked_bed_compensation_set(
            profile,
            tuple(converter.SCREEN_ANGLES_DEG.values()),
            along_samples=41,
            across_samples=21,
        )
        contours = [[(-20.0, 0.0), (20.0, 0.0)]]
        programs = {}
        for channel, angle in converter.SCREEN_ANGLES_DEG.items():
            channel_settings = dataclasses.replace(
                settings,
                row_lock_screen_angle_deg=angle,
                row_lock_projection=row_lock_set.for_screen_angle(angle),
            )
            programs[channel] = converter.contours_to_gcode(
                contours,
                channel_settings,
            )

        identity = converter.validate_program_set_identity(
            programs,
            expected_row_angles=converter.SCREEN_ANGLES_DEG,
        )

        self.assertEqual(identity["profile_fingerprint"], "f85ec410dbac")
        self.assertEqual(
            {
                channel: identity["row_angles_deg"][channel]
                for channel in converter.CHANNELS
            },
            converter.SCREEN_ANGLES_DEG,
        )

        programs["m"] = programs["m"].replace(
            "at row angle 75.000 deg",
            "at row angle 45.000 deg",
        )
        with self.assertRaisesRegex(ValueError, "row angle"):
            converter.validate_program_set_identity(
                programs,
                expected_row_angles=converter.SCREEN_ANGLES_DEG,
            )


if __name__ == "__main__":
    unittest.main()
