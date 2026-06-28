# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
from pathlib import Path

from pai_deps.package_metadata import load_package_descriptor


def _load_check_package_docs():
    module_path = Path(__file__).with_name("check_package_docs.py")
    spec = importlib.util.spec_from_file_location("check_package_docs", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


check_package_docs = _load_check_package_docs()


def test_check_doc_requires_standard_headings(tmp_path):
    doc = tmp_path / "build-notes.md"
    doc.write_text("Status: maintained.\nResearch date: 2026-06-27.\n## Status\n")

    errors = check_package_docs._check_doc(doc)

    assert any("## Local Build Entry Point" in error for error in errors)


def test_check_doc_accepts_template(tmp_path):
    doc = tmp_path / "build-notes.md"
    doc.write_text(
        "Status: maintained.\n"
        "Research date: 2026-06-27.\n" + "\n".join(f"## {heading}" for heading in check_package_docs.REQUIRED_HEADINGS)
    )

    assert check_package_docs._check_doc(doc) == []


def test_check_descriptor_requires_matching_pyproject_name(tmp_path):
    package_dir = tmp_path / "pkg"
    agents_dir = package_dir / "agents"
    agents_dir.mkdir(parents=True)
    (package_dir / "build.sh").write_text("#!/usr/bin/env bash\n")
    (package_dir / "pyproject.toml").write_text('[project]\nname = "other"\nversion = "0.1.0"\n')
    (package_dir / "pai-package.toml").write_text(
        "\n".join(
            [
                "schema_version = 1",
                'name = "pkg"',
                'status = "maintained"',
                'upstream = "local"',
                'gpu_risk = "none"',
                "[build]",
                'backend = "uv-build"',
            ]
        )
    )
    (agents_dir / "build-notes.md").write_text(
        "Status: maintained.\n"
        "Research date: 2026-06-27.\n" + "\n".join(f"## {heading}" for heading in check_package_docs.REQUIRED_HEADINGS)
    )
    package = load_package_descriptor(package_dir / "pai-package.toml")

    errors = check_package_docs._check_descriptor(package)

    assert any("project.name='other'" in error for error in errors)
