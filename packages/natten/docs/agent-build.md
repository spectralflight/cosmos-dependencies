# NATTEN Agent Build Notes

Status: agent notes from official docs audit, 2026-06-27.

Official source of truth:

- NATTEN install docs: `https://natten.org/install/`
- NATTEN changelog and `setup.py`: `https://github.com/SHI-Labs/NATTEN`

## Local Blackwell RTX Smoke Target

For the local RTX PRO 6000 Blackwell workstation, use a single SM120 build:

```dotenv
NATTEN_CUDA_ARCH=12.0
TORCH_CUDA_ARCH_LIST=12.0
```

The NATTEN docs' `10.0;10.3` example is for SM100/SM103 Blackwell server parts,
not Blackwell RTX. The local `packages/natten/build.sh` default appends `10.3`
for GB300 coverage, so always override `NATTEN_CUDA_ARCH` for single-arch local
experiments.

## Parallelism

Use `NATTEN_N_WORKERS`; generic `MAX_JOBS` is not the primary NATTEN build
control. Target 30-50% host memory during experiments before widening.

Measured single-arch experiment matrix on this workstation:

| Workers | Approx Wall Time | Peak Sampled RSS | Result |
| --- | ---: | ---: | --- |
| 4 | 10m05s | 5.8 GiB | pass |
| 8 | 6m46s | 9.6 GiB | pass |
| 16 | 5m06s | 13.2 GiB | pass |
| 24 | 5m22s | 21.4 GiB | pass |

Use `NATTEN_N_WORKERS=16` for local single-arch SM120 smoke builds. It was the
best wall-clock result while staying well below the 30-50% memory target. The
24-worker run raced the broad compile phase but lost time in the tail.

Recommended single-arch smoke command:

```dotenv
NATTEN_CUDA_ARCH=12.0
NATTEN_AUTOGEN_POLICY=coarse
NATTEN_N_WORKERS=16
```

For a new machine, start at 8 workers, sample memory, then try 16 if peak
memory is safely inside the target.

## Commands

Run builds in Docker and keep wheels under `/tmp` for scratch experiments:

```bash
COSMOS_DEPS_BUILD_ENV='NATTEN_CUDA_ARCH=12.0 NATTEN_N_WORKERS=16 NATTEN_AUTOGEN_POLICY=coarse CCACHE_DISABLE=1' \
  just build docker natten 0.21.6.dev6 3.12 2.9 /tmp/cosmos-dependencies-wheelhouse/natten-j16-coarse 12.8.1
```

Monitor the container while it compiles:

```bash
docker stats --no-stream
tail -n 80 /tmp/cosmos-dependencies-builds/natten-j4-coarse/driver.log
```

## Stale Local Defaults

- `build.sh` forces `NATTEN_VERBOSE=1`.
- `build.sh` defaults workers to half the host CPU count, which can be too
  aggressive before memory is measured.
- `build.sh` defaults `NATTEN_CUDA_ARCH` to `${TORCH_CUDA_ARCH_LIST};10.3`,
  which is not a single-arch RTX Blackwell smoke.
