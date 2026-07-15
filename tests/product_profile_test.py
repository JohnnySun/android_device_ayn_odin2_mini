#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import re
import unittest
from pathlib import Path


DEVICE_ROOT = Path(__file__).resolve().parents[1]


class ProductProfileTest(unittest.TestCase):
    def test_uses_wifi_only_tablet_product_profiles(self):
        product = (DEVICE_ROOT / "lineage_odin2_mini.mk").read_text()
        inherited_products = set(
            re.findall(
                r"^\s*\$\(call\s+inherit-product,\s*(.+?)\s*\)\s*$",
                product,
                flags=re.MULTILINE,
            )
        )

        self.assertIn("$(SRC_TARGET_DIR)/product/full_base.mk", inherited_products)
        self.assertIn(
            "vendor/lineage/config/common_full_tablet_wifionly.mk",
            inherited_products,
        )
        self.assertNotIn(
            "$(SRC_TARGET_DIR)/product/full_base_telephony.mk",
            inherited_products,
        )
        self.assertNotIn(
            "vendor/lineage/config/common_full_phone.mk",
            inherited_products,
        )


if __name__ == "__main__":
    unittest.main()
