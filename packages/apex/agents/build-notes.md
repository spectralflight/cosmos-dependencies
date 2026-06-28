# apex Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

Apex is retained for historical wheel documentation. Do not assume current
scripts build against new Torch/CUDA versions without a dedicated test.

## Local Build Entry Point

- Package descriptor: `pai-package.toml`
- Build script: `packages/apex/build.sh`

## Upstream Sources

- Upstream repository: <https://github.com/NVIDIA/apex>
- Upstream setup: <https://github.com/NVIDIA/apex/blob/master/setup.py>

## Version Constraints

Apex has no regular GitHub releases. Local `PACKAGE_VERSION=0.1.0` maps to a
fixed commit. Upstream recommends recent PyTorch and requires a CUDA toolkit
with `nvcc` for CUDA extensions.

## Build Environment

Local script sets:

- `APEX_CPP_EXT=1`
- `APEX_CUDA_EXT=1`
- `APEX_PARALLEL_BUILD=8`
- `NVCC_APPEND_FLAGS="--threads 4"`

Optional upstream extension flags include `APEX_FAST_MULTIHEAD_ATTN`,
`APEX_FUSED_CONV_BIAS_RELU`, and `APEX_ALL_CONTRIB_EXT=1`.

## OOM Controls

For constrained builders, lower:

```dotenv
APEX_PARALLEL_BUILD=1
NVCC_APPEND_FLAGS=--threads 1
MAX_JOBS=1
TORCH_CUDA_ARCH_LIST=9.0
```

## Smoke Test

After install, import `apex` and instantiate a CUDA extension such as
`apex.normalization.FusedLayerNorm` or `apex.optimizers.FusedAdam`.

## Known Risks

- Apex commit pinning means the package version is not a real upstream version.
- Existing indices do not show modern Torch 2.10 coverage.

## Future Fixes

- Move commit pins into manifest/docs for review before future builds.
- Re-evaluate which Apex extension flags are actually needed.

## Research Notes

Imported from upstream README/setup and read-only package research on
2026-06-27. No Docker builds or package builds were run.
