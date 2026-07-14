#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


AIDL_BINARY = Path("vendor/bin/hw/android.hardware.thermal-service.qti")
AIDL_RC = Path("vendor/etc/init/android.hardware.thermal-service.qti.rc")
AIDL_MANIFEST = Path(
    "vendor/etc/vintf/manifest/android.hardware.thermal-service.qti.xml"
)
REQUIRED_FILES = (AIDL_BINARY, AIDL_RC, AIDL_MANIFEST)

SERVICE_NAME = "vendor.thermal-hal"
SERVICE_EXECUTABLE = "/vendor/bin/hw/android.hardware.thermal-service.qti"
AIDL_INTERFACE = "android.hardware.thermal.IThermal/default"
THERMAL_HAL = "android.hardware.thermal"

HIDL_NAME = re.compile(r"android\.hardware\.thermal@")
AIDL_BINARY_NAME = re.compile(r"^android\.hardware\.thermal-service\.")


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def child_texts(element, name):
    return [
        (child.text or "").strip()
        for child in element
        if local_name(child.tag) == name
    ]


def read_text(path, relative, errors):
    try:
        return path.read_text()
    except (OSError, UnicodeError) as error:
        errors.append(f"cannot read {relative}: {error}")
        return None


def uncommented_lines(text):
    for raw_line in text.splitlines():
        yield raw_line.split("#", 1)[0].rstrip()


def validate_required_files(product_out, errors):
    for relative in REQUIRED_FILES:
        if not (product_out / relative).is_file():
            errors.append(f"missing required file: {relative}")


def validate_required_rc(product_out, errors):
    path = product_out / AIDL_RC
    if not path.is_file():
        return
    text = read_text(path, AIDL_RC, errors)
    if text is None:
        return

    lines = list(uncommented_lines(text))
    services = []
    restarts = []
    boot_restarts = []
    interfaces = []
    in_boot_action = False
    for line in lines:
        if line and not line[0].isspace():
            in_boot_action = bool(re.match(r"^on\s+boot(?:\s|$)", line))
        service = re.match(r"^\s*service\s+(\S+)\s+(\S+)(?:\s|$)", line)
        if service:
            services.append(service.groups())
        restart = re.match(r"^\s*restart\s+(\S+)(?:\s|$)", line)
        if restart:
            restarts.append(restart.group(1))
            if in_boot_action:
                boot_restarts.append(restart.group(1))
        interface = re.match(r"^\s*interface\s+(\S+)\s+(\S+)(?:\s|$)", line)
        if interface:
            interfaces.append(interface.groups())

    expected_service = (SERVICE_NAME, SERVICE_EXECUTABLE)
    if services.count(expected_service) != 1:
        errors.append(
            f"{AIDL_RC}: expected exactly one service declaration "
            f"'{SERVICE_NAME} {SERVICE_EXECUTABLE}'"
        )
    thermal_services = [
        service
        for service in services
        if "thermal" in service[0] or "android.hardware.thermal" in service[1]
    ]
    if thermal_services != [expected_service]:
        errors.append(
            f"{AIDL_RC}: duplicate or unexpected thermal service declaration"
        )

    if (
        restarts.count(SERVICE_NAME) != 1
        or len(restarts) != 1
        or boot_restarts != [SERVICE_NAME]
    ):
        errors.append(
            f"{AIDL_RC}: expected exactly one 'restart {SERVICE_NAME}' under "
            "'on boot' and no other restart target"
        )
    expected_interface = ("aidl", AIDL_INTERFACE)
    if interfaces.count(expected_interface) != 1:
        errors.append(
            f"{AIDL_RC}: expected exactly one AIDL interface '{AIDL_INTERFACE}'"
        )
    if any(kind != "aidl" or name != AIDL_INTERFACE for kind, name in interfaces):
        errors.append(f"{AIDL_RC}: unexpected or non-AIDL thermal interface")


