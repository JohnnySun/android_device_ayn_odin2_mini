#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


DEVICE_ROOT = Path(__file__).resolve().parents[1]
FEATURE_XML = "permissions/odin2_mini_unavailable_features.xml"
SYSTEM_FEATURE_XML = (
    "$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/"
    "odin2_mini_unavailable_features.xml"
)

EXPECTED_UNAVAILABLE_FEATURES = {
    "android.hardware.camera",
    "android.hardware.camera.any",
    "android.hardware.camera.autofocus",
    "android.hardware.camera.capability.manual_post_processing",
    "android.hardware.camera.capability.manual_sensor",
    "android.hardware.camera.capability.raw",
    "android.hardware.camera.concurrent",
    "android.hardware.camera.flash",
    "android.hardware.camera.front",
    "android.hardware.camera.level.full",
    "android.hardware.location.gps",
    "android.hardware.nfc",
    "android.hardware.nfc.any",
    "android.hardware.nfc.ese",
    "android.hardware.nfc.hce",
    "android.hardware.nfc.hcef",
    "android.hardware.nfc.uicc",
    "android.hardware.se.omapi.ese",
    "android.hardware.se.omapi.uicc",
    "android.hardware.sensor.ambient_temperature",
    "android.hardware.sensor.barometer",
    "android.hardware.sensor.dynamic.head_tracker",
    "android.hardware.sensor.light",
    "android.hardware.sensor.proximity",
    "android.hardware.sensor.relative_humidity",
    "android.hardware.telephony",
    "android.hardware.telephony.calling",
    "android.hardware.telephony.cdma",
    "android.hardware.telephony.data",
    "android.hardware.telephony.gsm",
    "android.hardware.telephony.ims",
    "android.hardware.telephony.mbms",
    "android.hardware.telephony.messaging",
    "android.hardware.telephony.radio.access",
    "android.hardware.telephony.subscription",
    "com.android.se",
    "com.nxp.mifare",
}


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


class UnavailableFeaturesTest(unittest.TestCase):
    def test_masks_exactly_the_unsupported_stock_vendor_features(self):
        root = ET.parse(DEVICE_ROOT / FEATURE_XML).getroot()
        self.assertEqual("permissions", root.tag)
        self.assertTrue(all(child.tag == "unavailable-feature" for child in root))

        unavailable_features = [child.get("name") for child in root]
        self.assertNotIn(None, unavailable_features)
        self.assertEqual(len(unavailable_features), len(set(unavailable_features)))
        self.assertEqual(EXPECTED_UNAVAILABLE_FEATURES, set(unavailable_features))

        device_mk = (DEVICE_ROOT / "device.mk").read_text()
        copies = make_values(device_mk, "PRODUCT_COPY_FILES")
        expected_copy = f"$(DEVICE_PATH)/{FEATURE_XML}:{SYSTEM_FEATURE_XML}"
        self.assertEqual(1, copies.count(expected_copy))


if __name__ == "__main__":
    unittest.main()
