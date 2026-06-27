# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
from pathlib import Path


def _load_create_index():
    module_path = Path(__file__).with_name("create_index.py")
    spec = importlib.util.spec_from_file_location("create_index", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


create_index = _load_create_index()


def test_collect_index_lines_groups_release_assets_by_project():
    assets = [
        {
            "name": "natten-0.21.6.dev5+cu130.torch210-cp313-cp313-linux_x86_64.whl",
            "url": "https://github.com/example/releases/download/v1.0.0/natten.whl",
            "digest": "sha256:abc123",
        },
        {
            "name": "flash_attn-2.7.4.post1+cu130.torch29-cp313-cp313-linux_x86_64.whl",
            "url": "https://github.com/example/releases/download/v1.0.0/flash_attn.whl",
            "digest": "sha256:def456",
        },
        {
            "name": "build.log",
            "url": "https://github.com/example/releases/download/v1.0.0/build.log",
            "digest": "sha256:ignored",
        },
    ]

    all_lines = create_index._collect_index_lines(assets=assets)

    assert set(all_lines) == {"flash-attn", "natten"}
    assert {line.name for line in all_lines["natten"]} == {
        "natten-0.21.6.dev5+cu130.torch210-cp313-cp313-linux_x86_64.whl"
    }
    assert {line.url for line in all_lines["flash-attn"]} == {
        "https://github.com/example/releases/download/v1.0.0/flash_attn.whl#sha256=def456"
    }


def test_collect_index_lines_includes_wheels_file_urls(tmp_path):
    wheels_file = tmp_path / "wheels.txt"
    wheels_file.write_text(
        "\n".join(
            [
                "# external wheels",
                "https://download.pytorch.org/whl/cu130/torch-2.10.0%2Bcu130-cp313-cp313-manylinux_2_28_x86_64.whl#sha256=abc",
                "",
                "https://download.pytorch.org/whl/cu130/torchvision-0.25.0%2Bcu130-cp313-cp313-manylinux_2_28_x86_64.whl#sha256=def",
            ]
        )
        + "\n"
    )

    all_lines = create_index._collect_index_lines(assets=[], wheels_file=wheels_file)

    assert set(all_lines) == {"torch", "torchvision"}
    assert {line.name for line in all_lines["torch"]} == {"torch-2.10.0+cu130-cp313-cp313-manylinux_2_28_x86_64.whl"}


def test_write_index_writes_global_and_package_indices(tmp_path):
    all_lines = {
        "natten": {
            create_index._IndexLine(
                "natten-0.21.6.dev5+cu130.torch210-cp313-cp313-linux_x86_64.whl",
                "https://github.com/example/releases/download/v1.0.0/natten.whl#sha256=abc",
            )
        },
        "xformers": {
            create_index._IndexLine(
                "xformers-0.0.33+cu130.torch29-cp39-abi3-linux_x86_64.whl",
                "https://github.com/example/releases/download/v1.0.0/xformers.whl?download=1&asset=wheel",
            )
        },
    }

    create_index._write_index(tmp_path, all_lines)

    assert (
        (tmp_path / "index.html").read_text()
        == """<!DOCTYPE html>
<html>
<body>
<a href='natten/'>natten</a><br>
<a href='xformers/'>xformers</a><br>
</body>
</html>
"""
    )
    assert "sha256=abc" in (tmp_path / "natten" / "index.html").read_text()
    assert "download=1&amp;asset=wheel" in (tmp_path / "xformers" / "index.html").read_text()
