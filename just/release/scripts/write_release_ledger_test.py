# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
import sys
from pathlib import Path


def _load_write_release_ledger():
    module_path = Path(__file__).with_name("write_release_ledger.py")
    spec = importlib.util.spec_from_file_location("write_release_ledger", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


write_release_ledger = _load_write_release_ledger()


def test_write_ledger_expands_wheel_artifact_set(tmp_path: Path) -> None:
    wheel = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    for path in [
        tmp_path / "pkg-1.0.0-py3-none-any.whl.build.log",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.build.json",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.licenses.json",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.attributions.md",
        tmp_path / "pkg-1.0.0-py3-none-any.whl.sbom.cdx.json",
        wheel,
    ]:
        path.write_text(path.name)

    artifacts = write_release_ledger.collect_release_artifacts([wheel])
    ledger = write_release_ledger.build_ledger(
        artifacts=artifacts,
        repo="spectralflight/pai-deps",
        release_tag="wheels-v1.6.0-batch.test",
        base=tmp_path,
    )
    ledger_path, digest_path = write_release_ledger.write_ledger(
        ledger=ledger,
        output=tmp_path / "release-ledger.json",
    )

    data = json.loads(ledger_path.read_text())
    assert data["artifact_count"] == 6
    assert data["repo"] == "spectralflight/pai-deps"
    assert [artifact["name"] for artifact in data["artifacts"]] == [
        "pkg-1.0.0-py3-none-any.whl",
        "pkg-1.0.0-py3-none-any.whl.attributions.md",
        "pkg-1.0.0-py3-none-any.whl.build.json",
        "pkg-1.0.0-py3-none-any.whl.build.log",
        "pkg-1.0.0-py3-none-any.whl.licenses.json",
        "pkg-1.0.0-py3-none-any.whl.sbom.cdx.json",
    ]
    assert digest_path.read_text().endswith("  release-ledger.json\n")
