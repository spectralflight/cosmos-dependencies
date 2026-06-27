# Legal Audit Notes

Status: candidate, 2026-06-27. This is an engineering compliance checklist,
not legal advice.

## Scope Split

`ATTRIBUTIONS.md` covers the locked root project, the `build` extra, and the
`legal` dependency group. It intentionally does not try to summarize every
third-party project wheel that this repository builds and hosts.

Release wheels are checked separately because they are the distributed
third-party artifacts. Upload planning and release validation require wheel
metadata to expose at least one license signal: `License-Expression`, a
non-`UNKNOWN` `License` field, license classifiers, declared `License-File`
entries, or license/notice files under `.dist-info`.

## Commands

- `just license::attributions`: regenerate `ATTRIBUTIONS.md` from an isolated
  locked uv environment.
- `just license::attributions-check`: fail if committed attributions are stale.
- `just license::wheel-check`: validate staged wheel sidecars and wheel license
  metadata.
- `just license::audit`: run the local legal lane.
- `just check::no-gpu`: includes the legal lane and does not start Docker.

## Package Policy

Package scripts that synthesize a wheel from selected upstream files must copy
upstream `LICENSE`, `NOTICE`, or `COPYING` files into the generated wheel and
declare them with `license_files`.

Package scripts that set explicit license-confirmation environment variables
must declare `[license_review]` metadata in `pai-package.toml`. The descriptor
should link to the upstream reference and include a short release-review note.

## Manual Deep Audit

Use ScanCode Toolkit manually for a deeper source/binary review when adding
vendored code, generated wrappers, binary artifacts, or a new package with
unclear licensing. Keep it out of default free CI unless a lightweight locked
workflow proves useful.
