# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Shared naming rules for wheel release artifacts."""

from __future__ import annotations

WHEEL_BUILD_SIDECAR_SUFFIXES = (".build.log", ".build.json")
WHEEL_LEGAL_SIDECAR_SUFFIXES = (".licenses.json", ".attributions.md", ".sbom.cdx.json")
WHEEL_SIDECAR_SUFFIXES = WHEEL_BUILD_SIDECAR_SUFFIXES + WHEEL_LEGAL_SIDECAR_SUFFIXES

WHEEL_SIDECAR_LABELS = {
    ".build.log": "build log",
    ".build.json": "provenance",
    ".licenses.json": "licenses",
    ".attributions.md": "attributions",
    ".sbom.cdx.json": "SBOM",
}


def wheel_sidecar_names(wheel_name: str) -> tuple[str, ...]:
    return tuple(wheel_name + suffix for suffix in WHEEL_SIDECAR_SUFFIXES)


def wheel_upload_names(wheel_name: str) -> tuple[str, ...]:
    return (*wheel_sidecar_names(wheel_name), wheel_name)
