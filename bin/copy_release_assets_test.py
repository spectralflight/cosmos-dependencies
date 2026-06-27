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
