# These are commands I stored so that I wouldn't have to type them out every time.
# They're examples of how to run the program.

# EXPERIMENT

# Setup node
git clone github.com/pgalatic/thesis.git
cd thesis
bash install.sh

# 0 nodes
# 0 cuts
cd core
time bash stylizeVideo.sh ../videos/ava_cadu.mp4 ../styles/checkpoint-WomanHat-video.t7
# 1 cuts
time bash stylizeVideo.sh ../videos/chicken.mp4 ../styles/checkpoint-picasso-video.t7
# 3 cuts
time bash stylizeVideo.sh ../videos/night.mp4 ../styles/checkpoint-schlief-video.t7
# 4 cuts
time bash stylizeVideo.sh ../videos/face.mp4 ../styles/checkpoint-candy-video.t7
cd -

# N nodes
# 0 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/ava_cadu.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.t7 --local_video=videos/ava_cadu.mp4 --local_style=styles/checkpoint-WomanHat-video.t7 --local=/proj/videorendering-PG0/pgalatic/ --no_cuts
# 1 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/chicken.mp4 /proj/videorendering-PG0/pgalatic/picasso.t7 --local_video=videos/chicken.mp4 --local_style=styles/checkpoint-picasso-video.t7 --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/chicken.csv
# 3 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/night.mp4 /proj/videorendering-PG0/pgalatic/schlief.t7 --local_video=videos/night.mp4 --local_style=styles/checkpoint-schlief-video.t7 --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/night.csv
# 4 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/face.mp4 /proj/videorendering-PG0/pgalatic/scream.t7 --local_video=videos/face.mp4 --local_style=styles/checkpoint-scream-video.t7 --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/face.csv

# 13 cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/face.mp4 /proj/videorendering-PG0/pgalatic/scream.t7 --local_video=videos/face.mp4 --local_style=styles/checkpoint-scream-video.t7 --local=/proj/videorendering-PG0/pgalatic/ --read_cuts=cuts/face.csv