#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Check wheel build-log and provenance sidecars before release upload."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "package",
    "package_version",
    "python_version",
    "torch_version",
    "cuda_version",
    "output_name",
    "git_commit",
    "git_dirty",
    "docker_image",
    "platform",
    "build_env",
    "wheel",
    "build_log",
}
SENSITIVE_BUILD_ENV_RE = re.compile(
    r"(?:^|_)(?:TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE_KEY|CREDENTIAL|API_KEY|ACCESS_KEY|SESSION_TOKEN)(?:_|$)"
)
LICENSE_FILE_RE = re.compile(r"^(?:licen[cs]e|copying|notice|authors?)(?:[.-].*)?$", re.IGNORECASE)


def _expand_patterns(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = [Path(path) for path in glob.glob(pattern, recursive=True)]
        path = Path(pattern)
        if not matches and path.is_file():
            matches = [path]
        files.extend(matches)
    return sorted({path for path in files if path.is_file()})


def _wheel_paths(files: list[Path]) -> list[Path]:
    return sorted({path for path in files if path.name.endswith(".whl")})


def upload_files_for_wheels(wheels: list[Path]) -> list[Path]:
    """Return sidecar-first upload order for wheel release artifacts."""

    files: list[Path] = []
    for wheel in sorted(wheels):
        files.extend(
            [
                wheel.with_name(wheel.name + ".build.log"),
                wheel.with_name(wheel.name + ".build.json"),
                wheel,
            ]
        )
    return files


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_hash_table(table: Any, *, source: Path, key: str, filename: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(table, dict):
        return [f"{source}: {key} must be an object"]
    if table.get("filename") != filename:
        errors.append(f"{source}: {key}.filename={table.get('filename')!r}, expected {filename!r}")
    sha256 = table.get("sha256")
    if not isinstance(sha256, str) or not SHA256_RE.fullmatch(sha256):
        errors.append(f"{source}: {key}.sha256 must be a lowercase sha256 hex digest")
    size = table.get("size")
    if not isinstance(size, int) or size <= 0:
        errors.append(f"{source}: {key}.size must be a positive integer")
    return errors


def _check_file_hash_table(path: Path, table: Any, *, source: Path, key: str) -> list[str]:
    errors = _check_hash_table(table, source=source, key=key, filename=path.name)
    if not isinstance(table, dict):
        return errors
    actual_sha256 = _sha256(path)
    if table.get("sha256") != actual_sha256:
        errors.append(f"{source}: {key}.sha256 does not match {path.name}")
    actual_size = path.stat().st_size
    if table.get("size") != actual_size:
        errors.append(f"{source}: {key}.size={table.get('size')!r}, expected {actual_size}")
    return errors


def _check_provenance(wheel: Path, provenance_path: Path, build_log: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(provenance_path.read_text())
    except json.JSONDecodeError as error:
        return [f"{provenance_path}: invalid JSON: {error}"]
    if not isinstance(data, dict):
        return [f"{provenance_path}: provenance must be a JSON object"]
    if data.get("schema_version") != 1:
        errors.append(f"{provenance_path}: schema_version must be 1")
    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        errors.append(f"{provenance_path}: missing fields: {', '.join(missing)}")
    if not isinstance(data.get("git_dirty"), bool):
        errors.append(f"{provenance_path}: git_dirty must be boolean")
    build_env = data.get("build_env")
    if not isinstance(build_env, dict):
        errors.append(f"{provenance_path}: build_env must be an object")
    else:
        sensitive_keys = sorted(
            key for key in build_env if isinstance(key, str) and SENSITIVE_BUILD_ENV_RE.search(key.upper())
        )
        if sensitive_keys:
            errors.append(f"{provenance_path}: build_env contains sensitive-looking keys: {', '.join(sensitive_keys)}")
    errors.extend(_check_file_hash_table(wheel, data.get("wheel"), source=provenance_path, key="wheel"))
    errors.extend(_check_file_hash_table(build_log, data.get("build_log"), source=provenance_path, key="build_log"))
    return errors


def _wheel_license_file_exists(names: set[str], *, dist_info_dir: str, license_file: str) -> bool:
    normalized = license_file.strip().lstrip("/")
    candidates = {
        normalized,
        f"{dist_info_dir}/{normalized}",
        f"{dist_info_dir}/licenses/{Path(normalized).name}",
    }
    return any(candidate in names for candidate in candidates)


def _dist_info_license_files(names: set[str], *, dist_info_dir: str) -> list[str]:
    prefix = f"{dist_info_dir}/"
    license_prefix = f"{dist_info_dir}/licenses/"
    files: list[str] = []
    for name in sorted(names):
        if not name.startswith(prefix) or name.endswith("/"):
            continue
        relative = name.removeprefix(prefix)
        if name.startswith(license_prefix) or LICENSE_FILE_RE.fullmatch(Path(relative).name):
            files.append(name)
    return files


def _check_wheel_license_metadata(wheel: Path) -> list[str]:
    errors: list[str] = []
    try:
        with zipfile.ZipFile(wheel) as archive:
            names = set(archive.namelist())
            metadata_paths = sorted(name for name in names if name.endswith(".dist-info/METADATA"))
            if len(metadata_paths) != 1:
                return [f"{wheel}: expected exactly one .dist-info/METADATA file, found {len(metadata_paths)}"]
            metadata_path = metadata_paths[0]
            dist_info_dir = metadata_path.rsplit("/", 1)[0]
            metadata = Parser().parsestr(archive.read(metadata_path).decode("utf-8", errors="replace"))
    except zipfile.BadZipFile:
        return [f"{wheel}: invalid wheel zip archive"]

    declared_license_files = [value.strip() for value in metadata.get_all("License-File", []) if value.strip()]
    missing_license_files = [
        value
        for value in declared_license_files
        if not _wheel_license_file_exists(names, dist_info_dir=dist_info_dir, license_file=value)
    ]
    for license_file in missing_license_files:
        errors.append(f"{wheel}: License-File {license_file!r} is declared but not present in the wheel")

    license_expression = (metadata.get("License-Expression") or "").strip()
    license_field = (metadata.get("License") or "").strip()
    license_classifiers = [
        classifier for classifier in metadata.get_all("Classifier", []) if classifier.strip().startswith("License ::")
    ]
    dist_info_license_files = _dist_info_license_files(names, dist_info_dir=dist_info_dir)
    has_license_field = bool(license_field and license_field.upper() != "UNKNOWN")
    if not any(
        (license_expression, has_license_field, license_classifiers, declared_license_files, dist_info_license_files)
    ):
        errors.append(
            f"{wheel}: wheel metadata has no license evidence; add License-Expression, license classifiers, "
            "or license files"
        )
    return errors


def check_wheel(wheel: Path) -> list[str]:
    errors: list[str] = []
    build_log = wheel.with_name(wheel.name + ".build.log")
    provenance = wheel.with_name(wheel.name + ".build.json")
    if not build_log.is_file():
        errors.append(f"{wheel}: missing build log sidecar {build_log.name}")
    if not provenance.is_file():
        errors.append(f"{wheel}: missing provenance sidecar {provenance.name}")
    if build_log.is_file() and provenance.is_file():
        errors.extend(_check_provenance(wheel, provenance, build_log))
    errors.extend(_check_wheel_license_metadata(wheel))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patterns", nargs="+", help="Wheel files or glob patterns.")
    parser.add_argument("--allow-empty", action="store_true", help="Pass when no wheels match.")
    parser.add_argument(
        "--print-upload-files",
        action="store_true",
        help="Print sidecar-first wheel triplets for a release upload after validation.",
    )
    args = parser.parse_args()

    files = _expand_patterns(args.patterns)
    wheels = _wheel_paths(files)
    if not wheels:
        if args.allow_empty:
            print("No wheel artifacts matched.")
            return 0
        print("Error: no wheel artifacts matched.", file=sys.stderr)
        return 1

    errors: list[str] = []
    for wheel in wheels:
        errors.extend(check_wheel(wheel))
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    if args.print_upload_files:
        for path in upload_files_for_wheels(wheels):
            print(path)
    else:
        for wheel in wheels:
            print(wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
