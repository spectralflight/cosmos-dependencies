# Grounded-SAM-2 Helper Build Notes

Status: maintained.
Research date: 2026-06-27.

## Status

This is a thin helper package for TransferBench utilities that historically
imported files directly from a Grounded-SAM-2 checkout. It should package helper
modules/config files only and keep model weights external.

## Local Build Entry Point

- Package descriptor: `cosmos-package.toml`
- Build script: `packages/grounded-sam2-helper/build.sh`
- Generic recipe:
  `just build package grounded-sam2-helper <version> <python> <torch> <output>`

## Upstream Sources

- Upstream repository: https://github.com/IDEA-Research/Grounded-SAM-2
- GroundingDINO model docs:
  https://huggingface.co/docs/transformers/en/model_doc/grounding-dino

## Version Constraints

Local package environment requires Python `>=3.10`. The build script clones a
pinned upstream commit via `GROUNDED_SAM2_GIT_REF` and synthesizes a small wheel
from selected files.

## Build Environment

Important variables:

- `GROUNDED_SAM2_GIT_REF`: upstream commit containing the helper files and SAM2
  configs to package.

The consuming Transfer environment should provide `sam2`, `transformers`, media
libraries, and checkpoints.

## OOM Controls

This helper wheel is pure Python/config packaging. It does not compile CUDA
extensions and should not need GPU memory or large worker counts.

## Smoke Test

Start with package contents and no-deps import checks:

```bash
python -m zipfile -l <wheel> | rg 'grounded_sam2_helper/paths.py|sam2_configs/.+\\.yaml'
python -c "from grounded_sam2_helper import sam2_configs_path; print(sam2_configs_path())"
```

Then run a small segmentation scorer fixture in the eval project once the
backend is wired.

## Known Risks

- The package intentionally does not vendor GroundingDINO, SAM2, Transformers,
  or model weights.
- The helper file list is local policy; upstream may move paths without a
  package metadata signal.

## Future Fixes

- Add a regression test for the expected helper files once the consuming scorer
  import path is stable.
- Decide whether to version this helper independently from the upstream commit.

## Research Notes

Imported from upstream source and transfer-wheel smoke notes on 2026-06-27. A
prior no-deps smoke verified `grounded_sam2_helper/paths.py` and packaged SAM2
YAML configs.
