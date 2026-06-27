# Release Safety

Status: candidate, 2026-06-27.

This repository serves package indices whose entries are consumed by tools that
record exact wheel hashes. A changed wheel URL or hash can break existing
lockfiles.

## Index Manifests

Each maintained index has a manifest at `indices/<index-name>/manifest.json`.
Index names are arbitrary public slugs such as `cosmos3`, `cosmos3-scratch`, or
`cosmos-eval`.

Manifest shape:

```json
{
  "schema_version": 1,
  "index_name": "cosmos3-scratch",
  "stability": "unstable",
  "default_repo": "spectralflight/pai-deps",
  "releases": [
    { "tag": "cosmos3-scratch" }
  ]
}
```

- `stability: "unstable"` means the public index is scratch space for testing.
  Its manifest, generated docs, and scratch release assets may be regenerated or
  clobbered intentionally.
- `stability: "stable"` means downstream users may lock against it. Existing
  wheel links and hash fragments are append-only.

## Stable Surfaces

Treat these as stable compatibility contracts:

- Existing GitHub release assets referenced by stable manifests.
- Existing wheel links and URL fragments in stable package indices.
- Existing `default_repo` values and release references in stable manifests.

Allowed changes:

- Edits to unstable indices and scratch releases.
- New index directories under `docs/`.
- New release assets with unique filenames.
- Append-only additions to stable manifests and generated stable index links.

## Copying Wheels

Scratch releases are useful while dialing in wheel build parameters. Once a
wheel is correct, copy it into a stable release instead of pointing a stable
index at scratch assets.

Use:

```shell
just release copy-assets spectralflight/pai-deps cosmos3-scratch \
  spectralflight/pai-deps cosmos3-20260627.1 'cosmos_dummy*'
```

Source releases are never modified. Destination releases are created when
needed; existing destination assets are replaced only when `--clobber` is passed
with `PAI_DEPS_ALLOW_CLOBBER=1`.

## Build Sidecars

Successful builds write sidecars next to each wheel:

- `<wheel>.build.log`: the build log for the wheel.
- `<wheel>.build.json`: package, Python, torch, CUDA, explicit build env,
  Docker image, git commit, and wheel/log hashes.

Upload and copy commands expand matched wheels to include their sidecars and
scan wheels, logs, and provenance before GitHub writes. Package indices include
only `.whl` assets. Do not pass secrets through `PAI_DEPS_BUILD_ENV_FILE` or
`PAI_DEPS_BUILD_ENV`; explicit build env values are recorded in provenance.

Check staged wheel/log/provenance triplets before upload:

```shell
just release artifact-check 'tmp/build/**/*.whl'
```

## Checks

Run this before publishing or opening a release PR:

```shell
just release upload-plan 'tmp/build/**/*.whl' spectralflight/pai-deps cosmos3-scratch
just release create-dry-run cosmos3
just check index-guard origin/main
just check manifest-guard origin/main
```

`index-guard` allows arbitrary edits for unstable indices. For stable indices,
existing links must remain present with the same URL and hash.

`manifest-guard` prevents stable manifests from becoming unstable, changing
their default repository, or removing existing release references.

## Hash Policy

New index entries should include the release asset digest in the URL fragment
when GitHub provides one. Existing entries without URL fragments are historical
records and should not be rewritten just to normalize formatting.
