# Agent Guide

Mode: brownfield hardening.

This repository publishes Python package indices from GitHub release assets.
Those indices are compatibility contracts for downstream lockfiles.

## Hard Rules

- Do not modify, delete, rewrite, reformat, or regenerate published package
  index files under `docs/**/index.html`.
- The only freely editable package index docs are indices whose
  `indices/<index-name>/manifest.json` has `stability: "unstable"`.
- Do not alter existing GitHub releases or replace existing release assets for
  stable indices.
- Publish new wheels for stable indices only as new release assets with
  unique filenames and hashes.
- Keep agent-facing workflow notes in `docs/dev/`; keep the README human-facing.
- Run wheel builds inside Docker. Use trusted root steps only for image/package
  setup; run third-party package build code without extra privileges whenever
  possible.

## Useful Commands

- `mise install`: install pinned standalone tools such as `just`, `uv`, `ruff`,
  `shellcheck`, `shfmt`, `gh`, `gitleaks`, `actionlint`, and `pre-commit`.
- `just help`: list root and module recipes.
- `just check fast`: shell, ruff, Pyrefly, unit, and index-guard checks.
- `just test`: lint, Pyrefly, unit tests, and package-index smoke checks.
- `just index-guard upstream/main`: verify existing package indices were not
  changed relative to upstream.
- `just manifest-guard upstream/main`: verify stable index manifests remain
  append-only.
- `just audit`: run `uv audit` for the root project and package build
  environments. Audit allowlists live in each affected project's
  `[tool.uv.audit]` config, not in the wrapper script.
- `just build docker-dummy`: quick Docker/build-loop smoke package.
- `just build docker-natten <version> <python> <torch>`: common maintained
  package path.
- `just deps lock-all` and `just deps upgrade-all`: refresh root and package
  lockfiles.

## Pointers

- See `docs/dev/agent-guide.md` for the work loop and package-build guidance.
- See `docs/dev/release-safety.md` for index and release invariants.
