set shell := ["bash", "-c"]

deps_dir := source_directory()
repo := deps_dir + "/../.."
scripts := deps_dir + "/scripts"
export UV_CACHE_DIR := env_var_or_default("UV_CACHE_DIR", repo + "/tmp/uv-cache")

# Show dependency recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Lock the root project.
lock:
    cd "{{ repo }}" && mise exec -- uv lock

# Check the root project lockfile.
lock-check:
    cd "{{ repo }}" && mise exec -- uv lock --check

# Check all root and package lockfiles.
lock-check-all:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/lock-projects.sh" --check

# Lock all root and package projects.
lock-all:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/lock-projects.sh"

# Upgrade and lock all root and package projects.
upgrade-all:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/lock-projects.sh" --upgrade

# Upgrade and lock one project directory.
upgrade project_dir:
    cd "{{ repo }}" && mise exec -- uv lock --project {{ quote(project_dir) }} --upgrade

# Audit root and package build dependencies.
audit:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/uv-audit.sh"

# Audit without advisory allowlist ignores.
audit-strict:
    cd "{{ repo }}" && PAI_DEPS_AUDIT_STRICT=1 mise exec -- "{{ scripts }}/uv-audit.sh"
