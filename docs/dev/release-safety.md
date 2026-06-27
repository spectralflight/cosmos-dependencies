# Release Safety

Status: candidate, 2026-06-27.

This repository serves package indices whose entries are consumed by tools that
record exact wheel hashes. A changed wheel or changed historical index can break
existing lockfiles.

## Index States

Each maintained index version can have a manifest at
`indices/<version>/manifest.json`.

- `status: "unreleased"` means the index is still staging. Its manifest,
  generated docs, and staging releases may be edited while testing.
- `status: "released"` means downstream users may lock against it. Existing
  wheel links and hash fragments are immutable.

The `v1.6.0` index starts as unreleased. Keep it unreleased until the wheel set
and generated docs are ready to become a compatibility contract.

## Immutable Surfaces

Treat these as immutable once published:

- Existing GitHub release assets in released wheel batches.
- Existing package index files for released or legacy index versions.
- Existing wheel URLs and URL fragments in released package indices.

Allowed changes:

- New source code, tests, and development docs.
- Edits to unreleased index versions.
- New version directories under `docs/`.
- New wheel batch releases with unique filenames.

## Wheel Batches

Prefer one release per additive wheel batch. Use tags like:

```text
wheels-v1.6.0-batch.20260627.1
```

For released indices, add wheels by creating a new batch release and adding that
batch to the index manifest. Do not replace files in old batch releases and do
not use `--clobber` for released batches.

When release immutability is enabled on GitHub, create the release with all
assets attached in one `gh release create` call, or create it as a draft, upload
assets, then publish. The `just release upload-batch ...` helper uses the first
pattern for new releases.

## Checks

Run this before publishing or opening a release PR:

```shell
just index-guard upstream/main
```

In pull requests, CI should compare the branch to the base branch and fail if an
existing published package index file is modified, deleted, renamed, or
type-changed. Index versions whose manifest status is `unreleased` are editable.

## Hash Policy

New index entries should include the release asset digest in the URL fragment
when GitHub provides one. Existing entries without URL fragments are historical
records and should not be rewritten just to normalize formatting.
