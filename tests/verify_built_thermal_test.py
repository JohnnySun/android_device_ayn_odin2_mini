#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


DEVICE_ROOT = Path(__file__).resolve().parents[1]
VERIFIER = DEVICE_ROOT / "tools/verify-built-thermal.py"


VALID_RC = """\
service vendor.thermal-hal /vendor/bin/hw/android.hardware.thermal-service.qti
    interface aidl android.hardware.thermal.IThermal/default
    class hal

on boot
    restart vendor.thermal-hal
"""

VALID_MANIFEST = """\
<manifest version="2.0" type="device">
    <hal format="aidl">
        <name>android.hardware.thermal</name>
        <version>2</version>
        <fqname>IThermal/default</fqname>
    </hal>
</manifest>
"""

HIDL_RC = """\
service vendor.thermal-hal-2-0 /vendor/bin/hw/android.hardware.thermal@2.0-service.qti
    interface android.hardware.thermal@2.0::IThermal default
"""

HIDL_MANIFEST = """\
<manifest version="1.0" type="device">
    <hal format="hidl">
        <name>android.hardware.thermal</name>
        <transport>hwbinder</transport>
        <version>2.0</version>
        <interface>
            <name>IThermal</name>
            <instance>default</instance>
        </interface>
    </hal>
</manifest>
"""


