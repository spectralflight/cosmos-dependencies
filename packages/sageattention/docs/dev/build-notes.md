# sageattention Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

SageAttention wheels are historical in this repo. Treat Blackwell support and
architecture lists as tag-specific.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/sageattention/build.sh`

## Upstream Sources

- Upstream repository: https://github.com/thu-ml/SageAttention

## Version Constraints

Upstream docs list Python `>=3.9`, Torch `>=2.3.0`, Triton `>=3.0.0`, CUDA
`>=12.0` for Ampere, CUDA `>=12.3` for Hopper FP8, CUDA `>=12.4` for Ada FP8,
and CUDA `>=12.8` for Blackwell/SageAttention2++ paths.

## Build Environment

Local script sets:

- `EXT_PARALLEL=4`
- `NVCC_APPEND_FLAGS="--threads 8"`
- `MAX_JOBS=32`
- `TORCH_CUDA_ARCH_LIST='9.0'`

The hard-coded arch list means the current script is Hopper-oriented.

## OOM Controls

Override local defaults for first attempts:

```dotenv
EXT_PARALLEL=1
NVCC_APPEND_FLAGS=--threads 1
MAX_JOBS=1
TORCH_CUDA_ARCH_LIST=9.0
```

## Smoke Test

```bash
python - <<'PY'
import torch
from sageattention import sageattn
q = torch.randn(1, 4, 64, 64, device="cuda", dtype=torch.float16)
out = sageattn(q, q, q, tensor_layout="HND", is_causal=False)
assert out.shape == q.shape
PY
```

## Known Risks

- `packages/sageattention/pyproject.toml` currently declares
  `name = "flash-attn"`; this looks copy-paste stale.
- The build script hard-codes Hopper arch and has a Blackwell TODO.

## Future Fixes

- Fix the pyproject project name after checking lockfile impacts.
- Make arch selection explicit through package docs or env defaults before
  future builds.

## Research Notes

Imported from upstream docs/source and read-only package research on
2026-06-27. No Docker builds or package builds were run.
