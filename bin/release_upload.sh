#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

usage() {
	cat >&2 <<'EOF'
Usage: bin/release_upload.sh [OPTIONS] FILE_OR_GLOB...

Create a GitHub release when needed and upload wheel assets without deleting
local build artifacts.

Options:
  --repo OWNER/REPO  Release repository, default: COSMOS_DEPENDENCIES_RELEASE_REPO or upstream
  --tag TAG          Release tag, default: COSMOS_DEPENDENCIES_RELEASE_TAG or current pyproject tag
  --title TITLE      Release title, default: TAG
  --notes NOTES      Release notes, default: local build artifact upload
  --target TARGET    Git commitish for a new release, default: HEAD
  --clobber          Replace existing assets with matching names
  -h, --help         Show this help
EOF
}

version="$(awk -F'"' '/^version = / { print $2; exit }' pyproject.toml)"
repo="${COSMOS_DEPENDENCIES_RELEASE_REPO:-nvidia-cosmos/cosmos-dependencies}"
tag="${COSMOS_DEPENDENCIES_RELEASE_TAG:-v${version}}"
title=""
notes="Local build artifact upload."
target="$(git rev-parse HEAD)"
upload_args=()
patterns=()

while [[ $# -gt 0 ]]; do
	case "$1" in
	--repo)
		repo="$2"
		shift 2
		;;
	--tag)
		tag="$2"
		shift 2
		;;
	--title)
		title="$2"
		shift 2
		;;
	--notes)
		notes="$2"
		shift 2
		;;
	--target)
		target="$2"
		shift 2
		;;
	--clobber)
		upload_args+=("--clobber")
		shift
		;;
	-h | --help)
		usage
		exit 0
		;;
	*)
		patterns+=("$1")
		shift
		;;
	esac
done

if [[ ${#patterns[@]} -eq 0 ]]; then
	usage
	exit 1
fi

files=()
for pattern in "${patterns[@]}"; do
	mapfile -t matches < <(compgen -G "${pattern}" | sort)
	if [[ ${#matches[@]} -eq 0 && -f "${pattern}" ]]; then
		matches=("${pattern}")
	fi
	files+=("${matches[@]}")
done

if [[ ${#files[@]} -eq 0 ]]; then
	echo "Error: no files matched upload patterns: ${patterns[*]}" >&2
	exit 1
fi

title="${title:-${tag}}"
if ! gh release view --repo "${repo}" "${tag}" >/dev/null 2>&1; then
	gh release create \
		--repo "${repo}" \
		--title "${title}" \
		--notes "${notes}" \
		--target "${target}" \
		"${tag}"
fi

for file in "${files[@]}"; do
	gh release upload --repo "${repo}" "${tag}" "${file}" "${upload_args[@]}"
done
