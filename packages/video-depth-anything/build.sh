#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# https://github.com/DepthAnything/Video-Depth-Anything

temp_dir="$(mktemp -d)"
trap 'rm -rf "${temp_dir}"' EXIT

git clone --depth 1 --branch "v${PACKAGE_VERSION}" https://github.com/DepthAnything/Video-Depth-Anything.git "${temp_dir}/src"
cd "${temp_dir}/src"

touch \
	video_depth_anything/__init__.py \
	video_depth_anything/motion_module/__init__.py \
	video_depth_anything/util/__init__.py \
	utils/__init__.py \
	loss/__init__.py \
	benchmark/dataset_extract/__init__.py \
	benchmark/eval/__init__.py \
	benchmark/infer/__init__.py

cat >setup.py <<EOF
from setuptools import find_packages, setup

setup(
    name="video-depth-anything",
    version="${PACKAGE_VERSION}",
    description="Packaged import surface for Video-Depth-Anything",
    packages=find_packages(include=["video_depth_anything", "video_depth_anything.*", "utils", "utils.*", "loss", "loss.*", "benchmark", "benchmark.*"]),
    py_modules=["run", "run_streaming"],
    python_requires=">=3.10",
    install_requires=[
        "einops",
        "numpy",
        "opencv-python-headless",
        "pillow",
    ],
)
EOF

pai_deps_pip_wheel \
	. \
	"$@"
