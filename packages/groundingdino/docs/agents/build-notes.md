# groundingdino Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

GroundingDINO appears historical and may have stale tag assumptions. Do not
revive without checking upstream tags and extension behavior.
For current TransferBench work, prioritize `sam2`, `video-depth-anything`,
`grounded-sam2-helper`, and `decord` before reviving the compiled
GroundingDINO package.

## Local Build Entry Point

- Package descriptor: `pai-package.toml`
- Build script: `packages/groundingdino/build.sh`

## Upstream Sources

- Upstream repository: https://github.com/IDEA-Research/GroundingDINO
- Upstream setup: https://github.com/IDEA-Research/GroundingDINO/blob/main/setup.py
- Requirements: https://github.com/IDEA-Research/GroundingDINO/blob/main/requirements.txt

## Version Constraints

Local package environment requires Python `>=3.10`. Upstream requirements are
loose and include Torch, TorchVision, Transformers, and Timm; this repo's
Torch/CUDA matrix owns compatibility.

## Build Environment

Local script builds from `git+https://github.com/IDEA-Research/GroundingDINO`.
Upstream compiles CUDA extension code only when `CUDA_HOME` is present and
either `torch.cuda.is_available()` or `TORCH_CUDA_ARCH_LIST` is set.

For headless builds, pass:

```dotenv
CUDA_HOME=/usr/local/cuda
TORCH_CUDA_ARCH_LIST=9.0
MAX_JOBS=1
```

Do not bundle model weights in wheels.

## OOM Controls

This is a PyTorch `BuildExtension`; `MAX_JOBS=1` plus a narrow
`TORCH_CUDA_ARCH_LIST` is the first throttle.

## Smoke Test

```bash
python -c "import groundingdino; import groundingdino._C"
```

This catches the common pure-Python/no-CUDA-extension failure without model
weights.

## Known Risks

- Upstream tags visible during research were `v0.1.0-alpha` and
  `v0.1.0-alpha2`, not plain `v0.1.0`.
- Existing generated index shows a `py3-none-any` wheel despite expected CUDA
  extension behavior.

## Future Fixes

- Pin exact upstream tag/commit in the docs before any future build.
- Verify whether the wheel should contain `groundingdino._C`.

## Research Notes

Imported from upstream docs/source and read-only package research on
2026-06-27. No Docker builds or package builds were run.
