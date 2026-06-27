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

pai_deps_copy_license_files_py() {
	local source_dir="${1:?source directory is required}"
	local dest_dir="${2:?destination directory is required}"
	local license_file
	local copied=()
	local list_items=""
	local candidate_names=(
		LICENSE
		LICENSE.txt
		LICENSE.md
		LICENCE
		LICENCE.txt
		NOTICE
		NOTICE.txt
		COPYING
		COPYING.txt
	)

	for license_file in "${candidate_names[@]}"; do
		if [[ -f "${source_dir}/${license_file}" ]]; then
			if [[ "$(realpath "${source_dir}/${license_file}")" != "$(realpath -m "${dest_dir}/${license_file}")" ]]; then
				cp "${source_dir}/${license_file}" "${dest_dir}/${license_file}"
			fi
			copied+=("${license_file}")
		fi
	done
	if [[ ${#copied[@]} -eq 0 ]]; then
		echo "Error: no upstream license/notice files found in ${source_dir}" >&2
		return 1
	fi

	for license_file in "${copied[@]}"; do
		list_items+="\"${license_file}\", "
	done
	printf '[%s]' "${list_items}"
}
