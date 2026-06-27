#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Check package descriptors against package-local build scripts."""

from __future__ import annotations

import sys

from pai_deps.package_metadata import PackageDescriptor, discover_package_descriptors

COMMON_PIP_WHEEL_TOKENS = [
    "pip wheel",
    "--no-deps",
    "--no-build-isolation",
    "--check-build-dependencies",
    "--wheel-dir",
    '"$@"',
]
UV_BUILD_TOKENS = ["uv build", "--wheel", "-o", '"$@"']


def _script_text(package: PackageDescriptor) -> str:
    parts = [package.build_script_path.read_text()]
    for script in package.build.prebuild_scripts:
        parts.append((package.directory / script).read_text())
    return "\n".join(parts)


def _check_contains(source: str, token: str, *, label: str) -> list[str]:
    if token not in source:
        return [f"{label}: missing {token!r}"]
    return []


def _check_package(package: PackageDescriptor) -> list[str]:
    errors: list[str] = []
    text = _script_text(package)
    label = package.descriptor_path.relative_to(package.descriptor_path.parents[2]).as_posix()

    match package.build.backend:
        case "pip-wheel-git":
            if package.build.common_pip_flags:
                for token in COMMON_PIP_WHEEL_TOKENS:
                    errors.extend(_check_contains(text, token, label=label))
            errors.extend(_check_contains(text, package.build.source.url, label=label))
            if package.build.source.subdirectory:
                errors.extend(_check_contains(text, f"#subdirectory={package.build.source.subdirectory}", label=label))
        case "uv-build":
            for token in UV_BUILD_TOKENS:
                errors.extend(_check_contains(text, token, label=label))
        case _:
            errors.append(f"{label}: unsupported backend {package.build.backend!r}")

    for version, revision in package.build.revision_overrides.items():
        errors.extend(_check_contains(text, version, label=label))
        errors.extend(_check_contains(text, revision, label=label))
    for env_name in sorted(set(package.build.env_exports) | set(package.build.env_defaults)):
        errors.extend(_check_contains(text, env_name, label=label))
    for system_package in package.build.system_packages:
        errors.extend(_check_contains(text, system_package, label=label))
    for script in package.build.prebuild_scripts:
        if not (package.directory / script).is_file():
            errors.append(f"{label}: missing prebuild script {script}")
        errors.extend(_check_contains(package.build_script_path.read_text(), script, label=label))
    return errors


def check_packages(packages: list[PackageDescriptor] | None = None) -> list[str]:
    errors: list[str] = []
    for package in packages or discover_package_descriptors():
        errors.extend(_check_package(package))
    return errors


def main() -> int:
    errors = check_packages()
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
