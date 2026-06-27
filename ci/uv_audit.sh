#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# Audit the root project and package build environments with uv.

set -euo pipefail

args=("$@")
if [ "${#args[@]}" -eq 0 ]; then
	args=(--frozen)
fi

_torch_version_from_lock() {
	local lock_file="$1"
	awk '
		/^name = "torch"$/ {
			in_torch = 1
			next
		}
		in_torch && /^version = / {
			gsub("\"", "", $3)
			print $3
			exit
		}
		/^\[\[package\]\]$/ {
			in_torch = 0
		}
	' "${lock_file}"
}

_audit_project() {
	local project_dir="$1"
	local lock_file="${project_dir}/uv.lock"
	local project_args=("${args[@]}")
	local torch_version

	if [ "${project_dir}" = "." ]; then
		lock_file="uv.lock"
	fi

	if [ "${COSMOS_DEPENDENCIES_AUDIT_STRICT:-0}" != "1" ] && [ -f "${lock_file}" ]; then
		torch_version="$(_torch_version_from_lock "${lock_file}")"
		case "${torch_version}" in
		2.10.0+*)
			project_args+=(--ignore-until-fixed GHSA-rrmf-rvhw-rf47)
			;;
		2.10.0 | 2.9.0)
			project_args+=(
				--ignore-until-fixed GHSA-rrmf-rvhw-rf47
				--ignore-until-fixed PYSEC-2026-139
			)
			;;
		esac
	fi

	if [ "${project_dir}" = "." ]; then
		uv audit "${project_args[@]}"
	else
		uv audit --project "${project_dir}" "${project_args[@]}"
	fi
}

status=0

echo "Auditing root project" >&2
_audit_project "." || status=1

for project_dir in packages/*; do
	if [ ! -f "${project_dir}/pyproject.toml" ]; then
		continue
	fi
	echo "Auditing ${project_dir}" >&2
	_audit_project "${project_dir}" || status=1
done

exit "${status}"
