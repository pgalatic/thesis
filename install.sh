# Install FFMPEG
sudo apt-get -y install ffmpeg

# Install CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-ubuntu1604.pin
sudo mv cuda-ubuntu1604.pin /etc/apt/preferences.d/cuda-repository-pin-600sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
sudo add-apt-repository "deb http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/ /"
sudo apt-get update
sudo apt-get -y install cuda

# Install CUDNN (TODO)

# Install Torch with LUA 5.1
git clone https://github.com/torch/distro.git ~/torch --recursive
cd ~/torch; bash install-deps;
TORCH_LUA_VERSION=LUA51 ./install.sh
yes

cd ~/

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

mkdir stnbhwd; cd stnbhwd
luarocks make stnbdhw-scm-1.rockspec
cd ~/

# Clean installation
sudo apt-get update
sudo apt-get upgrade
sudo apt-get autoremove