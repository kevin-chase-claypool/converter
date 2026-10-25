"""ioSender App.config backup and restore utilities."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which("powershell.exe")
VALID_CONFIG = """<?xml version="1.0"?>
<Config>
  <PortParams>10.10.10.2:23</PortParams>
  <Macros>
    <Macro>
      <Id>1</Id>
      <Name>HOME + REGISTER</Name>
      <ConfirmOnExecute>true</ConfirmOnExecute>
      <Code>G65 P113</Code>
    </Macro>
    <Macro>
      <Id>2</Id>
      <Name>PEN UP + PARK</Name>
      <ConfirmOnExecute>true</ConfirmOnExecute>
      <Code>G65 P116</Code>
    </Macro>
  </Macros>
</Config>
"""


@unittest.skipUnless(
    os.name == "nt" and POWERSHELL,
    "ioSender backup scripts require Windows PowerShell",
)
class IoSenderConfigBackupTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix="iosender-backup-test-")
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def run_script(self, name, *arguments):
        return subprocess.run(
            [
                POWERSHELL,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "tools" / name),
                *map(str, arguments),
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_committed_recovery_snapshot_contains_operator_macros(self):
        config = ET.parse(ROOT / "config" / "iosender" / "ioSender-App.config")
        macros = {
            element.findtext("Name"): element.findtext("Code")
            for element in config.findall("./Macros/Macro")
        }
        self.assertEqual(macros["HOME + REGISTER"], "G65 P113")
        self.assertEqual(macros["PEN UP + PARK"], "G65 P116")
        manifest = (
            ROOT
            / "firmware"
            / "grblhal"
            / "macros"
            / "controller-manifest-2026-10-25.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("2543", manifest)
        self.assertIn("P116.macro", manifest)

    def test_valid_config_is_backed_up_with_macro_count(self):
        source = self.root / "App.config"
        source.write_text(VALID_CONFIG, encoding="utf-8")
        (self.root / "settings.txt").write_text(
            "%\n$100=80.000\n%\n",
            encoding="utf-8",
        )
        (self.root / "offsets.nc").write_text(
            "%\nG90G10L2P1X0Y0Z0A0\n%\n",
            encoding="utf-8",
        )
        backup_dir = self.root / "backups"

        result = self.run_script(
            "backup_iosender_config.ps1",
            "-Source",
            source,
            "-BackupDirs",
            backup_dir,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        latest = backup_dir / "ioSender-App.config.latest"
        self.assertEqual(latest.read_text(encoding="utf-8"), VALID_CONFIG)
        manifest = (backup_dir / "ioSender-App.config.latest.json").read_text(
            encoding="utf-8-sig"
        )
        self.assertEqual(json.loads(manifest)["macro_count"], 2)
        self.assertTrue((backup_dir / "grblhal-settings.latest.txt").exists())
        self.assertTrue((backup_dir / "grblhal-offsets.latest.nc").exists())

    def test_invalid_source_does_not_replace_last_good_backup(self):
        source = self.root / "App.config"
        source.write_bytes(b"")
        backup_dir = self.root / "backups"
        backup_dir.mkdir()
        latest = backup_dir / "ioSender-App.config.latest"
        latest.write_text(VALID_CONFIG, encoding="utf-8")

        result = self.run_script(
            "backup_iosender_config.ps1",
            "-Source",
            source,
            "-BackupDirs",
            backup_dir,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(latest.read_text(encoding="utf-8"), VALID_CONFIG)

    def test_restore_preserves_existing_target(self):
        backup = self.root / "backup.config"
        backup.write_text(VALID_CONFIG, encoding="utf-8")
        target = self.root / "App.config"
        target.write_text("<Config><Macros /></Config>", encoding="utf-8")

        result = self.run_script(
            "restore_iosender_config.ps1",
            "-Backup",
            backup,
            "-Target",
            target,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), VALID_CONFIG)
        preserved = list(self.root.glob("App.config.before-restore-*"))
        self.assertEqual(len(preserved), 1)
        self.assertIn("<Macros />", preserved[0].read_text(encoding="utf-8"))

    def test_startup_backup_can_be_installed_and_removed(self):
        startup = self.root / "Startup"
        startup.mkdir()
        installer = "install_iosender_config_backup_startup.ps1"

        result = self.run_script(installer, "-StartupDir", startup)
        self.assertEqual(result.returncode, 0, result.stderr)
        launcher = startup / "ioSender Config Backup.cmd"
        self.assertTrue(launcher.exists())
        self.assertIn(
            "backup_iosender_config.ps1",
            launcher.read_text(encoding="ascii"),
        )

        result = self.run_script(
            installer,
            "-StartupDir",
            startup,
            "-Remove",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(launcher.exists())


if __name__ == "__main__":
    unittest.main()
