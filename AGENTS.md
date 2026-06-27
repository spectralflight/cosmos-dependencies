# Agent Guide

Mode: brownfield hardening.

This repository publishes Python package indices from GitHub release assets.
Those indices are compatibility contracts for downstream lockfiles.

## Hard Rules

- Do not modify, delete, rewrite, reformat, or regenerate existing package index
  files under `docs/**/index.html`.
- Do not alter existing GitHub releases or replace existing release assets.
- Publish new wheels only as new release assets with unique filenames and hashes.
- Add new index snapshots in new version directories instead of editing old ones.
- Keep agent-facing workflow notes in `docs/dev/`; keep the README human-facing.
- Run wheel builds inside Docker. Use trusted root steps only for image/package
  setup; run third-party package build code without extra privileges whenever
  possible.

## Useful Commands

- `just test`: lint, unit tests, and package-index smoke checks.
- `just index-guard upstream/main`: verify existing package indices were not
  changed relative to upstream.
- `just audit`: run `uv audit` for the root project and package build
  environments.
- `just build-dummy`: quick Docker/build-loop smoke package.
- `just build natten <version> <python> <torch>`: common maintained package path.

## Pointers

- See `docs/dev/agent-guide.md` for the work loop and package-build guidance.
- See `docs/dev/release-safety.md` for index and release invariants.
