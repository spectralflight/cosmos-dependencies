#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Fail when a stable package index under docs/ is changed unsafely.

New index files and unstable indices are allowed. Stable package index files
are append-only because downstream lockfiles can rely on their wheel URLs and
hashes.
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

from cosmos_dependencies.index_manifest import load_index_manifests


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


def parse_jj_summary(output: str) -> list[ChangedPath]:
    changes: list[ChangedPath] = []
    for line in output.splitlines():
        if not line:
            continue
        status, path = line.split(maxsplit=1)
        if status not in {"A", "M", "D"}:
            raise ValueError(f"Unexpected jj summary line: {line!r}")
        changes.append(ChangedPath(status=status, path=path))
    return changes


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href is not None:
            self.links.add(href)


def _links_from_html(text: str) -> set[str]:
    parser = _LinkParser()
    parser.feed(text)
    return parser.links


def _read_index_stabilities(indices_dir: Path = Path("indices")) -> dict[str, str]:
    return {index_name: manifest.stability for index_name, manifest in load_index_manifests(indices_dir).items()}


def _is_unstable_index_path(path: str, index_stabilities: dict[str, str]) -> bool:
    version = _index_version(path)
    return version is not None and index_stabilities.get(version) == "unstable"


def _append_only_html_change(
    path: str,
    *,
    old_texts: dict[str, str],
    new_texts: dict[str, str],
) -> bool:
    old_text = old_texts.get(path)
    new_text = new_texts.get(path)
    if old_text is None or new_text is None:
        return False
    return _links_from_html(old_text) <= _links_from_html(new_text)


def forbidden_index_changes(
    changes: list[ChangedPath],
    *,
    index_stabilities: dict[str, str] | None = None,
    old_texts: dict[str, str] | None = None,
    new_texts: dict[str, str] | None = None,
) -> list[ChangedPath]:
    index_stabilities = index_stabilities or {}
    old_texts = old_texts or {}
    new_texts = new_texts or {}
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
        if all(_is_unstable_index_path(path, index_stabilities) for path in changed_index_paths):
            continue
        if (
            status == "M"
            and change.old_path is None
            and _is_package_index(change.path)
            and _append_only_html_change(change.path, old_texts=old_texts, new_texts=new_texts)
        ):
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
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)
    return result.stdout


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


def _jj_name_status(base: str) -> str:
    output = _jj_run_with_ref(
        base,
        [
            "jj",
            "--no-pager",
            "diff",
            "--summary",
            "--from",
            "{rev}",
            "--to",
            "@",
            "docs",
        ],
    )
    if output is None:
        raise subprocess.CalledProcessError(returncode=1, cmd=["jj", "diff", "--summary", "--from", base])
    return output


def _changed_paths(base: str) -> list[ChangedPath]:
    try:
        return parse_name_status(_git_name_status(base))
    except (FileNotFoundError, subprocess.CalledProcessError):
        return parse_jj_summary(_jj_name_status(base))


def _git_show(ref: str, path: str) -> str | None:
    cmd = ["git", "show", f"{ref}:{path}"]
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def _jj_show(ref: str, path: str) -> str | None:
    return _jj_run_with_ref(ref, ["jj", "--no-pager", "file", "show", "-r", "{rev}", path])


def _vcs_show(ref: str, path: str) -> str | None:
    return _git_show(ref, path) or _jj_show(ref, path)


def _read_changed_index_texts(changes: list[ChangedPath], *, base: str) -> tuple[dict[str, str], dict[str, str]]:
    old_texts: dict[str, str] = {}
    new_texts: dict[str, str] = {}
    for change in changes:
        for path in (change.path, change.old_path):
            if path is None or not _is_package_index(path):
                continue
            if path not in old_texts:
                old_text = _vcs_show(base, path)
                if old_text is not None:
                    old_texts[path] = old_text
            if path not in new_texts:
                new_path = Path(path)
                if new_path.exists():
                    new_texts[path] = new_path.read_text()
    return old_texts, new_texts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Git ref to compare against, such as upstream/main.")
    args = parser.parse_args()

    changes = _changed_paths(args.base)
    old_texts, new_texts = _read_changed_index_texts(changes, base=args.base)
    forbidden = forbidden_index_changes(
        changes,
        index_stabilities=_read_index_stabilities(),
        old_texts=old_texts,
        new_texts=new_texts,
    )
    if not forbidden:
        return 0

    print("Stable package index files are append-only. Forbidden changes:")
    for change in forbidden:
        if change.old_path is not None:
            print(f"  {change.status}\t{change.old_path}\t{change.path}")
        else:
            print(f"  {change.status}\t{change.path}")
    print()
    print("Add links without changing existing links, or use an index manifest with stability 'unstable'.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
