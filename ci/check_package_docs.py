#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Validate package descriptors and colocated agent build docs."""

from __future__ import annotations

import sys
from pathlib import Path

from cosmos_dependencies.package_metadata import (
    DESCRIPTOR_NAME,
    VALID_BACKENDS,
    VALID_GPU_RISKS,
    VALID_STATUSES,
    PackageDescriptor,
    discover_package_descriptors,
)

REPO = Path(__file__).resolve().parents[1]
REQUIRED_HEADINGS = [
    "Status",
    "Local Build Entry Point",
    "Upstream Sources",
    "Version Constraints",
    "Build Environment",
    "OOM Controls",
    "Smoke Test",
    "Known Risks",
    "Future Fixes",
    "Research Notes",
]


def _display_path(path: Path) -> str:
    if path.is_relative_to(REPO):
        return path.relative_to(REPO).as_posix()
    return str(path)


def _check_doc(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing package docs: {_display_path(path)}"]
    text = path.read_text()
    for heading in REQUIRED_HEADINGS:
        if f"## {heading}" not in text:
            errors.append(f"{_display_path(path)} missing heading: ## {heading}")
    if "Status:" not in text:
        errors.append(f"{_display_path(path)} must include a Status: label")
    if "Research date:" not in text:
        errors.append(f"{_display_path(path)} must include a Research date: label")
    return errors


def _check_descriptor(package: PackageDescriptor) -> list[str]:
    errors: list[str] = []
    source = _display_path(package.descriptor_path)
    if package.name != package.directory.name:
        errors.append(f"{source} name must match package directory: {package.directory.name}")
    if package.status not in VALID_STATUSES:
        errors.append(f"{source} status must be one of {sorted(VALID_STATUSES)}")
    if package.gpu_risk not in VALID_GPU_RISKS:
        errors.append(f"{source} gpu_risk must be one of {sorted(VALID_GPU_RISKS)}")
    if package.build.backend not in VALID_BACKENDS:
        errors.append(f"{source} build.backend must be one of {sorted(VALID_BACKENDS)}")
    if not (package.directory / "pyproject.toml").is_file():
        errors.append(f"{source} missing pyproject.toml in {_display_path(package.directory)}")
    if not package.build_script_path.is_file():
        errors.append(f"{source} build script does not exist: {_display_path(package.build_script_path)}")
    if not package.docs_path.is_relative_to(package.directory):
        errors.append(f"{source} docs path must be inside package directory")
    if not package.upstream.startswith("https://") and package.upstream != "local":
        errors.append(f"{source} upstream must be an https URL or 'local'")
    if package.build.backend == "pip-wheel-git" and not package.build.source.url.startswith("https://"):
        errors.append(f"{source} pip-wheel-git packages must declare build.source.url")
    for script in package.build.prebuild_scripts:
        prebuild_path = package.directory / script
        if not prebuild_path.is_file():
            errors.append(f"{source} prebuild script does not exist: {_display_path(prebuild_path)}")
    errors.extend(_check_doc(package.docs_path))
    return errors


def check_descriptors() -> list[str]:
    errors: list[str] = []
    packages = discover_package_descriptors()
    seen: set[str] = set()
    descriptor_dirs = {package.directory for package in packages}

    for package in packages:
        if package.name in seen:
            errors.append(f"duplicate package descriptor name: {package.name}")
        seen.add(package.name)
        errors.extend(_check_descriptor(package))

    package_dirs = {path.parent for path in (REPO / "packages").glob("*/pyproject.toml")}
    missing_dirs = sorted(path.relative_to(REPO).as_posix() for path in package_dirs - descriptor_dirs)
    stale_dirs = sorted(path.relative_to(REPO).as_posix() for path in descriptor_dirs - package_dirs)
    if missing_dirs:
        errors.append(f"packages with pyproject.toml missing {DESCRIPTOR_NAME}: " + ", ".join(missing_dirs))
    if stale_dirs:
        errors.append(f"{DESCRIPTOR_NAME} directories without pyproject.toml: " + ", ".join(stale_dirs))
    return errors


def main() -> int:
    errors = check_descriptors()
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
