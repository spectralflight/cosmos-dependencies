import os
import subprocess
import textwrap
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT_DIR / "bin" / "build.sh"


def _write_fake_build_script(work_dir: Path) -> None:
    bin_dir = work_dir / "bin"
    bin_dir.mkdir()
    fake_build = bin_dir / "_build.sh"
    fake_build.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            env | sort > "${OUTPUT_DIR}/env.txt"
            printf "%s\\n" "$@" > "${OUTPUT_DIR}/args.txt"
            """
        )
    )
    fake_build.chmod(0o755)


def _run_build_script(work_dir: Path, env_file: Path | None = None) -> subprocess.CompletedProcess[str]:
    _write_fake_build_script(work_dir)
    env = {
        "CUDA_VERSION": "12.8",
        "HOST_ONLY_VARIABLE": "must-not-leak",
        "HOME": str(work_dir / "home"),
        "NATTEN_N_WORKERS": "99",
        "PATH": os.environ["PATH"],
        "USER": "tester",
    }
    if env_file is not None:
        env["COSMOS_DEPENDENCIES_ENV_FILE"] = str(env_file)
    return subprocess.run(
        [
            str(BUILD_SCRIPT),
            "cosmos-dummy",
            "0.1.0",
            "3.12",
            "2.9",
            "build",
            "--config-settings=--dummy",
        ],
        cwd=work_dir,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )


def _read_build_env(work_dir: Path) -> str:
    env_files = list((work_dir / "build").glob("*/env.txt"))
    assert len(env_files) == 1
    return env_files[0].read_text()


def test_build_script_loads_explicit_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / "natten.env"
    env_file.write_text(
        textwrap.dedent(
            """\
            # Small local smoke settings.
            MAX_JOBS=1
            export NATTEN_N_WORKERS="2"
            TORCH_CUDA_ARCH_LIST='9.0'
            SPACED_VALUE="hello world"
            """
        )
    )

    result = _run_build_script(tmp_path, env_file)

    assert result.returncode == 0, result.stdout + result.stderr
    build_env = _read_build_env(tmp_path)
    assert "MAX_JOBS=1\n" in build_env
    assert "NATTEN_N_WORKERS=2\n" in build_env
    assert "NATTEN_N_WORKERS=99\n" not in build_env
    assert "TORCH_CUDA_ARCH_LIST=9.0\n" in build_env
    assert "SPACED_VALUE=hello world\n" in build_env
    assert "HOST_ONLY_VARIABLE=must-not-leak\n" not in build_env
    assert "CUDA_VERSION=12.8\n" not in build_env


def test_build_script_rejects_reserved_env_file_variables(tmp_path: Path) -> None:
    env_file = tmp_path / "bad.env"
    env_file.write_text("PACKAGE_NAME=other\n")

    result = _run_build_script(tmp_path, env_file)

    assert result.returncode != 0
    assert "PACKAGE_NAME is controlled by bin/build.sh" in result.stderr
    assert not (tmp_path / "build").exists()
