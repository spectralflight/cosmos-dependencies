# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
import zipfile
from pathlib import Path

SCAN_SCRIPT = Path(__file__).with_name("scan_release_artifacts.py")


def _fake_gitleaks(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.txt"
    gitleaks = bin_dir / "gitleaks"
    gitleaks.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "${FAKE_GITLEAKS_CALLS}"
scan_path="${!#}"
if grep -R -q FAIL_SCAN "${scan_path}"; then
  exit 1
fi
"""
    )
    gitleaks.chmod(0o755)
    return bin_dir, calls


def _write_wheel(path: Path, *, contents: bytes = b"safe") -> None:
    with zipfile.ZipFile(path, "w") as wheel:
        wheel.writestr("pkg/__init__.py", contents)
        wheel.writestr("pkg-1.0.0.dist-info/METADATA", b"Name: pkg\nVersion: 1.0.0\n")


def _env(tmp_path: Path, bin_dir: Path, calls: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_GITLEAKS_CALLS"] = str(calls)
    env["TMPDIR"] = str(tmp_path)
    return env


def test_scans_wheel_and_existing_sidecars(tmp_path: Path) -> None:
    bin_dir, calls = _fake_gitleaks(tmp_path)
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    _write_wheel(wheel)
    (tmp_path / f"{wheel.name}.build.log").write_text("safe log\n")
    (tmp_path / f"{wheel.name}.build.json").write_text('{"safe": true}\n')
    (tmp_path / f"{wheel.name}.licenses.json").write_text('{"safe": true}\n')
    (tmp_path / f"{wheel.name}.attributions.md").write_text("# safe\n")
    (tmp_path / f"{wheel.name}.sbom.cdx.json").write_text('{"safe": true}\n')

    result = subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), str(wheel)],
        env=_env(tmp_path, bin_dir, calls),
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert len(calls.read_text().splitlines()) == 6


def test_fails_when_extracted_wheel_triggers_gitleaks(tmp_path: Path) -> None:
    bin_dir, calls = _fake_gitleaks(tmp_path)
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    _write_wheel(wheel, contents=b"FAIL_SCAN\n")

    result = subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), str(wheel)],
        env=_env(tmp_path, bin_dir, calls),
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1
    assert "potential secrets" in result.stderr
