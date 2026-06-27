#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Check stable index manifests for append-only release references."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

from cosmos_dependencies.index_manifest import IndexManifest, load_index_manifest_text


@dataclass(frozen=True)
class ManifestError:
    path: str
    message: str


def _manifest_path_index_name(path: str) -> str:
    return Path(path).parent.name


def _load_manifest_from_text(path: str, text: str) -> IndexManifest:
    manifest = load_index_manifest_text(text, source=path)
    expected_index_name = _manifest_path_index_name(path)
    if manifest.index_name != expected_index_name:
        raise ValueError(f"{path} index_name must match its directory name: {expected_index_name}")
    return manifest


def _git_manifest_paths(ref: str) -> set[str] | None:
    cmd = ["git", "ls-tree", "-r", "--name-only", ref, "--", "indices"]
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return {path for path in result.stdout.splitlines() if path.endswith("/manifest.json")}


def _jj_rev_candidates(ref: str) -> list[str]:
    candidates = [ref]
    if ref.startswith("refs/remotes/"):
        remote_ref = ref.removeprefix("refs/remotes/")
        remote, _, branch = remote_ref.partition("/")
        if remote and branch:
            candidates.insert(0, f"{branch}@{remote}")
            candidates.append(branch)
    elif "/" in ref and "@" not in ref:
        remote, branch = ref.split("/", 1)
        candidates.insert(0, f"{branch}@{remote}")
        candidates.append(branch)
    return list(dict.fromkeys(candidates))


def _jj_run_with_ref(ref: str, command: list[str]) -> str | None:
    for candidate in _jj_rev_candidates(ref):
        cmd = [arg if arg != "{rev}" else candidate for arg in command]
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if result.returncode == 0:
            return result.stdout
    return None


def _jj_manifest_paths(ref: str) -> set[str]:
    output = _jj_run_with_ref(ref, ["jj", "--no-pager", "file", "list", "-r", "{rev}", "indices"])
    if output is None:
        return set()
    return {path for path in output.splitlines() if path.endswith("/manifest.json")}


def _base_manifest_paths(ref: str) -> set[str]:
    git_paths = _git_manifest_paths(ref)
    if git_paths is not None:
        return git_paths
    return _jj_manifest_paths(ref)


def _worktree_manifest_paths(indices_dir: Path = Path("indices")) -> set[str]:
    return {str(path) for path in indices_dir.glob("*/manifest.json")}


def _git_show(ref: str, path: str) -> str | None:
    cmd = ["git", "show", f"{ref}:{path}"]
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def _jj_show(ref: str, path: str) -> str | None:
    return _jj_run_with_ref(ref, ["jj", "--no-pager", "file", "show", "-r", "{rev}", path])


def _vcs_show(ref: str, path: str) -> str | None:
    old_text = _git_show(ref, path)
    if old_text is not None:
        return old_text
    return _jj_show(ref, path)


def check_manifest_change(
    path: str,
    *,
    old_text: str | None,
    new_text: str | None,
) -> list[ManifestError]:
    errors: list[ManifestError] = []
    try:
        old_manifest = _load_manifest_from_text(path, old_text) if old_text is not None else None
    except ValueError as exc:
        return [ManifestError(path=path, message=str(exc))]
    try:
        new_manifest = _load_manifest_from_text(path, new_text) if new_text is not None else None
    except ValueError as exc:
        return [ManifestError(path=path, message=str(exc))]

    if old_manifest is None:
        return errors

    if old_manifest.stability != "stable":
        return errors

    if new_manifest is None:
        return [ManifestError(path=path, message="stable manifest was deleted")]

    if new_manifest.stability != "stable":
        errors.append(ManifestError(path=path, message="stable manifest cannot become unstable"))

    old_releases = set(old_manifest.releases)
    new_releases = set(new_manifest.releases)
    removed_releases = sorted(old_releases - new_releases)
    for release in removed_releases:
        errors.append(
            ManifestError(
                path=path,
                message=f"stable manifest removed release {release.repo} {release.tag}",
            )
        )
    return errors


def check_manifests_against_base(base: str) -> list[ManifestError]:
    paths = _base_manifest_paths(base) | _worktree_manifest_paths()
    errors: list[ManifestError] = []
    for path in sorted(paths):
        old_text = _vcs_show(base, path)
        new_path = Path(path)
        new_text = new_path.read_text() if new_path.exists() else None
        errors.extend(check_manifest_change(path, old_text=old_text, new_text=new_text))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Git ref to compare against, such as upstream/main.")
    args = parser.parse_args()

    errors = check_manifests_against_base(args.base)
    if not errors:
        return 0

    print("Stable index manifests are append-only. Forbidden changes:")
    for error in errors:
        print(f"  {error.path}: {error.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
