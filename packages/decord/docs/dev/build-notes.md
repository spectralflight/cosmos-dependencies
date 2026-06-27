# decord Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

`decord` is retained for historical GPU/NVDEC wheel documentation. It is not a
Torch extension; the Torch suffix is this repo's index convention.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/decord/build.sh`
- Native library helper: `packages/decord/build_lib.sh`

## Upstream Sources

- Upstream repository: https://github.com/dmlc/decord
- PyPI: https://pypi.org/project/decord/0.6.0/

## Version Constraints

Local package environment requires Python `>=3.10`. Upstream PyPI wheels are
CPU-only; GPU/NVDEC support requires source builds with FFmpeg and CUDA/Video
Codec SDK pieces.

## Build Environment

Local helper uses Video Codec SDK 13.0.19 headers/stubs, configures CMake with
`-DUSE_CUDA=ON -DCMAKE_BUILD_TYPE=Release`, installs `libdecord.so`, then
wheels the Python package from the upstream `python` subdirectory.

Upstream build knobs include `-DUSE_CUDA=ON`, optional CUDA path,
`-DCMAKE_CUDA_COMPILER`, and optional `-DFFMPEG_DIR`.

Local wrapper variables:

- `DECORD_BUILD_JOBS`: passed to `make -j`.
- `DECORD_CUDA_ARCHITECTURES`: passed to CMake as
  `CMAKE_CUDA_ARCHITECTURES`.

## OOM Controls

Start with:

```dotenv
DECORD_BUILD_JOBS=4
DECORD_CUDA_ARCHITECTURES=120
```

Use `DECORD_CUDA_ARCHITECTURES` rather than `TORCH_CUDA_ARCH_LIST`; Decord is a
CMake/CUDA build, not a PyTorch extension build.

## Smoke Test

Generate a tiny MP4 with FFmpeg, then:

```bash
python - <<'PY'
from decord import VideoReader, cpu
vr = VideoReader("tiny.mp4", ctx=cpu(0))
assert len(vr)
assert vr[0].shape[-1] == 3
PY
```

Use GPU/NVDEC smoke only on a host with driver/video decode support.

## Known Risks

- FFmpeg 6 source patches in `build_lib.sh` are brittle against newer decord or
  FFmpeg changes.
- Decord installs system packages during the package prebuild step, so its
  Docker build currently needs `COSMOS_DEPS_DOCKER_AS_ROOT=1`.

## Future Fixes

- Split system package installation from untrusted package build code so Decord
  can install apt packages as root and compile as the non-root build user.

## Research Notes

Imported from upstream docs/source and read-only package research on
2026-06-27. No Docker builds or package builds were run.
