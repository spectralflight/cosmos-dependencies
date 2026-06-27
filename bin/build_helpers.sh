# shellcheck shell=bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

pai_deps_pip_wheel() {
	local output_dir="${OUTPUT_DIR:?OUTPUT_DIR must be set}"

	pip wheel \
		-v \
		--no-deps \
		--no-build-isolation \
		--check-build-dependencies \
		--wheel-dir="${output_dir}" \
		"$@"
}

pai_deps_uv_build_wheel() {
	local output_dir="${OUTPUT_DIR:?OUTPUT_DIR must be set}"

	uv build \
		--wheel \
		-o "${output_dir}" \
		"$@"
}
