#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

usage() {
	cat >&2 <<'EOF'
Usage:
  just/check/scripts/git-safety.sh submodules
  just/check/scripts/git-safety.sh large-files --max-kb KB [PATH...]

Run small Git safety checks suitable for pre-commit hooks.
EOF
}

check_submodules() {
	local submodules
	submodules="$(git ls-files --stage | awk '$1 == "160000" { print $4 }')"
	if [[ -n "${submodules}" ]]; then
		echo "Error: git submodules are not allowed:" >&2
		printf "%s\n" "${submodules}" >&2
		return 1
	fi
}

check_large_files() {
	local max_kb=5000
	local max_bytes
	local path
	local size
	local errors=0

	if [[ "${1:-}" == "--max-kb" ]]; then
		if [[ -z "${2:-}" || ! "${2}" =~ ^[1-9][0-9]*$ ]]; then
			echo "Error: --max-kb requires a positive integer." >&2
			return 1
		fi
		max_kb="$2"
		shift 2
	fi
	max_bytes=$((max_kb * 1024))

	for path in "$@"; do
		[[ -f "${path}" ]] || continue
		size="$(stat -c %s "${path}")"
		if ((size > max_bytes)); then
			echo "Error: ${path} is ${size} bytes; limit is ${max_bytes} bytes." >&2
			errors=1
		fi
	done
	return "${errors}"
}

if [[ $# -lt 1 ]]; then
	usage
	exit 1
fi

command="$1"
shift
case "${command}" in
submodules)
	check_submodules "$@"
	;;
large-files)
	check_large_files "$@"
	;;
-h | --help)
	usage
	;;
*)
	echo "Error: unknown command: ${command}" >&2
	usage
	exit 1
	;;
esac
