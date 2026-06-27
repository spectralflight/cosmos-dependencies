# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from pai_deps.package_metadata import discover_package_descriptors, load_package_descriptor


def test_discovers_repository_packages() -> None:
    packages = discover_package_descriptors()

    assert [package.name for package in packages] == sorted(package.name for package in packages)
    assert {package.name for package in packages} >= {"cosmos-dummy", "natten"}
    assert all(package.descriptor_path.name == "pai-package.toml" for package in packages)


def test_loads_descriptor_defaults(tmp_path: Path) -> None:
    package_dir = tmp_path / "sample"
    package_dir.mkdir()
    descriptor = package_dir / "pai-package.toml"
    descriptor.write_text(
        """
schema_version = 1
name = "sample"
status = "smoke"
upstream = "local"
gpu_risk = "none"

[build]
backend = "uv-build"
"""
    )

    package = load_package_descriptor(descriptor)

    assert package.name == "sample"
    assert package.project_name == "sample"
    assert package.build.script == "build.sh"
    assert package.build.requires_torch is True
    assert package.docs == "docs/dev/build-notes.md"
