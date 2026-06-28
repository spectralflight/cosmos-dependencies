# flash-attn-3-nv Build Notes

Status: historical.
Research date: 2026-06-27.

## Status

This package points to a third-party FA3 fork. Treat it as requiring extra
source provenance before any new release.

## Local Build Entry Point

- Package descriptor: `pai-package.toml`
- Build script: `packages/flash-attn-3-nv/build.sh`

## Upstream Sources

- Fork used by local script: <https://github.com/alihassanijr/flash_attn_3_nv>
- Closest primary baseline: <https://github.com/Dao-AILab/flash-attention>
- FA3 beta docs: <https://github.com/Dao-AILab/flash-attention#flashattention-3-beta-release>

## Version Constraints

Infer Hopper focus from the local script and FA3 baseline: H100/H800, CUDA
`>=12.3`, CUDA `12.8` preferred, Python `>=3.10`. Published repo wheels have
historically used `cp39-abi3`.

## Build Environment

Local script sets:

- `MAX_JOBS=${MAX_JOBS:-$(nproc / 4)}`
- `FLASH_ATTENTION_DISABLE_SM80=TRUE`
- `FLASH_ATTENTION_FORCE_BUILD=TRUE`

It builds `git+https://github.com/alihassanijr/flash_attn_3_nv.git`.

## OOM Controls

Start with:

```dotenv
MAX_JOBS=1
NVCC_THREADS=1
TORCH_CUDA_ARCH_LIST=9.0
```

## Smoke Test

On a Hopper GPU, import `flash_attn_interface` and run the same tiny FA3 forward
test used for `flash-attn-3`.

## Known Risks

- The fork was not discoverable in current public web search during the
  2026-06-27 research pass; pin exact tags and commits when using it.
- `FLASH_ATTENTION_DISABLE_SM80=TRUE` means the wheel is not intended for
  Ampere.

## Future Fixes

- Replace fork provenance with a stable upstream source if possible.
- Record exact tags and source checksums for any future stable release.

## Research Notes

Imported from local script plus FA3 upstream baseline on 2026-06-27. No Docker
builds or package builds were run.
