#!/bin/sh

set -e
# Get a carriage return into `cr`
cr=`echo $'\n.'`
cr=${cr%.}


# Find out whether ffmpeg or avconv is installed on the system
FFMPEG=ffmpeg
command -v $FFMPEG >/dev/null 2>&1 || {
  FFMPEG=avconv
  command -v $FFMPEG >/dev/null 2>&1 || {
    echo >&2 "This script requires either ffmpeg or avconv installed.  Aborting."; exit 1;
  }
}

if [ "$#" -le 1 ] || [ "$#" -ge 4 ]; then
   echo "Usage: ./stylizeVideo.sh <path_to_video> <path_to_pretrained_model> [<path_to_firstframe_model>]"
   exit 1
fi

# Parse arguments
filename=$(basename "$1")
extension="${filename##*.}"
filename="${filename%.*}"
#filename=${filename//[%]/x}
model_vid_path=$2
model_img_path=${3:-self}

# Create output folder
mkdir -p $filename


echo ""
read -p "In case of multiple GPUs, enter the zero-indexed ID of the GPU to use here, or enter -1 for CPU mode (slow!).\
 [0] $cr > " gpu
gpu=${gpu:-0}

if [ $gpu -ge 0 ]; then
  echo ""
  read -p "Which backend do you want to use? \
  For Nvidia GPUs it is recommended to use cudnn if installed. If not, use nn. \
  For non-Nvidia GPU, use opencl (not tested). Note: You have to have the given backend installed in order to use it. [cudnn] $cr > " backend
  backend="cudnn"

  if [ ${backend} = "cudnn" ]; then
    backend="cuda"
    use_cudnn=1
  elif [ ${backend} = "nn" ]; then
    backend="cuda"
    use_cudnn=0
  elif [ ${backend} = "opencl" ]; then
    use_cudnn=0 
  else
    echo "Unknown backend."
    exit 1
  fi
else
  backend="nn"
  use_cudnn=0
fi

echo ""
read -p "Please enter a resolution at which the video should be processed, \
in the format w:h, or leave blank to use the original resolution. \
If you run out of memory, reduce the resolution. $cr > " resolution

echo ""
read -p "Please enter a downsampling factor (on a log scale, integer) for the matching algorithm used by DeepFlow. \
If you run out of main memory or optical flow estimation is too slow, slightly increase this value, \
otherwise the default value will be fine. [2] $cr > " opt_res

echo ""
read -p "Enter the frame to continue at, if this process is to resume a previous computation. [1] $cr > " cont_num

# Save frames of the video as individual image files
if [ -z $resolution ]; then
  $FFMPEG -i $1 ${filename}/frame_%05d.ppm
  resolution=default
else
  $FFMPEG -i $1 -vf scale=$resolution ${filename}/frame_%05d.ppm
fi

if [ -z $cont_num ]; then
  cont_num=1
fi

# This launches optical flow computation (if it is not already computed)
# This section COULD be buggy if you exit computation just before the end of
# an original computation and try to start it later, but its primary purpose
# is to prevent the Nice Bash from flooding the screen with messages 
# unnecessarily
echo ""
if [ -e ${filename}/flow_$resolution/reliable_1_2.pgm ]; then
  echo "Optical flow computations already completed, moving on..."
else
  echo "Starting optical flow computation as a background task..."
  nice bash makeOptFlow.sh ./${filename}/frame_%05d.ppm ./${filename}/flow_$resolution 1 ${opt_res:-2} &
fi

echo "Starting video stylization..."
# Perform style transfer
th fast_artistic_video.lua \
-continue_with $cont_num \
-input_pattern ${filename}/frame_%05d.ppm \
-flow_pattern ${filename}/flow_${resolution}/backward_[%d]_{%d}.flo \
-occlusions_pattern ${filename}/flow_${resolution}/reliable_[%d]_{%d}.pgm \
-output_prefix ${filename}/out \
-backend $backend \
-use_cudnn $use_cudnn \
-gpu $gpu \
-model_vid $model_vid_path \
-model_img $model_img_path

# At this point some tuning is needed. FFMPEG by default will reassemble frames
# into a video with a LONGER DURATION than the original. I do not know why this
# is, but it means that any audio will be wildly out of sync. However, the 
# framerate can be tuned down--you just have to know the number of frames 
# produced by the program as well as the original duration of the video.

DURATION="$(ffprobe -i $filename.$extension -show_entries format=duration -v quiet -of csv="p=0")"
NUM_FRAMES="$(ls -lR $filename/*.ppm | wc -l)"

echo "$DURATION"
echo "$NUM_FRAMES"

# Create video from output images using libx264.
$FFMPEG -i ${filename}/out-%05d.png \
-c:v libx264 -preset veryslow \
-filter:v "setpts=${DURATION}/${NUM_FRAMES}*N/TB" \
-r ${NUM_FRAMES}/${DURATION} \
${filename}-stylized.$extension

# Add audio from original video to stylized video.
$FFMPEG -i ${filename}-stylized.$extension -i ${filename}.$extension \
-c copy -map 0:0 -map 1:1 \
${filename}-stylized-audio.$extension
