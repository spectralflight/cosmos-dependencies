#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Fail when a published package index under docs/ is changed.

New index files and unreleased index versions are allowed. Published index files
are treated as immutable because downstream lockfiles can rely on their wheel
URLs and hashes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class ChangedPath:
    status: str
    path: str
    old_path: str | None = None


def _is_package_index(path: str) -> bool:
    posix_path = PurePosixPath(path)
    return (
        len(posix_path.parts) >= 3
        and posix_path.parts[0] == "docs"
        and posix_path.parts[1] != "dev"
        and posix_path.name == "index.html"
    )


def _index_version(path: str) -> str | None:
    posix_path = PurePosixPath(path)
    if not _is_package_index(path):
        return None
    return posix_path.parts[1]


def parse_name_status(output: str) -> list[ChangedPath]:
    changes: list[ChangedPath] = []
    for line in output.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")):
            if len(parts) != 3:
                raise ValueError(f"Unexpected git name-status line: {line!r}")
            changes.append(ChangedPath(status=status, old_path=parts[1], path=parts[2]))
        else:
            if len(parts) != 2:
                raise ValueError(f"Unexpected git name-status line: {line!r}")
            changes.append(ChangedPath(status=status, path=parts[1]))
    return changes


def _read_unreleased_versions(indices_dir: Path = Path("indices")) -> set[str]:
    versions: set[str] = set()
    for manifest_path in indices_dir.glob("*/manifest.json"):
        data = json.loads(manifest_path.read_text())
        if isinstance(data, dict) and data.get("status") == "unreleased":
            versions.add(manifest_path.parent.name)
    return versions


def _is_unreleased_index_path(path: str, unreleased_versions: set[str]) -> bool:
    version = _index_version(path)
    return version is not None and version in unreleased_versions


def forbidden_index_changes(
    changes: list[ChangedPath],
    *,
    unreleased_versions: set[str] | None = None,
) -> list[ChangedPath]:
    unreleased_versions = unreleased_versions or set()
    forbidden: list[ChangedPath] = []
    for change in changes:
        status = change.status[0]
        if status == "A":
            continue

        changed_index_paths = [
            path for path in (change.path, change.old_path) if path is not None and _is_package_index(path)
        ]
        if not changed_index_paths:
            continue
        if all(_is_unreleased_index_path(path, unreleased_versions) for path in changed_index_paths):
            continue
        else:
            forbidden.append(change)
    return forbidden


def _git_name_status(base: str) -> str:
    cmd = [
        "git",
        "diff",
        "--name-status",
        "--find-renames",
        f"{base}...HEAD",
        "--",
        "docs",
    ]
    return subprocess.check_output(cmd, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Git ref to compare against, such as upstream/main.")
    args = parser.parse_args()

    changes = parse_name_status(_git_name_status(args.base))
    forbidden = forbidden_index_changes(changes, unreleased_versions=_read_unreleased_versions())
    if not forbidden:
        return 0

    print("Published package index files are immutable. Forbidden changes:")
    for change in forbidden:
        if change.old_path is not None:
            print(f"  {change.status}\t{change.old_path}\t{change.path}")
        else:
            print(f"  {change.status}\t{change.path}")
    print()
    print("Add a new versioned docs directory, or keep the index manifest status as unreleased while editing it.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
