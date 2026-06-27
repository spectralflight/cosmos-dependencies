# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import json

from ci.check_index_manifests import check_manifest_change


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
            "default_repo": "nvidia-cosmos/cosmos-dependencies",
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
    assert "removed release nvidia-cosmos/cosmos-dependencies cosmos3-20260627.1" in errors[0].message


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
