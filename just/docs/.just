set shell := ["bash", "-c"]

docs_dir := source_directory()
repo := docs_dir + "/../.."
scripts := docs_dir + "/scripts"

# Show docs recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Lint agent-only Markdown docs.
lint:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/markdown-lint.sh"
