set shell := ["bash", "-c"]

deps_dir := source_directory()
repo := deps_dir + "/../.."
scripts := deps_dir + "/scripts"
export UV_CACHE_DIR := env_var_or_default("UV_CACHE_DIR", repo + "/tmp/uv-cache")

# Show dependency recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Lock the root project.
lock *args:
    cd "{{ repo }}" && mise exec -- uv lock {{ args }}

# Check all root and package lockfiles.
lock-check-all:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/lock-projects.sh" --check

# Lock all root and package projects.
lock-all *args:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/lock-projects.sh" {{ args }}

# Upgrade and lock all root and package projects.
upgrade-all *args:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/lock-projects.sh" --upgrade {{ args }}

# Upgrade and lock one project directory.
upgrade project_dir *args:
    cd "{{ repo }}" && mise exec -- uv lock --project {{ quote(project_dir) }} --upgrade {{ args }}

# Audit root and package build dependencies.
audit *args:
    cd "{{ repo }}" && mise exec -- ./ci/uv_audit.sh {{ args }}

# Audit without advisory allowlist ignores.
audit-strict *args:
    cd "{{ repo }}" && PAI_DEPS_AUDIT_STRICT=1 mise exec -- ./ci/uv_audit.sh {{ args }}
