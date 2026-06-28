# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generate PEP 503 compliant index.

Reference: https://peps.python.org/pep-0503/
"""

import collections
import html
import json
import shutil
import subprocess
import urllib.parse
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Annotated

import tyro
from wheel_filename import WheelFilename

from pai_deps.index_manifest import load_index_manifest
from pai_deps.release_artifacts import WHEEL_LEGAL_SIDECAR_SUFFIXES, WHEEL_SIDECAR_LABELS

_TORCH_BASE_URL = "https://download.pytorch.org"
_TORCH_PACKAGES = [
    "torch",
    "torchvision",
    "triton",
    "xformers",
]

_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<body>
{body}
</body>
</html>
"""


@dataclass(frozen=True, order=True)
class _SidecarLink:
    label: str
    url: str

    def __str__(self) -> str:
        url = html.escape(self.url, quote=True)
        label = html.escape(self.label)
        return f"<a data-pai-artifact='true' href='{url}'>{label}</a>"


@dataclass(frozen=True, order=True)
class _IndexLine:
    """Index line."""

    name: str
    url: str | None = None
    sidecars: tuple[_SidecarLink, ...] = ()

    def __str__(self) -> str:
        if self.url is not None:
            url = html.escape(self.url, quote=True)
        else:
            url = html.escape(f"{self.name}/", quote=True)
        name = html.escape(self.name)
        line = f"<a href='{url}'>{name}</a>"
        if self.sidecars:
            line += " " + " ".join(map(str, self.sidecars))
        return f"{line}<br>"


def _download_html(url: str, html_path: Path, *, base_url: str) -> None:
    """Download index HTML file."""
    html_path.parent.mkdir(exist_ok=True, parents=True)
    cmd = [
        "wget",
        "--quiet",
        "--convert-links",
        f"--base={base_url}",
        url,
        "-O",
        html_path,
    ]
    subprocess.check_call(cmd)

    # Strip comments and empty lines
    lines: list[str] = []
    for line in html_path.read_text().splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("<!--"):
            continue
        lines.append(line)
    html_path.write_text("\n".join(lines) + "\n")


def _write_html(html_path: Path, lines: set[_IndexLine]) -> None:
    """Write index HTML file."""
    index_html = _HTML_TEMPLATE.format(body="\n".join(map(str, sorted(lines))))
    html_path.parent.mkdir(exist_ok=True, parents=True)
    html_path.write_text(index_html)


@dataclass(kw_only=True, frozen=True)
class Args:
    output_dir: Annotated[Path, tyro.conf.arg(aliases=("-o",))]
    """Output directory."""
    repo: str = "spectralflight/pai-deps"
    """GitHub repository. Used with --tag and as the manifest fallback repo."""
    tag: str | None = None
    """Release tag. Required unless --manifest is set."""
    manifest: Path | None = None
    """Index manifest containing one or more GitHub releases."""
    index_name: str | None = None
    """Index name. Uses indices/<name>/manifest.json when present, otherwise a release tag."""
    wheels_file: Path | None = None
    """Wheels file."""


def _get_release_assets(*, repo: str, tag: str) -> list[dict]:
    """Get release assets from GitHub."""
    cmd = [
        "gh",
        "release",
        "view",
        "--repo",
        repo,
        tag,
        "--json",
        "assets",
    ]
    return json.loads(subprocess.check_output(cmd, text=True))["assets"]


def _collect_release_assets(args: Args) -> list[dict]:
    if args.manifest is None:
        if args.tag is None:
            raise ValueError("Pass --tag or --manifest.")
        return _get_release_assets(repo=args.repo, tag=args.tag)

    if args.tag is not None:
        raise ValueError("Pass either --tag or --manifest, not both.")

    manifest = load_index_manifest(args.manifest, fallback_repo=args.repo)
    assets: list[dict] = []
    for release in manifest.releases:
        assets.extend(_get_release_assets(repo=release.repo, tag=release.tag))
    return assets


def _resolve_index_name(args: Args) -> Args:
    if args.index_name is None:
        return args
    if args.tag is not None or args.manifest is not None:
        raise ValueError("Pass --index-name by itself, or pass explicit --tag/--manifest.")
    manifest = Path("indices") / args.index_name / "manifest.json"
    if manifest.is_file():
        return replace(args, manifest=manifest.resolve())
    return replace(args, tag=args.index_name)


def _asset_url_with_digest(asset: dict) -> str:
    url = str(asset["url"])
    digest = str(asset.get("digest", ""))
    if ":" not in digest:
        return url
    hash_name, hash_value = digest.split(":", 1)
    if not hash_name or not hash_value:
        return url
    return f"{url}#{hash_name}={hash_value}"


def _collect_index_lines(*, assets: list[dict], wheels_file: Path | None = None) -> dict[str, set[_IndexLine]]:
    # Group wheels by package name
    all_wheels: dict[str, set[_IndexLine]] = collections.defaultdict(set)
    assets_by_name = {str(asset["name"]): asset for asset in assets}

    # Get wheels from release assets
    for asset in assets:
        filename: str = asset["name"]
        if not filename.endswith(".whl"):
            continue

        url = _asset_url_with_digest(asset)
        sidecars = tuple(
            _SidecarLink(WHEEL_SIDECAR_LABELS[suffix], _asset_url_with_digest(sidecar_asset))
            for suffix in WHEEL_LEGAL_SIDECAR_SUFFIXES
            if (sidecar_asset := assets_by_name.get(filename + suffix)) is not None
        )
        pwf = WheelFilename.parse(filename)
        package_name = pwf.project.replace("_", "-")

        all_wheels[package_name].add(_IndexLine(filename, url, sidecars))

    # Parse wheel URL files
    if wheels_file is not None:
        urls = wheels_file.read_text().splitlines()
        for url in urls:
            url = url.strip()
            if not url or url.startswith("#"):
                # Skip comments and empty lines
                continue
            url_parts = urllib.parse.urlparse(url)
            filename = urllib.parse.unquote(url_parts.path.rsplit("/", 1)[-1])
            pwf = WheelFilename.parse(filename)
            package_name = pwf.project.replace("_", "-")
            all_wheels[package_name].add(_IndexLine(filename, url))

    all_lines: dict[str, set[_IndexLine]] = collections.defaultdict(set)
    for package_name, package_wheels in all_wheels.items():
        all_lines[package_name].update(package_wheels)
    return all_lines


def _write_index(output_dir: Path, all_lines: dict[str, set[_IndexLine]]) -> None:
    """Write the global index and package index files."""

    # Create global index
    index_lines = set(_IndexLine(package_name) for package_name in all_lines)
    _write_html(output_dir / "index.html", index_lines)
    for package_name, package_lines in all_lines.items():
        _write_html(
            output_dir / package_name / "index.html",
            package_lines,
        )


def main(args: Args):
    args = _resolve_index_name(args)
    shutil.rmtree(args.output_dir, ignore_errors=True)
    assets = _collect_release_assets(args)
    all_lines = _collect_index_lines(assets=assets, wheels_file=args.wheels_file)
    _write_index(args.output_dir, all_lines)


if __name__ == "__main__":
    args = tyro.cli(Args, description=__doc__)
    main(args)
