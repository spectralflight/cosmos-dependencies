#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# https://github.com/IDEA-Research/Grounded-SAM-2

: "${GROUNDED_SAM2_GIT_REF:=b7a9c29f196edff0eb54dbe14588d7ae5e3dde28}"

temp_dir="$(mktemp -d)"
trap 'rm -rf "${temp_dir}"' EXIT

git clone --depth 1 https://github.com/IDEA-Research/Grounded-SAM-2.git "${temp_dir}/src"
cd "${temp_dir}/src"
git fetch --depth 1 origin "${GROUNDED_SAM2_GIT_REF}"
git checkout --detach FETCH_HEAD

package_dir="${temp_dir}/wheel/grounded_sam2_helper"
mkdir -p "${package_dir}/sam2_configs" "${package_dir}/utils"
cp utils/track_utils.py "${package_dir}/utils/track_utils.py"
cp -R sam2/configs/. "${package_dir}/sam2_configs/"
touch "${package_dir}/__init__.py" "${package_dir}/utils/__init__.py"
cat >"${package_dir}/paths.py" <<'EOF'
from importlib.resources import files


def sam2_configs_path() -> str:
    return str(files("grounded_sam2_helper").joinpath("sam2_configs"))
EOF

cd "${temp_dir}/wheel"
cat >setup.py <<EOF
from setuptools import find_packages, setup

setup(
    name="grounded-sam2-helper",
    version="${PACKAGE_VERSION}",
    description="Thin helper package for Grounded-SAM-2 TransferBench utilities",
    packages=find_packages(),
    include_package_data=True,
    package_data={"grounded_sam2_helper": ["sam2_configs/**/*.yaml"]},
    python_requires=">=3.10",
)
EOF

pip wheel \
	-v \
	--no-deps \
	--no-build-isolation \
	--check-build-dependencies \
	--wheel-dir="${OUTPUT_DIR}" \
	. \
	"$@"
