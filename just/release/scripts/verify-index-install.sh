#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

usage() {
	cat >&2 <<'EOF'
Usage: just/release/scripts/verify-index-install.sh INDEX_DIR PACKAGE VERSION [IMPORT_NAME]

Create a temporary uv environment and verify that PACKAGE==VERSION can be
installed from a local PEP 503 index. Installs with --no-deps so package-index
checks do not depend on unrelated dependency availability.
EOF
}

if [[ $# -lt 3 || $# -gt 4 ]]; then
	usage
	exit 1
fi

index_dir="$1"
package_name="$2"
package_version="$3"
import_name="${4:-${package_name//-/_}}"
python_version="${PYTHON_VERSION:-3.12}"

if [[ ! -d "${index_dir}" ]]; then
	echo "Error: index directory does not exist: ${index_dir}" >&2
	exit 1
fi

index_abs="$(realpath "${index_dir}")"
verify_dir="tmp/verify-index/${package_name}-${package_version}-py${python_version}"
rm -rf "${verify_dir}"
mkdir -p "${verify_dir}"
venv_dir="$(realpath "${verify_dir}/.venv")"

uv python install "${python_version}"
uv venv --python "${python_version}" "${venv_dir}"
uv pip install \
	--python "${venv_dir}/bin/python" \
	--no-deps \
	--index-url "file://${index_abs}" \
	"${package_name}==${package_version}"
"${venv_dir}/bin/python" -c "import ${import_name}; print(${import_name}.__name__)"
