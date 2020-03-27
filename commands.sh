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

# jordan, WomanHat
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/jordan.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/jordan.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# face, scream
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/face.mp4 /proj/videorendering-PG0/pgalatic/scream.pth --local_video=videos/face.mp4 --local_style=styles/scream.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/face.csv
# soul, picasso
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/soul.mp4 /proj/videorendering-PG0/pgalatic/picasso.pth --local_video=videos/soul.mp4 --local_style=styles/picasso.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# night, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/night.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/night.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/night.csv
# sonicfan, scream
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/sonicfan.mp4 /proj/videorendering-PG0/pgalatic/scream.pth --local_video=videos/sonicfan.mp4 --local_style=styles/scream.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# ava_cadu, WomanHat
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ava_cadu.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/ava_cadu.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# chicken, picasso
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/chicken.mp4 /proj/videorendering-PG0/pgalatic/picasso.pth --local_video=videos/chicken.mp4 --local_style=styles/picasso.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/chicken.csv
# sneeze, WomanHat
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/sneeze.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/sneeze.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# wow, candy
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/wow.mp4 /proj/videorendering-PG0/pgalatic/candy.pth --local_video=videos/wow.mp4 --local_style=styles/candy.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# dance, picasso
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/dance.mp4 /proj/videorendering-PG0/pgalatic/picasso.pth --local_video=videos/dance.mp4 --local_style=styles/picasso.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/dance.csv
# fad, candy
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/fad.mp4 /proj/videorendering-PG0/pgalatic/candy.pth --local_video=videos/fad.mp4 --local_style=styles/candy.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/fad.csv
# meowth, candy
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/meowth.mp4 /proj/videorendering-PG0/pgalatic/candy.pth --local_video=videos/meowth.mp4 --local_style=styles/candy.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/meowth.csv
# kiwi, mosaic
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/kiwi.mp4 /proj/videorendering-PG0/pgalatic/mosaic.pth --local_video=videos/kiwi.mp4 --local_style=styles/mosaic.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/kiwi.csv
# walk, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/walk.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/walk.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/walk.csv
# eggdog, WomanHat
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/eggdog.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/eggdog.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/eggdog.csv
# infinity, scream
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/infinity.mp4 /proj/videorendering-PG0/pgalatic/scream.pth --local_video=videos/infinity.mp4 --local_styles=styles/scream.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/infinity.csv
# ncis, picasso
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ncis.mp4 /proj/videorendering-PG0/pgalatic/picasso.pth --local_video=videos/ncis.mp4 --local_style=styles/picasso.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/ncis.csv
# zelda, candy
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/zelda.mp4 /proj/videorendering-PG0/pgalatic/candy.pth --local_video=videos/zelda.mp4 --local_style=styles/candy.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/zelda.csv

# roll, mosaic
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/roll.mp4 /proj/videorendering-PG0/pgalatic/mosaic.pth --local_video=videos/roll.mp4 --local_style=styles/mosaic.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/roll.csv
# endgame, mosaic
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/endgame.mp4 /proj/videorendering-PG0/pgalatic/mosaic.pth --local_video=videos/endgame.mp4 --local_style=styles/mosaic.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/endgame.csv
# gate, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/gate.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/gate.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/gate.csv
# ai, scream
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ai.mp4 /proj/videorendering-PG0/pgalatic/scream.pth --local_video=videos/ai.mp4 --local_style=styles/scream.pth --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# ori, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ori.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/ori.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/ori.csv
# smash, WomanHat
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/smash.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.pth --local_video=videos/smash.mp4 --local_style=styles/WomanHat.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/smash.csv
# obra, picasso
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/obra.mp4 /proj/videorendering-PG0/pgalatic/picasso.pth --local_video=videos/obra.mp4 --local_style=styles/picasso.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/obra.csv
# sekiro, scream
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/sekiro.mp4 /proj/videorendering-PG0/pgalatic/scream.pth --local_video=videos/sekiro.mp4 --local_style=styles/scream.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/sekiro.csv
# pyre, mosaic
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/pyre.mp4 /proj/videorendering-PG0/pgalatic/mosaic.pth --local_video=videos/pyre.mp4 --local_style=styles/mosaic.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/pyre.csv
# bastion, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/bastion.mp4 /proj/videorendering-PG0/pgalatic/schlief.pth --local_video=videos/bastion.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/bastion.csv
# trek, candy
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/trek.mp4 /proj/videorendering-PG0/pgalatic/candy.pth --local_video=videos/trek.mp4 --local_style=styles/candy.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/trek.csv
# transistor, mosaic
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/transistor.mp4 /proj/videorendering-PG0/pgalatic/mosaic.pth --local_video=videos/transistor.mp4 --local_style=styles/mosaic.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/transistor.csv
# hatkid, schlief
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/hatkid.mp4 --local_video=videos/hatkid.mp4 --local_style=styles/schlief.pth --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/hatkid.csv