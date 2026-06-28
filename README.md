# Physical AI Dependencies

Physical AI Dependencies (PAI Deps) is an agent-only repository for building
Python wheels and publishing package indices from GitHub release assets.

## Agent Entry

Read `AGENTS.md` first. It contains the active repo contract, index safety rules,
and verification commands.

## Locked Setup

```shell
mise install --locked
mise exec -- just help
```

Do not use unlocked committed workflows such as `uvx`, `uv tool install`,
`uv run --with ...`, curl-piped installers, or `eget`.

## Package Work

Package-specific truth is colocated under `packages/<name>`:

- `pai-package.toml`: package descriptor and build-contract deltas.
- `build.sh`: package-local build implementation.
- `docs/dev/build-notes.md`: package-local agent notes.
- `pyproject.toml` and `uv.lock`: package build environment.

Use shared commands instead of editing central package lists:

```shell
just package list
just package show natten
just package docs-check
just check package-contracts
```

## Safety Checks

```shell
just no-gpu-check
```

This lane does not start Docker, build packages, or use a GPU. It runs shell,
Python, type, package descriptor, package contract, release artifact, index,
manifest, and audit checks.

## Package Indices

Published `docs/**/index.html` files are compatibility contracts for downstream
lockfiles. Do not modify old published package indices or existing GitHub
release assets. Stable index manifests are append-only; scratch work belongs in
indices marked `stability: "unstable"`.

Release/index details live in `docs/dev/release-safety.md`.

## License

Apache License 2.0. See `LICENSE`.

Package-local third-party source notices live next to the relevant package, for
example `packages/decord/THIRD_PARTY.md`.
