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

# FAV
# jordan, WomanHat
time bash stylizeVideo_deepflow.sh videos/jordan.mp4 models/checkpoint-WomanHat-video.t7
# face, scream
time bash stylizeVideo_deepflow.sh videos/face.mp4 models/checkpoint-scream-video.t7
# soul, picasso
time bash stylizeVideo_deepflow.sh videos/soul.mp4 models/checkpoint-picasso-video.t7
# night, mosaic
time bash stylizeVideo_deepflow.sh videos/night.mp4 models/checkpoint-mosaic-video.t7
# sonicfan, scream
time bash stylizeVideo_deepflow.sh videos/sonicfan.mp4 models/checkpoint-scream-video.t7
# ava_cadu, WomanHat
time bash stylizeVideo_deepflow.sh videos/ava_cadu.mp4 models/checkpoint-WomanHat-video.t7
# chicken, mosaic
time bash stylizeVideo_deepflow.sh videos/chicken.mp4 models/checkpoint-mosaic-video.t7
# sneeze, WomanHat
time bash stylizeVideo_deepflow.sh videos/sneeze.mp4 models/checkpoint-WomanHat-video.t7
# wow, candy
time bash stylizeVideo_deepflow.sh videos/wow.mp4 models/checkpoint-candy-video.t7
# dance, picasso
time bash stylizeVideo_deepflow.sh videos/dance.mp4 models/checkpoint-picasso-video.t7

# night, schlief
python3 distribute.py /proj/videorendering-PG0/pgalatic/ videos/night.mp4 styles/schlief.pth --read_cuts=cuts/night.csv
# silksong, mosaic
python3 distribute.py /proj/videorendering-PG0/pgalatic/ videos/silksong.mp4 styles/mosaic.pth --read_cuts=cuts/silksong.csv
