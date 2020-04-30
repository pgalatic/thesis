# author: Paul Galatic

# Update package list
sudo apt-get -y update

# Install Python/Pip, dependencies, and submodule(s)
#sudo apt-get -y install ffmpeg
sudo apt-get -y install python3
sudo apt-get -y install python3-pip
pip3 install --upgrade pip
pip3 install -r requirements.txt
git submodule update --init
cd core
bash install.sh
git checkout repro
cd -
mv core/styles/* styles
rm -r core/styles

# Clean installation
sudo apt-get -y update
sudo apt-get -y autoremove
