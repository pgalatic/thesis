# author: Paul Galatic

# Update package list
sudo apt-get -y update

# Install Python/Pip, dependencies, and submodule(s)
#sudo apt-get -y install ffmpeg
sudo apt-get -y install python3
sudo apt-get -y install python3-pip
pip install --upgrade pip
pip install -r requirements.txt
git submodule update --init
cd core
git checkout master
bash install.sh
cd -
cp core/styles/* styles

# Clean installation
sudo apt-get -y update
sudo apt-get -y autoremove
