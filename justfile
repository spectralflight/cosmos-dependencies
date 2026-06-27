set shell := ["bash", "-c"]

version := `repo="$(git rev-parse --show-toplevel)" && awk -F'"' '/^version = / { print $2; exit }' "$repo/pyproject.toml"`
tag := "v" + version
release_repo := "nvidia-cosmos/cosmos-dependencies"

# Show the agent-facing command map.
default: help

# List root and module recipes.
help:
    @just --list --list-submodules --unsorted

# Build wheels locally or in Docker.
mod build "just/build/.just"

# Run tests, linters, type checks, and release guards.
mod check "just/check/.just"

# Lock, upgrade, and audit root/package dependency environments.
mod deps "just/deps/.just"

# Create, upload, serve, and verify package indices.
mod release "just/release/.just"

# Check and regenerate third-party license attribution.
mod license "just/license/.just"

# Setup the repository.
setup: check::setup

# Run linting and formatting hooks.
lint: check::lint

# Run the standard local test lane.
test: check::test

# Build a dummy package locally.
build-dummy: build::dummy

# Build a package inside Docker without an interactive TTY.
docker-build package_name package_version python_version torch_version build_dir='tmp/build' cuda_version='12.8.1' *args:
    just build docker {{ quote(package_name) }} {{ quote(package_version) }} {{ quote(python_version) }} {{ quote(torch_version) }} {{ quote(build_dir) }} {{ quote(cuda_version) }} {{ args }}

# Build the dummy package inside Docker.
docker-build-dummy cuda_version='12.8.1': (build::docker-dummy cuda_version)

# Build natten inside Docker.
docker-build-natten package_version='0.21.6.dev6' python_version='3.12' torch_version='2.9' cuda_version='12.8.1' *args:
    just build docker-natten {{ quote(package_version) }} {{ quote(python_version) }} {{ quote(torch_version) }} {{ quote(cuda_version) }} {{ args }}

# Run the CUDA 12.6 docker container.
docker-cu126 *args:
    just build docker-shell 12.6.3 {{ args }}

# Run the CUDA 12.8 docker container.
docker-cu128 *args:
    just build docker-shell 12.8.1 {{ args }}

# Run the CUDA 12.9 docker container.
docker-cu129 *args:
    just build docker-shell 12.9.1 {{ args }}

# Run the CUDA 13.0 docker container.
docker-cu130 *args:
    just build docker-shell 13.0.2 {{ args }}

# Check that existing package indices were not modified.
index-guard base='upstream/main': (check::index-guard base)

# Audit root and package build dependencies.
audit *args:
    just deps audit {{ args }}

# Create the package index for the current version.
index-create *args:
    just release create {{ args }}

# Create a package index for an arbitrary release under a caller-selected path.
index-create-release repo tag output_dir *args:
    just release create-release {{ quote(repo) }} {{ quote(tag) }} {{ quote(output_dir) }} {{ args }}

# Upload wheels to a GitHub release without deleting local artifacts.
release-upload pattern repo=release_repo release_tag=tag *args:
    just release upload {{ quote(pattern) }} {{ quote(repo) }} {{ quote(release_tag) }} {{ args }}

# Legacy release upload alias.
upload pattern *args:
    just release upload {{ quote(pattern) }} {{ quote(release_repo) }} {{ quote(tag) }} {{ args }}

# Verify that a package installs from a generated local index.
index-verify-install index_dir package_name package_version import_name='' python_version='3.12':
    just release verify-install {{ quote(index_dir) }} {{ quote(package_name) }} {{ quote(package_version) }} {{ quote(import_name) }} {{ quote(python_version) }}

# Locally serve the package index.
index-serve *args:
    just release serve {{ args }}

# Fix file permissions.
fix-permissions:
    sudo chown -R $(id -u):$(id -g) .
