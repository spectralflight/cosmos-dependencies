set shell := ["bash", "-c"]

release_dir := source_directory()
repo := release_dir + "/../.."
scripts := release_dir + "/scripts"
version := `repo="$(git rev-parse --show-toplevel)" && awk -F'"' '/^version = / { print $2; exit }' "$repo/pyproject.toml"`
tag := "v" + version
index_dir := "docs/" + tag
release_repo := "nvidia-cosmos/cosmos-dependencies"

# Show release recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Create the package index for the current version.
create *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o {{ quote(index_dir) }} --tag={{ quote(tag) }} {{ args }}

# Create a package index for an arbitrary release under a caller-selected path.
create-release repo_name release_tag output_dir *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o {{ quote(output_dir) }} --repo {{ quote(repo_name) }} --tag {{ quote(release_tag) }} {{ args }}

# Upload wheels to a GitHub release without deleting local artifacts.
upload pattern repo_name=release_repo release_tag=tag *args:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/release-upload.sh" --repo {{ quote(repo_name) }} --tag {{ quote(release_tag) }} {{ args }} {{ quote(pattern) }}

# Verify that a package installs from a generated local index.
verify-install index_dir package_name package_version import_name='' python_version='3.12':
    cd "{{ repo }}" && PYTHON_VERSION={{ quote(python_version) }} mise exec -- "{{ scripts }}/verify-index-install.sh" {{ quote(index_dir) }} {{ quote(package_name) }} {{ quote(package_version) }} {{ quote(import_name) }}

# Serve the package index.
serve *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen -m http.server -d {{ quote(index_dir) }} {{ args }}

# Generate a temporary package index for the current version.
test-index:
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o {{ quote("tmp/" + index_dir) }} --tag={{ quote(tag) }}
