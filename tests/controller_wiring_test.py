#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path


DEVICE_ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def find_hardware_root():
    configured = os.environ.get("AYN_HARDWARE_DIR")
    candidates = [
        Path(configured) if configured else None,
        DEVICE_ROOT.parents[2] / "hardware/ayn",
        DEVICE_ROOT.parent / "android_hardware_ayn",
    ]
    for candidate in candidates:
        if candidate and (candidate / "rsinputd.rc").is_file():
            return candidate.resolve()
    raise RuntimeError(
        "hardware/ayn not found; set AYN_HARDWARE_DIR to android_hardware_ayn"
    )


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


def resource_value(relative_path, tag, name):
    root = ET.parse(DEVICE_ROOT / relative_path).getroot()
    for element in root.findall(tag):
        if element.get("name") == name:
            return (element.text or "").strip()
    return None


hardware_root = find_hardware_root()
device_mk = (DEVICE_ROOT / "device.mk").read_text()
hardware_bp = (hardware_root / "Android.bp").read_text()
rsinputd_rc = (hardware_root / "rsinputd.rc").read_text()
rsinputd_source = (hardware_root / "src/rsinputd.cpp").read_text()

require("hardware/ayn" in make_values(device_mk, "PRODUCT_SOONG_NAMESPACES"),
        "device product must expose the hardware/ayn Soong namespace")
packages = make_values(device_mk, "PRODUCT_PACKAGES")
require("rsinputd" in packages, "device product must include rsinputd")
require("odinfand" not in packages, "device product must not include odinfand")
copies = make_values(device_mk, "PRODUCT_COPY_FILES")
require(
    "$(DEVICE_PATH)/keylayout/Vendor_2020_Product_3001.kl:"
    "$(TARGET_COPY_OUT_SYSTEM)/usr/keylayout/Vendor_2020_Product_3001.kl"
    in copies,
    "device product must install the exact rsinputd keylayout",
)

require('name: "rsinputd"' in hardware_bp, "hardware repo must define rsinputd")
require('init_rc: ["rsinputd.rc"]' in hardware_bp,
        "rsinputd must install its init rc")
require("device.id.vendor = 0x2020;" in rsinputd_source,
        "rsinputd vendor id must remain 0x2020")
require("device.id.product = 0x3001;" in rsinputd_source,
        "rsinputd product id must remain 0x3001")

rc_lines = [line.rstrip() for line in rsinputd_rc.splitlines()]
require(rc_lines.count(
    "on late-init && property:ro.product.device=odin2_mini") == 1,
    "rsinputd must have one exact odin2_mini late-init gate")
require(rc_lines.count("    start rsinputd") == 1,
        "rsinputd must have exactly one gated start")
service = rc_lines[rc_lines.index("service rsinputd /system/bin/rsinputd") + 1:]
require("    disabled" in service and "    oneshot" in service,
        "rsinputd must remain a disabled oneshot system service")

keylayout = (DEVICE_ROOT / "keylayout/Vendor_2020_Product_3001.kl").read_text()
mappings = set()
for raw_line in keylayout.splitlines():
    fields = raw_line.split("#", 1)[0].split()
    if len(fields) >= 3 and fields[0] in ("key", "axis"):
        mappings.add((fields[0], int(fields[1], 0), fields[2]))
required_mappings = {
    *(('key', code, name) for code, name in {
        278: 'F1', 304: 'BUTTON_A', 305: 'BUTTON_B', 307: 'BUTTON_X',
        308: 'BUTTON_Y', 310: 'BUTTON_L1', 311: 'BUTTON_R1',
        314: 'BUTTON_SELECT', 315: 'BUTTON_START', 316: 'BUTTON_MODE',
        317: 'BUTTON_THUMBL', 318: 'BUTTON_THUMBR', 544: 'DPAD_UP',
        545: 'DPAD_DOWN', 546: 'DPAD_LEFT', 547: 'DPAD_RIGHT',
    }.items()),
    *(('axis', code, name) for code, name in {
        0x00: 'X', 0x01: 'Y', 0x02: 'LTRIGGER',
        0x03: 'Z', 0x04: 'RZ', 0x05: 'RTRIGGER',
    }.items()),
}
require(mappings == required_mappings,
        "keylayout must match the required controller buttons and axes")

required_resources = {
    ("overlay/packages/apps/Launcher3/res/values/config.xml", "bool",
     "config_launcherControllerNavigation"): "true",
    ("overlay/packages/apps/SetupWizard/res/values/config.xml", "bool",
     "config_controllerInitialFocus"): "true",
    ("overlay/packages/apps/Settings/res/values/config.xml", "bool",
     "config_controllerInitialFocus"): "true",
    ("overlay/packages/apps/Settings/res/values-land/dimens.xml", "dimen",
     "settingslib_toolbar_layout_height"): "128dp",
    ("overlay/packages/apps/Settings/res/values-land/dimens.xml", "dimen",
     "settingslib_scrim_visible_height_trigger"): "96dp",
    ("overlay/packages/apps/Settings/res/values-land/dimens.xml", "dimen",
     "expanded_title_margin_bottom"): "48dp",
    ("overlay/packages/inputmethods/LatinIME/java/res/values/config.xml", "bool",
     "config_enable_controller_navigation"): "true",
}
for (path, tag, name), expected in required_resources.items():
    actual = resource_value(path, tag, name)
    require(actual == expected, f"{path}: expected {name}={expected}, got {actual}")

taskbar_flag_path = (
    DEVICE_ROOT
    / "release/aconfig/bp4a/com.android.wm.shell"
    / "enable_taskbar_navbar_unification_flag_values.textproto"
)
require(taskbar_flag_path.is_file(),
        "Odin2 Mini must override taskbar/navbar unification for three-button navigation")
taskbar_flag = taskbar_flag_path.read_text()
require('package: "com.android.wm.shell"' in taskbar_flag,
        "taskbar/navbar flag override must target com.android.wm.shell")
require('name: "enable_taskbar_navbar_unification"' in taskbar_flag,
        "taskbar/navbar flag override must target the exact aconfig flag")
require("state: DISABLED" in taskbar_flag,
        "taskbar/navbar unification must remain disabled on Odin2 Mini")
require("permission: READ_ONLY" in taskbar_flag,
        "taskbar/navbar override must be frozen in the release config")

print("controller wiring contract: PASS")
