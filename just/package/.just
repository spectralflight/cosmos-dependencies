set shell := ["bash", "-c"]

package_dir := source_directory()
repo := package_dir + "/../.."
export UV_CACHE_DIR := env_var_or_default("UV_CACHE_DIR", repo + "/tmp/uv-cache")

# Show package recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# List discovered package descriptors.
list *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen python bin/package_info.py list {{ args }}

# Show descriptor and build-doc details for one package.
show package_name *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen python bin/package_info.py show {{ quote(package_name) }} {{ args }}

# Check package descriptors and package-local agent docs.
docs-check:
    cd "{{ repo }}" && mise exec -- uv run --frozen python ci/check_package_docs.py

# Check package descriptors against package-local build scripts.
contracts-check:
    cd "{{ repo }}" && mise exec -- uv run --frozen python ci/check_package_build_contracts.py
