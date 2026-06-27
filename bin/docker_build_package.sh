#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

usage() {
	cat >&2 <<'EOF'
Usage: bin/docker_build_package.sh PACKAGE VERSION PYTHON_VERSION TORCH_VERSION BUILD_DIR [BUILD_ARGS...]

Run a package build inside Docker. Set COSMOS_DEPENDENCIES_BUILD_ATTEMPTS to
retry transient network failures while reusing Docker and uv caches.
EOF
}

if [[ $# -lt 5 ]]; then
	usage
	exit 1
fi

package_name="$1"
package_version="$2"
python_version="$3"
torch_version="$4"
build_dir="$5"
shift 5

attempts="${COSMOS_DEPENDENCIES_BUILD_ATTEMPTS:-1}"
retry_delay="${COSMOS_DEPENDENCIES_BUILD_RETRY_DELAY:-30}"
cuda_version="${COSMOS_DEPENDENCIES_DOCKER_CUDA_VERSION:-12.8.1}"
exit_code=0

if [[ ! "${attempts}" =~ ^[1-9][0-9]*$ ]]; then
	echo "Error: COSMOS_DEPENDENCIES_BUILD_ATTEMPTS must be a positive integer." >&2
	exit 1
fi

for ((attempt = 1; attempt <= attempts; attempt++)); do
	echo "Docker build attempt ${attempt}/${attempts}: ${package_name} ${package_version} py${python_version} torch${torch_version} cuda${cuda_version}"
	if bin/docker_run.sh --cuda-version "${cuda_version}" --no-tty -- \
		just build "${package_name}" "${package_version}" "${python_version}" "${torch_version}" "${build_dir}" "$@"; then
		exit 0
	fi
	exit_code=$?
	if ((attempt < attempts)); then
		echo "Build attempt ${attempt} failed with exit code ${exit_code}; retrying in ${retry_delay}s." >&2
		sleep "${retry_delay}"
	fi
done

exit "${exit_code}"
