#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import re
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
        if candidate and (candidate / "odinfand.rc").is_file():
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


def context_for(text, path):
    for raw_line in text.splitlines():
        fields = raw_line.split("#", 1)[0].split()
        if len(fields) == 2 and fields[0] == path:
            return fields[1]
    return None


def genfs_context_for(text, path):
    for raw_line in text.splitlines():
        fields = raw_line.split("#", 1)[0].split()
        if len(fields) == 4 and fields[:3] == ["genfscon", "sysfs", path]:
            return fields[3]
    return None


def allow_permissions(text, source, target, object_class):
    match = re.search(
        rf"allow\s+{re.escape(source)}\s+{re.escape(target)}:"
        rf"{re.escape(object_class)}\s+\{{([^}}]+)\}}\s*;",
        text,
    )
    require(match is not None,
            f"missing allow {source} {target}:{object_class}")
    return set(match.group(1).split())


hardware_root = find_hardware_root()
device_mk = (DEVICE_ROOT / "device.mk").read_text()
hardware_bp = (hardware_root / "Android.bp").read_text()
odinfand_rc = (hardware_root / "odinfand.rc").read_text()
policy_root = DEVICE_ROOT / "sepolicy/system_ext/private"
daemon_policy = (policy_root / "odinfand.te").read_text()
app_policy = (policy_root / "odinsettings_app.te").read_text()
device_policy = (policy_root / "device.te").read_text()
file_contexts = (policy_root / "file_contexts").read_text()
genfs_contexts = (policy_root / "genfs_contexts").read_text()
service_policy = (policy_root / "service.te").read_text()
service_contexts = (policy_root / "service_contexts").read_text()
seapp_contexts = (policy_root / "seapp_contexts").read_text()

packages = make_values(device_mk, "PRODUCT_PACKAGES")
require(packages.count("odinfand") == 1,
        "the Odin2 Mini product must include odinfand exactly once")
require('name: "odinfand"' in hardware_bp,
        "hardware/ayn must define odinfand")
require('init_rc: ["odinfand.rc"]' in hardware_bp,
        "odinfand must install its init rc")
rc_lines = [line.rstrip() for line in odinfand_rc.splitlines()]
require(rc_lines.count("    class late_start") == 1,
        "odinfand must start with the late_start class")
require("    disabled" not in rc_lines,
        "odinfand must not remain disabled after product wiring")

require("type odinfand, domain, coredomain;" in daemon_policy,
        "odinfand must have a dedicated core domain")
require("init_daemon_domain(odinfand)" in daemon_policy,
        "init must transition odinfand into its domain")
require("binder_use(odinfand)" in daemon_policy,
        "odinfand must use the framework Binder driver")
require("add_service(odinfand, odin_fan_service)" in daemon_policy,
        "only odinfand may register the private fan service")
require("get_prop(odinfand, build_prop)" in daemon_policy,
        "odinfand must read system product identity")
require("get_prop(odinfand, build_vendor_prop)" in daemon_policy,
        "odinfand must read vendor product identity")
require("binder_call(odinsettings_app, odinfand)" in daemon_policy,
        "Odin Settings must be the explicit Binder client")
require(
    allow_permissions(daemon_policy, "odinfand", "odin_fan_control_sysfs", "file")
    == {"open", "read", "write"},
    "fan control nodes must have only open/read/write",
)
require(
    allow_permissions(daemon_policy, "odinfand", "odin_fan_status_sysfs", "file")
    == {"open", "read"},
    "fan status nodes must remain read-only",
)

require("type odinsettings_app, domain, coredomain;" in app_policy,
        "Odin Settings must have a dedicated app domain")
require("app_domain(odinsettings_app)" in app_policy,
        "Odin Settings must retain the Android app sandbox")
require("allow odinsettings_app odin_fan_service:service_manager find;"
        in app_policy, "Odin Settings must find the private fan service")
require("type odin_fan_service, protected_service, service_manager_type;"
        in service_policy, "the fan Binder endpoint must be protected")
require(context_for(service_contexts, "com.ayn.fan.IOdinFan/default")
        == "u:object_r:odin_fan_service:s0",
        "the exact AIDL instance must have the private service label")
require("isPrivApp=true" in seapp_contexts
        and "seinfo=platform" in seapp_contexts
        and "name=com.odin2.odinsettings" in seapp_contexts
        and "domain=odinsettings_app" in seapp_contexts,
        "only the platform privileged Odin Settings package may enter its domain")
require(context_for(file_contexts, "/system/bin/odinfand")
        == "u:object_r:odinfand_exec:s0",
        "odinfand must have its dedicated executable label")

require("type odin_fan_control_sysfs, fs_type, sysfs_type;" in device_policy,
        "fan state and duty need a dedicated control type")
require("type odin_fan_status_sysfs, fs_type, sysfs_type;" in device_policy,
        "fan period and speed need a dedicated status type")
for node in ("state", "duty"):
    require(genfs_context_for(genfs_contexts, f"/class/gpio5_pwm2/{node}")
            == "u:object_r:odin_fan_control_sysfs:s0",
            f"{node} must receive the control label")
for node in ("period", "speed"):
    require(genfs_context_for(genfs_contexts, f"/class/gpio5_pwm2/{node}")
            == "u:object_r:odin_fan_status_sysfs:s0",
            f"{node} must receive the read-only status label")

all_policy = "\n".join(path.read_text()
                         for path in (DEVICE_ROOT / "sepolicy").rglob("*.te"))
require(not re.search(r"\bpermissive\s+(odinfand|odinsettings_app)\s*;", all_policy),
        "neither fan domain may be permissive")
require(not re.search(r"allow\s+(appdomain|priv_app|platform_app|system_app)\s+"
                      r"odin_fan_(control|status)_sysfs:file", all_policy),
        "generic app domains must never access fan sysfs")
require(not re.search(r"allow\s+odinfand\s+sysfs:file", all_policy),
        "odinfand must never receive generic sysfs access")

print("odinfand product and sepolicy contract: PASS")
