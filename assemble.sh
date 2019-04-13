if [ -z $1 ]; then
    echo "No folder specified; terminating."
elif [ ! -d $1 ]; then
    echo "Folder does not exist; terminating."
else
    # We need the duration and number of frames so that we can re-encode the 
    # video with the same length as the original.
    DURATION="$(ffprobe -i ${1}/${1}.mp4 -show_entries format=duration -v quiet -of csv="p=0")"
    NUM_FRAMES="$(ls -lR ${1}/output/*.png | wc -l)"
    
    # This script takes the original frames, mask frames, and style frames and 
    # assembles them such that only the frames that do not have a mask applied
    # are stylized.
    python assemble.py $1
    
    # This assembles the frames produced by the above Python script into a 
    # video.
    ffmpeg -framerate 30 -i ${1}/output/out_%05d.png \
        -filter:v "setpts=${DURATION}/${NUM_FRAMES}*N/TB" \
        -r ${NUM_FRAMES}/${DURATION} \
        ${1}/${1}-no-audio.mp4
   
    # Add audio from original video to stylized video. For some reason this 
    # video can't be played in chrome... but Windows Media Player seems to
    # work.
    ffmpeg -i ${1}/${1}-no-audio.mp4 \
        -i ${1}/${1}.mp4 \
        -c copy -map 0:0 -map 1:1 \
        -pix_fmt yuv420p \
        ${1}/${1}-final.mp4        
fi
