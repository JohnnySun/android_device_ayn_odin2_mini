#!/usr/bin/env python3

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BootWatchdogTest(unittest.TestCase):
    def test_watchdog_is_static_and_packaged(self):
        blueprint = (ROOT / "early_trace" / "Android.bp").read_text()
        product = (ROOT / "lineage_odin2_mini.mk").read_text()

        self.assertIn('name: "odin_boot_watchdog"', blueprint)
        self.assertIn('static_executable: true', blueprint)
        self.assertIn("odin_boot_watchdog", product)

    def test_watchdog_starts_after_metadata_and_disarms_only_on_completed_boot(self):
        rc = (ROOT / "early_trace" / "odin-early-trace.rc").read_text()

        self.assertIn("service odin_boot_watchdog /system/bin/odin_boot_watchdog", rc)
        self.assertRegex(
            rc,
            r"on post-fs-data[\s\S]*start odin_boot_watchdog",
        )
        self.assertRegex(
            rc,
            r"on property:sys\.boot_completed=1[\s\S]*stop odin_boot_watchdog",
        )

    def test_watchdog_has_bounded_bootloader_recovery(self):
        source = (ROOT / "early_trace" / "odin_boot_watchdog.c").read_text()

        self.assertIn("#define TIMEOUT_SECONDS 180", source)
        self.assertIn("CLOCK_BOOTTIME", source)
        self.assertIn('LINUX_REBOOT_CMD_RESTART2, "bootloader"', source)
        self.assertIn("LINUX_REBOOT_CMD_RESTART", source)
        self.assertIn("/metadata/odin-boot-watchdog.log", source)


if __name__ == "__main__":
    unittest.main()
