#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

usage() {
	cat >&2 <<'EOF'
Usage: just/release/scripts/release-upload.sh [OPTIONS] FILE_OR_GLOB...

Create a GitHub release when needed and upload wheel assets without deleting
local build artifacts. New releases are created with all matched files attached
in one gh command, so immutable repositories publish only after assets exist.

Options:
  --repo OWNER/REPO  Release repository, required unless PAI_DEPS_RELEASE_REPO is set
  --tag TAG          Release tag, default: PAI_DEPS_RELEASE_TAG or current pyproject tag
  --title TITLE      Release title, default: TAG
  --notes NOTES      Release notes, default: local build artifact upload
  --target TARGET    Git commitish for a new release, default: HEAD
  --draft            Create a draft release when the release does not exist
  --prerelease       Mark a newly created release as a prerelease
  --not-latest       Do not mark a newly created release as latest
  --clobber          Replace existing assets with matching names
  --dry-run          Print the upload plan and validate sidecars without GitHub writes
  -h, --help         Show this help
EOF
}

version="$(awk -F'"' '/^version = / { print $2; exit }' pyproject.toml)"
repo="${PAI_DEPS_RELEASE_REPO:-${COSMOS_DEPS_RELEASE_REPO:-}}"
tag="${PAI_DEPS_RELEASE_TAG:-${COSMOS_DEPS_RELEASE_TAG:-v${version}}}"
title=""
notes="Local build artifact upload."
target=""
dry_run=0
clobber=0
create_args=()
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
	--dry-run)
		dry_run=1
		shift
		;;
	--draft)
		create_args+=("--draft")
		shift
		;;
	--prerelease)
		create_args+=("--prerelease")
		shift
		;;
	--not-latest)
		create_args+=("--latest=false")
		shift
		;;
	--clobber)
		if [[ "${PAI_DEPS_ALLOW_CLOBBER:-${COSMOS_DEPS_ALLOW_CLOBBER:-0}}" != "1" ]]; then
			echo "Error: --clobber requires PAI_DEPS_ALLOW_CLOBBER=1." >&2
			exit 1
		fi
		clobber=1
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
if [[ -z "${repo}" ]]; then
	echo "Error: --repo is required for release uploads." >&2
	exit 1
fi

files=()
shopt -s globstar
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
expanded_files="$(mktemp)"
trap 'rm -f "${expanded_files}"' EXIT
uv run --frozen python ci/check_release_artifacts.py --print-upload-files "${files[@]}" >"${expanded_files}"
mapfile -t files <"${expanded_files}"
uv run --frozen python ci/scan_release_artifacts.py "${files[@]}"
if [[ "${dry_run}" -eq 1 ]]; then
	echo "Release upload plan"
	echo "  repo: ${repo}"
	echo "  tag: ${tag}"
	echo "  title: ${title}"
	echo "  notes: ${notes}"
	echo "  files:"
	printf '    %s\n' "${files[@]}"
	exit 0
fi

release_exists=0
if gh release view --repo "${repo}" "${tag}" >/dev/null 2>&1; then
	release_exists=1
fi

if [[ "${release_exists}" -eq 1 && "${clobber}" -eq 0 ]]; then
	mapfile -t existing_assets < <(gh release view --repo "${repo}" "${tag}" --json assets --jq '.assets[].name')
	collisions=()
	for file in "${files[@]}"; do
		file_name="$(basename "${file}")"
		for existing_asset in "${existing_assets[@]}"; do
			if [[ "${file_name}" == "${existing_asset}" ]]; then
				collisions+=("${file_name}")
				break
			fi
		done
	done
	if [[ ${#collisions[@]} -gt 0 ]]; then
		echo "Error: release already has matching assets; use --clobber only for explicitly replaceable scratch releases." >&2
		printf '  %s\n' "${collisions[@]}" >&2
		exit 1
	fi
fi

if [[ "${release_exists}" -eq 0 ]]; then
	target="${target:-$(git rev-parse HEAD)}"
	gh release create \
		--repo "${repo}" \
		--title "${title}" \
		--notes "${notes}" \
		--target "${target}" \
		"${create_args[@]}" \
		"${tag}" \
		"${files[@]}"
	exit 0
fi

for file in "${files[@]}"; do
	gh release upload --repo "${repo}" "${tag}" "${file}" "${upload_args[@]}"
done
