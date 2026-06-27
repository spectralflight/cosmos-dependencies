# Agent Workflow

Status: candidate, 2026-06-27.

## First Rules

- Preserve existing package index links and hashes. Published `docs/**/index.html`
  files are downstream lockfile contracts.
- Treat indices with `stability: "stable"` as append-only. Only unstable
  manifest/index outputs are scratch space.
- Do not modify existing upstream GitHub release assets. For stable indices,
  publish new wheels as new asset filenames or copy validated scratch assets
  into a stable release.
- Do not start Docker containers or package builds when another package-build
  thread is active on the same one-GPU machine.
- Use `packages/<name>/docs/dev/build-notes.md` for package-local agent notes.

## Locked Tools

Standalone tools are managed by `.mise.toml` plus `mise.lock`.

Use:

```bash
mise install --locked
mise exec -- just help
```

Do not commit workflows that use `uvx`, `uv tool install`,
`uv run --with ...`, curl-piped installers, or `eget`. They are fine for a
one-off local spike, but committed commands must be backed by `mise.lock` or a
project `uv.lock`.

Docker installs `uv` and `just` directly from upstream release tarballs using
versions and SHA256s mirrored from `mise.lock`. Check drift with:

```bash
just build tool-versions-check
```

## Safe Check Lanes

Use the no-GPU lane when package builds are running elsewhere:

```bash
just no-gpu-check
```

This lane does not start Docker, does not build packages, and does not request
GPU access. It runs shell, Python, toolchain, package descriptor, package
contract, provenance, index, manifest, and audit checks.

Use focused checks while editing:

```bash
just check toolchain
just package docs-check
just package contracts-check
just release artifact-check
```

## Package Work

Package inventory is discovered from `packages/*/pai-package.toml`.

```bash
just package list
just package show natten
just check package-contracts
```

`natten` is the maintained non-trivial build path. `cosmos-dummy` is the cheap
smoke package. Most other package directories are historical and may be stale;
their docs record known risks instead of promising a current build.

Pass package-specific variables through `PAI_DEPS_BUILD_ENV_FILE` or
`PAI_DEPS_BUILD_ENV`. Do not add package-specific variables to global
allowlists.

## Release Dry Runs

Use dry runs before GitHub mutations:

```bash
just release upload-plan 'tmp/build/**/*.whl' spectralflight/pai-deps cosmos3-scratch
just release copy-plan spectralflight/pai-deps cosmos3-scratch spectralflight/pai-deps cosmos3-20260627.1 'cosmos_dummy*'
just release create-dry-run cosmos3
just release publish cosmos3
```

Release uploads should include wheel, `.build.log`, and `.build.json` sidecars.
Validate staged artifacts with:

```bash
just release artifact-check 'tmp/build/**/*.whl'
```

## Verification Labels

Use these labels in package docs:

- `verified`: command ran on the relevant machine/date.
- `observed`: seen in local files or logs.
- `imported`: copied from upstream docs or research without running a build.
- `candidate`: plausible future fix, not accepted behavior.
- `stale`: known or likely outdated.
