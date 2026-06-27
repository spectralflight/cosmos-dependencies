# Decord Agent Build Notes

Status: agent notes from official/local audit, 2026-06-27.

Official source of truth:

- `https://github.com/dmlc/decord`

## Role In TransferBench

Decord is a video IO dependency used by the legacy Video-Depth-Anything helper
and TransferBench utilities. It is a lower-level dependency than SAM2 or
Video-Depth-Anything, but it can block Transfer scorer packaging if no
compatible wheel is available.

## Build Controls

The local recipe builds the native library with CUDA and then builds the Python
wheel. Use:

```dotenv
DECORD_BUILD_JOBS=4
DECORD_CUDA_ARCHITECTURES=120
```

to avoid the historical `make -j "$(nproc)"` behavior during memory-sensitive
experiments and to keep local Blackwell smoke builds single-arch. Decord's CMake
build consumes `DECORD_CUDA_ARCHITECTURES` as `CMAKE_CUDA_ARCHITECTURES`; do not
use `TORCH_CUDA_ARCH_LIST` for Decord.

The Docker build normally runs as the host user. Decord installs system packages
with `apt-get`, so use root mode for this package:

```dotenv
COSMOS_DEPS_DOCKER_AS_ROOT=1
```

## Scratch Wheel Plan

```bash
COSMOS_DEPS_DOCKER_AS_ROOT=1 \
COSMOS_DEPS_BUILD_ENV='DECORD_BUILD_JOBS=4 DECORD_CUDA_ARCHITECTURES=120' \
  just build docker decord 0.6.0 3.12 2.9 /tmp/cosmos-dependencies-wheelhouse/decord-sm120-j4-root 12.8.1
```

The local pyproject name must remain `decord`; it was previously copied from
`flash-attn` and was stale.

The 2026-06-27 smoke build produced:

```text
/tmp/cosmos-dependencies-wheelhouse/decord-sm120-j4-root/20260627162332-decord-0.6.0-py3.12-cu12.8.1-torch2.9/decord-0.6.0+cu128.torch29-cp312-cp312-linux_x86_64.whl
```

Wheel contents include `decord/libdecord.so`. Import smoke passed after
installing NumPy in a Python 3.12 venv:

```bash
python3.12 -m venv /tmp/cosmos-dependencies-smoke/decord-py312
/tmp/cosmos-dependencies-smoke/decord-py312/bin/pip install --no-deps <wheel>
/tmp/cosmos-dependencies-smoke/decord-py312/bin/pip install 'numpy<3'
/tmp/cosmos-dependencies-smoke/decord-py312/bin/python -c 'import decord; print(decord.__version__)'
```
