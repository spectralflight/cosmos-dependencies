#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

while IFS= read -r -d '' path; do
	if [[ ! -f "${path}" ]]; then
		continue
	fi
	mkdir -p "${tmp_dir}/$(dirname "${path}")"
	cp -a "${path}" "${tmp_dir}/${path}"
done < <(git ls-files -z)

gitleaks dir --redact --no-banner "${tmp_dir}"
