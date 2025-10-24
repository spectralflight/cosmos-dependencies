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
	echo "Usage: $0 <package_name> <package_version> <python_version> <torch_version> <cuda_version>" >&2
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
export CUDA_VERSION="${1}"
shift

if [[ ! "${PYTHON_VERSION}" =~ ^[0-9]+\.[0-9]+$ ]]; then
	echo "Error: Python version must be '<major>.<minor>'." >&2
	exit 1
fi
if [[ ! "${TORCH_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
	echo "Error: Torch version must be '<major>.<minor>.<patch>'" >&2
	exit 1
fi
if [[ ! "${CUDA_VERSION}" =~ ^[0-9]+\.[0-9]+$ ]]; then
	echo "Error: CUDA version must be '<major>.<minor>'" >&2
	exit 1
fi

CUDA_NAME="${CUDA_VERSION//./}"
TORCH_NAME="${TORCH_VERSION//./}"

root_dir="$(pwd)"
package_dir="${root_dir}/packages/${PACKAGE_NAME}"

name="${PACKAGE_NAME//-/_}-${PACKAGE_VERSION}-py${PYTHON_VERSION}-cu${CUDA_VERSION}-torch${TORCH_VERSION}"
export OUTPUT_DIR="${root_dir}/build/${name}"
rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"

log_file="${OUTPUT_DIR}/build.log"
echo "Logging to ${log_file}"
{
	# Print system information.
	date
	uname -a
	cat /etc/os-release
	ldd --version
	gcc --version

	echo "Building ${PACKAGE_NAME}=${PACKAGE_VERSION} python=${PYTHON_VERSION} torch=${TORCH_VERSION} cuda=${CUDA_VERSION}" "$@"

	# Enable ccache.
	# export CCACHE_NOHASHDIR=1
	# ccache --zero-stats

	# Set CUDA environment variables
	set +u
	if [[ -z "${CUDA_HOME}" ]]; then
		export CUDA_HOME="/usr/local/cuda-${CUDA_VERSION}"
		export PATH="${CUDA_HOME}/bin:${PATH}"
		export LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}"
	fi
	set -u
	echo "CUDA_HOME=${CUDA_HOME}"
	echo "PATH=${PATH}"
	echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH}"
	nvcc --version

	# Install build dependencies
	pushd "${package_dir}"
	UV_CACHE_DIR="$(uv cache dir)"
	venv_dir="${UV_CACHE_DIR}/cosmos_dependencies/venv"
	uv venv --clear --python "${PYTHON_VERSION}" "${venv_dir}"
	# shellcheck source=/dev/null
	source "${venv_dir}/bin/activate"
	uv sync --active
	uv pip install "torch==${TORCH_VERSION}" --index-url "https://download.pytorch.org/whl/cu${CUDA_NAME}"

	# Set build environment variables
	eval "$(python -c "
import torch
print(f'export _GLIBCXX_USE_CXX11_ABI={1 if torch.compiled_with_cxx11_abi() else 0}')
")"
	echo "_GLIBCXX_USE_CXX11_ABI=${_GLIBCXX_USE_CXX11_ABI}"

	# Build the package.
	# shellcheck source=/dev/null
	source "${package_dir}/build.sh" "$@"
	deactivate
	popd

	# Fix wheel filenames.
	for whl_path in "${OUTPUT_DIR}"/*.whl; do
		uv run bin/fix_wheel_filename.py -i "${whl_path}" --cuda="${CUDA_NAME}" --torch="${TORCH_NAME}"
	done
} |& tee "${log_file}"
