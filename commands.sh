# These are commands I stored so that I wouldn't have to type them out every time.
# They're examples of how to run the program.

# EXPERIMENT

# Setup node
git clone https://github.com/pgalatic/thesis.git
cd thesis
bash install.sh

# Test
sudo mount -t drvfs 'O:' /mnt/o
python3 thesis.py /mnt/o/thesis/ /mnt/o/thesis/floating360.mp4 /mnt/o/thesis/candy.pth --local_video=videos/floating360.mp4 --local_style=styles/candy.pth --no_cuts
python3 thesis.py /mnt/o/thesis/ /mnt/o/thesis/zelda.mp4 /mnt/o/thesis/candy.pth --local_video=videos/zelda.mp4 --local_style=styles/candy.pth --test --no_cuts

# 0 nodes
# 0 cuts
cd core
time bash stylizeVideo.sh ../videos/ava_cadu.mp4 ../styles/WomanHat.pth
# 1 cuts
time bash stylizeVideo.sh ../videos/chicken.mp4 ../styles/picasso.pth
# 3 cuts
time bash stylizeVideo.sh ../videos/night.mp4 ../styles/schlief.pth
# 4 cuts
time bash stylizeVideo.sh ../videos/face.mp4 ../styles/scream.pth
cd -

# N nodes
# 0 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ava_cadu.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/ava_cadu.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# 1 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/chicken.mp4 /proj/videorendering-PG0/pgalatic/picasso.pth --local_video=videos/chicken.mp4 --local_style=styles/picasso.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/chicken.csv
# 3 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/night.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/night.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/night.csv
# 4 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/face.mp4 /proj/videorendering-PG0/pgalatic/scream.pth --local_video=videos/face.mp4 --local_style=styles/scream.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/face.csv

# 13 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/eggdog.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/eggdog.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/eggdog.csv
# 18 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/zelda.mp4 /proj/videorendering-PG0/pgalatic/candy.pth --local_video=videos/zelda.mp4 --local_style=styles/candy.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/zelda.csv