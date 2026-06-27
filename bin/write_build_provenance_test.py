# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import importlib.util
from pathlib import Path


def _load_write_build_provenance():
    module_path = Path(__file__).with_name("write_build_provenance.py")
    spec = importlib.util.spec_from_file_location("write_build_provenance", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


write_build_provenance = _load_write_build_provenance()


def test_build_provenance_records_wheel_log_and_explicit_env(tmp_path):
    wheel = tmp_path / "cosmos_dummy-0.1.0+cu128.torch29-py3-none-any.whl"
    wheel.write_bytes(b"wheel")
    build_log = tmp_path / "cosmos_dummy-0.1.0+cu128.torch29-py3-none-any.whl.build.log"
    build_log.write_text("build log")

    provenance = write_build_provenance.build_provenance(
        argparse.Namespace(
            wheel=str(wheel),
            build_log=str(build_log),
            package_name="cosmos-dummy",
            package_version="0.1.0",
            python_version="3.12",
            torch_version="2.9",
            cuda_version="12.8.1",
            local_version_suffix="",
            output_name="out",
            git_commit="abc123",
            git_dirty="true",
            docker_image="sha256:123",
            build_env=["MAX_JOBS=1", "NATTEN_N_WORKERS=2"],
        )
    )

    assert provenance["package"] == "cosmos-dummy"
    assert provenance["build_env"] == {"MAX_JOBS": "1", "NATTEN_N_WORKERS": "2"}
    assert provenance["wheel"]["filename"] == wheel.name
    assert provenance["build_log"]["filename"] == build_log.name
    assert provenance["docker_image"] == "sha256:123"
    assert provenance["git_dirty"] is True
