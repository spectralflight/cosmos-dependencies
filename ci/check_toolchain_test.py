# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import re
from pathlib import Path


def _load_check_toolchain():
    module_path = Path(__file__).with_name("check_toolchain.py")
    spec = importlib.util.spec_from_file_location("check_toolchain", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


check_toolchain = _load_check_toolchain()


def test_docker_args_reads_quoted_values():
    args = check_toolchain._docker_args(
        'ARG COSMOS_DEPS_UV_VERSION="0.11.23"\nARG COSMOS_DEPS_JUST_LINUX_X64_SHA256="abc123"\n'
    )

    assert args == {
        "COSMOS_DEPS_UV_VERSION": "0.11.23",
        "COSMOS_DEPS_JUST_LINUX_X64_SHA256": "abc123",
    }


def test_platform_record_requires_sha256_and_https():
    record = {
        "platforms.linux-x64": {
            "checksum": "sha256:" + "a" * 64,
            "url": "https://example.com/tool.tar.gz",
        }
    }

    assert check_toolchain._platform_record(record, "linux-x64", tool="tool") == {
        "checksum": "a" * 64,
        "url": "https://example.com/tool.tar.gz",
    }


def test_forbidden_patterns_catch_mise_exec_uvx_without_flagging_policy_prose():
    uvx_pattern = next(pattern for pattern in check_toolchain.FORBIDDEN_PATTERNS if "uvx" in pattern)

    assert re.search(uvx_pattern, "mise exec -- uvx pip-licenses\n")
    assert not re.search(uvx_pattern, "Do not use `uvx` in committed workflows.\n")
