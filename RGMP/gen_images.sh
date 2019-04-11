# author: Paul Galatic

# Make the directories in which to store the images
mkdir images
mkdir images/shark

# Segment the videos into all their frames
ffmpeg -i shark.mp4 images/shark/%05d.png

# Ensure the file names are appropriate for DAVIS
# python adjust_names.py images/shark
