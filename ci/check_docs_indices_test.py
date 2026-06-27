# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from ci.check_docs_indices import ChangedPath, forbidden_index_changes, parse_name_status


def test_parse_name_status():
    assert parse_name_status(
        "M\tdocs/v1.5.0/index.html\nR100\tdocs/simple/index.html\tdocs/simple-old/index.html\n"
    ) == [
        ChangedPath(status="M", path="docs/v1.5.0/index.html"),
        ChangedPath(status="R100", old_path="docs/simple/index.html", path="docs/simple-old/index.html"),
    ]


def test_forbidden_index_changes_allows_new_index_files():
    changes = [
        ChangedPath(status="A", path="docs/v1.6.0/index.html"),
        ChangedPath(status="A", path="docs/v1.6.0/natten/index.html"),
        ChangedPath(status="M", path="docs/dev/agent-guide.md"),
    ]

    assert forbidden_index_changes(changes) == []


def test_forbidden_index_changes_blocks_existing_index_edits():
    changes = [
        ChangedPath(status="M", path="docs/v1.5.0/index.html"),
        ChangedPath(status="D", path="docs/simple/natten/index.html"),
        ChangedPath(status="R100", old_path="docs/v1.4.0/index.html", path="docs/v1.4.0-old/index.html"),
    ]

    assert forbidden_index_changes(changes) == changes
