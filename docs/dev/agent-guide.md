# Agent Development Guide

Status: candidate, 2026-06-26. This document is for coding agents and
maintainers reviewing agent work. Keep public user documentation in the README.

## Operating Model

This is a brownfield maintenance repository. Preserve published package
indices and release assets unless the owner explicitly authorizes a new release
flow. Prefer small, testable changes around the build and publishing harness.

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
cache directories. Set `COSMOS_DOCKER_AS_ROOT=1` only for an intentional root
debug shell.

## Fast Iteration Path

Start with the cheapest proof before attempting long package builds:

1. Run unit tests for changed Python code.
2. Run `just build docker-dummy` for a Docker dummy wheel smoke test.
3. Use `natten` for maintained non-trivial package testing.
4. Limit CUDA architectures and build threads during experiments.
5. Increase build scope only after the smaller proof passes.

OOM is a common build failure mode. Start with conservative thread counts and a
small CUDA architecture list, then widen deliberately.

Run `mise install` to converge standalone command-line tools. Use `uv` for
project-coupled Python tools such as Pyrefly.

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
COSMOS_DEPS_BUILD_ENV='MAX_JOBS=1 NATTEN_N_WORKERS=1 TORCH_CUDA_ARCH_LIST=9.0 NATTEN_CUDA_ARCH=9.0' just build docker-natten
```

The inline form is split on whitespace and does not support values containing
spaces. Use the env file for those.

Use `COSMOS_DEPS_BUILD_ATTEMPTS=3 just build docker-dummy` when testing
network-heavy paths. Failed attempts keep Docker and uv cache state, so retries
can often continue after a transient wheel download failure.

For fork-only publication drills:

1. Build a wheel with `just build docker-dummy`.
2. Upload it with `just release upload-batch 'tmp/build/*/*.whl'
   20260627.1 spectralflight/cosmos-dependencies v1.6.0`.
3. Add the generated batch tag to `indices/v1.6.0/manifest.json`.
4. Generate a temporary index with `just release create-manifest
   indices/v1.6.0/manifest.json tmp/index/v1.6.0`.
5. Verify installation with `just release verify-install tmp/index/v1.6.0
   cosmos-dummy 0.1.0 cosmos_dummy`.

Use a new batch id for each drill unless the owner explicitly asks to replace
assets on the fork. Do not run upload or index commands against the upstream
repository by accident.

## Package Scope

`natten` is the most actively maintained package and has the best upstream docs.
Several other package directories are retained as historical documentation and
may not build. Do not spend time reviving broken packages unless the owner
specifically asks for that package.

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
- Confirm the logical index version and batch tag.
- Confirm every wheel filename is unique for that batch.
- Keep unreleased indices editable; treat released indices as append-only.
- Generate the index from the manifest.
- Run the package-index guard.
