# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

DEFAULT_REPO = "spectralflight/pai-deps"
Stability = Literal["stable", "unstable"]


@dataclass(frozen=True, order=True)
class ReleaseRef:
    repo: str
    tag: str


@dataclass(frozen=True)
class IndexManifest:
    index_name: str
    stability: Stability
    default_repo: str
    releases: tuple[ReleaseRef, ...]


def _require_string(table: Mapping[str, Any], key: str, source: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{source} must contain a non-empty string field: {key}")
    return value


def _require_stability(table: Mapping[str, Any], source: str) -> Stability:
    stability = _require_string(table, "stability", source)
    if stability not in {"stable", "unstable"}:
        raise ValueError(f"{source} stability must be 'stable' or 'unstable'")
    return stability


def load_index_manifest_text(
    text: str,
    *,
    source: str,
    fallback_repo: str = DEFAULT_REPO,
) -> IndexManifest:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{source} must contain a JSON object")

    if data.get("schema_version") != 1:
        raise ValueError(f"{source} must contain schema_version 1")

    index_name = _require_string(data, "index_name", source)
    stability = _require_stability(data, source)

    default_repo = data.get("default_repo", fallback_repo)
    if not isinstance(default_repo, str) or not default_repo:
        raise ValueError(f"{source} default_repo must be a non-empty string when set")

    raw_releases = data.get("releases", [])
    if not isinstance(raw_releases, list):
        raise ValueError(f"{source} releases must be a list")

    releases: list[ReleaseRef] = []
    for index, raw_release in enumerate(raw_releases):
        release_source = f"{source} releases[{index}]"
        if not isinstance(raw_release, dict):
            raise ValueError(f"{release_source} must be a JSON object")
        tag = _require_string(raw_release, "tag", release_source)
        repo = raw_release.get("repo", default_repo)
        if not isinstance(repo, str) or not repo:
            raise ValueError(f"{release_source} repo must be a non-empty string when set")
        releases.append(ReleaseRef(repo=repo, tag=tag))

    return IndexManifest(
        index_name=index_name,
        stability=stability,
        default_repo=default_repo,
        releases=tuple(releases),
    )


def load_index_manifest(
    manifest_path: Path,
    *,
    fallback_repo: str = DEFAULT_REPO,
) -> IndexManifest:
    return load_index_manifest_text(
        manifest_path.read_text(),
        source=str(manifest_path),
        fallback_repo=fallback_repo,
    )


def load_index_manifests(indices_dir: Path = Path("indices")) -> dict[str, IndexManifest]:
    manifests: dict[str, IndexManifest] = {}
    for manifest_path in indices_dir.glob("*/manifest.json"):
        manifest = load_index_manifest(manifest_path)
        manifests[manifest_path.parent.name] = manifest
    return manifests
