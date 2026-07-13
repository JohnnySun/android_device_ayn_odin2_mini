#!/bin/bash
set -euo pipefail

MY_DIR="${BASH_SOURCE%/*}"
if [[ ! -d "${MY_DIR}" ]]; then
  MY_DIR="${PWD}"
fi

cd "${MY_DIR}"
exec ./setup-makefiles.py "$@"
