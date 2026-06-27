set shell := ["bash", "-c"]

build_dir := source_directory()
repo := build_dir + "/../.."
scripts := build_dir + "/scripts"

# Show build recipes.
default:
    @just --justfile "{{ source_file() }}" --list

# Build a package locally.
package package_name package_version python_version torch_version output_dir='build' *args:
    cd "{{ repo }}" && mise exec -- bin/build.sh {{ quote(package_name) }} {{ quote(package_version) }} {{ quote(python_version) }} {{ quote(torch_version) }} {{ quote(output_dir) }} {{ args }}

# Build the dummy package locally.
dummy: (package "cosmos-dummy" "0.1.0" "3.12" "2.9" "tmp/build")

# Build a package inside Docker without an interactive TTY.
docker package_name package_version python_version torch_version output_dir='tmp/build' cuda_version='12.8.1' *args:
    cd "{{ repo }}" && COSMOS_DEPS_DOCKER_CUDA_VERSION={{ quote(cuda_version) }} mise exec -- "{{ scripts }}/docker-build-package.sh" {{ quote(package_name) }} {{ quote(package_version) }} {{ quote(python_version) }} {{ quote(torch_version) }} {{ quote(output_dir) }} {{ args }}

# Build the dummy package inside Docker.
docker-dummy cuda_version='12.8.1': (docker "cosmos-dummy" "0.1.0" "3.12" "2.9" "tmp/build" cuda_version)

# Build natten inside Docker.
docker-natten package_version='0.21.6.dev6' python_version='3.12' torch_version='2.9' cuda_version='12.8.1' *args:
    cd "{{ repo }}" && COSMOS_DEPS_DOCKER_CUDA_VERSION={{ quote(cuda_version) }} mise exec -- "{{ scripts }}/docker-build-package.sh" natten {{ quote(package_version) }} {{ quote(python_version) }} {{ quote(torch_version) }} tmp/build {{ args }}

# Run the docker container for a CUDA version.
docker-shell cuda_version='12.8.1' *args:
    cd "{{ repo }}" && mise exec -- "{{ scripts }}/docker-run.sh" --cuda-version {{ quote(cuda_version) }} {{ args }}

# Run the CUDA 12.6 docker container.
cu126 *args:
    just --justfile "{{ source_file() }}" docker-shell 12.6.3 {{ args }}

# Run the CUDA 12.8 docker container.
cu128 *args:
    just --justfile "{{ source_file() }}" docker-shell 12.8.1 {{ args }}

# Run the CUDA 12.9 docker container.
cu129 *args:
    just --justfile "{{ source_file() }}" docker-shell 12.9.1 {{ args }}

# Run the CUDA 13.0 docker container.
cu130 *args:
    just --justfile "{{ source_file() }}" docker-shell 13.0.2 {{ args }}