class VerifyBuiltThermalTest(unittest.TestCase):
    def make_product_out(self):
        temporary = tempfile.TemporaryDirectory()
        product_out = Path(temporary.name)
        files = {
            "vendor/bin/hw/android.hardware.thermal-service.qti": "",
            "vendor/etc/init/android.hardware.thermal-service.qti.rc": VALID_RC,
            "vendor/etc/vintf/manifest/android.hardware.thermal-service.qti.xml": (
                VALID_MANIFEST
            ),
        }
        for relative, contents in files.items():
            path = product_out / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
        return temporary, product_out

    def run_verifier(self, product_out):
        return subprocess.run(
            [sys.executable, str(VERIFIER), str(product_out)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_accepts_aidl_v2_built_product(self):
        temporary, product_out = self.make_product_out()
        self.addCleanup(temporary.cleanup)

        result = self.run_verifier(product_out)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("built thermal verification: PASS", result.stdout)

    def test_does_not_modify_product_out(self):
        temporary, product_out = self.make_product_out()
        self.addCleanup(temporary.cleanup)
        before = {
            path.relative_to(product_out): path.read_bytes()
            for path in product_out.rglob("*")
            if path.is_file()
        }

        result = self.run_verifier(product_out)

        after = {
            path.relative_to(product_out): path.read_bytes()
            for path in product_out.rglob("*")
            if path.is_file()
        }
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(after, before)

    def test_rejects_each_missing_required_file(self):
        required = (
            "vendor/bin/hw/android.hardware.thermal-service.qti",
            "vendor/etc/init/android.hardware.thermal-service.qti.rc",
            "vendor/etc/vintf/manifest/android.hardware.thermal-service.qti.xml",
        )
        for missing in required:
            with self.subTest(missing=missing):
                temporary, product_out = self.make_product_out()
                try:
                    (product_out / missing).unlink()
                    result = self.run_verifier(product_out)
                finally:
                    temporary.cleanup()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(missing, result.stderr)

    def test_rejects_restart_target_that_differs_from_service(self):
        temporary, product_out = self.make_product_out()
        self.addCleanup(temporary.cleanup)
        rc = product_out / "vendor/etc/init/android.hardware.thermal-service.qti.rc"
        rc.write_text(VALID_RC.replace(
            "restart vendor.thermal-hal", "restart vendor.wrong-thermal-hal"
        ))

        result = self.run_verifier(product_out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("restart vendor.thermal-hal", result.stderr)

    def test_rejects_wrong_required_rc_contract(self):
        replacements = {
            "service": (
                "service vendor.thermal-hal",
                "service vendor.wrong-thermal-hal",
            ),
            "executable": (
                "/vendor/bin/hw/android.hardware.thermal-service.qti",
                "/vendor/bin/hw/android.hardware.thermal-service.wrong",
            ),
            "interface": (
                "android.hardware.thermal.IThermal/default",
                "android.hardware.thermal.IThermal/secondary",
            ),
        }
        for field, (old, new) in replacements.items():
            with self.subTest(field=field):
                temporary, product_out = self.make_product_out()
                try:
                    rc = product_out / (
                        "vendor/etc/init/android.hardware.thermal-service.qti.rc"
                    )
                    rc.write_text(VALID_RC.replace(old, new, 1))
                    result = self.run_verifier(product_out)
                finally:
                    temporary.cleanup()

                self.assertNotEqual(result.returncode, 0)

    def test_rejects_restart_outside_boot_action(self):
        temporary, product_out = self.make_product_out()
        self.addCleanup(temporary.cleanup)
        rc = product_out / "vendor/etc/init/android.hardware.thermal-service.qti.rc"
        rc.write_text(VALID_RC.replace("on boot", "on property:sys.boot_completed=1"))

        result = self.run_verifier(product_out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("under 'on boot'", result.stderr)

    def test_rejects_each_stock_hidl_artifact_alongside_aidl(self):
        artifacts = {
            "vendor/bin/hw/android.hardware.thermal@2.0-service.qti": "",
            "vendor/etc/init/android.hardware.thermal@2.0-service.qti.rc": HIDL_RC,
            "vendor/etc/vintf/manifest/android.hardware.thermal@2.0-service.qti.xml": (
                HIDL_MANIFEST
            ),
            "vendor/lib64/android.hardware.thermal@2.0-impl.so": "",
        }
        for relative, contents in artifacts.items():
            with self.subTest(relative=relative):
                temporary, product_out = self.make_product_out()
                try:
                    path = product_out / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(contents)
                    result = self.run_verifier(product_out)
                finally:
                    temporary.cleanup()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("HIDL", result.stderr)

    def test_rejects_duplicate_aidl_thermal_provider(self):
        temporary, product_out = self.make_product_out()
        self.addCleanup(temporary.cleanup)
        duplicate = product_out / "vendor/etc/vintf/manifest/duplicate-thermal.xml"
        duplicate.write_text(VALID_MANIFEST)

        result = self.run_verifier(product_out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one thermal HAL provider", result.stderr)

    def test_rejects_duplicate_aidl_binary_or_init_provider(self):
        artifacts = {
            "vendor/bin/hw/android.hardware.thermal-service.other": "",
            "vendor/etc/init/duplicate-thermal.rc": (
                "service vendor.thermal-hal-other "
                "/vendor/bin/hw/android.hardware.thermal-service.other\n"
            ),
        }
        for relative, contents in artifacts.items():
            with self.subTest(relative=relative):
                temporary, product_out = self.make_product_out()
                try:
                    path = product_out / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(contents)
                    result = self.run_verifier(product_out)
                finally:
                    temporary.cleanup()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("duplicate", result.stderr)

    def test_rejects_malformed_vintf_xml(self):
        temporary, product_out = self.make_product_out()
        self.addCleanup(temporary.cleanup)
        manifest = product_out / (
            "vendor/etc/vintf/manifest/android.hardware.thermal-service.qti.xml"
        )
        manifest.write_text("<manifest><hal></manifest>")

        result = self.run_verifier(product_out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot parse VINTF manifest", result.stderr)

    def test_rejects_invalid_vintf_root(self):
        temporary, product_out = self.make_product_out()
        self.addCleanup(temporary.cleanup)
        manifest = product_out / (
            "vendor/etc/vintf/manifest/android.hardware.thermal-service.qti.xml"
        )
        manifest.write_text(VALID_MANIFEST.replace("manifest", "not-manifest"))

        result = self.run_verifier(product_out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid VINTF manifest root", result.stderr)

    def test_rejects_malformed_thermal_hal_name_list(self):
        temporary, product_out = self.make_product_out()
        self.addCleanup(temporary.cleanup)
        manifest = product_out / (
            "vendor/etc/vintf/manifest/android.hardware.thermal-service.qti.xml"
        )
        manifest.write_text(VALID_MANIFEST.replace(
            "<name>android.hardware.thermal</name>",
            "<name>unrelated.hal</name><name>android.hardware.thermal</name>",
        ))

        result = self.run_verifier(product_out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected exactly one name", result.stderr)

    def test_rejects_wrong_aidl_provider_contract(self):
        replacements = {
            "format": ('format="aidl"', 'format="hidl"'),
            "version": ("<version>2</version>", "<version>1</version>"),
            "instance": (
                "<fqname>IThermal/default</fqname>",
                "<fqname>IThermal/secondary</fqname>",
            ),
        }
        for field, (old, new) in replacements.items():
            with self.subTest(field=field):
                temporary, product_out = self.make_product_out()
                try:
                    manifest = product_out / (
                        "vendor/etc/vintf/manifest/"
                        "android.hardware.thermal-service.qti.xml"
                    )
                    manifest.write_text(VALID_MANIFEST.replace(old, new))
                    result = self.run_verifier(product_out)
                finally:
                    temporary.cleanup()

                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
