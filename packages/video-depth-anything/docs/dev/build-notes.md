# Video-Depth-Anything Build Notes

Status: maintained.
Research date: 2026-06-27.

## Status

Video-Depth-Anything is an active TransferBench dependency for `depth_si_rmse`.
The wheel should package importable Python code only; checkpoints stay outside
this repository.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/video-depth-anything/build.sh`
- Generic recipe:
  `just build package video-depth-anything <version> <python> <torch> <output>`

## Upstream Sources

- Upstream repository: https://github.com/DepthAnything/Video-Depth-Anything
- Upstream requirements: `requirements.txt`
- Upstream checkpoint helper: `get_weights.sh`

## Version Constraints

Local package environment requires Python `>=3.10`. The build script clones the
upstream `v${PACKAGE_VERSION}` tag and writes a minimal `setup.py` so the repo
can be built as a wheel without inheriting CUDA-sensitive Torch pins.

## Build Environment

The script creates missing `__init__.py` files before `find_packages()`. Without
that step, the wheel can silently omit important import packages. The generated
metadata intentionally omits Torch and TorchVision; the consuming Transfer
environment should own CUDA compatibility.

## OOM Controls

This is a pure Python packaging wrapper. It does not compile CUDA extensions and
should not need GPU memory or high worker counts.

## Smoke Test

Use a no-deps import/content smoke first:

```bash
python -m zipfile -l <wheel> | rg 'video_depth_anything/video_depth.py|run_streaming.py'
python -c "import video_depth_anything; print(video_depth_anything.__file__)"
```

Scorer parity needs a later GPU/runtime test with actual checkpoints mounted
from the eval cache.

## Known Risks

- Upstream is not primarily distributed as a wheel, so this local wrapper owns
  the package layout.
- Checkpoint licenses differ; do not publish checkpoint assets from this repo.

## Future Fixes

- Add a minimal import fixture that verifies `video_depth_anything.video_depth`
  and `video_depth_anything.motion_module.motion_module`.
- Revisit metadata dependencies after the consuming Transfer environment is
  locked.

## Research Notes

Imported from upstream source and transfer-wheel smoke notes on 2026-06-27. A
prior smoke wheel included `video_depth_anything/video_depth.py`,
`video_depth_anything/motion_module/motion_module.py`, `run.py`, and
`run_streaming.py`.
