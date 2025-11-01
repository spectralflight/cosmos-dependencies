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

ARG BASE_IMAGE="nvidia/cuda:12.8.1-cudnn-devel-ubuntu20.04"

FROM ${BASE_IMAGE}

# Set the DEBIAN_FRONTEND environment variable to avoid interactive prompts during apt operations.
ENV DEBIAN_FRONTEND=noninteractive

# Update apt and install essential build dependencies in a single layer.
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ccache \
        curl \
        ffmpeg \
        git-lfs \
        tree \
        wget

# Create a user and group for the application.
ARG USERNAME=user
ARG USER_ID=1000
ARG GROUP_ID=$USER_ID
RUN groupadd --gid $GROUP_ID $USERNAME \
    && useradd --uid $USER_ID --gid $GROUP_ID -m $USERNAME \
    && apt-get update \
    && apt-get install -y --no-install-recommends sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set the working directory for the application.
WORKDIR /app

USER $USERNAME

ENV HOME=/home/$USERNAME
ENV XDG_BIN_HOME=$HOME/.local/bin
ENV XDG_CACHE_HOME=$HOME/.cache
ENV UV_CACHE_DIR=$XDG_CACHE_HOME/uv
ENV UV_PYTHON_CACHE_DIR=$UV_CACHE_DIR
ENV CCACHE_DIR=$HOME/.ccache
RUN mkdir -p $XDG_BIN_HOME $XDG_CACHE_HOME
ENV PATH="/usr/lib/ccache:$XDG_BIN_HOME:$PATH"

# Install uv: https://docs.astral.sh/uv/getting-started/installation/
# https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /uvx $XDG_BIN_HOME/

# Install just: https://just.systems/man/en/pre-built-binaries.html
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to $XDG_BIN_HOME --tag 1.42.4

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["/bin/bash"]
