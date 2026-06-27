# cosmos-dummy Build Notes

Status: smoke.
Research date: 2026-06-27.

## Status

`cosmos-dummy` is a local smoke package for wrapper, provenance, upload, and
index workflows. It is not a CUDA package.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/cosmos-dummy/build.sh`
- Local recipe: `just build dummy`
- Docker recipe: `just build dummy`

## Upstream Sources

- Local package source: `packages/cosmos-dummy/src/cosmos_dummy`
- Build frontend docs: https://docs.astral.sh/uv/concepts/projects/build/

## Version Constraints

The package declares Python `>=3.10`. Torch and CUDA labels in produced wheel
names are pipeline provenance only; the package has no functional Torch/CUDA
runtime requirement.

## Build Environment

The package runs:

```bash
uv build --wheel -o "${OUTPUT_DIR}"
```

The repo wrapper still creates the standard build environment and applies the
local wheel suffix convention.

## OOM Controls

No package-specific controls are needed. If this OOMs, the failure is in the
wrapper, Docker image, or host resource state rather than package compilation.

## Smoke Test

After index generation:

```bash
just release verify-install docs/cosmos3 cosmos-dummy 0.1.0 cosmos_dummy
```

For a direct import smoke:

```bash
python -c "import cosmos_dummy"
```

## Known Risks

- The package README is intentionally tiny because `pyproject.toml` uses it for
  package metadata.
- Identical dummy wheel filenames can have different hashes across scratch
  indices. Keep scratch indices unstable and do not rewrite stable links.

## Future Fixes

- Replace the package README with a short package-local smoke description.
- Keep this package as the first proof for release/index commands.

## Research Notes

This package has no third-party upstream. Notes were verified from local files
on 2026-06-27 without Docker or package builds.
