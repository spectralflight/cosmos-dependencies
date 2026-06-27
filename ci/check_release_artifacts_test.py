# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import hashlib
import importlib.util
import json
from pathlib import Path


def _load_check_release_artifacts():
    module_path = Path(__file__).with_name("check_release_artifacts.py")
    spec = importlib.util.spec_from_file_location("check_release_artifacts", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


check_release_artifacts = _load_check_release_artifacts()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_check_wheel_requires_sidecars(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel")

    errors = check_release_artifacts.check_wheel(wheel)

    assert any("missing build log" in error for error in errors)
    assert any("missing provenance" in error for error in errors)


def test_check_wheel_accepts_valid_sidecars(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    log = tmp_path / (wheel.name + ".build.log")
    provenance = tmp_path / (wheel.name + ".build.json")
    wheel_bytes = b"wheel"
    log_bytes = b"log"
    wheel.write_bytes(wheel_bytes)
    log.write_bytes(log_bytes)
    provenance.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package": "pkg",
                "package_version": "1.0.0",
                "python_version": "3.12",
                "torch_version": "2.9",
                "cuda_version": "12.8.1",
                "output_name": "out",
                "git_commit": "abc123",
                "git_dirty": False,
                "docker_image": "sha256:abc",
                "platform": {"machine": "x86_64", "system": "Linux"},
                "build_env": {},
                "wheel": {"filename": wheel.name, "sha256": _sha256(wheel_bytes), "size": len(wheel_bytes)},
                "build_log": {"filename": log.name, "sha256": _sha256(log_bytes), "size": len(log_bytes)},
            }
        )
    )

    assert check_release_artifacts.check_wheel(wheel) == []


def test_check_wheel_rejects_stale_provenance_hash(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    log = tmp_path / (wheel.name + ".build.log")
    provenance = tmp_path / (wheel.name + ".build.json")
    wheel.write_bytes(b"wheel")
    log.write_bytes(b"log")
    provenance.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package": "pkg",
                "package_version": "1.0.0",
                "python_version": "3.12",
                "torch_version": "2.9",
                "cuda_version": "12.8.1",
                "output_name": "out",
                "git_commit": "abc123",
                "git_dirty": False,
                "docker_image": "sha256:abc",
                "platform": {"machine": "x86_64", "system": "Linux"},
                "build_env": {},
                "wheel": {"filename": wheel.name, "sha256": _sha256(b"old"), "size": len(b"old")},
                "build_log": {"filename": log.name, "sha256": _sha256(b"log"), "size": len(b"log")},
            }
        )
    )

    errors = check_release_artifacts.check_wheel(wheel)

    assert any("wheel.sha256 does not match" in error for error in errors)
    assert any("wheel.size" in error for error in errors)
