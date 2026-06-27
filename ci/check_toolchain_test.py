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
        'ARG PAI_DEPS_UV_VERSION="0.11.23"\nARG PAI_DEPS_JUST_LINUX_X64_SHA256="abc123"\n'
    )

    assert args == {
        "PAI_DEPS_UV_VERSION": "0.11.23",
        "PAI_DEPS_JUST_LINUX_X64_SHA256": "abc123",
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


def test_check_just_argument_forwarding_rejects_variadic_passthrough(tmp_path: Path):
    justfile = tmp_path / ".just"
    justfile.write_text(
        """
package *args:
    echo {{ args }}
"""
    )

    errors = check_toolchain.check_just_argument_forwarding([justfile])

    assert len(errors) == 2
    assert all("just recipes must not" in error for error in errors)


def test_check_forbidden_public_artifacts_rejects_video_codec_sdk_bundle(tmp_path: Path):
    sdk_dir = tmp_path / "packages" / "decord" / "Video_Codec_SDK_13.0.19"
    sdk_dir.mkdir(parents=True)

    errors = check_toolchain.check_forbidden_public_artifacts(tmp_path)

    assert errors == [
        "packages/decord/Video_Codec_SDK_13.0.19: do not vendor full NVIDIA Video Codec SDK bundles in the public repo"
    ]
