# author: Paul Galatic

# Update package list
sudo apt-get -y update

# Install Python/Pip, dependencies, and submodule(s)
#sudo apt-get -y install ffmpeg
sudo apt-get -y install python3
sudo apt-get -y install python3-pip
pip3 install --upgrade pip3
pip3 install -r requirements.txt
git submodule update --init
cd core
bash install.sh
cd -
mv core/styles styles

# Clean installation
sudo apt-get -y update
sudo apt-get -y autoremove
