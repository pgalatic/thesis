# author: Paul Galatic
# Script assumes that .deb package files for cuda/cudnn are already present 
#   and in the home directory

cd ~/

# Update package lists
sudo apt-get -y update
sudo apt-get -y upgrade

# Install FFMPEG
sudo apt-get -y install ffmpeg

# Install CUDA v7.5
sudo dpkg -i cuda-repo-ubuntu1404_7.5-18_amd64.deb
sudo apt-get update
sudo apt-get install cuda-7-5
# Let Cmake find CUDA
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}

# Install CUDNN v5.0
tar -xzvf cudnn-7.5-linux-x64-v5.0-ga.tgz
sudo cp cuda/include/cudnn.h /usr/local/cuda/include
sudo cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
sudo chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*
export CUDNN_PATH="/usr/local/cuda/lib64/libcudnn.so.5"

# Install the latest Torch
export TORCH_NVCC_FLAGS="-D__CUDA_NO_HALF_OPERATORS__"
git clone https://github.com/torch/distro.git ~/torch --recursive
cd ~/torch; bash install-deps;
./install.sh
./update.sh

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
cd ~/thesis/core/stnbhw
luarocks make stnbdhw-scm-1.rockspec

# Download models
cd ~/thesis/styles
bash _download_models.sh
cd ~

# Clean installation
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y autoremove