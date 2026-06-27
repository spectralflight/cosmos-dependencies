# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Write a JSON provenance sidecar for a built wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_build_env(assignments: list[str]) -> dict[str, str]:
    build_env: dict[str, str] = {}
    for assignment in assignments:
        key, separator, value = assignment.partition("=")
        if not separator:
            raise ValueError(f"build env assignment must be KEY=VALUE: {assignment}")
        build_env[key] = value
    return build_env


def build_provenance(args: argparse.Namespace) -> dict:
    wheel = Path(args.wheel)
    build_log = Path(args.build_log)
    return {
        "schema_version": 1,
        "package": args.package_name,
        "package_version": args.package_version,
        "python_version": args.python_version,
        "torch_version": args.torch_version,
        "cuda_version": args.cuda_version,
        "local_version_suffix": args.local_version_suffix,
        "output_name": args.output_name,
        "git_commit": args.git_commit,
        "git_dirty": args.git_dirty == "true",
        "docker_image": args.docker_image,
        "platform": {
            "machine": platform.machine(),
            "system": platform.system(),
        },
        "build_env": _parse_build_env(args.build_env),
        "wheel": {
            "filename": wheel.name,
            "sha256": _sha256(wheel),
            "size": wheel.stat().st_size,
        },
        "build_log": {
            "filename": build_log.name,
            "sha256": _sha256(build_log),
            "size": build_log.stat().st_size,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True)
    parser.add_argument("--build-log", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--package-version", required=True)
    parser.add_argument("--python-version", required=True)
    parser.add_argument("--torch-version", required=True)
    parser.add_argument("--cuda-version", required=True)
    parser.add_argument("--local-version-suffix", default="")
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--git-dirty", choices=["true", "false"], required=True)
    parser.add_argument("--docker-image", default="")
    parser.add_argument("--build-env", action="append", default=[])
    args = parser.parse_args()

    Path(args.output).write_text(json.dumps(build_provenance(args), indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
