# author: Paul Galatic
# Script assumes that .deb package files for cuda/cudnn are already present 
#   and in the home directory

cd ~/
sudo apt-get -y update

# Install FFMPEG
sudo apt-get -y install ffmpeg

# Install CUDA v9.2
sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
sudo dpkg -i cuda-repo-ubuntu1604_9.2.148-1_amd64.deb
sudo apt-get -y update
sudo apt-get -y install cuda-9-2

# Install CUDNN v7.6.5 (for CUDA v9.2)
tar -xzvf cudnn-9.2-linux-x64-v7.6.5.32.tgz
sudo cp cuda/include/cudnn.h /usr/local/cuda/include
sudo cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
sudo chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*

# Let Cmake find CUDA/CUDNN
export PATH=/usr/local/cuda${PATH:+:${PATH}}
export CUDNN_PATH="/usr/local/cuda/lib64/libcudnn.so.7"
export TORCH_NVCC_FLAGS="-D__CUDA_NO_HALF_OPERATORS__"

# Install the latest Torch
git clone https://github.com/torch/distro.git ~/torch --recursive
cd ~/torch
bash install-deps
bash install.sh
bash update.sh

# Add Torch to PATH
source ~/.bashrc
source ~/.profile

# Add required lua packages
luarocks install torch
luarocks install nn
luarocks install image
luarocks install lua-cjson
luarocks install cutorch
luarocks install cunn
luarocks install cudnn

# This package is included with the repo for reasons of compatibility and is 
# compiled manually
cd ~/thesis/core/stnbdhw
luarocks make stnbdhw-scm-1.rockspec

# Download models
cd ~/thesis/styles
bash _download_models.sh
cd ~

# Update Torch bindings
git clone https://github.com/soumith/cudnn.torch -b R7
cd cudnn.torch
luarocks make cudnn-scm-1.rockspec

# Let Cmake find CUDA/CUDNN
export PATH=/usr/local/cuda${PATH:+:${PATH}}
export CUDNN_PATH="/usr/local/cuda/lib64/libcudnn.so.7"
export TORCH_NVCC_FLAGS="-D__CUDA_NO_HALF_OPERATORS__"

# Clean installation
sudo apt-get -y update
sudo apt-get -y autoremove