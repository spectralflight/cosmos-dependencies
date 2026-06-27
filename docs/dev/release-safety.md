# Release Safety

Status: candidate, 2026-06-26.

This repository serves package indices whose entries are consumed by tools that
record exact wheel hashes. A changed wheel or changed historical index can break
existing lockfiles.

## Immutable Surfaces

Treat these as immutable once published:

- Existing GitHub release assets.
- Existing committed package index files matching `docs/**/index.html`.
- Existing wheel URLs and URL fragments in those package indices.

Allowed changes:

- New source code, tests, and development docs.
- New future version directories under `docs/`.
- New package index files for a new release snapshot.
- New release assets with unique filenames.

## Checks

Run this before publishing or opening a release PR:

```shell
just index-guard upstream/main
```

In pull requests, CI should compare the branch to the base branch and fail if an
existing package index file is modified, deleted, renamed, or type-changed.

## Hash Policy

New index entries should include the release asset digest in the URL fragment
when GitHub provides one. Existing entries without URL fragments are historical
records and should not be rewritten just to normalize formatting.
