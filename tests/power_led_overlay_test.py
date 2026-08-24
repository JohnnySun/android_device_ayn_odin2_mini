#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


DEVICE_ROOT = Path(__file__).resolve().parents[1]
OVERLAY_CONFIG = Path("overlay/frameworks/base/core/res/res/values/config.xml")
EXPECTED_COLORS = {
    "config_notificationsBatteryLowARGB": 0xFF080000,
    "config_notificationsBatteryMediumARGB": 0xFF080800,
    "config_notificationsBatteryFullARGB": 0xFF000800,
}
EXPECTED_BRIGHTNESS_CAP = 1


def make_values(text, variable):
    values = []
    lines = iter(text.splitlines())
    for line in lines:
        match = re.match(rf"^{re.escape(variable)}\s*\+=\s*(.*)$", line)
        if not match:
            continue
        remainder = match.group(1)
        while True:
            continued = remainder.rstrip().endswith("\\")
            values.extend(remainder.replace("\\", "").split())
            if not continued:
                break
            remainder = next(lines, "")
    return values


class PowerLedOverlayTest(unittest.TestCase):
    def test_overrides_exact_battery_led_colors(self):
        root = ET.parse(DEVICE_ROOT / OVERLAY_CONFIG).getroot()
        self.assertEqual("resources", root.tag)

        integers = [
            item
            for item in root.findall("integer")
            if item.get("name") in EXPECTED_COLORS
        ]
        names = [item.get("name") for item in integers]
        self.assertEqual(set(EXPECTED_COLORS), set(names))
        self.assertEqual(len(names), len(set(names)))

        actual = {item.get("name"): int(item.text, 0) for item in integers}
        self.assertEqual(EXPECTED_COLORS, actual)

    def test_caps_indicator_light_brightness(self):
        root = ET.parse(DEVICE_ROOT / OVERLAY_CONFIG).getroot()
        caps = root.findall("integer[@name='config_indicatorLightBrightnessCap']")

        self.assertEqual(1, len(caps))
        self.assertEqual(EXPECTED_BRIGHTNESS_CAP, int(caps[0].text, 0))

    def test_color_channels_never_use_full_intensity(self):
        root = ET.parse(DEVICE_ROOT / OVERLAY_CONFIG).getroot()
        for item in root.findall("integer"):
            if item.get("name") not in EXPECTED_COLORS:
                continue
            color = int(item.text, 0)
            channels = ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)
            self.assertNotIn(0xFF, channels, item.get("name"))
            self.assertLessEqual(max(channels), 0x08, item.get("name"))

    def test_device_mk_mounts_the_overlay_root(self):
        device_mk = (DEVICE_ROOT / "device.mk").read_text()
        overlays = make_values(device_mk, "DEVICE_PACKAGE_OVERLAYS")
        self.assertEqual(1, overlays.count("$(DEVICE_PATH)/overlay"))

    def test_production_files_do_not_bypass_battery_service(self):
        production_files = [DEVICE_ROOT / OVERLAY_CONFIG, DEVICE_ROOT / "device.mk"]
        for path in production_files:
            text = path.read_text()
            self.assertNotIn("/sys/class/leds", text, str(path))
            self.assertNotIn("sn3112", text.lower(), str(path))


if __name__ == "__main__":
    unittest.main()
