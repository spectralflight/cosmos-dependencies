# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
import sys
import zipfile
from pathlib import Path


def _load_write_wheel_legal_sidecars():
    module_path = Path(__file__).with_name("write_wheel_legal_sidecars.py")
    spec = importlib.util.spec_from_file_location("write_wheel_legal_sidecars", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


write_wheel_legal_sidecars = _load_write_wheel_legal_sidecars()


def _write_wheel(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as wheel:
        wheel.writestr(
            "pkg-1.0.0.dist-info/METADATA",
            """Metadata-Version: 2.4
Name: pkg
Version: 1.0.0
License-Expression: MIT
License-File: LICENSE
""",
        )
        wheel.writestr("pkg-1.0.0.dist-info/WHEEL", "Wheel-Version: 1.0\n")
        wheel.writestr("pkg-1.0.0.dist-info/licenses/LICENSE", "Permission granted.\n")


def test_write_sidecars(tmp_path: Path) -> None:
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    _write_wheel(wheel)

    sidecars = write_wheel_legal_sidecars.write_sidecars(wheel)

    assert sidecars == [
        tmp_path / "pkg-1.0.0-py3-none-any.whl.licenses.json",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.attributions.md",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.sbom.cdx.json",
    ]
    license_data = json.loads(sidecars[0].read_text())
    assert license_data["metadata"]["license_expression"] == "MIT"
    assert license_data["license_files"][0]["path"] == "pkg-1.0.0.dist-info/licenses/LICENSE"
    attribution_text = sidecars[1].read_text()
    assert "pkg-1.0.0-py3-none-any.whl Attributions" in attribution_text
    assert "Permission granted." in attribution_text
    sbom_data = json.loads(sidecars[2].read_text())
    assert sbom_data["bomFormat"] == "CycloneDX"
    assert sbom_data["components"][0]["name"] == "pkg"
