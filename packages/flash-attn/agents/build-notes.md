# flash-attn Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

This package has been published before but is not the primary maintained path.
Treat current scripts as historical until a real build is requested.

## Local Build Entry Point

- Package descriptor: `pai-package.toml`
- Build script: `packages/flash-attn/build.sh`

## Upstream Sources

- Upstream repository: <https://github.com/Dao-AILab/flash-attention>
- PyPI: <https://pypi.org/project/flash-attn/>
- Upstream setup: <https://github.com/Dao-AILab/flash-attention/blob/main/setup.py>

## Version Constraints

Local environment requires Python `>=3.10`. Upstream current package supports
Python `>=3.9`, PyTorch `>=2.2`, CUDA `>=12.0`, and NVIDIA Ampere/Ada/Hopper
GPUs. Check TransformerEngine compatibility before moving to a newer
`flash-attn` release.

## Build Environment

Local script sets:

- `MAX_JOBS=${MAX_JOBS:-$(nproc / 4)}`
- `FLASH_ATTENTION_FORCE_BUILD=TRUE`
- `FLASH_ATTN_CUDA_ARCHS="${TORCH_CUDA_ARCH_LIST//./}"`

Use semicolon-separated `TORCH_CUDA_ARCH_LIST`, for example `9.0` or
`8.0;9.0`. Avoid `+PTX` and space-separated forms unless retested.

## OOM Controls

Start with:

```dotenv
MAX_JOBS=1
NVCC_THREADS=1
TORCH_CUDA_ARCH_LIST=9.0
```

## Smoke Test

In a matching Torch/CUDA environment:

```bash
python - <<'PY'
import torch
from flash_attn import flash_attn_func
q = torch.randn(1, 64, 4, 64, device="cuda", dtype=torch.float16)
out = flash_attn_func(q, q, q)
assert out.shape == q.shape
PY
```

## Known Risks

- Existing indices publish older releases such as `2.7.4.post1`.
- TransformerEngine may cap compatible FlashAttention versions.
- Builds are sensitive to Torch, CUDA, GCC, and arch-list combinations.

## Future Fixes

- Record a package-version to TransformerEngine-version compatibility table.
- Add a non-build install smoke against the fork index after a new wheel batch.

## Research Notes

Imported from upstream docs/source and read-only package research on
2026-06-27. No Docker builds or package builds were run.
