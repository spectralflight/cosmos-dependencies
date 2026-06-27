# Video-Depth-Anything Agent Build Notes

Status: agent notes from official docs audit, 2026-06-27.

Official source of truth:

- `https://github.com/DepthAnything/Video-Depth-Anything`
- Upstream `requirements.txt`
- Upstream `get_weights.sh`

## Role In TransferBench

TransferBench computes `depth_si_rmse` with Video-Depth-Anything. The legacy
runtime exposes this by cloning the repository under `/opt` and patching import
paths; V2 should package importable Python code and keep weights external.

## Packaging Shape

Upstream is not primarily distributed as a wheel. Treat the first recipe as an
import-hygiene wheel:

1. Clone a pinned commit.
2. Create a minimal package wrapper for the importable model code.
3. Do not bundle checkpoints.
4. Avoid upstream's old Torch pins in the wheel metadata; the V2 Transfer env
   should own Torch/CUDA compatibility.

Upstream `video_depth_anything`, `video_depth_anything/motion_module`,
`video_depth_anything/util`, `utils`, `loss`, and some `benchmark` subpackages
do not all include `__init__.py` files. The build recipe must create those files
before calling `find_packages()`, otherwise the wheel can silently contain only
the `benchmark` package.

The 2026-06-27 smoke build produced:

```text
/tmp/cosmos-dependencies-wheelhouse/video-depth-anything-fixed-no-torch-meta/20260627162553-video_depth_anything-1.3.1-py3.12-cu12.8.1-torch2.9/video_depth_anything-1.3.1+cu128.torch29-py3-none-any.whl
```

Wheel contents included `video_depth_anything/video_depth.py`,
`video_depth_anything/motion_module/motion_module.py`, `run.py`, and
`run_streaming.py`. Wheel metadata intentionally omits Torch and TorchVision;
the locked Transfer environment should own those CUDA-sensitive dependencies.

## License Note

The small checkpoint is Apache-2.0. Larger checkpoints may be non-commercial.
Do not publish any checkpoint assets from this repository.

## Smoke Checks

The first useful check is import-only:

```bash
python -c 'import video_depth_anything; print(video_depth_anything)'
```

The no-deps smoke passed with:

```bash
python -m venv /tmp/cosmos-dependencies-smoke/video-depth-anything
/tmp/cosmos-dependencies-smoke/video-depth-anything/bin/pip install --no-deps <wheel>
/tmp/cosmos-dependencies-smoke/video-depth-anything/bin/python - <<'PY'
import importlib.util
import video_depth_anything
print(video_depth_anything.__file__)
print(importlib.util.find_spec("video_depth_anything.video_depth") is not None)
print(importlib.util.find_spec("video_depth_anything.motion_module.motion_module") is not None)
PY
```

Scorer parity needs a later GPU test with the actual checkpoint mounted from
the eval cache.
