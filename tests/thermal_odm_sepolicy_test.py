#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import re
from pathlib import Path


DEVICE_ROOT = Path(__file__).resolve().parents[1]
BOARD_CONFIG = DEVICE_ROOT / "BoardConfig.mk"
FILE_CONTEXTS = DEVICE_ROOT / "sepolicy/odm/file_contexts"
THERMAL_EXEC_PATTERN = (
    r"/odm/bin/hw/android\.hardware\.thermal-service\.qti"
)
THERMAL_EXEC_CONTEXT = "u:object_r:hal_thermal_default_exec:s0"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


entries = []
for raw_line in FILE_CONTEXTS.read_text().splitlines():
    fields = raw_line.split("#", 1)[0].split()
    if len(fields) == 2:
        entries.append(tuple(fields))

require(
    "BOARD_ODM_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/odm"
    in BOARD_CONFIG.read_text(),
    "BoardConfig must route ODM file contexts through the ODM policy split",
)
require(
    entries.count((THERMAL_EXEC_PATTERN, THERMAL_EXEC_CONTEXT)) == 1,
    "ODM thermal service must receive hal_thermal_default_exec exactly once",
)
require(
    not any(
        context == THERMAL_EXEC_CONTEXT
        and pattern != THERMAL_EXEC_PATTERN
        and re.fullmatch(pattern, "/odm/bin/hw/android.hardware.thermal-service.qti")
        for pattern, context in entries
    ),
    "ODM thermal executable label must not come from a broader matching rule",
)

print("thermal ODM sepolicy contract: PASS")
