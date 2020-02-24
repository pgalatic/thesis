# These are commands I stored so that I wouldn't have to type them out every time.
# They're examples of how to run the program.

# Test on floating240 master no cuts
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/floating240.mp4 /proj/videorendering-PG0/pgalatic/schlief.t7 --local_video=videos/floating240.mp4 --local_style=styles/checkpoint-schlief-video.t7 --test --no_cuts

# Test on floating240 worker
python thesis.py /mnt/o/thesis/ /mnt/o/thesis/floating240.mp4 /mnt/o/thesis/schlief.t7 --test

# Run meowth240 master
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/meowth240.mp4 /proj/videorendering-PG0/pgalatic/mosaic.t7 --local_video=videos/meowth240.mp4 --local_style=styles/checkpoint-mosaic-video.t7 --read_cuts=videos/meowth.csv

# Run meowth240 worker
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/meowth240.mp4 /proj/videorendering-PG0/pgalatic/mosaic.t7 --read_cuts=videos/meowth.csv

# Test on meowth240 worker
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/meowth240.mp4 /proj/videorendering-PG0/pgalatic/mosaic.t7 --test

# Run eggdog720 master
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/eggdog720.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.t7 --local_video=videos/eggdog720.mp4 --local_style=styles/checkpoint-WomanHat-video.t7 --read_cuts=videos/eggdog.csv

# Run eggdog720 worker
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/eggdog720.mp4 /proj/videorendering-PG0/pgalatic/WomanHat.t7 --read_cuts=videos/eggdog.csv 

# Run silksong720 master
python3 thesis.py /proj/videorendering-PG0/pgalatic/ /proj/videorendering-PG0/pgalatic/silksong720.mp4 /proj/videorendering-PG0/pgalatic/mosaic.t7 --local_video=videos/silksong720.mp4 --local_style=styles/checkpoint-mosaic-video.t7 --read_cuts=videos/silksong.csv

