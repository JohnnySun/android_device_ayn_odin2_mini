#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import xml.etree.ElementTree as ET
from pathlib import Path
import unittest


DEVICE_ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = "overlay/lineage-sdk/lineage/res/res/values/config.xml"
DEFAULTS = (
    "overlay/lineage-sdk/packages/LineageSettingsProvider/"
    "res/values/defaults.xml"
)


def integer_resource(relative_path, name):
    root = ET.parse(DEVICE_ROOT / relative_path).getroot()
    for element in root.findall("integer"):
        if element.get("name") == name:
            return int((element.text or "").strip())
    return None


class BatteryLightOverlayTest(unittest.TestCase):
    def test_declares_rgb_battery_light_with_software_brightness(self):
        capabilities = integer_resource(
            CAPABILITIES, "config_deviceLightCapabilities"
        )

        self.assertEqual(66, capabilities)
        self.assertNotEqual(0, capabilities & 2, "RGB battery LED is required")
        self.assertNotEqual(0, capabilities & 64, "battery LED is required")
        self.assertEqual(
            0,
            capabilities & 128,
            "stock QTI HAL alpha-channel brightness is not proven",
        )

    def test_brightness_defaults_preserve_the_framework_color_cap(self):
        normal = integer_resource(DEFAULTS, "def_battery_brightness_level")
        zen = integer_resource(DEFAULTS, "def_battery_brightness_level_zen")

        self.assertEqual(255, normal)
        self.assertEqual(255, zen)
        self.assertGreaterEqual(normal, 1)
        self.assertLessEqual(normal, 255)


if __name__ == "__main__":
    unittest.main()
