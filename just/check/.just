set shell := ["bash", "-c"]

check_dir := source_directory()
repo := check_dir + "/../.."
version := `repo="$(git rev-parse --show-toplevel)" && awk -F'"' '/^version = / { print $2; exit }' "$repo/pyproject.toml"`
tag := "v" + version

# Show check recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Install system tools and the Python version specified in .python-version.
setup:
    cd "{{ repo }}" && mise install
    cd "{{ repo }}" && mise exec -- uv python install

# Setup pre-commit hooks.
hooks *args: setup
    cd "{{ repo }}" && mise exec -- pre-commit install -c ci/.pre-commit-config-base.yaml {{ args }}

# Run pre-commit base safety hooks.
pre-commit-base *args:
    cd "{{ repo }}" && mise exec -- pre-commit run -c ci/.pre-commit-config-base.yaml -a {{ args }}

# Run full pre-commit hooks.
pre-commit *args: pre-commit-base
    cd "{{ repo }}" && mise exec -- pre-commit run -a {{ args }} || mise exec -- pre-commit run -a {{ args }}

# Run linting and formatting hooks.
lint: pre-commit

# Run shell checks on maintained shell scripts.
shell:
    cd "{{ repo }}" && mise exec -- shellcheck bin/build.sh just/build/scripts/*.sh just/release/scripts/*.sh just/deps/scripts/*.sh docker/entrypoint.sh ci/uv_audit.sh

# Check shell script formatting.
shell-format:
    cd "{{ repo }}" && mise exec -- shfmt -d bin/build.sh just/build/scripts/*.sh just/release/scripts/*.sh just/deps/scripts/*.sh docker/entrypoint.sh ci/uv_audit.sh

# Run Python linting.
ruff:
    cd "{{ repo }}" && mise exec -- ruff check bin ci cosmos_dependencies

# Check Python formatting.
format:
    cd "{{ repo }}" && mise exec -- ruff format --check bin ci cosmos_dependencies

# Type-check maintained Python code.
typecheck:
    cd "{{ repo }}" && mise exec -- uv run --frozen pyrefly check

# Run focused unit tests.
unit:
    cd "{{ repo }}" && mise exec -- uv run --frozen pytest bin/build_script_test.py bin/copy_release_assets_test.py bin/write_build_provenance_test.py ci/check_docs_indices_test.py ci/check_index_manifests_test.py bin/create_index_test.py cosmos_dependencies/build_test.py

# Check that existing package indices were not modified.
index-guard base='upstream/main':
    cd "{{ repo }}" && mise exec -- uv run --frozen python ci/check_docs_indices.py --base {{ quote(base) }}

# Check that stable index manifests are append-only.
manifest-guard base='upstream/main':
    cd "{{ repo }}" && mise exec -- uv run --frozen python ci/check_index_manifests.py --base {{ quote(base) }}

# Generate a temporary package index.
index-smoke index_name=tag:
    cd "{{ repo }}" && if [[ -f "indices/{{ index_name }}/manifest.json" ]]; then mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o "tmp/docs/{{ index_name }}" --manifest "indices/{{ index_name }}/manifest.json"; else mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o "tmp/docs/{{ index_name }}" --tag={{ quote(index_name) }}; fi

# Run the standard local test lane.
test: lint typecheck unit index-smoke

# Run fast local checks without mutating hooks.
fast: shell shell-format ruff format typecheck unit index-guard manifest-guard

# Run dependency security checks.
security:
    cd "{{ repo }}" && mise exec -- ./ci/uv_audit.sh --frozen

# Run the full local check ladder.
all: fast security index-smoke
