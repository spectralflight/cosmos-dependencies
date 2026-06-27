set shell := ["bash", "-c"]

license_dir := source_directory()
repo := license_dir + "/../.."
allow_licenses := "MIT BSD-2-CLAUSE BSD-3-CLAUSE APACHE-2.0 ISC"
ignore_package_licenses := "nvidia-*"

# Show license recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Run licensecheck.
licensecheck *args:
    cd "{{ repo }}" && mise exec -- uvx licensecheck@2025.1.0 --show-only-failing --only-licenses {{ allow_licenses }} --ignore-packages {{ ignore_package_licenses }} --zero {{ args }}

# Regenerate ATTRIBUTIONS.md with pip-licenses.
attributions *args:
    cd "{{ repo }}" && mise exec -- uv sync && mise exec -- uvx pip-licenses@5.5.1 --python .venv/bin/python --format=plain-vertical --with-license-file --no-license-path --no-version --with-urls --output-file ATTRIBUTIONS.md {{ args }} && mise exec -- pre-commit run --files ATTRIBUTIONS.md || true

# Check licenses and attributions.
check: licensecheck attributions
