#!/usr/bin/env -S bash -euxo pipefail
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# CUDA 12.8 requires gcc<=14: `/usr/local/cuda-12.8/targets/x86_64-linux/include/crt/host_config.h`

# Build a package.

if [[ $# -lt 5 ]]; then
	echo "Usage: $0 <package_name> <package_version> <python_version> <torch_version> <build_dir>" >&2
	exit 1
fi
export PACKAGE_NAME="${1}"
shift
export PACKAGE_VERSION="${1}"
shift
export PYTHON_VERSION="${1}"
shift
export TORCH_VERSION="${1}"
shift
export BUILD_DIR="${1}"
shift

if [[ ! "${PYTHON_VERSION}" =~ ^[0-9]+\.[0-9]+$ ]]; then
	echo "Error: Python version must be '<major>.<minor>'." >&2
	exit 1
fi
if [[ ! "${TORCH_VERSION}" =~ ^[0-9]+\.[0-9]+$ ]]; then
	echo "Error: Torch version must be '<major>.<minor>'" >&2
	exit 1
fi

_trim() {
	local value="$1"
	value="${value#"${value%%[![:space:]]*}"}"
	value="${value%"${value##*[![:space:]]}"}"
	printf "%s" "${value}"
}

_is_reserved_env_name() {
	local name="$1"
	local reserved_name
	local reserved_env_names=(
		PACKAGE_NAME
		PACKAGE_VERSION
		PYTHON_VERSION
		TORCH_VERSION
		LOCAL_VERSION_SUFFIX
		OUTPUT_NAME
		OUTPUT_DIR
		PATH
		HOME
		USER
		XDG_CACHE_HOME
		XDG_DATA_HOME
		XDG_BIN_HOME
		UV_CACHE_DIR
		UV_PROJECT_ENVIRONMENT
		CCACHE_DIR
		CUDA_HOME
		LD_LIBRARY_PATH
		CUDA_VERSION
	)
	for reserved_name in "${reserved_env_names[@]}"; do
		if [[ "${name}" == "${reserved_name}" ]]; then
			return 0
		fi
	done
	return 1
}

_strip_matching_quotes() {
	local value="$1"
	local first_char
	local last_char
	if [[ "${#value}" -lt 2 ]]; then
		printf "%s" "${value}"
		return
	fi
	first_char="${value:0:1}"
	last_char="${value: -1}"
	if [[ "${first_char}" == "${last_char}" && ( "${first_char}" == "'" || "${first_char}" == '"' ) ]]; then
		printf "%s" "${value:1:${#value}-2}"
		return
	fi
	printf "%s" "${value}"
}

_load_env_file() {
	local env_file="$1"
	local env_line
	local line_no=0
	local key
	local value

	if [[ -z "${env_file}" ]]; then
		return
	fi
	if [[ ! -f "${env_file}" ]]; then
		echo "Error: COSMOS_DEPENDENCIES_ENV_FILE does not exist: ${env_file}" >&2
		exit 1
	fi

	while IFS= read -r env_line || [[ -n "${env_line}" ]]; do
		line_no=$((line_no + 1))
		env_line="${env_line%$'\r'}"
		env_line="$(_trim "${env_line}")"
		if [[ -z "${env_line}" || "${env_line:0:1}" == "#" ]]; then
			continue
		fi
		if [[ "${env_line}" == export[[:space:]]* ]]; then
			env_line="$(_trim "${env_line#export}")"
		fi
		if [[ ! "${env_line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]]; then
			echo "Error: ${env_file}:${line_no}: expected KEY=VALUE" >&2
			exit 1
		fi
		key="${BASH_REMATCH[1]}"
		value="$(_trim "${BASH_REMATCH[2]}")"
		value="$(_strip_matching_quotes "${value}")"
		if _is_reserved_env_name "${key}"; then
			echo "Error: ${env_file}:${line_no}: ${key} is controlled by bin/build.sh and cannot be set in COSMOS_DEPENDENCIES_ENV_FILE" >&2
			exit 1
		fi
		build_env_file_args+=("${key}=${value}")
	done <"${env_file}"
}

build_env_file_args=()
_load_env_file "${COSMOS_DEPENDENCIES_ENV_FILE:-}"

timestamp=$(date +%Y%m%d%H%M%S)
export OUTPUT_NAME="${timestamp}-${PACKAGE_NAME//-/_}-${PACKAGE_VERSION}-py${PYTHON_VERSION}-cu${CUDA_VERSION}-torch${TORCH_VERSION}"
OUTPUT_DIR="${BUILD_DIR}/${OUTPUT_NAME}"
rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"
OUTPUT_DIR="$(realpath "${OUTPUT_DIR}")"
export OUTPUT_DIR="${OUTPUT_DIR}"
log_file="${OUTPUT_DIR}/build.log"
echo "Logging to ${log_file}"

export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_BIN_HOME="${XDG_BIN_HOME:-$XDG_DATA_HOME/../bin}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$XDG_CACHE_HOME/uv}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$XDG_DATA_HOME/cosmos-dependencies/project-venv}"
export CCACHE_DIR="${CCACHE_DIR:-$HOME/.ccache}"
build_env_args=(
	PACKAGE_NAME="${PACKAGE_NAME}"
	PACKAGE_VERSION="${PACKAGE_VERSION}"
	PYTHON_VERSION="${PYTHON_VERSION}"
	TORCH_VERSION="${TORCH_VERSION}"
	LOCAL_VERSION_SUFFIX="${LOCAL_VERSION_SUFFIX:-}"
	OUTPUT_NAME="${OUTPUT_NAME}"
	OUTPUT_DIR="${OUTPUT_DIR}"
	PATH="${PATH:-}"
	HOME="${HOME:-}"
	USER="${USER:-}"
	XDG_CACHE_HOME="${XDG_CACHE_HOME}"
	XDG_DATA_HOME="${XDG_DATA_HOME}"
	XDG_BIN_HOME="${XDG_BIN_HOME}"
	UV_CACHE_DIR="${UV_CACHE_DIR}"
	UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT}"
	CCACHE_DIR="${CCACHE_DIR}"
)
env -i "${build_env_args[@]}" "${build_env_file_args[@]}" bash -euxo pipefail "bin/_build.sh" "$@" |& tee "${log_file}"
