default:
  just --list

# Install pre-commit
_pre-commit-install *args:
  uv tool install "pre-commit>=4.3.0"
  pre-commit install -c .pre-commit-config-base.yaml {{args}}

# Setup the repository
setup: _pre-commit-install

# Run pre-commit
_pre-commit *args: setup
  pre-commit run -a {{args}} || pre-commit run -a {{args}}

# Run linting and formatting
lint: _pre-commit

# Build a package.
build package_name package_version python_version torch_version cuda_version build_dir='build' *args:
  ./bin/build.sh {{package_name}} {{package_version}} {{python_version}} {{torch_version}} {{cuda_version}} {{build_dir}} {{args}}

# Build a dummy package.
build-dummy cuda_version: (build 'cosmos-dummy' '0.1.0' '3.10' '2.7' cuda_version 'tmp/build')

# Run the docker container.
_docker base_image build_args='' run_args='':
  #!/usr/bin/env bash
  set -euxo pipefail
  build_args="--build-arg=BASE_IMAGE={{base_image}} {{build_args}}"
  docker build $build_args .
  image_tag=$(docker build $build_args -q .)
  # Mount cache directories to avoid re-downloading dependencies.
  # Mount bin/data directories to avoid re-downloading python binaries and tools.
  export XDG_CACHE_HOME=${XDG_CACHE_HOME:-${HOME}/.cache}
  export XDG_DATA_HOME=${XDG_DATA_HOME:-${HOME}/.local/share}
  export XDG_BIN_HOME=${XDG_BIN_HOME:-${XDG_DATA_HOME}/../bin}
  export UV_CACHE_DIR=${UV_CACHE_DIR:-${XDG_CACHE_HOME}/uv}
  export CCACHE_DIR=${CCACHE_DIR:-${HOME}/.ccache}
  # Some packages use `torch.cuda.is_available()` which requires a GPU.
  docker run \
    -it \
    --rm \
    --gpus 1 \
    -v .:/app \
    -v ${XDG_CACHE_HOME}:${HOME}/.cache \
    -v ${XDG_DATA_HOME}:${HOME}/.local/share \
    -v ${XDG_BIN_HOME}:${HOME}/.local/bin \
    -v ${UV_CACHE_DIR}:${HOME}/.cache/uv \
    -v ${CCACHE_DIR}:${HOME}/.ccache \
    -v /etc/passwd:/etc/passwd:ro \
    -v /etc/group:/etc/group:ro \
    --user=$(id -u):$(id -g) \
    {{run_args}} $image_tag

# Run the CUDA 12.6 docker container.
docker-cu126 *args: (_docker 'nvidia/cuda:12.6.3-cudnn-devel-ubuntu20.04' args)

# Run the CUDA 12.8 docker container.
docker-cu128 *args: (_docker 'nvidia/cuda:12.8.1-cudnn-devel-ubuntu20.04' args)

# Run the CUDA 12.9 docker container.
docker-cu129 *args: (_docker 'nvidia/cuda:12.9.1-cudnn-devel-ubuntu20.04' args)

# Run the CUDA 13.0 docker container.
docker-cu130 *args: (_docker 'nvidia/cuda:13.0.1-cudnn-devel-ubuntu22.04' args)

upload pattern *args:
  gh release upload --repo nvidia-cosmos/cosmos-dependencies v$(uv version --short) {{pattern}} {{args}}
  rm -rfv {{pattern}}

version := `uv version --short`
tag := 'v' + version
index_dir := 'docs/' + tag

# Create the package index
_index-create *args:
  uv run bin/create_index.py -i assets -o {{index_dir}} --tag={{tag}} {{args}}

# Create the package index
index-create *args: license (_index-create args)

# Locally serve the package index
index-serve *args: index-create
  uv run -m http.server -d {{index_dir}} {{args}}

# Test the package index
_index-test: (index-create '-o' 'tmp/' + index_dir)

# Run tests
test: lint _index-test

# https://spdx.org/licenses/
allow_licenses := "MIT BSD-2-CLAUSE BSD-3-CLAUSE APACHE-2.0 ISC"
ignore_package_licenses := "nvidia-*"

# Run licensecheck
_licensecheck *args:
  uv run --all-groups licensecheck --show-only-failing --only-licenses {{allow_licenses}} --ignore-packages {{ignore_package_licenses}} --zero {{args}}

# Run pip-licenses
_pip-licenses *args:
  uv run --all-groups pip-licenses --python .venv/bin/python --format=plain-vertical --with-license-file --no-license-path --no-version --with-urls --output-file ATTRIBUTIONS.md {{args}}
  pre-commit run --files ATTRIBUTIONS.md || true

# Check licenses
license: _licensecheck _pip-licenses
