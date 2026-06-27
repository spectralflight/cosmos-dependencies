# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from ci.check_package_build_contracts import check_packages
from cosmos_dependencies.package_metadata import discover_package_descriptors


def test_repository_package_contracts_match_build_scripts() -> None:
    assert check_packages() == []


def test_detects_missing_source_url(tmp_path: Path) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "cosmos-package.toml").write_text(
        """
schema_version = 1
name = "pkg"
status = "smoke"
upstream = "https://example.invalid/pkg"
gpu_risk = "none"

[build]
backend = "pip-wheel-git"
script = "build.sh"
common_pip_flags = true

[build.source]
url = "https://example.invalid/pkg.git"
revision = "v{package_version}"
"""
    )
    (package_dir / "build.sh").write_text('pip wheel --no-deps --no-build-isolation --check-build-dependencies "$@"\n')

    packages = discover_package_descriptors(tmp_path)

    errors = check_packages(packages)

    assert any("https://example.invalid/pkg.git" in error for error in errors)
