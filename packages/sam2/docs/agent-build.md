# SAM2 Agent Build Notes

Status: agent notes from official docs audit, 2026-06-27.

Official source of truth:

- `https://github.com/facebookresearch/sam2`
- `https://github.com/facebookresearch/sam2/blob/main/INSTALL.md`
- `https://github.com/facebookresearch/sam2/blob/main/setup.py`

## Role In TransferBench

TransferBench uses SAM2 through the Grounded-SAM-2 helper path for video object
tracking and segmentation metrics. Package code and CUDA extensions as wheels;
keep checkpoints external.

## Build Controls

Officially relevant environment variables:

```dotenv
CUDA_HOME=/usr/local/cuda
TORCH_CUDA_ARCH_LIST=12.0
MAX_JOBS=4
SAM2_BUILD_CUDA=1
SAM2_BUILD_ALLOW_ERRORS=0
```

For a quick Python-only smoke, `SAM2_BUILD_CUDA=0` can prove packaging shape,
but it should not be considered a TransferBench scorer proof.

## Scratch Wheel Plan

1. Build a source wheel from a pinned upstream commit or tag.
2. Use single-arch `TORCH_CUDA_ARCH_LIST=12.0` for local proof builds.
3. Install into a fresh env with Torch CUDA and verify `import sam2`.
4. Run a scorer-level smoke later with the Grounded-SAM-2 helper and model
   checkpoints mounted from cache.

The 2026-06-27 CUDA smoke build passed with:

```bash
COSMOS_DEPS_BUILD_ENV='TORCH_CUDA_ARCH_LIST=12.0 MAX_JOBS=4 SAM2_BUILD_CUDA=1 SAM2_BUILD_ALLOW_ERRORS=0' \
  just build docker sam2 1.0 3.12 2.9 /tmp/cosmos-dependencies-wheelhouse/sam2-cu120-j4 12.8.1
```

It produced:

```text
/tmp/cosmos-dependencies-wheelhouse/sam2-cu120-j4/20260627162103-sam2-1.0-py3.12-cu12.8.1-torch2.9/sam_2-1.0+cu128.torch29-cp312-cp312-linux_x86_64.whl
```

Wheel-content smoke:

```bash
python -m zipfile -l <wheel> | rg 'sam2/_C\\.so|sam2/configs/.+\\.yaml'
```

The wheel contains `sam2/_C.so` and SAM2 config YAMLs. A no-deps import will
fail at `hydra`; run full import smoke in an environment that installs runtime
dependencies from wheel metadata.
