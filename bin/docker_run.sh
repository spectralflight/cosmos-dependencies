#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

usage() {
	cat >&2 <<'EOF'
Usage: bin/docker_run.sh [OPTIONS] [-- COMMAND...]

Build the CUDA Docker image and run it with the repository mounted at /app.

Options:
  --cuda-version VERSION   CUDA image version to build, default: 12.8.1
  --no-tty                Do not allocate an interactive TTY
  --tty                   Force an interactive TTY
  --root                  Keep the container command running as root
  --build-arg ARG         Extra docker build argument, e.g. FOO=bar
  --run-arg ARG           Extra docker run argument token; repeat as needed
  -h, --help              Show this help
EOF
}

repo_root="$(git rev-parse --show-toplevel)"
cuda_version="${COSMOS_DEPENDENCIES_DOCKER_CUDA_VERSION:-12.8.1}"
cache_volume="${COSMOS_DEPENDENCIES_DOCKER_CACHE_VOLUME:-cosmos-dependencies-cache}"
tty_mode="auto"
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
	--root)
		run_args+=("-e" "COSMOS_DOCKER_AS_ROOT=1")
		shift
		;;
	--build-arg)
		build_args+=("--build-arg=$2")
		shift 2
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

env_file="${COSMOS_DEPENDENCIES_ENV_FILE:-}"
if [[ -n "${env_file}" ]]; then
	if [[ ! -f "${env_file}" ]]; then
		echo "Error: COSMOS_DEPENDENCIES_ENV_FILE does not exist: ${env_file}" >&2
		exit 1
	fi
	env_file_abs="$(realpath "${env_file}")"
	case "${env_file_abs}" in
	"${repo_root}"/*)
		env_file="${env_file_abs#"${repo_root}/"}"
		;;
	*)
		echo "Error: COSMOS_DEPENDENCIES_ENV_FILE must be inside the repository mounted at /app: ${env_file}" >&2
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
never)
	;;
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
	-e COSMOS_BUILD_UID="$(id -u)" \
	-e COSMOS_BUILD_GID="$(id -g)" \
	-e COSMOS_BUILD_HOME="/home/cosmos" \
	-e XDG_CACHE_HOME="/cache/xdg" \
	-e XDG_DATA_HOME="/home/cosmos/.local/share" \
	-e XDG_BIN_HOME="/home/cosmos/.local/bin" \
	-e UV_CACHE_DIR="/cache/uv" \
	-e UV_PROJECT_ENVIRONMENT="/home/cosmos/.venv/cosmos-dependencies" \
	-e CCACHE_DIR="/cache/ccache" \
	-e COSMOS_DEPENDENCIES_ENV_FILE="${env_file}" \
	-v "${repo_root}:/app" \
	-v "${cache_volume}:/cache" \
	"${run_args[@]}" \
	"${image_tag}" \
	"${command[@]}"
