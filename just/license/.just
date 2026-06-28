set shell := ["bash", "-c"]

license_dir := source_directory()
repo := license_dir + "/../.."
scripts := license_dir + "/scripts"
export UV_CACHE_DIR := env_var_or_default("UV_CACHE_DIR", repo + "/tmp/uv-cache")

# Show license recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Regenerate source/build-tool attributions from the locked legal environment.
attributions:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/generate-attributions.sh"

# Check that ATTRIBUTIONS.md matches the locked legal environment.
attributions-check:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/generate-attributions.sh" --check

# Check staged wheel artifacts for license metadata and license files.
wheel-check pattern='tmp/build/**/*.whl':
    cd "{{ repo }}" && mise exec -- uv run --frozen python "{{ scripts }}/write_wheel_legal_sidecars.py" --allow-empty {{ quote(pattern) }}
    cd "{{ repo }}" && mise exec -- uv run --frozen python just/release/scripts/check_release_artifacts.py --allow-empty {{ quote(pattern) }}

# Generate per-wheel legal/SBOM sidecars for staged wheel artifacts.
sidecars pattern='tmp/build/**/*.whl':
    cd "{{ repo }}" && mise exec -- uv run --frozen python "{{ scripts }}/write_wheel_legal_sidecars.py" --allow-empty {{ quote(pattern) }}

# Export a CycloneDX SBOM for the locked root build/legal dependency set.
sbom output='tmp/legal-sbom/pai-deps-root.cdx.json':
    cd "{{ repo }}" && mkdir -p "$(dirname -- {{ quote(output) }})"
    cd "{{ repo }}" && mise exec -- uv export --preview-features sbom-export --locked --no-dev --group legal --extra build --format cyclonedx1.5 --output-file {{ quote(output) }} >/dev/null

# Run local legal/compliance checks that do not contact GitHub.
audit: attributions-check wheel-check sbom
