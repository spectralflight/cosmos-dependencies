#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Write legal and SBOM sidecars for wheel release artifacts."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from email.parser import Parser
from pathlib import Path

LICENSE_FILE_RE = re.compile(r"^(?:licen[cs]e|copying|notice|authors?)(?:[.-].*)?$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class WheelLicenseInfo:
    wheel: Path
    dist_info_dir: str
    name: str
    version: str
    license_expression: str
    license_field: str
    license_classifiers: tuple[str, ...]
    declared_license_files: tuple[str, ...]
    license_files: tuple[str, ...]
    license_file_text: dict[str, str]


def _expand_patterns(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = [Path(path) for path in glob.glob(pattern, recursive=True)]
        path = Path(pattern)
        if not matches and path.is_file():
            matches = [path]
        files.extend(matches)
    return sorted({path for path in files if path.is_file() and path.name.endswith(".whl")})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _license_file_exists(names: set[str], *, dist_info_dir: str, license_file: str) -> bool:
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


def read_wheel_license_info(wheel: Path) -> WheelLicenseInfo:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_paths = sorted(name for name in names if name.endswith(".dist-info/METADATA"))
        if len(metadata_paths) != 1:
            raise ValueError(f"{wheel}: expected exactly one .dist-info/METADATA file, found {len(metadata_paths)}")
        metadata_path = metadata_paths[0]
        dist_info_dir = metadata_path.rsplit("/", 1)[0]
        metadata = Parser().parsestr(archive.read(metadata_path).decode("utf-8", errors="replace"))
        declared_license_files = tuple(value.strip() for value in metadata.get_all("License-File", []) if value.strip())
        missing = [
            value
            for value in declared_license_files
            if not _license_file_exists(names, dist_info_dir=dist_info_dir, license_file=value)
        ]
        if missing:
            raise ValueError(f"{wheel}: declared License-File entries are missing: {', '.join(missing)}")
        license_files = tuple(_dist_info_license_files(names, dist_info_dir=dist_info_dir))
        license_file_text = {
            path: archive.read(path).decode("utf-8", errors="replace")
            for path in license_files
            if not path.endswith("/")
        }
    name = metadata.get("Name") or wheel.name
    version = metadata.get("Version") or ""
    return WheelLicenseInfo(
        wheel=wheel,
        dist_info_dir=dist_info_dir,
        name=name,
        version=version,
        license_expression=(metadata.get("License-Expression") or "").strip(),
        license_field=(metadata.get("License") or "").strip(),
        license_classifiers=tuple(
            classifier
            for classifier in metadata.get_all("Classifier", [])
            if classifier.strip().startswith("License ::")
        ),
        declared_license_files=declared_license_files,
        license_files=license_files,
        license_file_text=license_file_text,
    )


def _license_json(info: WheelLicenseInfo) -> dict[str, object]:
    return {
        "schema_version": 1,
        "wheel": {
            "filename": info.wheel.name,
            "sha256": _sha256(info.wheel),
            "size": info.wheel.stat().st_size,
        },
        "package": {"name": info.name, "version": info.version},
        "metadata": {
            "license_expression": info.license_expression,
            "license": info.license_field,
            "license_classifiers": list(info.license_classifiers),
            "declared_license_files": list(info.declared_license_files),
            "dist_info_license_files": list(info.license_files),
        },
        "license_files": [
            {
                "path": path,
                "sha256": _sha256_bytes(text.encode()),
                "size": len(text.encode()),
            }
            for path, text in sorted(info.license_file_text.items())
        ],
    }


def _attribution_md(info: WheelLicenseInfo) -> str:
    lines = [
        f"# {info.wheel.name} Attributions",
        "",
        f"- Package: `{info.name}`",
        f"- Version: `{info.version}`",
        f"- Wheel SHA256: `{_sha256(info.wheel)}`",
    ]
    if info.license_expression:
        lines.append(f"- License expression: `{info.license_expression}`")
    if info.license_field:
        lines.append(f"- License field: `{info.license_field}`")
    if info.license_classifiers:
        lines.append("- License classifiers:")
        lines.extend(f"  - `{classifier}`" for classifier in info.license_classifiers)
    if info.declared_license_files:
        lines.append("- Declared license files:")
        lines.extend(f"  - `{path}`" for path in info.declared_license_files)
    if not info.license_file_text:
        lines.extend(["", "No license files were found in the wheel; attribution relies on wheel metadata."])
    for path, text in sorted(info.license_file_text.items()):
        lines.extend(["", f"## {path}", "", "```text", text.rstrip(), "```"])
    return "\n".join(lines) + "\n"


def _license_entries(info: WheelLicenseInfo) -> list[dict[str, str]]:
    if info.license_expression:
        return [{"expression": info.license_expression}]
    if info.license_field and info.license_field.upper() != "UNKNOWN":
        return [{"license": {"name": info.license_field}}]
    return [{"license": {"name": classifier}} for classifier in info.license_classifiers]


def _cyclonedx_sbom(info: WheelLicenseInfo) -> dict[str, object]:
    component: dict[str, object] = {
        "type": "library",
        "name": info.name,
        "version": info.version,
        "bom-ref": f"pkg:pypi/{info.name}@{info.version}",
        "purl": f"pkg:pypi/{info.name}@{info.version}",
        "hashes": [{"alg": "SHA-256", "content": _sha256(info.wheel)}],
    }
    licenses = _license_entries(info)
    if licenses:
        component["licenses"] = licenses
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "component": component,
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "pai-deps",
                    }
                ]
            },
        },
        "components": [component],
    }


def write_sidecars(wheel: Path) -> list[Path]:
    info = read_wheel_license_info(wheel)
    licenses_path = wheel.with_name(wheel.name + ".licenses.json")
    attributions_path = wheel.with_name(wheel.name + ".attributions.md")
    sbom_path = wheel.with_name(wheel.name + ".sbom.cdx.json")
    licenses_path.write_text(json.dumps(_license_json(info), indent=2, sort_keys=True) + "\n")
    attributions_path.write_text(_attribution_md(info))
    sbom_path.write_text(json.dumps(_cyclonedx_sbom(info), indent=2, sort_keys=True) + "\n")
    return [licenses_path, attributions_path, sbom_path]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patterns", nargs="+", help="Wheel files or glob patterns.")
    parser.add_argument("--allow-empty", action="store_true", help="Pass when no wheels match.")
    args = parser.parse_args()

    wheels = _expand_patterns(args.patterns)
    if not wheels:
        if args.allow_empty:
            print("No wheel artifacts matched.")
            return 0
        print("Error: no wheel artifacts matched.", file=sys.stderr)
        return 1
    for wheel in wheels:
        for path in write_sidecars(wheel):
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
