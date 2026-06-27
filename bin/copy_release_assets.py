# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Copy selected GitHub release assets from one release to another."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class ReleaseAsset:
    name: str


def select_assets(
    assets: list[ReleaseAsset],
    *,
    include: list[str],
    exclude: list[str],
) -> list[ReleaseAsset]:
    selected: list[ReleaseAsset] = []
    for asset in sorted(assets):
        if include and not any(fnmatch.fnmatchcase(asset.name, pattern) for pattern in include):
            continue
        if any(fnmatch.fnmatchcase(asset.name, pattern) for pattern in exclude):
            continue
        selected.append(asset)
    return selected


def _get_release_assets(*, repo: str, tag: str) -> list[ReleaseAsset]:
    cmd = [
        "gh",
        "release",
        "view",
        "--repo",
        repo,
        tag,
        "--json",
        "assets",
    ]
    data = json.loads(subprocess.check_output(cmd, text=True))
    return [ReleaseAsset(name=asset["name"]) for asset in data["assets"]]


def _release_exists(*, repo: str, tag: str) -> bool:
    cmd = ["gh", "release", "view", "--repo", repo, tag]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0


def _download_assets(*, repo: str, tag: str, assets: list[ReleaseAsset], output_dir: Path) -> list[Path]:
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    for asset in assets:
        cmd = [
            "gh",
            "release",
            "download",
            tag,
            "--repo",
            repo,
            "--pattern",
            asset.name,
            "--dir",
            str(output_dir),
        ]
        subprocess.check_call(cmd)
        downloaded.append(output_dir / asset.name)
    return downloaded


def _upload_assets(
    *,
    repo: str,
    tag: str,
    files: list[Path],
    title: str,
    notes: str,
    target: str,
    clobber: bool,
) -> None:
    if not _release_exists(repo=repo, tag=tag):
        cmd = [
            "gh",
            "release",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--notes",
            notes,
            "--target",
            target,
            "--latest=false",
            tag,
        ]
        cmd.extend(str(file) for file in files)
        subprocess.check_call(cmd)
        return

    upload_args = ["--clobber"] if clobber else []
    for file in files:
        subprocess.check_call(["gh", "release", "upload", "--repo", repo, tag, str(file), *upload_args])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", required=True)
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--dest-repo", required=True)
    parser.add_argument("--dest-tag", required=True)
    parser.add_argument("--include", action="append", default=[], help="Asset glob to include; may be repeated.")
    parser.add_argument("--exclude", action="append", default=[], help="Asset glob to exclude; may be repeated.")
    parser.add_argument("--output-dir", type=Path, default=Path("tmp/release-copy"))
    parser.add_argument("--title", default="", help="Destination release title, default: destination tag.")
    parser.add_argument("--notes", default="Copied wheel assets.")
    parser.add_argument("--target", default="", help="Destination release target, default: current HEAD.")
    parser.add_argument("--clobber", action="store_true", help="Replace destination assets with matching names.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print selected assets without downloading or uploading."
    )
    args = parser.parse_args()
    if args.clobber and os.environ.get("COSMOS_DEPS_ALLOW_CLOBBER") != "1":
        raise SystemExit("--clobber requires COSMOS_DEPS_ALLOW_CLOBBER=1.")

    assets = _get_release_assets(repo=args.source_repo, tag=args.source_tag)
    selected_assets = select_assets(assets, include=args.include or ["*"], exclude=args.exclude)
    if not selected_assets:
        raise SystemExit("No source release assets matched the requested filters.")

    for asset in selected_assets:
        print(asset.name)

    if args.dry_run:
        return 0

    target = args.target or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    title = args.title or args.dest_tag
    copy_dir = args.output_dir / args.source_repo.replace("/", "_") / args.source_tag
    files = _download_assets(repo=args.source_repo, tag=args.source_tag, assets=selected_assets, output_dir=copy_dir)
    _upload_assets(
        repo=args.dest_repo,
        tag=args.dest_tag,
        files=files,
        title=title,
        notes=args.notes,
        target=target,
        clobber=args.clobber,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
