# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import textwrap
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DOCKER_BUILD_SCRIPT = ROOT_DIR / "just" / "build" / "scripts" / "docker-build-package.sh"


def test_docker_build_package_preserves_failed_exit_code(tmp_path: Path) -> None:
    script = _copy_wrapper_with_fake_docker_run(tmp_path)
    args_path = tmp_path / "docker-run-args.txt"

    result = subprocess.run(
        [str(script), "cosmos-dummy", "0.1.0", "3.12", "2.9", "build"],
        env=_test_env(args_path, status=17),
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 17
    assert "Docker build attempt 1/1" in result.stdout


def test_docker_build_package_mounts_absolute_output_and_root_mode(tmp_path: Path) -> None:
    script = _copy_wrapper_with_fake_docker_run(tmp_path)
    args_path = tmp_path / "docker-run-args.txt"
    output_dir = tmp_path / "wheelhouse"

    result = subprocess.run(
        [
            str(script),
            "cosmos-dummy",
            "0.1.0",
            "3.12",
            "2.9",
            str(output_dir),
            "--config-settings=--dummy",
        ],
        env=_test_env(args_path, status=0, docker_as_root=True),
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert args_path.read_text().splitlines() == [
        "--cuda-version",
        "12.8.1",
        "--no-tty",
        "--root",
        "--run-arg",
        "-v",
        "--run-arg",
        f"{output_dir}:/cosmos-output",
        "--",
        "bin/build.sh",
        "cosmos-dummy",
        "0.1.0",
        "3.12",
        "2.9",
        "/cosmos-output",
        "--config-settings=--dummy",
    ]


def _copy_wrapper_with_fake_docker_run(tmp_path: Path) -> Path:
    scripts_dir = tmp_path / "just" / "build" / "scripts"
    scripts_dir.mkdir(parents=True)
    script = scripts_dir / "docker-build-package.sh"
    script.write_text(DOCKER_BUILD_SCRIPT.read_text())
    script.chmod(0o755)
    fake_docker_run = scripts_dir / "docker-run.sh"
    fake_docker_run.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            printf "%s\\n" "$@" > "${FAKE_DOCKER_RUN_ARGS}"
            exit "${FAKE_DOCKER_RUN_STATUS}"
            """
        )
    )
    fake_docker_run.chmod(0o755)
    return script


def _test_env(args_path: Path, *, status: int, docker_as_root: bool = False) -> dict[str, str]:
    env = {
        "COSMOS_DEPS_BUILD_ATTEMPTS": "1",
        "FAKE_DOCKER_RUN_ARGS": str(args_path),
        "FAKE_DOCKER_RUN_STATUS": str(status),
        "PATH": os.environ["PATH"],
    }
    if docker_as_root:
        env["COSMOS_DEPS_DOCKER_AS_ROOT"] = "true"
    return env
