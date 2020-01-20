# author: Paul Galatic
# Script assumes that .deb package files for cuda/cudnn are already present

# Install FFMPEG
sudo apt-get -y install ffmpeg

# Install CUDA
sudo dpkg -i cuda-repo-ubuntu1604_9.2.148-1_amd64.deb
sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
sudo apt-get -y update
sudo apt-get -y install cuda-libraries-9-2
sudo apt-get -y install cuda-9-2

# Install CUDNN (TODO)
sudo dpkg -i libcudnn*

# Install Torch with LUA 5.1
git clone https://github.com/torch/distro.git ~/torch --recursive
cd ~/torch; bash install-deps;
sudo export TORCH_NVCC_FLAGS="-D__CUDA_NO_HALF_OPERATORS__"
TORCH_LUA_VERSION=LUA51 ./install.sh

cd ~/

# Add Torch to PATH
source ~/.bashrc
source ~/.profile

# Add required lua packages
sudo luarocks install torch
sudo luarocks install nn
sudo luarocks install image
sudo luarocks install lua-cjson
sudo luarocks install cutorch
sudo luarocks install cunn

mkdir stnbhwd; cd stnbhwd
sudo luarocks make stnbdhw-scm-1.rockspec
cd ~/

# Clean installation
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y autoremove