# Grounded-SAM-2 Helper Agent Build Notes

Status: agent notes from official docs audit, 2026-06-27.

Official source of truth:

- `https://github.com/IDEA-Research/Grounded-SAM-2`
- GroundingDINO through Transformers:
  `https://huggingface.co/docs/transformers/en/model_doc/grounding-dino`

## Role In TransferBench

The legacy TransferBench path imports helper files from a Grounded-SAM-2 source
checkout, especially tracking utilities and SAM2 config assets. It does not need
the original compiled GroundingDINO package when using Hugging Face
`AutoModelForZeroShotObjectDetection`.

## Packaging Shape

Prefer a thin helper wheel over a full upstream editable clone:

1. Clone a pinned Grounded-SAM-2 commit.
2. Package only the helper modules/config files needed by TransferBench.
3. Depend on `sam2`, `transformers`, and normal Python media deps in the V2
   Transfer environment rather than vendoring them into this helper.
4. Keep GroundingDINO and SAM2 model weights external.

## Smoke Checks

Start with import/config checks:

```bash
python -c 'import grounded_sam2_helper; print(grounded_sam2_helper)'
```

The 2026-06-27 smoke build produced:

```text
/tmp/cosmos-dependencies-wheelhouse/grounded-sam2-helper/20260627155907-grounded_sam2_helper-0.1.0-py3.12-cu12.8.1-torch2.9/grounded_sam2_helper-0.1.0+cu128.torch29-py3-none-any.whl
```

No-deps smoke passed:

```bash
python -m zipfile -l <wheel> | rg 'grounded_sam2_helper/paths.py|sam2_configs/.+\\.yaml'
python -m venv /tmp/cosmos-dependencies-smoke/grounded-sam2-helper
/tmp/cosmos-dependencies-smoke/grounded-sam2-helper/bin/pip install --no-deps <wheel>
/tmp/cosmos-dependencies-smoke/grounded-sam2-helper/bin/python - <<'PY'
from pathlib import Path

from grounded_sam2_helper import sam2_configs_path

print(len(list(Path(sam2_configs_path()).rglob("*.yaml"))))
PY
```

Then run a small segmentation scorer fixture in the V2 Transfer metric package
once the real scorer backend is wired.
