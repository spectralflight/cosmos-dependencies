default:
  just --list

# Install the Python version specified in .python-version
_python-install:
  uv python install

# Setup the repository
setup: _python-install

# Setup pre-commit
_pre-commit-setup *args: setup
  uv tool install "pre-commit>=4.3.0"
  pre-commit install -c ci/.pre-commit-config-base.yaml {{args}}

# Run pre-commit
_pre-commit *args: _pre-commit-setup
  pre-commit run -c ci/.pre-commit-config-base.yaml -a {{args}}
  pre-commit run -a {{args}} || pre-commit run -a {{args}}

# Run linting and formatting
lint: _pre-commit

# Build a package.
build package_name package_version python_version torch_version build_dir='build' *args:
  ./bin/build.sh {{package_name}} {{package_version}} {{python_version}} {{torch_version}} {{build_dir}} {{args}}

# Build a dummy package.
build-dummy: (build 'cosmos-dummy' '0.1.0' '3.12' '2.9' 'tmp/build')

# Build a package inside Docker without an interactive TTY.
docker-build package_name package_version python_version torch_version build_dir='tmp/build' cuda_version='12.8.1' *args:
  COSMOS_DEPENDENCIES_DOCKER_CUDA_VERSION={{cuda_version}} bin/docker_build_package.sh {{package_name}} {{package_version}} {{python_version}} {{torch_version}} {{build_dir}} {{args}}

# Build the dummy package inside Docker.
docker-build-dummy cuda_version='12.8.1': (docker-build 'cosmos-dummy' '0.1.0' '3.12' '2.9' 'tmp/build' cuda_version)

# Build natten inside Docker.
docker-build-natten package_version='0.21.6.dev6' python_version='3.12' torch_version='2.9' cuda_version='12.8.1' *args:
  COSMOS_DEPENDENCIES_DOCKER_CUDA_VERSION={{cuda_version}} bin/docker_build_package.sh natten {{package_version}} {{python_version}} {{torch_version}} tmp/build {{args}}

# Run the docker container.
_docker cuda_version *args:
  bin/docker_run.sh --cuda-version {{cuda_version}} {{args}}

# Run the CUDA 12.6 docker container.
docker-cu126 *args: (_docker '12.6.3' args)

# Run the CUDA 12.8 docker container.
docker-cu128 *args: (_docker '12.8.1' args)

# Run the CUDA 12.9 docker container.
docker-cu129 *args: (_docker '12.9.1' args)

# Run the CUDA 13.0 docker container.
docker-cu130 *args: (_docker '13.0.2' args)

# Fix file permissions.
fix-permissions:
  sudo chown -R $(id -u):$(id -g) .

version := `awk -F'"' '/^version = / { print $2; exit }' pyproject.toml`
tag := 'v' + version
index_dir := 'docs/' + tag
release_repo := 'nvidia-cosmos/cosmos-dependencies'

# Create the package index
_index-create *args:
  uv run bin/create_index.py --wheels-file=wheels.txt -o {{index_dir}} --tag={{tag}} {{args}}

# Create the package index
index-create *args: license (_index-create args)

# Create a package index for an arbitrary release under a caller-selected path.
index-create-release repo tag output_dir *args:
  uv run bin/create_index.py --wheels-file=wheels.txt -o {{output_dir}} --repo {{repo}} --tag {{tag}} {{args}}

# Upload wheels to a GitHub release without deleting local artifacts.
release-upload pattern repo=release_repo tag=tag *args:
  bin/release_upload.sh --repo {{repo}} --tag {{tag}} {{args}} {{pattern}}

upload pattern *args: (release-upload pattern release_repo tag args)

# Verify that a package installs from a generated local index.
index-verify-install index_dir package_name package_version import_name='' python_version='3.12':
  PYTHON_VERSION={{python_version}} bin/verify_index_install.sh {{index_dir}} {{package_name}} {{package_version}} {{import_name}}

# Serve the package index
_index-serve *args:
  uv run -m http.server -d {{index_dir}} {{args}}

# Locally serve the package index
index-serve *args: index-create _index-serve

# Test the package index
_index-test: (index-create '-o' 'tmp/' + index_dir)

_pytest *args:
  uv run pytest {{args}}

# Run tests
test: lint _pytest _index-test

# Check that existing package indices were not modified.
index-guard base='upstream/main':
  python ci/check_docs_indices.py --base {{base}}

# Audit root and package build dependencies.
audit *args:
  ./ci/uv_audit.sh {{args}}

# https://spdx.org/licenses/
allow_licenses := "MIT BSD-2-CLAUSE BSD-3-CLAUSE APACHE-2.0 ISC"
ignore_package_licenses := "nvidia-*"

# Run licensecheck
_licensecheck *args:
  uvx licensecheck@2025.1.0 --show-only-failing --only-licenses {{allow_licenses}} --ignore-packages {{ignore_package_licenses}} --zero {{args}}

# Run pip-licenses
_pip-licenses *args:
  uv sync
  uvx pip-licenses@5.5.1 --python .venv/bin/python --format=plain-vertical --with-license-file --no-license-path --no-version --with-urls --output-file ATTRIBUTIONS.md {{args}}
  pre-commit run --files ATTRIBUTIONS.md || true

# Check licenses
license: _licensecheck _pip-licenses
