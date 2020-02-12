# author: Paul Galatic

sudo apt-get -y update

# Install the latest Torch
git clone https://github.com/torch/distro.git ~/torch --recursive
bash ~/torch/install-deps
bash ~/torch/install.sh
bash update.sh

# Add required lua packages
luarocks install torch
luarocks install nn
luarocks install image
luarocks install lua-cjson

# Download models
bash styles/_download_models.sh
mv *.t7 styles

# Add Torch to PATH
source ~/.bashrc
source ~/.profile

# Clean installation
sudo apt-get -y update
sudo apt-get -y autoremove