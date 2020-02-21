# author: Paul Galatic

sudo apt-get -y update

# Install ffmpeg
sudo apt-get -y install ffmpeg

# Install Python/Pip
sudo apt-get -y install python3
sudo apt-get -y install python-pip

# Install the latest Torch
git clone https://github.com/torch/distro.git ~/torch --recursive
bash ~/torch/install-deps
bash ~/torch/install.sh

# Add Torch to PATH
source ~/.bashrc
source ~/.profile

# Add required lua packages
luarocks install torch
luarocks install nn
luarocks install image
luarocks install lua-cjson

# Update torch AFTER installing packages (otherwise, hidden bugs will cause bad output)
bash ~/torch/update.sh

# Download models
bash styles/_download_models.sh
mv *.t7 styles

# Make ConsistencyChecker
cd core/consistencyChecker/
make
cd -

# Clean installation
sudo apt-get -y update
sudo apt-get -y autoremove