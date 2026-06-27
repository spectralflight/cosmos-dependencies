#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

usage() {
	cat >&2 <<'EOF'
Usage: just/deps/scripts/lock-projects.sh [--check] [--upgrade] [PROJECT_DIR...]

Lock every root/package uv project by default. Pass project directories to limit
the scope.
EOF
}

check=0
upgrade=0
projects=()

while [[ $# -gt 0 ]]; do
	case "$1" in
	--check)
		check=1
		shift
		;;
	--upgrade)
		upgrade=1
		shift
		;;
	-h | --help)
		usage
		exit 0
		;;
	*)
		projects+=("$1")
		shift
		;;
	esac
done

if ((check && upgrade)); then
	echo "Error: --check and --upgrade are mutually exclusive." >&2
	exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../../.." && pwd)"
cd "${repo_root}"

if [[ ${#projects[@]} -eq 0 ]]; then
	projects=(".")
	for project_file in packages/*/pyproject.toml; do
		[[ -f "${project_file}" ]] || continue
		projects+=("$(dirname "${project_file}")")
	done
fi

for project_dir in "${projects[@]}"; do
	if [[ ! -f "${project_dir}/pyproject.toml" ]]; then
		echo "Error: ${project_dir} does not contain pyproject.toml" >&2
		exit 1
	fi
	echo "Locking ${project_dir}" >&2
	args=(lock --project "${project_dir}")
	if ((check)); then
		args+=(--check)
	fi
	if ((upgrade)); then
		args+=(--upgrade)
	fi
	uv "${args[@]}"
done
