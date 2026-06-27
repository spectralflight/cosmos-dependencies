# GroundingDINO Agent Build Notes

Status: agent notes from official docs audit, 2026-06-27.

Official source of truth:

- `https://github.com/IDEA-Research/GroundingDINO`
- `https://huggingface.co/IDEA-Research/grounding-dino-tiny`
- `https://huggingface.co/docs/transformers/en/model_doc/grounding-dino`

## Role In TransferBench

The original compiled GroundingDINO package is not the first TransferBench wheel
target because the current legacy wrapper uses Hugging Face Transformers'
GroundingDINO model interface. Keep this package around, but prioritize `sam2`,
`video-depth-anything`, `grounded-sam2-helper`, and `decord` first.

## Build Controls

Official docs rely on `CUDA_HOME` and an editable/source install. No
package-specific thread control was found in the official docs. If this package
becomes necessary, use the common build controls:

```dotenv
CUDA_HOME=/usr/local/cuda
TORCH_CUDA_ARCH_LIST=12.0
MAX_JOBS=4
NVCC_THREADS=1
```

Do not bundle model weights in wheels.
