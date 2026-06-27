# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from ci.check_docs_indices import ChangedPath, forbidden_index_changes, parse_jj_summary, parse_name_status


def test_parse_name_status():
    assert parse_name_status(
        "M\tdocs/v1.5.0/index.html\nR100\tdocs/simple/index.html\tdocs/simple-old/index.html\n"
    ) == [
        ChangedPath(status="M", path="docs/v1.5.0/index.html"),
        ChangedPath(status="R100", old_path="docs/simple/index.html", path="docs/simple-old/index.html"),
    ]


def test_parse_jj_summary():
    assert parse_jj_summary("M docs/v1.5.0/index.html\nA docs/dev/agent-workflow.md\n") == [
        ChangedPath(status="M", path="docs/v1.5.0/index.html"),
        ChangedPath(status="A", path="docs/dev/agent-workflow.md"),
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


def test_forbidden_index_changes_allows_unstable_index_edits():
    changes = [
        ChangedPath(status="M", path="docs/cosmos3-scratch/index.html"),
        ChangedPath(status="D", path="docs/cosmos3-scratch/natten/index.html"),
        ChangedPath(
            status="R100",
            old_path="docs/cosmos3-scratch/flash-attn/index.html",
            path="docs/cosmos3-scratch/fa/index.html",
        ),
    ]

    assert forbidden_index_changes(changes, index_stabilities={"cosmos3-scratch": "unstable"}) == []


def test_forbidden_index_changes_blocks_renames_from_stable_to_unstable():
    change = ChangedPath(status="R100", old_path="docs/v1.5.0/index.html", path="docs/cosmos3-scratch/index.html")

    assert forbidden_index_changes([change], index_stabilities={"cosmos3-scratch": "unstable"}) == [change]


def test_forbidden_index_changes_allows_append_only_stable_index_edits():
    change = ChangedPath(status="M", path="docs/cosmos3/natten/index.html")
    old_text = "<a href='https://example.invalid/natten-1.whl#sha256=abc'>old</a><br>"
    new_text = old_text + "<a href='https://example.invalid/natten-2.whl#sha256=def'>new</a><br>"

    assert (
        forbidden_index_changes(
            [change],
            index_stabilities={"cosmos3": "stable"},
            old_texts={change.path: old_text},
            new_texts={change.path: new_text},
        )
        == []
    )


def test_forbidden_index_changes_blocks_changed_stable_index_links():
    change = ChangedPath(status="M", path="docs/cosmos3/natten/index.html")
    old_text = "<a href='https://example.invalid/natten-1.whl#sha256=abc'>old</a><br>"
    new_text = "<a href='https://example.invalid/natten-1.whl#sha256=changed'>old</a><br>"

    assert forbidden_index_changes(
        [change],
        index_stabilities={"cosmos3": "stable"},
        old_texts={change.path: old_text},
        new_texts={change.path: new_text},
    ) == [change]
