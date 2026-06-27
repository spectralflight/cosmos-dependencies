# xformers Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

`xformers` has historical wheels in this repo. Treat scripts as version-sensitive
and retest before publishing new wheel batches.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/xformers/build.sh`

## Upstream Sources

- Upstream repository: https://github.com/facebookresearch/xformers
- Upstream setup: https://github.com/facebookresearch/xformers/blob/main/setup.py
- Releases: https://github.com/facebookresearch/xformers/releases

## Version Constraints

Upstream current releases require recent PyTorch and Python `>=3.9`; local
package environment requires Python `>=3.10`. Match Torch exactly to the wheel
matrix being built.

## Build Environment

Local script sets `XFORMERS_BUILD_TYPE=Release` and builds from
`git+https://github.com/facebookresearch/xformers.git`.

Useful upstream/local knobs:

- `TORCH_CUDA_ARCH_LIST`
- `MAX_JOBS`
- `FORCE_CUDA=1`
- `NVCC_FLAGS`
- `XFORMERS_ENABLE_DEBUG_ASSERTIONS`
- `XFORMERS_SELECTIVE_BUILD`

## OOM Controls

Start with:

```dotenv
MAX_JOBS=1
TORCH_CUDA_ARCH_LIST=9.0
```

Upstream specifically recommends lowering `MAX_JOBS` if source builds OOM.

## Smoke Test

```bash
python -m xformers.info
```

For a CUDA smoke, call `xformers.ops.memory_efficient_attention` on tiny fp16
tensors.

## Known Risks

- Existing v1.5.0 wheels target Torch 2.9 while current upstream releases have
  moved on.
- FlashAttention compatibility inside xformers can change by release.

## Future Fixes

- Record Torch/xformers compatibility beside each future release manifest.
- Add an index-install smoke for `python -m xformers.info`.

## Research Notes

Imported from upstream docs/source and read-only package research on
2026-06-27. No Docker builds or package builds were run.
