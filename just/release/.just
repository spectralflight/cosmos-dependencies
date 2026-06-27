set shell := ["bash", "-c"]

release_dir := source_directory()
repo := release_dir + "/../.."
scripts := release_dir + "/scripts"
version := `awk -F'"' '/^version = / { print $2; exit }' ../../pyproject.toml`
tag := "v" + version
export UV_CACHE_DIR := env_var_or_default("UV_CACHE_DIR", repo + "/tmp/uv-cache")

# Show release recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Generate a temporary package index for an index name.
create index_name=tag *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o "tmp/docs/{{ index_name }}" --index-name {{ quote(index_name) }} {{ args }}

# Publish a package index under docs for GitHub Pages.
publish index_name=tag *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o "docs/{{ index_name }}" --index-name {{ quote(index_name) }} {{ args }}

# Create a package index from an explicit manifest.
create-manifest manifest_path output_dir *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o {{ quote(output_dir) }} --manifest {{ quote(manifest_path) }} {{ args }}

# Create a package index for an arbitrary release under a caller-selected path.
create-release repo_name release_tag output_dir *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o {{ quote(output_dir) }} --repo {{ quote(repo_name) }} --tag {{ quote(release_tag) }} {{ args }}

# Upload wheels to a GitHub release without deleting local artifacts.
upload pattern repo_name release_tag=tag *args:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/release-upload.sh" --repo {{ quote(repo_name) }} --tag {{ quote(release_tag) }} {{ args }} {{ quote(pattern) }}

# Print the assets and sidecar status for a release upload without touching GitHub.
upload-plan pattern repo_name release_tag=tag *args:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/release-upload.sh" --dry-run --repo {{ quote(repo_name) }} --tag {{ quote(release_tag) }} {{ args }} {{ quote(pattern) }}

# Upload wheels to a dated batch release for a logical package index.
upload-batch pattern batch_id repo_name index_tag=tag *args:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/release-upload.sh" --repo {{ quote(repo_name) }} --tag {{ quote("wheels-" + index_tag + "-batch." + batch_id) }} --title {{ quote("Wheel batch " + index_tag + " " + batch_id) }} --notes {{ quote("Wheel batch for " + index_tag + ".") }} --not-latest {{ args }} {{ quote(pattern) }}

# Copy selected assets from one GitHub release to another.
copy-assets source_repo source_tag dest_repo dest_tag include='*':
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/copy_release_assets.py --source-repo {{ quote(source_repo) }} --source-tag {{ quote(source_tag) }} --dest-repo {{ quote(dest_repo) }} --dest-tag {{ quote(dest_tag) }} --include {{ quote(include) }}

# Print selected release assets for a copy operation without downloading or uploading.
copy-plan source_repo source_tag dest_repo dest_tag include='*':
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/copy_release_assets.py --dry-run --source-repo {{ quote(source_repo) }} --source-tag {{ quote(source_tag) }} --dest-repo {{ quote(dest_repo) }} --dest-tag {{ quote(dest_tag) }} --include {{ quote(include) }}

# Verify that a package installs from a generated local index.
verify-install index_dir package_name package_version import_name='' python_version='3.12':
    cd "{{ repo }}" && PYTHON_VERSION={{ quote(python_version) }} mise exec -- "{{ scripts }}/verify-index-install.sh" {{ quote(index_dir) }} {{ quote(package_name) }} {{ quote(package_version) }} {{ quote(import_name) }}

# Serve the package index.
serve index_name=tag *args:
    cd "{{ repo }}" && mise exec -- uv run --frozen -m http.server -d {{ quote("docs/" + index_name) }} {{ args }}

# Generate a temporary package index for the current version.
test-index index_name=tag:
    cd "{{ repo }}" && mise exec -- uv run --frozen bin/create_index.py --wheels-file=wheels.txt -o "tmp/docs/{{ index_name }}" --index-name {{ quote(index_name) }}

# Generate a temporary package index without modifying docs.
create-dry-run index_name=tag: (create index_name)

# Validate wheel/log/provenance triplets for staged release artifacts.
artifact-check pattern='tmp/build/**/*.whl':
    cd "{{ repo }}" && mise exec -- uv run --frozen python ci/check_release_artifacts.py --allow-empty {{ quote(pattern) }}
