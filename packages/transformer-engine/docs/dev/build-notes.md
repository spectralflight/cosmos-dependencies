# transformer-engine Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

Transformer Engine wheels are historically important but highly sensitive to
Torch, CUDA, cuDNN, GCC, FlashAttention, and local header workarounds.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/transformer-engine/build.sh`

## Upstream Sources

- Upstream repository: https://github.com/NVIDIA/TransformerEngine
- Installation docs: https://github.com/NVIDIA/TransformerEngine/blob/main/docs/installation.rst
- Build tools: https://github.com/NVIDIA/TransformerEngine/tree/main/build_tools

## Version Constraints

Upstream lists Linux x86_64, CUDA `>=12.1`, CUDA `>=12.8` for Blackwell,
cuDNN `>=9.3`, GCC `>=9` or Clang `>=10`, C++17, and Python 3.12 as a
recommended version. Local pyproject also pulls JAX/Flax build dependencies.

## Build Environment

Local script sets:

- `NVTE_FRAMEWORK=pytorch`
- `NVTE_CUDA_ARCHS="${TORCH_CUDA_ARCH_LIST//./}"`

Useful upstream knobs include `MAX_JOBS`, `NVTE_BUILD_THREADS_PER_JOB`,
`CUDA_PATH`, `CUDNN_PATH`, `CXX`, `NVTE_USE_CCACHE`, `NVTE_CCACHE_BIN`, and
`NVTE_CMAKE_BUILD_DIR`.

## OOM Controls

Start with:

```dotenv
MAX_JOBS=1
NVTE_BUILD_THREADS_PER_JOB=1
TORCH_CUDA_ARCH_LIST=9.0
```

Upstream calls out FlashAttention compilation as RAM-heavy.

## Smoke Test

Run a tiny PyTorch TE module in a matching CUDA environment:

```bash
python - <<'PY'
import torch
import transformer_engine.pytorch as te
layer = te.Linear(8, 8).cuda()
x = torch.randn(2, 8, device="cuda")
layer(x).sum().backward()
PY
```

## Known Risks

- Local script writes a missing PyTorch header into the installed Torch include
  tree. Treat that as a version-specific workaround.
- Existing indices publish older TE versions than current upstream releases.

## Future Fixes

- Replace the header shim with an upstream fix or exact version guard.
- Document FlashAttention compatibility per TE release before new builds.

## Research Notes

Imported from upstream docs/source and read-only package research on
2026-06-27. No Docker builds or package builds were run.
