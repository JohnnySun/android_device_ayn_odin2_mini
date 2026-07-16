#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import re
from pathlib import Path


DEVICE_ROOT = Path(__file__).resolve().parents[1]

SERVICE_NAME = "com.ayn.performance.IOdinPerformance/default"
INIT_NODE_PATHS = {
    "/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq",
    "/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq",
    "/sys/devices/system/cpu/cpu3/cpufreq/scaling_min_freq",
    "/sys/devices/system/cpu/cpu3/cpufreq/scaling_max_freq",
    "/sys/devices/system/cpu/cpu7/cpufreq/scaling_min_freq",
    "/sys/devices/system/cpu/cpu7/cpufreq/scaling_max_freq",
    "/sys/class/kgsl/kgsl-3d0/devfreq/min_freq",
    "/sys/class/kgsl/kgsl-3d0/devfreq/max_freq",
    "/sys/devices/system/cpu/bus_dcvs/DDR/hw_min_freq",
    "/sys/devices/system/cpu/bus_dcvs/DDR/soc:qcom,memlat:ddr:gold/min_freq",
}
CANONICAL_GENFS_PATHS = {
    "/devices/system/cpu/cpufreq/policy0/scaling_min_freq",
    "/devices/system/cpu/cpufreq/policy0/scaling_max_freq",
    "/devices/system/cpu/cpufreq/policy3/scaling_min_freq",
    "/devices/system/cpu/cpufreq/policy3/scaling_max_freq",
    "/devices/system/cpu/cpufreq/policy7/scaling_min_freq",
    "/devices/system/cpu/cpufreq/policy7/scaling_max_freq",
    "/devices/platform/soc/3d00000.qcom,kgsl-3d0/devfreq/3d00000.qcom,kgsl-3d0/min_freq",
    "/devices/platform/soc/3d00000.qcom,kgsl-3d0/devfreq/3d00000.qcom,kgsl-3d0/max_freq",
    "/devices/system/cpu/bus_dcvs/DDR/hw_min_freq",
    "/devices/system/cpu/bus_dcvs/DDR/soc:qcom,memlat:ddr:gold/min_freq",
}


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
        if candidate and (candidate / "odinperformanced.rc").is_file():
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


def performance_genfs_paths(text):
    paths = set()
    for raw_line in text.splitlines():
        fields = raw_line.split("#", 1)[0].split()
        if (len(fields) == 4 and fields[:2] == ["genfscon", "sysfs"]
                and fields[3] == "u:object_r:odin_performance_sysfs:s0"):
            paths.add(fields[2])
    return paths


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
service_rc = (hardware_root / "odinperformanced.rc").read_text()
ownership_rc = (DEVICE_ROOT / "init/odinperformanced-device.rc").read_text()
policy_root = DEVICE_ROOT / "sepolicy/system_ext/private"
daemon_policy = (policy_root / "odinperformanced.te").read_text()
app_policy = (policy_root / "odinsettings_app.te").read_text()
device_policy = (policy_root / "device.te").read_text()
file_contexts = (policy_root / "file_contexts").read_text()
genfs_contexts = (policy_root / "genfs_contexts").read_text()
service_policy = (policy_root / "service.te").read_text()
service_contexts = (policy_root / "service_contexts").read_text()

packages = make_values(device_mk, "PRODUCT_PACKAGES")
require(packages.count("odinperformanced") == 1,
        "the Odin2 Mini product must include odinperformanced exactly once")
require('name: "odinperformanced"' in hardware_bp,
        "hardware/ayn must define odinperformanced")
require('init_rc: ["odinperformanced.rc"]' in hardware_bp,
        "odinperformanced must install its init rc")
require("$(DEVICE_PATH)/init/odinperformanced-device.rc:"
        "$(TARGET_COPY_OUT_SYSTEM)/etc/init/odinperformanced-device.rc"
        in device_mk.replace(" ", ""),
        "the device ownership rc must be installed into system/etc/init")

service_lines = [line.rstrip() for line in service_rc.splitlines()]
require("service odinperformanced /system/bin/odinperformanced" in service_lines,
        "init must launch only the fixed odinperformanced executable")
require(service_lines.count("    class late_start") == 1,
        "odinperformanced must start with the late_start class")
require(service_lines.count("    user system") == 1,
        "odinperformanced must run as system")
