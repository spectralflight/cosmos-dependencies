# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import re
from pathlib import Path


def _load_check_toolchain():
    module_path = Path(__file__).with_name("check_toolchain.py")
    spec = importlib.util.spec_from_file_location("check_toolchain", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


check_toolchain = _load_check_toolchain()


def test_docker_args_reads_quoted_values():
    args = check_toolchain._docker_args(
        'ARG PAI_DEPS_UV_VERSION="0.11.23"\nARG PAI_DEPS_JUST_LINUX_X64_SHA256="abc123"\n'
    )

    assert args == {
        "PAI_DEPS_UV_VERSION": "0.11.23",
        "PAI_DEPS_JUST_LINUX_X64_SHA256": "abc123",
    }


def test_platform_record_requires_sha256_and_https():
    record = {
        "platforms.linux-x64": {
            "checksum": "sha256:" + "a" * 64,
            "url": "https://example.com/tool.tar.gz",
        }
    }

    assert check_toolchain._platform_record(record, "linux-x64", tool="tool") == {
        "checksum": "a" * 64,
        "url": "https://example.com/tool.tar.gz",
    }


def test_forbidden_patterns_catch_mise_exec_uvx_without_flagging_policy_prose():
    uvx_pattern = next(pattern for pattern in check_toolchain.FORBIDDEN_PATTERNS if "uvx" in pattern)

    assert re.search(uvx_pattern, "mise exec -- uvx pip-licenses\n")
    assert not re.search(uvx_pattern, "Do not use `uvx` in committed workflows.\n")


def test_forbidden_patterns_catch_remote_pre_commit_hooks():
    repo_pattern = next(pattern for pattern in check_toolchain.FORBIDDEN_PATTERNS if "repo:" in pattern)

    assert re.search(repo_pattern, "  - repo: https://github.com/pre-commit/pre-commit-hooks\n")
    assert not re.search(repo_pattern, "  - repo: local\n")


def test_forbidden_patterns_catch_legacy_agent_doc_references():
    docs_pattern = next(pattern for pattern in check_toolchain.FORBIDDEN_PATTERNS if "docs/(?:agents|dev)" in pattern)
    tasks_pattern = next(pattern for pattern in check_toolchain.FORBIDDEN_PATTERNS if "tasks/" in pattern)

    assert re.search(docs_pattern, "See docs/agents/agent-workflow.md.\n")
    assert re.search(tasks_pattern, "Run tasks/check.sh.\n")
    assert not re.search(tasks_pattern, "Runtime artifacts use tasks/{task_id}/outputs.\n")


def test_check_just_argument_forwarding_rejects_variadic_passthrough(tmp_path: Path):
    justfile = tmp_path / ".just"
    justfile.write_text(
        """
package *args:
    echo {{ args }}
"""
    )

    errors = check_toolchain.check_just_argument_forwarding([justfile])

    assert len(errors) == 2
    assert all("just recipes must not" in error for error in errors)


def test_check_forbidden_public_artifacts_rejects_video_codec_sdk_bundle(tmp_path: Path):
    sdk_dir = tmp_path / "packages" / "decord" / "Video_Codec_SDK_13.0.19"
    sdk_dir.mkdir(parents=True)

    errors = check_toolchain.check_forbidden_public_artifacts(tmp_path)

    assert errors == [
        "packages/decord/Video_Codec_SDK_13.0.19: do not vendor full NVIDIA Video Codec SDK bundles in the public repo"
    ]


def test_check_forbidden_public_artifacts_rejects_tracked_wheels(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(check_toolchain, "_tracked_files", lambda repo: ["dist/pkg-1.0.0-py3-none-any.whl"])

    errors = check_toolchain.check_forbidden_public_artifacts(tmp_path)

    assert errors == [
        "dist/pkg-1.0.0-py3-none-any.whl: do not commit built binary/archive artifacts to the public repo"
    ]


def test_check_ci_directory_is_config_only_rejects_scripts(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(check_toolchain, "_tracked_files", lambda repo: ["ci/check.py", "ci/vendor-config.yml"])

    errors = check_toolchain.check_ci_directory_is_config_only(tmp_path)

    assert errors == ["ci/check.py: ci/ is for vendor CI config; move implementation scripts under just/*/scripts"]


def test_check_legacy_layout_paths_rejects_tracked_legacy_paths(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        check_toolchain,
        "_tracked_files",
        lambda repo: [
            "docs/agents/agent-guide.md",
            "docs/dev/notes.md",
            "docs/subsystems/indexing.md",
            "tasks/check.sh",
            "bin/tool.py",
            "packages/pkg/docs/agents/build-notes.md",
            "packages/pkg/agents/build-notes.md",
        ],
    )

    errors = check_toolchain.check_legacy_layout_paths(tmp_path)

    assert errors == [
        "docs/agents/agent-guide.md: use agents/ for agent-only docs; docs/ is the published package index root",
        "docs/dev/notes.md: use agents/ for agent-only docs; docs/dev is legacy",
        "docs/subsystems/indexing.md: use docs/design/ for human architecture docs",
        "tasks/check.sh: root tasks/ is legacy for command code; use just/*/scripts",
        "bin/tool.py: root bin/ is legacy for command code; use importable modules or just/*/scripts",
        "packages/pkg/docs/agents/build-notes.md: use packages/<name>/agents/ for package-local agent notes",
    ]


def test_check_workflow_command_surface_requires_just_or_pre_commit(tmp_path: Path):
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        """
jobs:
  check:
    steps:
      - run: mise exec -- just check fast
      - run: mise exec -- pre-commit run --all-files
      - run: mise exec -- uv run --frozen python just/check/scripts/check_toolchain.py
"""
    )

    errors = check_toolchain.check_workflow_command_surface([workflow])

    assert errors == [
        f"{workflow}:7: workflow run commands must call a public just recipe or the minimal pre-commit hook"
    ]
