#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Check locked standalone tools and Docker tool pins."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import tomllib

REPO = Path(__file__).resolve().parents[1]
TARGET_PLATFORMS = ("linux-arm64", "linux-x64")
DOCKER_TOOLS = ("uv", "just")
COMMAND_PREFIX = r"(?m)(?:^|\brun:\s+|[;&|]\s*|\bmise\s+exec\s+--\s+)"
FORBIDDEN_PATTERNS = {
    COMMAND_PREFIX + r"uvx(?:\s|$)": "committed workflows must not use uvx; use mise or uv run --frozen",
    COMMAND_PREFIX + r"mise\s+install\b(?!\s+--locked)": (
        "committed workflows must install tools with mise install --locked"
    ),
    COMMAND_PREFIX + r"uv\s+tool\s+install\b": "committed workflows must not install unlocked uv tools",
    COMMAND_PREFIX + r"uv\s+run\s+--with\b": "committed workflows must not use unlocked uv --with deps",
    r"curl\b[^\n|]*\|\s*(?:sh|bash)\b": "curl-piped installers are not allowed in committed workflows",
    r"just\.systems/install\.sh": "install just from mise.lock, not the installer script",
    COMMAND_PREFIX + r"eget\b": "install standalone tools through mise, not eget",
    r"\bCOSMOS_DEPS_": "use PAI_DEPS_* environment variables; COSMOS_DEPS_* aliases are retired",
}
SCAN_PATHS = [
    "README.md",
    "Dockerfile",
    "justfile",
    "bin",
    "ci",
    "docker",
    "just",
    ".github",
]
SCAN_SKIP = {
    "ci/check_toolchain.py",
    "ci/check_toolchain_test.py",
}
JUST_ARGUMENT_FORWARDING_PATTERNS = {
    r"\{\{\s*args\s*\}\}": "just recipes must not interpolate variadic args; use explicit recipes or scripts",
    r"(?m)^\s*[^#\s][^:\n]*\*args\s*:": "just recipes must not use variadic args; use explicit recipes or scripts",
}
FORBIDDEN_PUBLIC_ARTIFACT_PATTERNS = {
    "packages/**/Video_Codec_SDK_*": "do not vendor full NVIDIA Video Codec SDK bundles in the public repo",
    "packages/**/libnvcuvid.so": "do not vendor NVIDIA Video Codec binary link stubs in the public repo",
    "packages/**/libnvidia-encode.so": "do not vendor NVIDIA Video Codec binary link stubs in the public repo",
}


def _load_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text())


def _load_mise_tools(path: Path) -> set[str]:
    tools = _load_toml(path).get("tools", {})
    if not isinstance(tools, dict):
        raise ValueError(f"{path} [tools] must be a table")
    return set(tools)


def _load_lock(path: Path) -> dict[str, list[dict[str, Any]]]:
    tools = _load_toml(path).get("tools", {})
    if not isinstance(tools, dict):
        raise ValueError(f"{path} tools must be a table")
    return tools


def _one_lock_record(lock_tools: dict[str, list[dict[str, Any]]], tool: str) -> dict[str, Any]:
    records = lock_tools.get(tool)
    if not isinstance(records, list) or len(records) != 1:
        raise ValueError(f"mise.lock must contain exactly one record for {tool}")
    return records[0]


def _platform_record(record: dict[str, Any], platform: str, *, tool: str) -> dict[str, str]:
    raw_platform = record.get(f"platforms.{platform}")
    if not isinstance(raw_platform, dict):
        raise ValueError(f"mise.lock {tool} missing platform {platform}")
    checksum = raw_platform.get("checksum")
    url = raw_platform.get("url")
    if not isinstance(checksum, str) or not checksum.startswith("sha256:"):
        raise ValueError(f"mise.lock {tool} {platform} missing sha256 checksum")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError(f"mise.lock {tool} {platform} missing https URL")
    return {"checksum": checksum.removeprefix("sha256:"), "url": url}


