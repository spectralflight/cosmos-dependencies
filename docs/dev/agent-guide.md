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
2. Run `just build-dummy` for a dummy wheel smoke test.
3. Use `natten` for maintained non-trivial package testing.
4. Limit CUDA architectures and build threads during experiments.
5. Increase build scope only after the smaller proof passes.

OOM is a common build failure mode. Start with conservative thread counts and a
small CUDA architecture list, then widen deliberately. Useful knobs include
`MAX_JOBS`, `NATTEN_N_WORKERS`, `NVCC_THREADS`, `NVCC_APPEND_FLAGS`, and
`TORCH_CUDA_ARCH_LIST`.

## Package Scope

`natten` is the most actively maintained package and has the best upstream docs.
Several other package directories are retained as historical documentation and
may not build. Do not spend time reviving broken packages unless the owner
specifically asks for that package.

It is acceptable to update dependency locks for documentation-only packages to
clear CVEs, but do not treat a lock update as proof that the package builds.

## Release Workflow

Use the personal fork for experiments and publication drills. The upstream
repository is the public compatibility surface; do not push experimental wheels
or generated indices there.

Before publishing anything:

- Confirm the target repository.
- Confirm the release tag.
- Confirm every wheel filename is unique for that release.
- Generate a new index snapshot; do not edit an existing snapshot.
- Run the package-index guard.
