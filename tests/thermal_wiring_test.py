#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import re
from pathlib import Path


DEVICE_ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


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


device_mk = (DEVICE_ROOT / "device.mk").read_text()
packages = make_values(device_mk, "PRODUCT_PACKAGES")
copies = make_values(device_mk, "PRODUCT_COPY_FILES")

require(
    packages.count("android.hardware.thermal-service.qti") == 1,
    "device product must include the QTI AIDL thermal service exactly once",
)
require(
    "thermal-engine-v2" not in packages,
    "device.mk must not package the legacy thermal-engine-v2 service",
)
require(
    not any("thermal" in copy.lower() for copy in copies),
    "device product must not copy proprietary thermal binaries or configs",
)

print("thermal wiring contract: PASS")
