#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

usage() {
	cat >&2 <<'EOF'
Usage: just/build/scripts/docker-run.sh [OPTIONS] [-- COMMAND...]

Build the CUDA Docker image and run it with the repository mounted at /app.

Options:
  --cuda-version VERSION   CUDA image version to build, default: 12.8.1
  --no-tty                Do not allocate an interactive TTY
  --tty                   Force an interactive TTY
  --build-arg ARG         Extra docker build argument, e.g. FOO=bar
  --root                  Run the command as container root
  --run-arg ARG           Extra docker run argument
  -h, --help              Show this help
EOF
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../../.." && pwd)"
cuda_version="${PAI_DEPS_DOCKER_CUDA_VERSION:-${COSMOS_DEPS_DOCKER_CUDA_VERSION:-12.8.1}}"
cache_volume="${PAI_DEPS_DOCKER_CACHE_VOLUME:-${COSMOS_DEPS_DOCKER_CACHE_VOLUME:-pai-deps-cache}}"
tty_mode="auto"
docker_as_root="0"
build_args=()
run_args=()
command=()

while [[ $# -gt 0 ]]; do
	case "$1" in
	--cuda-version)
		cuda_version="$2"
		shift 2
		;;
	--no-tty)
		tty_mode="never"
		shift
		;;
	--tty)
		tty_mode="always"
		shift
		;;
	--build-arg)
		build_args+=("--build-arg=$2")
		shift 2
		;;
	--root)
		docker_as_root="1"
		shift
		;;
	--run-arg)
		run_args+=("$2")
		shift 2
		;;
	-h | --help)
		usage
		exit 0
		;;
	--)
		shift
		command=("$@")
		break
		;;
	*)
		command=("$@")
		break
		;;
	esac
done

env_file="${PAI_DEPS_BUILD_ENV_FILE:-${COSMOS_DEPS_BUILD_ENV_FILE:-}}"
if [[ -n "${env_file}" ]]; then
	if [[ ! -f "${env_file}" ]]; then
		echo "Error: PAI_DEPS_BUILD_ENV_FILE does not exist: ${env_file}" >&2
		exit 1
	fi
	env_file_abs="$(realpath "${env_file}")"
	case "${env_file_abs}" in
	"${repo_root}"/*)
		env_file="${env_file_abs#"${repo_root}/"}"
		;;
	*)
		echo "Error: PAI_DEPS_BUILD_ENV_FILE must be inside the repository mounted at /app: ${env_file}" >&2
		exit 1
		;;
	esac
fi

tty_args=()
case "${tty_mode}" in
always)
	tty_args=(-it)
	;;
auto)
	if [[ -t 0 && -t 1 ]]; then
		tty_args=(-it)
	fi
	;;
never) ;;
*)
	echo "Error: invalid tty mode: ${tty_mode}" >&2
	exit 1
	;;
esac

image_tag="$(docker build --build-arg="CUDA_VERSION=${cuda_version}" "${build_args[@]}" -q "${repo_root}")"

docker run \
	"${tty_args[@]}" \
	--rm \
	--runtime=nvidia \
	-e PAI_DEPS_BUILD_UID="$(id -u)" \
	-e PAI_DEPS_BUILD_GID="$(id -g)" \
	-e PAI_DEPS_BUILD_HOME="/home/cosmos" \
	-e PAI_DEPS_DOCKER_AS_ROOT="${docker_as_root}" \
	-e XDG_CACHE_HOME="/cache/xdg" \
	-e XDG_DATA_HOME="/home/cosmos/.local/share" \
	-e XDG_BIN_HOME="/home/cosmos/.local/bin" \
	-e UV_CACHE_DIR="/cache/uv" \
	-e UV_PROJECT_ENVIRONMENT="/home/cosmos/.venv/pai-deps" \
	-e CCACHE_DIR="/cache/ccache" \
	-e PAI_DEPS_DOCKER_IMAGE="${image_tag}" \
	-e PAI_DEPS_BUILD_ENV_FILE="${env_file}" \
	-e PAI_DEPS_BUILD_ENV="${PAI_DEPS_BUILD_ENV:-${COSMOS_DEPS_BUILD_ENV:-}}" \
	-v "${repo_root}:/app" \
	-v "${cache_volume}:/cache" \
	"${run_args[@]}" \
	"${image_tag}" \
	"${command[@]}"
