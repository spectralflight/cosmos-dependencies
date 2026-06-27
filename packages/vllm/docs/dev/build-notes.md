# vllm Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

vLLM is a heavy historical package path. It is OOM-prone and version-sensitive;
do not build concurrently with other package builds.

## Local Build Entry Point

- Package descriptor: `pai-package.toml`
- Build script: `packages/vllm/build.sh`

## Upstream Sources

- Upstream repository: https://github.com/vllm-project/vllm
- GPU install docs: https://docs.vllm.ai/en/latest/getting_started/installation/gpu/
- Env vars: https://docs.vllm.ai/en/latest/configuration/env_vars/

## Version Constraints

Upstream docs list Linux, Python `3.10` through `3.13`, NVIDIA compute
capability `>=7.5`, and current binary defaults around recent CUDA releases.
Blackwell requires at least CUDA `12.8`. Match Torch to the exact vLLM release.

## Build Environment

Local script sets:

- `VLLM_TARGET_DEVICE=cuda`
- `VLLM_MAIN_CUDA_VERSION="${CUDA_VERSION}"`
- `CMAKE_BUILD_TYPE=Release`
- `MAX_JOBS=${MAX_JOBS:-$(nproc)}`
- `NVCC_THREADS=${NVCC_THREADS:-2}`

Useful upstream knobs include `CUDA_HOME=/usr/local/cuda`,
`PATH=$CUDA_HOME/bin:$PATH`, and explicit `TORCH_CUDA_ARCH_LIST`.

## OOM Controls

Override the local fast defaults:

```dotenv
MAX_JOBS=1
NVCC_THREADS=1
TORCH_CUDA_ARCH_LIST=9.0
```

Upstream specifically recommends lowering `MAX_JOBS` on constrained machines.

## Smoke Test

A real smoke needs a small cached model. Example shape:

```bash
python - <<'PY'
from vllm import LLM, SamplingParams
llm = LLM(model="facebook/opt-125m", max_model_len=128, enforce_eager=True)
print(llm.generate(["hi"], SamplingParams(max_tokens=1))[0].outputs[0].text)
PY
```

## Known Risks

- Existing generated docs show only older vLLM wheels.
- Local pyproject Torch pin is for audit/build-env resolution, not proof that a
  specific vLLM release builds with that Torch version.
- Default `MAX_JOBS=$(nproc)` is fast but risky on one-GPU workstations.

## Future Fixes

- Pin vLLM release to exact Torch/CUDA requirements in package docs before any
  new wheel batch.
- Consider making `MAX_JOBS` conservative by default.

## Research Notes

Imported from upstream docs/source and read-only package research on
2026-06-27. No Docker builds or package builds were run.
