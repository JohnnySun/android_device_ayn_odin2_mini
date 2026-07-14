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
    packages.count("$(ODIN2_THERMAL_PACKAGE)") == 1,
    "device product must include the selected thermal package exactly once",
)
require(
    "ODIN2_THERMAL_ODM_OVERRIDE ?= false" in device_mk,
    "ODM thermal override must remain opt-in",
)
require(
    "ODIN2_THERMAL_PACKAGE := android.hardware.thermal-service.qti\n"
    in device_mk,
    "default product profile must retain the vendor thermal provider",
)
require(
    re.search(
        r"ifeq \(\$\(ODIN2_THERMAL_ODM_OVERRIDE\),true\)\n"
        r"ODIN2_THERMAL_PACKAGE := "
        r"android\.hardware\.thermal-service\.qti\.odm\n"
        r"endif",
        device_mk,
    ) is not None,
    "opt-in profile must select the ODM thermal override module",
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
