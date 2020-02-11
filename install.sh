# author: Paul Galatic

cd ~/
sudo apt-get -y update

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

# Download models
cd ~/thesis/styles
bash _download_models.sh
cd ~

# Clean installation
sudo apt-get -y update
sudo apt-get -y autoremove