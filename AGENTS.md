# Agent Contract

Mode: yellowfield agent-only. Simplify aggressively, but preserve wheel output,
package-index, and release-asset contracts.

## Hard Rules

- Do not modify, delete, rewrite, reformat, or regenerate published package
  index files under `docs/**/index.html`.
- The only freely editable package index docs are indices whose
  `indices/<index-name>/manifest.json` has `stability: "unstable"`.
- Do not alter existing GitHub releases or replace existing release assets for
  stable indices.
- Publish new wheels for stable indices only as new release assets with unique
  filenames and hashes.
- Run wheel builds inside Docker. Do not build packages on the host.
- Do not start Docker containers, package builds, or GPU work while another
  package-build thread is active on the same one-GPU machine.
- Use committed lockfiles for tool and Python dependency resolution. Do not add
  committed workflows that use `uvx`, `uv tool install`, `uv run --with ...`,
  curl-piped installers, or `eget`.
- Use `spectralflight/...` bookmarks for public GitHub fork work and
  `joallen/...` bookmarks for internal GitLab work.

## Package Boundary

- Package-specific truth belongs under `packages/<name>`.
- Each package owns `cosmos-package.toml`, `build.sh`, `pyproject.toml`,
  `uv.lock`, and `docs/dev/build-notes.md`.
- Shared discovery, checks, and harness code belong in `cosmos_dependencies/`,
  `ci/`, `bin/`, or `just/`.
- Prefer shared parametrized tests over per-package boilerplate.

## Useful Commands

- `mise install --locked`: install pinned standalone tools.
- `just help`: list root and module recipes.
- `just no-gpu-check`: safe lane with no Docker, package build, or GPU use.
- `just check fast`: shell, Python, type, package, release, index, and manifest
  checks without audit or index smoke.
- `just check package-contracts`: validate package descriptors against
  package-local build scripts.
- `just deps lock-all` and `just deps upgrade-all`: refresh root and package
  lockfiles.
- `just package list` and `just package show <name>`: inspect package-local
  descriptors and agent docs.
- `just release create-dry-run <index>`: generate a temporary package index.

## Pointers

- `docs/dev/agent-workflow.md`: locked tools, no-GPU checks, package workflow.
- `docs/dev/agent-guide.md`: Docker build loop and package-build notes.
- `docs/dev/release-safety.md`: index and release invariants.
