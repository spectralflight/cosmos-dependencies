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

# https://natten.org/install/#build-natten-libnatten
export NATTEN_N_WORKERS=${NATTEN_N_WORKERS:-$(($(nproc) / 2))}
export NATTEN_VERBOSE=1

# Support Ampere and newer
# https://github.com/SHI-Labs/NATTEN/blob/14318035fa8926557e7ac72c13f52aebd6c2db45/scripts/packaging/pkg_helpers.bash#L25
# Only support Ampere and newer
case "${CUDA_VERSION}" in
12.9 | 13.0)
	export NATTEN_CUDA_ARCH="8.0;8.6;8.9;9.0;10.0;10.3;12.0"
	;;
12.8)
	export NATTEN_CUDA_ARCH="8.0;8.6;8.9;9.0;10.0;12.0"
	;;
*)
	export NATTEN_CUDA_ARCH="8.0;8.6;8.9;9.0"
	;;
esac

pip wheel \
	-v \
	--no-deps \
	--no-build-isolation \
	--check-build-dependencies \
	--wheel-dir="${OUTPUT_DIR}" \
	"git+https://github.com/SHI-Labs/NATTEN.git@v${PACKAGE_VERSION}" \
	"$@"
