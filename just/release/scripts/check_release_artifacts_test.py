# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path


def _load_check_release_artifacts():
    module_path = Path(__file__).with_name("check_release_artifacts.py")
    spec = importlib.util.spec_from_file_location("check_release_artifacts", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


check_release_artifacts = _load_check_release_artifacts()


def _load_write_wheel_legal_sidecars():
    module_path = Path(__file__).resolve().parents[2] / "license" / "scripts" / "write_wheel_legal_sidecars.py"
    spec = importlib.util.spec_from_file_location("write_wheel_legal_sidecars", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


write_wheel_legal_sidecars = _load_write_wheel_legal_sidecars()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_wheel(path: Path, metadata: str | None = None, extra_files: dict[str, str] | None = None) -> bytes:
    metadata = (
        metadata
        or """Metadata-Version: 2.4
Name: pkg
Version: 1.0.0
License-Expression: MIT
"""
    )
    with zipfile.ZipFile(path, "w") as wheel:
        wheel.writestr("pkg-1.0.0.dist-info/METADATA", metadata)
        wheel.writestr("pkg-1.0.0.dist-info/WHEEL", "Wheel-Version: 1.0\n")
        for name, content in (extra_files or {}).items():
            wheel.writestr(name, content)
    return path.read_bytes()


def _write_valid_sidecars(
    wheel: Path,
    *,
    wheel_bytes: bytes | None = None,
    build_env: dict[str, str] | None = None,
    legal: bool = True,
) -> None:
    log = wheel.with_name(wheel.name + ".build.log")
    provenance = wheel.with_name(wheel.name + ".build.json")
    if wheel_bytes is None:
        wheel_bytes = wheel.read_bytes()
    log_bytes = b"log"
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
                "build_env": build_env or {},
                "wheel": {"filename": wheel.name, "sha256": _sha256(wheel_bytes), "size": len(wheel_bytes)},
                "build_log": {"filename": log.name, "sha256": _sha256(log_bytes), "size": len(log_bytes)},
            }
        )
    )
    if legal:
        write_wheel_legal_sidecars.write_sidecars(wheel)


def test_check_wheel_requires_sidecars(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    _write_wheel(wheel)

    errors = check_release_artifacts.check_wheel(wheel)

    assert any("missing build log" in error for error in errors)
    assert any("missing provenance" in error for error in errors)


def test_check_wheel_accepts_valid_sidecars(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    wheel_bytes = _write_wheel(wheel)
    _write_valid_sidecars(wheel, wheel_bytes=wheel_bytes)

    assert check_release_artifacts.check_wheel(wheel) == []


def test_check_wheel_rejects_stale_provenance_hash(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    log = tmp_path / (wheel.name + ".build.log")
    provenance = tmp_path / (wheel.name + ".build.json")
    _write_wheel(wheel)
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


def test_check_wheel_rejects_sensitive_build_env_keys(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    wheel_bytes = _write_wheel(wheel)
    _write_valid_sidecars(wheel, wheel_bytes=wheel_bytes, build_env={"MY_SECRET_TOKEN": "redacted"})

    errors = check_release_artifacts.check_wheel(wheel)

    assert any("sensitive-looking keys" in error for error in errors)


def test_check_wheel_rejects_missing_license_evidence(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    wheel_bytes = _write_wheel(
        wheel,
        """Metadata-Version: 2.4
Name: pkg
Version: 1.0.0
License: UNKNOWN
""",
    )
    _write_valid_sidecars(wheel, wheel_bytes=wheel_bytes)

    errors = check_release_artifacts.check_wheel(wheel)

    assert any("no license evidence" in error for error in errors)


def test_check_wheel_accepts_license_file_evidence(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    wheel_bytes = _write_wheel(
        wheel,
        """Metadata-Version: 2.4
Name: pkg
Version: 1.0.0
License-File: LICENSE
""",
        {"pkg-1.0.0.dist-info/licenses/LICENSE": "Permission granted.\n"},
    )
    _write_valid_sidecars(wheel, wheel_bytes=wheel_bytes)

    assert check_release_artifacts.check_wheel(wheel) == []


def test_check_wheel_rejects_missing_declared_license_file(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    wheel_bytes = _write_wheel(
        wheel,
        """Metadata-Version: 2.4
Name: pkg
Version: 1.0.0
License-File: LICENSE
""",
    )
    _write_valid_sidecars(wheel, wheel_bytes=wheel_bytes, legal=False)

    errors = check_release_artifacts.check_wheel(wheel)

    assert any("declared but not present" in error for error in errors)


def test_upload_files_for_wheels_orders_sidecars_before_wheel(tmp_path):
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"

    assert check_release_artifacts.upload_files_for_wheels([wheel]) == [
        tmp_path / "pkg-1.0.0-py3-none-any.whl.build.log",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.build.json",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.licenses.json",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.attributions.md",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.sbom.cdx.json",
        wheel,
    ]
