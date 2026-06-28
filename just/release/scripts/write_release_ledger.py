#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Write a deterministic release artifact ledger and digest file."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from pathlib import Path

from pai_deps.release_artifacts import wheel_upload_names


def _expand_patterns(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = [Path(path) for path in glob.glob(pattern, recursive=True)]
        path = Path(pattern)
        if not matches and path.is_file():
            matches = [path]
        files.extend(matches)
    return sorted({path for path in files if path.is_file()})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path, *, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def collect_release_artifacts(paths: list[Path]) -> list[Path]:
    artifacts = set(paths)
    for wheel in paths:
        if not wheel.name.endswith(".whl"):
            continue
        for name in wheel_upload_names(wheel.name):
            artifact = wheel.with_name(name)
            if not artifact.is_file():
                raise ValueError(f"{wheel}: missing required release artifact {artifact.name}")
            artifacts.add(artifact)

    by_name: dict[str, Path] = {}
    for artifact in artifacts:
        existing = by_name.get(artifact.name)
        if existing is not None and existing.resolve() != artifact.resolve():
            raise ValueError(f"duplicate release asset name {artifact.name}: {existing} and {artifact}")
        by_name[artifact.name] = artifact
    return sorted(artifacts, key=lambda path: path.name)


def build_ledger(*, artifacts: list[Path], repo: str, release_tag: str, base: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "repo": repo,
        "release_tag": release_tag,
        "artifact_count": len(artifacts),
        "artifacts": [
            {
                "name": artifact.name,
                "path": _display_path(artifact, base=base),
                "sha256": _sha256(artifact),
                "size": artifact.stat().st_size,
            }
            for artifact in artifacts
        ],
    }


def write_ledger(*, ledger: dict[str, object], output: Path) -> tuple[Path, Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    digest_path = output.with_name(output.name + ".sha256")
    digest_path.write_text(f"{_sha256(output)}  {output.name}\n")
    return output, digest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patterns", nargs="+", help="Release artifact files or glob patterns.")
    parser.add_argument("--output", type=Path, required=True, help="Ledger JSON output path.")
    parser.add_argument("--repo", default="", help="Release repository.")
    parser.add_argument("--release-tag", default="", help="Release tag.")
    args = parser.parse_args()

    paths = _expand_patterns(args.patterns)
    if not paths:
        print("Error: no release artifacts matched.", file=sys.stderr)
        return 1
    try:
        artifacts = collect_release_artifacts(paths)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    ledger = build_ledger(artifacts=artifacts, repo=args.repo, release_tag=args.release_tag, base=Path.cwd())
    for path in write_ledger(ledger=ledger, output=args.output):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
