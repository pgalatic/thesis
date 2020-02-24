# author: Paul Galatic

sudo apt-get -y update

# Install ffmpeg
sudo apt-get -y install ffmpeg

# Install Python/Pip and dependencies
sudo apt-get -y install python3
sudo apt-get -y install python3-pip
pip3 install -r requirements.txt

# Install the latest Torch
git clone https://github.com/torch/distro.git ~/torch --recursive
cd ~/torch

bash install-deps
bash install.sh

# Add Torch to PATH
export PATH=$PATH:~/torch/install/bin/
source ~/.bashrc
source ~/.profile

# Add required lua packages
luarocks install torch
luarocks install nn
luarocks install image
luarocks install lua-cjson

# Update torch AFTER installing packages (otherwise, hidden bugs will cause bad output)
bash update.sh

cd -

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
