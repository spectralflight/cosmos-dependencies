# NATTEN Build Notes

Status: maintained.
Research date: 2026-06-27.

## Status

NATTEN is the primary maintained package in this repository. Prefer it after
`cosmos-dummy` when validating non-trivial CUDA wheel workflows.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/natten/build.sh`
- Default recipe: `just build natten`

## Upstream Sources

- Upstream repository: https://github.com/SHI-Labs/NATTEN
- Install docs: https://natten.org/install/
- Upstream pyproject: https://github.com/SHI-Labs/NATTEN/blob/main/pyproject.toml
- Changelog: https://github.com/SHI-Labs/NATTEN/blob/main/CHANGELOG.md

## Version Constraints

Local package environment requires Python `>=3.10`. Upstream source supports
Python `>=3.9`; current install docs say NATTEN `0.21.5+` supports PyTorch
`2.8+`, while source metadata has historically allowed lower Torch versions.
`libnatten` requires CUDA `>=12.0`; Blackwell kernels need CUDA `>=12.8`.

## Build Environment

The local wrapper builds from `git+https://github.com/SHI-Labs/NATTEN.git`.
Important variables:

- `NATTEN_CUDA_ARCH`: NATTEN architecture list. Local script appends `10.3`
  for GB300/Blackwell Ultra.
- `NATTEN_N_WORKERS`: CMake worker count.
- `NATTEN_VERBOSE`: local script sets `1`.
- `TORCH_CUDA_ARCH_LIST`: set by the repo wrapper if not provided.
- Useful upstream knobs: `NATTEN_AUTOGEN_POLICY`,
  `NATTEN_BUILD_WITH_PTX`, `NATTEN_BUILD_WITH_LINEINFO`,
  `NATTEN_BUILD_DIR`.

## OOM Controls

Start with an explicit build env file:

```dotenv
MAX_JOBS=1
NATTEN_N_WORKERS=1
NVCC_THREADS=1
TORCH_CUDA_ARCH_LIST=9.0
NATTEN_CUDA_ARCH=9.0
```

Widen architecture lists and worker counts only after the small build passes.
On the local RTX PRO 6000 Blackwell workstation, use `12.0` for single-arch
smoke builds; the upstream docs' `10.0;10.3` Blackwell examples target server
parts rather than Blackwell RTX.

## Smoke Test

After installing a built wheel in a matching Torch/CUDA environment:

```bash
python -c "import torch, natten; print(torch.__version__, natten.__version__, natten.HAS_LIBNATTEN)"
```

`natten.HAS_LIBNATTEN` should be true for CUDA wheels.

## Known Risks

- `just build natten` defaults to `0.21.6.dev6`; upstream currently has
  stable `0.21.6`.
- Existing indices include custom `gb300` local suffixes. Do not rewrite old
  links or rebuild old wheel filenames.
- NATTEN architecture names do not always match `TORCH_CUDA_ARCH_LIST`
  exactly; preserve the local `10.3` handling unless retested.
- Generic `MAX_JOBS` is not the primary NATTEN throttle; prefer
  `NATTEN_N_WORKERS` when tuning memory pressure.

## Future Fixes

- Re-evaluate whether the default recipe should move from `0.21.6.dev6` to the
  stable upstream release.
- Add a tiny import smoke command that can run against a local index without
  starting a package build.

## Research Notes

Imported from upstream docs and read-only package research on 2026-06-27. No
Docker builds or package builds were run for these notes.