def validate_thermal_binaries(product_out, errors):
    binary_root = product_out / "vendor/bin"
    if not binary_root.is_dir():
        errors.append("missing required directory: vendor/bin")
        return

    for path in sorted(binary_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(product_out)
        if AIDL_BINARY_NAME.match(path.name) and relative != AIDL_BINARY:
            errors.append(
                f"duplicate AIDL thermal HAL binary is forbidden: {relative}"
            )


def validate_legacy_hidl_artifacts(product_out, errors):
    vendor_root = product_out / "vendor"
    for path in sorted(vendor_root.rglob("*")):
        if HIDL_NAME.search(path.name):
            relative = path.relative_to(product_out)
            errors.append(f"legacy HIDL thermal artifact is forbidden: {relative}")


def validate_init_tree(product_out, errors):
    init_root = product_out / "vendor/etc/init"
    if not init_root.is_dir():
        errors.append("missing required directory: vendor/etc/init")
        return

    for path in sorted(init_root.rglob("*.rc")):
        relative = path.relative_to(product_out)
        text = read_text(path, relative, errors)
        if text is None:
            continue
        if HIDL_NAME.search(text):
            errors.append(f"stock HIDL thermal init rc is forbidden: {relative}")
            continue
        if relative == AIDL_RC:
            continue
        for line in uncommented_lines(text):
            service = re.match(r"^\s*service\s+(\S+)\s+(\S+)(?:\s|$)", line)
            if service and (
                "thermal" in service.group(1)
                or "android.hardware.thermal" in service.group(2)
            ):
                errors.append(f"duplicate thermal HAL init provider: {relative}")
                break


def interface_instances(hal):
    instances = []
    for child in hal:
        if local_name(child.tag) == "fqname":
            instances.append((child.text or "").strip())
        elif local_name(child.tag) == "interface":
            names = child_texts(child, "name")
            for instance in child_texts(child, "instance"):
                for name in names:
                    instances.append(f"{name}/{instance}")
    return instances


def manifest_files(product_out):
    vintf_root = product_out / "vendor/etc/vintf"
    files = []
    combined = vintf_root / "manifest.xml"
    if combined.is_file():
        files.append(combined)
    fragment_root = vintf_root / "manifest"
    if fragment_root.is_dir():
        files.extend(path for path in fragment_root.rglob("*.xml") if path.is_file())
    return sorted(set(files))


def validate_manifests(product_out, errors):
    thermal_providers = []
    for path in manifest_files(product_out):
        relative = path.relative_to(product_out)
        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as error:
            errors.append(f"cannot parse VINTF manifest {relative}: {error}")
            continue

        if local_name(root.tag) != "manifest":
            errors.append(f"invalid VINTF manifest root in {relative}")
            continue

        for hal in root.iter():
            if local_name(hal.tag) != "hal":
                continue
            names = child_texts(hal, "name")
            if THERMAL_HAL not in names:
                continue
            thermal_providers.append(
                {
                    "path": relative,
                    "names": names,
                    "format": (hal.get("format") or "").strip().lower(),
                    "versions": child_texts(hal, "version"),
                    "instances": interface_instances(hal),
                }
            )

    for provider in thermal_providers:
        if provider["format"] != "aidl":
            errors.append(
                f"stock HIDL or unknown thermal VINTF provider is forbidden: "
                f"{provider['path']}"
            )

    if len(thermal_providers) != 1:
        locations = ", ".join(str(item["path"]) for item in thermal_providers)
        errors.append(
            "expected exactly one thermal HAL provider in vendor VINTF manifests; "
            f"found {len(thermal_providers)}"
            + (f" ({locations})" if locations else "")
        )
        return

    provider = thermal_providers[0]
    if provider["path"] != AIDL_MANIFEST:
        errors.append(f"thermal HAL provider must be declared by {AIDL_MANIFEST}")
    if provider["names"] != [THERMAL_HAL]:
        errors.append(
            f"{AIDL_MANIFEST}: expected exactly one name '{THERMAL_HAL}', got "
            f"{provider['names']}"
        )
    if provider["format"] != "aidl":
        return
    if provider["versions"] != ["2"]:
        errors.append(
            f"{AIDL_MANIFEST}: expected exactly AIDL version 2, got "
            f"{provider['versions'] or 'no version'}"
        )
    if provider["instances"] != ["IThermal/default"]:
        errors.append(
            f"{AIDL_MANIFEST}: expected exactly IThermal/default, got "
            f"{provider['instances'] or 'no instance'}"
        )


def verify(product_out):
    errors = []
    if not product_out.is_dir():
        return [f"product-out is not a directory: {product_out}"]
    if not (product_out / "vendor").is_dir():
        return [f"missing vendor install tree: {product_out / 'vendor'}"]

    validate_required_files(product_out, errors)
    validate_required_rc(product_out, errors)
    validate_legacy_hidl_artifacts(product_out, errors)
    validate_thermal_binaries(product_out, errors)
    validate_init_tree(product_out, errors)
    validate_manifests(product_out, errors)
    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Verify the installed vendor Thermal HAL in an Android product-out.",
    )
    parser.add_argument("product_out", type=Path, help="path to $PRODUCT_OUT")
    args = parser.parse_args()

    product_out = args.product_out.expanduser().resolve()
    errors = verify(product_out)
    if errors:
        for error in errors:
            print(f"built thermal verification: FAIL: {error}", file=sys.stderr)
        return 1

    print(
        "built thermal verification: PASS: "
        "sole provider is android.hardware.thermal AIDL v2 IThermal/default"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
