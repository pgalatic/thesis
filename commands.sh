# These are commands I stored so that I wouldn't have to type them out every time.
# They're examples of how to run the program.

# EXPERIMENT

# Setup node
git clone https://github.com/pgalatic/thesis.git
cd thesis
bash install.sh

# Test local
python3 thesis.py out videos/floating360.mp4 styles/candy.pth --test

# Test remote
sudo mount -t drvfs 'O:' /mnt/o
python3 thesis.py /mnt/o/thesis/ /mnt/o/thesis/floating360.mp4 /mnt/o/thesis/candy.pth --local_video=videos/floating360.mp4 --local_style=styles/candy.pth
python3 thesis.py /mnt/o/thesis/ /mnt/o/thesis/zelda.mp4 /mnt/o/thesis/candy.pth --local_video=videos/zelda.mp4 --local_style=styles/candy.pth --test --no_cuts

# 0 cuts
time bash stylizeVideo_deepflow.sh videos/ava_cadu.mp4 models/checkpoint-mosaic-video.t7
# 1 cuts
time bash stylizeVideo_deepflow.sh videos/chicken.mp4 models/checkpoint-mosaic-video.t7
# 3 cuts
time bash stylizeVideo_deepflow.sh videos/night.mp4 models/checkpoint-mosaic-video.t7
# 4 cuts
time bash stylizeVideo_deepflow.sh videos/face.mp4 models/checkpoint-scream-video.t7

# ava_cadu, WomanHat
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ava_cadu.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/ava_cadu.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# chicken, picasso
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/chicken.mp4 /proj/videorendering-PG0/pgalatic/picasso.pth --local_video=videos/chicken.mp4 --local_style=styles/picasso.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/chicken.csv
# night, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/night.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/night.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/night.csv
# face, scream
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/face.mp4 /proj/videorendering-PG0/pgalatic/scream.pth --local_video=videos/face.mp4 --local_style=styles/scream.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/face.csv
# eggdog, WomanHat
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/eggdog.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/eggdog.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/eggdog.csv
# zelda, candy
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/zelda.mp4 /proj/videorendering-PG0/pgalatic/candy.pth --local_video=videos/zelda.mp4 --local_style=styles/candy.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/zelda.csv
# sekiro, scream
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/sekiro.mp4 /proj/videorendering-PG0/pgalatic/scream.pth --local_video=videos/sekiro.mp4 --local_style=styles/scream.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/sekiro.csv
# ori, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ori.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/ori.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/ori.csv
# obra, picasso
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/obra.mp4 /proj/videorendering-PG0/pgalatic/picasso.pth --local_video=videos/obra.mp4 --local_style=styles/picasso.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/obra.csv
# meowth, candy
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/meowth.mp4 /proj/videorendering-PG0/pgalatic/candy.pth --local_video=videos/meowth.mp4 --local_style=styles/candy.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/meowth.csv
# smash, WomanHat
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/smash.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/smash.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/smash.csv
# pyre, mosaic
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/pyre.mp4 /proj/videorendering-PG0/pgalatic/mosaic.pth --local_video=videos/pyre.mp4 --local_style=styles/mosaic.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/pyre.csv
# transistor, mosaic
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/transistor.mp4 /proj/videorendering-PG0/pgalatic/mosaic.pth --local_video=videos/transistor.mp4 --local_style=styles/mosaic.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/transistor.csv
# bastion, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/bastion.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/bastion.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/bastion.csv

# ai, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ai.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/ai.mp4 --local_style=schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