def check_mise_lock() -> list[str]:
    errors: list[str] = []
    declared_tools = _load_mise_tools(REPO / ".mise.toml")
    lock_tools = _load_lock(REPO / "mise.lock")
    locked_tools = set(lock_tools)

    missing = sorted(declared_tools - locked_tools)
    stale = sorted(locked_tools - declared_tools)
    if missing:
        errors.append("mise.lock missing tools from .mise.toml: " + ", ".join(missing))
    if stale:
        errors.append("mise.lock has stale tools not in .mise.toml: " + ", ".join(stale))

    for tool in sorted(declared_tools):
        record = _one_lock_record(lock_tools, tool)
        backend = record.get("backend")
        if not isinstance(backend, str) or not backend:
            errors.append(f"mise.lock {tool} missing backend")
            continue
        if backend.startswith("pipx:"):
            continue
        for platform in TARGET_PLATFORMS:
            try:
                _platform_record(record, platform, tool=tool)
            except ValueError as error:
                errors.append(str(error))

    return errors


def _docker_args(text: str) -> dict[str, str]:
    args: dict[str, str] = {}
    for match in re.finditer(r'^ARG\s+([A-Z0-9_]+)="?([^"\n]+)"?$', text, re.MULTILINE):
        args[match.group(1)] = match.group(2)
    return args


def check_docker_tool_pins() -> list[str]:
    errors: list[str] = []
    lock_tools = _load_lock(REPO / "mise.lock")
    docker_args = _docker_args((REPO / "Dockerfile").read_text())

    for tool in DOCKER_TOOLS:
        record = _one_lock_record(lock_tools, tool)
        version = record.get("version")
        if not isinstance(version, str):
            errors.append(f"mise.lock {tool} missing version")
            continue
        version_arg = f"PAI_DEPS_{tool.upper()}_VERSION"
        if docker_args.get(version_arg) != version:
            errors.append(f"Dockerfile {version_arg}={docker_args.get(version_arg)!r}, expected {version!r}")
        for platform, arg_suffix in (("linux-arm64", "LINUX_ARM64"), ("linux-x64", "LINUX_X64")):
            try:
                platform_record = _platform_record(record, platform, tool=tool)
            except ValueError as error:
                errors.append(str(error))
                continue
            checksum_arg = f"PAI_DEPS_{tool.upper()}_{arg_suffix}_SHA256"
            if docker_args.get(checksum_arg) != platform_record["checksum"]:
                errors.append(
                    f"Dockerfile {checksum_arg}={docker_args.get(checksum_arg)!r}, "
                    f"expected {platform_record['checksum']!r}"
                )

    docker_text = (REPO / "Dockerfile").read_text()
    if "ghcr.io/astral-sh/uv" in docker_text:
        errors.append("Dockerfile must install uv from mise.lock release checksums, not a floating image copy")
    if "just.systems/install.sh" in docker_text:
        errors.append("Dockerfile must install just from mise.lock release checksums, not install.sh")
    return errors


def _scan_files() -> list[Path]:
    files: list[Path] = []
    for raw_path in SCAN_PATHS:
        path = REPO / raw_path
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                item
                for item in path.rglob("*")
                if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
            )
    return sorted(files)


def check_unlocked_tool_invocations() -> list[str]:
    errors: list[str] = []
    for path in _scan_files():
        relative = path.relative_to(REPO).as_posix()
        if relative in SCAN_SKIP:
            continue
        text = path.read_text(errors="ignore")
        for pattern, message in FORBIDDEN_PATTERNS.items():
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{relative}:{line}: {message}")
    return errors


def check_just_argument_forwarding(paths: list[Path] | None = None) -> list[str]:
    if paths is None:
        paths = [REPO / "justfile", *sorted((REPO / "just").glob("**/.just"))]
    errors: list[str] = []
    for path in paths:
        text = path.read_text(errors="ignore")
        relative = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path)
        for pattern, message in JUST_ARGUMENT_FORWARDING_PATTERNS.items():
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{relative}:{line}: {message}")
    return errors


def check_forbidden_public_artifacts(repo: Path = REPO) -> list[str]:
    errors: list[str] = []
    for pattern, message in FORBIDDEN_PUBLIC_ARTIFACT_PATTERNS.items():
        for path in sorted(repo.glob(pattern)):
            if path.exists():
                relative = path.relative_to(repo).as_posix()
                errors.append(f"{relative}: {message}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker-only", action="store_true", help="Only check Docker pins against mise.lock.")
    args = parser.parse_args()

    errors = check_docker_tool_pins()
    if not args.docker_only:
        errors.extend(check_mise_lock())
        errors.extend(check_unlocked_tool_invocations())
        errors.extend(check_just_argument_forwarding())
        errors.extend(check_forbidden_public_artifacts())
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
