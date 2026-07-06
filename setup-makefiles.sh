#!/bin/bash
set -euo pipefail

DEVICE=odin2_mini
VENDOR=ayn

MY_DIR="${BASH_SOURCE%/*}"
if [[ ! -d "${MY_DIR}" ]]; then
  MY_DIR="${PWD}"
fi

ANDROID_ROOT="${ANDROID_ROOT:-$(cd "${MY_DIR}/../../.." && pwd)}"
HELPER="${ANDROID_ROOT}/tools/extract-utils/extract_utils.sh"

if [[ ! -f "${HELPER}" ]]; then
  echo "Missing Lineage extract helper: ${HELPER}" >&2
  exit 1
fi

source "${HELPER}"
setup_vendor "${DEVICE}" "${VENDOR}" "${ANDROID_ROOT}"
write_headers
write_makefiles "${MY_DIR}/proprietary-files.txt" true
write_footers
