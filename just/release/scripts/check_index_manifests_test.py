# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
import sys
from pathlib import Path


def _load_check_index_manifests():
    module_path = Path(__file__).with_name("check_index_manifests.py")
    spec = importlib.util.spec_from_file_location("check_index_manifests", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


check_index_manifests = _load_check_index_manifests()
check_manifest_change = check_index_manifests.check_manifest_change


def _manifest(
    *,
    index_name: str = "cosmos3",
    stability: str = "stable",
    releases: list[dict[str, str]] | None = None,
) -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "index_name": index_name,
            "stability": stability,
            "default_repo": "spectralflight/pai-deps",
            "releases": releases if releases is not None else [{"tag": "cosmos3-20260627.1"}],
        }
    )


def test_check_manifest_change_allows_stable_append_only_releases():
    old_text = _manifest(releases=[{"tag": "cosmos3-20260627.1"}])
    new_text = _manifest(releases=[{"tag": "cosmos3-20260627.1"}, {"tag": "cosmos3-20260727.1"}])

    assert check_manifest_change("indices/cosmos3/manifest.json", old_text=old_text, new_text=new_text) == []


def test_check_manifest_change_blocks_stable_release_removal():
    old_text = _manifest(releases=[{"tag": "cosmos3-20260627.1"}, {"tag": "cosmos3-20260727.1"}])
    new_text = _manifest(releases=[{"tag": "cosmos3-20260727.1"}])

    errors = check_manifest_change("indices/cosmos3/manifest.json", old_text=old_text, new_text=new_text)

    assert len(errors) == 1
    assert "removed release spectralflight/pai-deps cosmos3-20260627.1" in errors[0].message


def test_check_manifest_change_blocks_stable_default_repo_change():
    old_text = _manifest(releases=[{"tag": "cosmos3-20260627.1"}])
    new_manifest = json.loads(old_text)
    new_manifest["default_repo"] = "example/repo"

    errors = check_manifest_change(
        "indices/cosmos3/manifest.json", old_text=old_text, new_text=json.dumps(new_manifest)
    )

    assert [error.message for error in errors] == [
        "stable manifest default_repo cannot change from spectralflight/pai-deps to example/repo",
        "stable manifest removed release spectralflight/pai-deps cosmos3-20260627.1",
    ]


def test_check_manifest_change_blocks_stable_to_unstable():
    old_text = _manifest(stability="stable")
    new_text = _manifest(stability="unstable")

    errors = check_manifest_change("indices/cosmos3/manifest.json", old_text=old_text, new_text=new_text)

    assert [error.message for error in errors] == ["stable manifest cannot become unstable"]


def test_check_manifest_change_allows_unstable_rewrites():
    old_text = _manifest(index_name="cosmos3-scratch", stability="unstable", releases=[{"tag": "scratch-a"}])
    new_text = _manifest(index_name="cosmos3-scratch", stability="unstable", releases=[{"tag": "scratch-b"}])

    assert check_manifest_change("indices/cosmos3-scratch/manifest.json", old_text=old_text, new_text=new_text) == []


def test_check_manifest_change_requires_index_name_to_match_path():
    errors = check_manifest_change(
        "indices/cosmos3/manifest.json",
        old_text=None,
        new_text=_manifest(index_name="other"),
    )

    assert [error.message for error in errors] == [
        "indices/cosmos3/manifest.json index_name must match its directory name: cosmos3"
    ]
