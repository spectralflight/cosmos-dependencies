# Agent Development Guide

Status: candidate, 2026-06-26. This document is for coding agents working on
the build and publishing harness.

For locked-tool policy, no-GPU checks, package descriptor commands, and release
dry runs, start with `docs/dev/agent-workflow.md`.

## Operating Model

This is a yellowfield agent-only repository. Simplify aggressively, but preserve
published package indices, release assets, and wheel build contracts unless the
owner explicitly authorizes a new release flow.

## Build Hosts

Use the local x86_64 workstation for x86_64 wheel experiments. Use the
designated ARM build host for aarch64 work when explicitly requested. Avoid
shared service hosts for wheel builds unless the owner asks for them.

All wheel builds should run inside Docker. Build scripts may install trusted
system packages as root during image setup or a controlled preflight, but
third-party package build code should run with the least privilege that still
lets the package build.

The default Docker entrypoint creates a build user matching the invoking host
UID/GID and uses a named Docker cache volume instead of bind-mounting host root
cache directories. Root container execution is reserved for explicit debugging
or trusted preflight work, not normal package builds.

## Fast Iteration Path

Start with the cheapest proof before attempting long package builds:

1. Run unit tests for changed Python code.
2. Run `just build dummy` for a Docker dummy wheel smoke test.
3. Use `natten` for maintained non-trivial package testing.
4. Limit CUDA architectures and build threads during experiments.
5. Increase build scope only after the smaller proof passes.

OOM is a common build failure mode. Start with conservative thread counts and a
small CUDA architecture list, then widen deliberately.

Run `mise install --locked` to converge standalone command-line tools. Use `uv` for
project-coupled Python tools such as Pyrefly.

Use committed lockfiles for supply-chain-sensitive workflows. Do not add
committed commands that use `uvx`, `uv tool install`, `uv run --with ...`,
curl-piped installers, or `eget`.

Builds run under a mostly empty environment. To pass package-specific or
tool-specific variables, point `COSMOS_DEPS_BUILD_ENV_FILE` at a local file
inside the repository. The file accepts literal `KEY=VALUE` lines, optional
`export KEY=VALUE` lines, blank lines, and whole-line comments. It does not
perform shell expansion, and it cannot override core wrapper-controlled
variables such as `PACKAGE_NAME`, `OUTPUT_DIR`, cache paths, or `PATH`.
`COSMOS_DEPENDENCIES_ENV_FILE` and `COSMOS_DEPENDENCIES_BUILD_ENV_FILE` remain
accepted as legacy aliases.

Example local env file for a small `natten` smoke build:

```dotenv
MAX_JOBS=1
NATTEN_N_WORKERS=1
NVCC_THREADS=1
TORCH_CUDA_ARCH_LIST=9.0
NATTEN_CUDA_ARCH=9.0
```

For simple values, use `COSMOS_DEPS_BUILD_ENV` instead of a file:

```bash
COSMOS_DEPS_BUILD_ENV='MAX_JOBS=1 NATTEN_N_WORKERS=1 TORCH_CUDA_ARCH_LIST=9.0 NATTEN_CUDA_ARCH=9.0' just build natten
```

The inline form is split on whitespace and does not support values containing
spaces. Use the env file for those.

Use `COSMOS_DEPS_BUILD_ATTEMPTS=3 just build dummy` when testing
network-heavy paths. Failed attempts keep Docker and uv cache state, so retries
can often continue after a transient wheel download failure.

For fork-only publication drills:

1. Build a wheel with `just build dummy`.
2. Upload the wheel and sidecars to an unstable scratch release, for example
   `just release upload 'tmp/build/*/*.whl*' spectralflight/cosmos-dependencies
   cosmos3-scratch`.
3. Generate the scratch index with `just release create cosmos3-scratch`.
4. Copy selected assets into a stable release with `just release copy-assets
   spectralflight/cosmos-dependencies cosmos3-scratch
   spectralflight/cosmos-dependencies cosmos3-20260627.1 'cosmos_dummy*'`.
5. Publish the stable index with `just release publish cosmos3`.
6. Verify installation with `just release verify-install docs/cosmos3
   cosmos-dummy 0.1.0 cosmos_dummy`.

Use scratch releases for replaceable testing and stable releases for copied
assets that should remain immutable. Do not run upload or index commands against
the upstream repository by accident.

## Package Scope

`natten` is the most actively maintained package and has the best upstream docs.
Several other package directories are retained as historical documentation and
may not build. Do not spend time reviving broken packages unless the owner
specifically asks for that package.

Package-local agent notes live at `packages/<name>/docs/dev/build-notes.md`.
Use `just package list` and `just package show <name>` to inspect the package
descriptor before editing package scripts or docs.

It is acceptable to update dependency locks for documentation-only packages to
clear CVEs, but do not treat a lock update as proof that the package builds.

`uv audit` allowlists belong in each affected project's `[tool.uv.audit]`
configuration. Prefer `ignore-until-fixed` for no-fix advisories so newly
fixable vulnerabilities fail the normal audit. Use `just deps audit-strict` or
`COSMOS_DEPS_AUDIT_STRICT=1` to bypass uv config and see the raw audit result.

## Release Workflow

Use the personal fork for experiments and publication drills. The upstream
repository is the public compatibility surface; do not push experimental wheels
or generated indices there.

Before publishing anything:

- Confirm the target repository.
- Confirm the index name, stability, and release tag.
- Confirm every wheel filename is unique for stable releases.
- Keep unstable indices editable; treat stable indices as append-only.
- Generate the index from the manifest.
- Run the package-index guard.
