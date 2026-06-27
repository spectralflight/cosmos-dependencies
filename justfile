set shell := ["bash", "-c"]

# Show the agent-facing command map.
default: help

# List root and module recipes.
help:
    @just --list --list-submodules --unsorted

# Build wheels in Docker and enter build containers.
mod build "just/build/.just"

# Run tests, linters, type checks, and release guards.
mod check "just/check/.just"

# Lock, upgrade, and audit root/package dependency environments.
mod deps "just/deps/.just"

# Inspect package-local descriptors and agent docs.
mod package "just/package/.just"

# Create, upload, serve, and verify package indices.
mod release "just/release/.just"

# Run the no-GPU verification lane.
no-gpu-check: check::no-gpu
