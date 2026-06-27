# flash-attn-3 Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

FlashAttention-3 support is historical in this repo. Use only when a release
explicitly needs Hopper FA3 wheels.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/flash-attn-3/build.sh`

## Upstream Sources

- FlashAttention repository: https://github.com/Dao-AILab/flash-attention
- FA3 beta docs: https://github.com/Dao-AILab/flash-attention#flashattention-3-beta-release
- Hopper setup: https://github.com/Dao-AILab/flash-attention/blob/main/hopper/setup.py

## Version Constraints

Upstream describes FA3 as beta and optimized for H100/H800. CUDA `>=12.3` is
required; CUDA `12.8` is recommended. Hopper setup requires Python `>=3.10`.

## Build Environment

Local script builds the `hopper` subdirectory and sets:

- `MAX_JOBS=${MAX_JOBS:-$(nproc / 4)}`
- `FLASH_ATTENTION_FORCE_BUILD=TRUE`

Upstream setup exposes pruning flags such as
`FLASH_ATTENTION_DISABLE_BACKWARD`, `FLASH_ATTENTION_DISABLE_FP8`,
`FLASH_ATTENTION_DISABLE_VARLEN`, and `NVCC_THREADS`.

## OOM Controls

Start with:

```dotenv
MAX_JOBS=1
NVCC_THREADS=1
TORCH_CUDA_ARCH_LIST=9.0
```

Consider disabling unused kernel families only after checking the target wheel
contract.

## Smoke Test

On a Hopper GPU:

```bash
python - <<'PY'
import torch
from flash_attn_interface import flash_attn_func
q = torch.randn(1, 64, 4, 64, device="cuda", dtype=torch.float16)
out = flash_attn_func(q, q, q)
assert out.shape == q.shape
PY
```

## Known Risks

- Verify that `PACKAGE_VERSION` maps to a real upstream `v...` tag before
  attempting a build.
- This package appears only in older generated indices.

## Future Fixes

- Document exact supported GPU architectures per version if this package is
  revived.
- Consider pruning SM80 kernels when building Hopper-only wheels.

## Research Notes

Imported from upstream docs/source and read-only package research on
2026-06-27. No Docker builds or package builds were run.
