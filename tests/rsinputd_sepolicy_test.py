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


def context_for(text, path):
    for raw_line in text.splitlines():
        fields = raw_line.split("#", 1)[0].split()
        if len(fields) == 2 and fields[0] == path:
            return fields[1]
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


board_config = (DEVICE_ROOT / "BoardConfig.mk").read_text()
public_policy = (
    DEVICE_ROOT / "sepolicy/system_ext/public/rsinputd.te"
).read_text()
private_policy = (
    DEVICE_ROOT / "sepolicy/system_ext/private/rsinputd.te"
).read_text()
private_device_policy = (
    DEVICE_ROOT / "sepolicy/system_ext/private/device.te"
).read_text()
private_genfs_contexts = (
    DEVICE_ROOT / "sepolicy/system_ext/private/genfs_contexts"
).read_text()
system_file_contexts = (
    DEVICE_ROOT / "sepolicy/system_ext/private/file_contexts"
).read_text()
vendor_device_policy = (
    DEVICE_ROOT / "sepolicy/vendor/device.te"
).read_text()
vendor_rsinputd_policy = (
    DEVICE_ROOT / "sepolicy/vendor/rsinputd.te"
).read_text()
vendor_file_contexts = (
    DEVICE_ROOT / "sepolicy/vendor/file_contexts"
).read_text()

device_path = "$(DEVICE_PATH)/sepolicy"
require(
    make_values(board_config, "SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS").count(
        f"{device_path}/system_ext/public"
    ) == 1,
    "BoardConfig must expose the Odin2 Mini system_ext public policy once",
)
require(
    make_values(board_config, "SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS").count(
        f"{device_path}/system_ext/private"
    ) == 1,
    "BoardConfig must include the Odin2 Mini system_ext private policy once",
)
require(
    make_values(board_config, "BOARD_VENDOR_SEPOLICY_DIRS").count(
        f"{device_path}/vendor"
    ) == 1,
    "BoardConfig must include the Odin2 Mini vendor policy once",
)

require("type rsinputd, domain;" in public_policy,
        "rsinputd must export its domain type to vendor policy")
require("typeattribute rsinputd coredomain;" in private_policy,
        "the /system daemon must remain a core domain")
require(
    "type rsinputd_exec, system_file_type, exec_type, file_type;"
    in private_policy,
    "rsinputd executable must have a dedicated system exec type",
)
require("init_daemon_domain(rsinputd)" in private_policy,
        "init must transition rsinputd into its dedicated domain")
require("get_prop(rsinputd, build_prop)" in private_policy,
        "rsinputd must read ro.product.device in its own domain")
require("write_logd(rsinputd)" not in private_policy,
        "rsinputd logging must not grant pmsg_device access")
require("unix_socket_send(rsinputd, logdw, logd)" in private_policy,
        "rsinputd logging must use only the logd datagram socket")
require("pmsg_device" not in private_policy,
        "rsinputd must not receive direct pmsg_device access")
require(
    context_for(system_file_contexts, "/system/bin/rsinputd")
    == "u:object_r:rsinputd_exec:s0",
    "/system/bin/rsinputd must receive the dedicated exec label",
)

require("type rsinputd_uart_device, dev_type;" in vendor_device_policy,
        "the RSInput UART must have a dedicated device type")
require(
    context_for(vendor_file_contexts, "/dev/ttyHS1")
    == "u:object_r:rsinputd_uart_device:s0",
    "/dev/ttyHS1 must receive the dedicated RSInput UART label",
)
require(
    allow_permissions(
        vendor_rsinputd_policy,
        "rsinputd",
        "rsinputd_uart_device",
        "chr_file",
    ) == {"getattr", "open", "read", "write", "ioctl"},
    "RSInput UART access must stay at the observed permission set",
)
require(
    allow_permissions(
        vendor_rsinputd_policy, "rsinputd", "uhid_device", "chr_file"
    ) == {"open", "write", "ioctl"},
    "/dev/uinput access must match its write-only open and ioctl use",
)
require("type rsinputd_mcu_sysfs, fs_type, sysfs_type;" in private_device_policy,
        "the controller MCU power node must have a dedicated sysfs type")
require(
    "genfscon sysfs /devices/platform/rsgpio/driver_ctl "
    "u:object_r:rsinputd_mcu_sysfs:s0" in private_genfs_contexts,
    "the exact controller MCU power node must receive its dedicated label",
)
require(
    allow_permissions(
        private_policy, "rsinputd", "rsinputd_mcu_sysfs", "file"
    ) == {"open", "write"},
    "controller MCU power access must remain write-only and path-specific",
)
require("rsinputd_mcu_sysfs" not in vendor_device_policy,
        "the MCU type must ship in system_ext, not the preserved stock vendor")
require("rsinputd_mcu_sysfs" not in vendor_rsinputd_policy,
        "the MCU allow rule must ship in system_ext, not the preserved stock vendor")

all_policy = "\n".join(
    path.read_text()
    for path in (DEVICE_ROOT / "sepolicy").rglob("*.te")
)
require(not re.search(r"\bpermissive\s+rsinputd\s*;", all_policy),
        "rsinputd must not be made permissive")
require(not re.search(r"\ballow\s+rsinputd\s+device:", all_policy),
        "rsinputd must never receive generic device access")
require("rw_file_perms" not in vendor_rsinputd_policy,
        "rsinputd device grants must enumerate exact permissions")
require(
    len(re.findall(r"\ballow\s+rsinputd\b[^;]*;", all_policy)) == 3,
    "rsinputd must have only the three explicit UART, uinput, and MCU rules",
)

print("rsinputd sepolicy contract: PASS")
