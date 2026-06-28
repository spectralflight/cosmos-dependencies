#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Scan release artifacts for secrets before GitHub release publication."""

from __future__ import annotations

import argparse
import glob
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from pai_deps.release_artifacts import WHEEL_SIDECAR_SUFFIXES


def _expand_patterns(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = [Path(path) for path in glob.glob(pattern, recursive=True)]
        path = Path(pattern)
        if not matches and path.is_file():
            matches = [path]
        files.extend(matches)
    return sorted({path for path in files if path.is_file()})


def _add_existing_sidecars(files: list[Path]) -> list[Path]:
    expanded = set(files)
    for wheel in files:
        if not wheel.name.endswith(".whl"):
            continue
        for suffix in WHEEL_SIDECAR_SUFFIXES:
            sidecar = wheel.with_name(wheel.name + suffix)
            if sidecar.is_file():
                expanded.add(sidecar)
    return sorted(expanded)


def _run_gitleaks(*, scan_dir: Path, source: Path, gitleaks: str) -> list[str]:
    print(f"Scanning {source}", file=sys.stderr)
    result = subprocess.run(
        [gitleaks, "dir", "--redact", "--no-banner", str(scan_dir)],
        check=False,
    )
    if result.returncode != 0:
        return [f"{source}: gitleaks reported potential secrets"]
    return []


def _scan_regular_file(path: Path, *, gitleaks: str) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="pai-deps-secret-scan-") as temp_dir:
        temp_path = Path(temp_dir) / path.name
        shutil.copy2(path, temp_path)
        return _run_gitleaks(scan_dir=Path(temp_dir), source=path, gitleaks=gitleaks)


def _scan_wheel(path: Path, *, gitleaks: str) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="pai-deps-wheel-scan-") as temp_dir:
        extract_dir = Path(temp_dir) / "wheel"
        extract_dir.mkdir()
        try:
            with zipfile.ZipFile(path) as wheel:
                wheel.extractall(extract_dir)
        except zipfile.BadZipFile:
            return [f"{path}: invalid wheel zip archive"]
        return _run_gitleaks(scan_dir=extract_dir, source=path, gitleaks=gitleaks)


def scan_paths(paths: list[Path], *, gitleaks: str = "gitleaks") -> list[str]:
    errors: list[str] = []
    for path in _add_existing_sidecars(paths):
        if path.name.endswith(".whl"):
            errors.extend(_scan_wheel(path, gitleaks=gitleaks))
        else:
            errors.extend(_scan_regular_file(path, gitleaks=gitleaks))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patterns", nargs="+", help="Release artifact files or glob patterns.")
    parser.add_argument("--allow-empty", action="store_true", help="Pass when no artifacts match.")
    parser.add_argument("--gitleaks", default="gitleaks", help="gitleaks executable name or path.")
    args = parser.parse_args()

    if shutil.which(args.gitleaks) is None:
        print(f"Error: {args.gitleaks!r} is not on PATH. Run mise install --locked.", file=sys.stderr)
        return 1

    paths = _expand_patterns(args.patterns)
    if not paths:
        if args.allow_empty:
            print("No release artifacts matched.")
            return 0
        print("Error: no release artifacts matched.", file=sys.stderr)
        return 1

    errors = scan_paths(paths, gitleaks=args.gitleaks)
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