require(service_lines.count("    group system") == 1,
        "odinperformanced must retain only the system group")
require(service_lines.count("    oneshot") == 1,
        "odinperformanced must remain oneshot")
require("    disabled" not in service_lines,
        "odinperformanced must start automatically with late_start")

ownership_lines = [line.rstrip() for line in ownership_rc.splitlines()]
require("on post-fs-data" in ownership_lines,
        "node ownership must be established before late_start services")

chown_paths = []
for line in ownership_lines:
    fields = line.strip().split()
    if fields and fields[0] == "chown":
        require(len(fields) == 4 and fields[1:3] == ["system", "system"],
                "every init chown must be exactly 'chown system system <path>'")
        chown_paths.append(fields[3])
require(len(chown_paths) == 10 and set(chown_paths) == INIT_NODE_PATHS,
        "init must chown exactly the ten proved performance nodes once")
require(not re.search(r"(^|\s)(chmod|exec|exec_background|start|write)\b",
                      ownership_rc, re.MULTILINE),
        "performance init wiring must not add chmod, shell, start, or writes")
require(not re.search(r"[*?\[\]{}$`]", ownership_rc),
        "performance init wiring must not contain glob or shell syntax")
require("service " not in ownership_rc,
        "the device ownership rc must not duplicate the hardware service")

require("type odinperformanced, domain, coredomain;" in daemon_policy,
        "odinperformanced must have a dedicated core domain")
require("type odinperformanced_exec, system_file_type, exec_type, file_type;"
        in daemon_policy, "odinperformanced needs a dedicated executable type")
require("init_daemon_domain(odinperformanced)" in daemon_policy,
        "init must transition odinperformanced into its domain")
require("binder_use(odinperformanced)" in daemon_policy,
        "odinperformanced must use the framework Binder driver")
require("add_service(odinperformanced, odin_performance_service)"
        in daemon_policy, "only odinperformanced may add its Binder service")
require("binder_call(odinsettings_app, odinperformanced)" in daemon_policy,
        "Odin Settings must be the explicit Binder caller")
require(
    allow_permissions(daemon_policy, "odinperformanced",
                      "odin_performance_sysfs", "file")
    == {"open", "read", "write"},
    "the daemon may only open/read/write the labelled performance nodes",
)

require("allow odinsettings_app odin_performance_service:service_manager find;"
        in app_policy, "only Odin Settings may find the performance service")
require("type odin_performance_service, protected_service, service_manager_type;"
        in service_policy, "the performance Binder endpoint must be protected")
require(context_for(service_contexts, SERVICE_NAME)
        == "u:object_r:odin_performance_service:s0",
        "the exact AIDL instance must have the private service label")
require(context_for(file_contexts, "/system/bin/odinperformanced")
        == "u:object_r:odinperformanced_exec:s0",
        "odinperformanced must have its dedicated executable label")
require("type odin_performance_sysfs, fs_type, sysfs_type;" in device_policy,
        "the ten performance nodes need a dedicated sysfs type")
require(performance_genfs_paths(genfs_contexts) == CANONICAL_GENFS_PATHS,
        "SELinux must label exactly the ten canonical performance node paths")

all_policy = "\n".join(path.read_text()
                         for path in (DEVICE_ROOT / "sepolicy").rglob("*.te"))
require(not re.search(r"\bpermissive\s+(odinperformanced|odinsettings_app)\s*;",
                      all_policy),
        "neither performance domain may be permissive")
require(not re.search(r"allow\s+(appdomain|priv_app|platform_app|system_app)\s+"
                      r"odin_performance_(service|sysfs)", all_policy),
        "generic app domains must not reach the performance control plane")
require(not re.search(r"allow\s+odinperformanced\s+sysfs:file", all_policy),
        "odinperformanced must never receive generic sysfs access")
require(not re.search(r"allow\s+(?!odinperformanced\b)\w+\s+"
                      r"odin_performance_sysfs:file", all_policy),
        "only odinperformanced may access performance sysfs")
require(not re.search(r"allow\s+(?!odinsettings_app\b)\w+\s+"
                      r"odin_performance_service:service_manager\s+find",
                      all_policy),
        "only odinsettings_app may find the performance service")

print("odinperformanced product, init, and sepolicy contract: PASS")
