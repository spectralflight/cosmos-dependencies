# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import sys
from pathlib import Path


def _load_copy_release_assets():
    module_path = Path(__file__).with_name("copy_release_assets.py")
    spec = importlib.util.spec_from_file_location("copy_release_assets", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["copy_release_assets"] = module
    spec.loader.exec_module(module)
    return module


copy_release_assets = _load_copy_release_assets()


def test_select_assets_includes_and_excludes_by_glob():
    assets = [
        copy_release_assets.ReleaseAsset("cosmos_dummy-0.1.0.whl"),
        copy_release_assets.ReleaseAsset("cosmos_dummy-0.1.0.whl.build.json"),
        copy_release_assets.ReleaseAsset("cosmos_dummy-0.1.0.whl.build.log"),
        copy_release_assets.ReleaseAsset("README.txt"),
    ]

    selected = copy_release_assets.select_assets(
        assets,
        include=["cosmos_dummy*"],
        exclude=["*.build.log"],
    )

    assert [asset.name for asset in selected] == [
        "cosmos_dummy-0.1.0.whl",
        "cosmos_dummy-0.1.0.whl.build.json",
    ]


def test_select_assets_uses_sorted_output():
    assets = [
        copy_release_assets.ReleaseAsset("z.whl"),
        copy_release_assets.ReleaseAsset("a.whl"),
    ]

    assert [asset.name for asset in copy_release_assets.select_assets(assets, include=["*"], exclude=[])] == [
        "a.whl",
        "z.whl",
    ]


def test_expand_wheel_triplets_adds_required_sidecars():
    assets = [
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl"),
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl.build.json"),
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl.build.log"),
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl.licenses.json"),
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl.attributions.md"),
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl.sbom.cdx.json"),
        copy_release_assets.ReleaseAsset("README.txt"),
    ]

    expanded = copy_release_assets.expand_wheel_triplets([copy_release_assets.ReleaseAsset("pkg-1.0.0.whl")], assets)

    assert [asset.name for asset in expanded] == [
        "pkg-1.0.0.whl.build.log",
        "pkg-1.0.0.whl.build.json",
        "pkg-1.0.0.whl.licenses.json",
        "pkg-1.0.0.whl.attributions.md",
        "pkg-1.0.0.whl.sbom.cdx.json",
        "pkg-1.0.0.whl",
    ]


def test_expand_wheel_triplets_rejects_missing_sidecars():
    assets = [
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl"),
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl.build.json"),
    ]

    try:
        copy_release_assets.expand_wheel_triplets([copy_release_assets.ReleaseAsset("pkg-1.0.0.whl")], assets)
    except ValueError as error:
        assert "missing required release asset sidecar" in str(error)
    else:
        raise AssertionError("expected ValueError")


def test_destination_collisions_reports_matching_asset_names(tmp_path: Path):
    files = [
        tmp_path / "pkg-1.0.0.whl.build.log",
        tmp_path / "pkg-1.0.0.whl.build.json",
        tmp_path / "pkg-1.0.0.whl",
    ]
    assets = [
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl"),
        copy_release_assets.ReleaseAsset("other.whl"),
        copy_release_assets.ReleaseAsset("pkg-1.0.0.whl.build.log"),
    ]

    assert copy_release_assets.destination_collisions(assets, files) == [
        "pkg-1.0.0.whl",
        "pkg-1.0.0.whl.build.log",
    ]
