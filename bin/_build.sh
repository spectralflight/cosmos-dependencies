root_dir="$(pwd)"
package_dir="${root_dir}/packages/${PACKAGE_NAME}"

CUDA_NAME="${CUDA_VERSION//./}"
TORCH_NAME="${TORCH_VERSION//./}"

# Print system information.
date
uname -a
cat /etc/os-release
ldd --version
gcc --version

echo "Building ${PACKAGE_NAME}=${PACKAGE_VERSION} python=${PYTHON_VERSION} torch=${TORCH_VERSION} cuda=${CUDA_VERSION}" "$@"

# Set CUDA environment variables
export CUDA_HOME="/usr/local/cuda-${CUDA_VERSION}"
export PATH="${CUDA_HOME}/bin:${PATH:-}"
export LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH:-}"
echo "CUDA_HOME=${CUDA_HOME}"
echo "PATH=${PATH}"
echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH}"
nvcc --version

# Install build dependencies
pushd "${package_dir}"
venv_dir="$(uv cache dir)/cosmos_dependencies/venv"
uv venv --clear --python "${PYTHON_VERSION}" "${venv_dir}"
# shellcheck source=/dev/null
source "${venv_dir}/bin/activate"
uv sync --active
uv pip install "torch==${TORCH_VERSION}" --index-url "https://download.pytorch.org/whl/cu${CUDA_NAME}"

# Set build environment variables
eval "$(python -c "
import torch
print(f'export _GLIBCXX_USE_CXX11_ABI={1 if torch.compiled_with_cxx11_abi() else 0}')
")"
echo "_GLIBCXX_USE_CXX11_ABI=${_GLIBCXX_USE_CXX11_ABI}"

# Build the package.
# shellcheck source=/dev/null
source "${package_dir}/build.sh" "$@"
deactivate
popd

# Fix wheel filenames.
for whl_path in "${OUTPUT_DIR}"/*.whl; do
    uv run bin/fix_wheel_filename.py -i "${whl_path}" --cuda="${CUDA_NAME}" --torch="${TORCH_NAME}"
done