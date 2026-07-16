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


def context_for(text, name):
    for raw_line in text.splitlines():
        fields = raw_line.split("#", 1)[0].split()
        if len(fields) >= 2 and fields[0] == name:
            return fields[1]
    return None


device_mk = (DEVICE_ROOT / "device.mk").read_text()
policy_root = DEVICE_ROOT / "sepolicy/system_ext/private"
rsinputd_policy = (policy_root / "rsinputd.te").read_text()
app_policy = (policy_root / "odinsettings_app.te").read_text()
service_policy = (policy_root / "service.te").read_text()
service_contexts = (policy_root / "service_contexts").read_text()
property_policy = (policy_root / "property.te").read_text()
property_contexts = (policy_root / "property_contexts").read_text()
all_policy = "\n".join(
    path.read_text() for path in (DEVICE_ROOT / "sepolicy").rglob("*.te")
)

packages = make_values(device_mk, "PRODUCT_PACKAGES")
require(packages.count("rsinputd") == 1,
        "the Odin2 Mini product must include rsinputd exactly once")
require(packages.count("com.ayn.controller-java") == 1,
        "the Odin controller Java AIDL backend must be included exactly once")

require("type odin_controller_service, protected_service, service_manager_type;"
        in service_policy,
        "the controller Binder endpoint must use its dedicated protected service type")
require(context_for(service_contexts, "com.ayn.controller.IOdinController/default")
        == "u:object_r:odin_controller_service:s0",
        "the exact controller AIDL instance must have the controller service label")

require("system_internal_prop(odin_controller_config_prop)" in property_policy,
        "the controller profile must use the exact internal property type")
require(context_for(property_contexts, "persist.sys.ayn.controller.profile")
        == "u:object_r:odin_controller_config_prop:s0",
        "the exact controller profile property must have its dedicated label")

require("binder_use(rsinputd)" in rsinputd_policy,
        "rsinputd must use Binder to register the controller service")
require("add_service(rsinputd, odin_controller_service)" in rsinputd_policy,
        "only rsinputd may register the controller service")
require("get_prop(rsinputd, odin_controller_config_prop)" in rsinputd_policy,
        "rsinputd must read the controller profile property")
require("set_prop(rsinputd, odin_controller_config_prop)" in rsinputd_policy,
        "rsinputd must write the controller profile property")

require("allow odinsettings_app odin_controller_service:service_manager find;"
        in app_policy,
        "Odin Settings must find the controller Binder service")
require("binder_call(odinsettings_app, rsinputd)" in app_policy,
        "Odin Settings must call rsinputd only through Binder")
require(not re.search(r"\b(?:get_prop|set_prop)\(odinsettings_app,\s*"
                      r"odin_controller_config_prop\)", all_policy),
        "Odin Settings must not access the controller profile property")
require(not re.search(r"allow\s+odinsettings_app\s+"
                      r"odin_controller_config_prop:property_service", all_policy),
        "Odin Settings must not set the controller profile property directly")

property_access = re.findall(
    r"\b(?:get_prop|set_prop)\((\w+),\s*odin_controller_config_prop\)",
    all_policy,
)
require(set(property_access) == {"rsinputd"},
        "only rsinputd may access the controller profile property")
require(not re.search(r"allow\s+rsinputd\s+\S*(?:sysfs|gpio|mcu)\S*:", all_policy),
        "controller Binder wiring must not grant rsinputd sysfs, GPIO, or MCU access")

print("controller Binder and sepolicy contract: PASS")
