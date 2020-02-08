# author: Paul Galatic
#
# Handles initial task of splitting video and uploading frames to the shared system.

# STD LIB
import os
import pdb
import sys
import glob
import time
import shutil
import threading
import subprocess

# EXTERNAL LIB

# LOCAL LIB
from const import *

def check_deps(processor):
    check = shutil.which(processor)
    if not check:
        print('Video processor {p} not installed. Aborting'.format(p=processor))
        sys.exit(1)
    
    if not (os.path.exists('core/deepmatching-static') and os.path.exists('core/deepflow2-static')):
        print('Deepmatching/Deepflow static binaries are missing. Aborting')
        sys.exit(1)
    else:
        # Ensure that Deepmatching/Deepflow can be executed.
        subprocess.Popen(['chmod', '+x', 'core/deepmatching-static'])
        subprocess.Popen(['chmod', '+x', 'core/deepflow2-static'])

def split_frames(processor, video, resolution, remote, local):
    # Preliminary operations to make sure that the environment is set up properly.
    check_deps(args.processor)

    # Split video into a collection of frames. It's necessary to have a local copy of the frames.
    # Don't split the video if we've already done so.
    if not os.path.isfile(str(local / 'frame_00001.ppm')):
        if resolution == RESOLUTION_DEFAULT:
            proc = subprocess.Popen([processor, '-i', video, str(local / FRAME_NAME)])
        else:
            proc = subprocess.Popen([processor, '-i', video, '-vf', 'scale=' + resolution, 
                str(local / FRAME_NAME)])
    
        # Wait until splitting the frames is finished, so we know how many there are.
        proc.wait()
    
    # Spawn a thread to upload the files to the common area (is this necessary?).
    # threading.Thread(target=common.upload_frames...
    
    # Return the number of frames.
    return len(glob.glob1(str(local), '*.ppm'))

def combine_frames(processor):
    # Combine the stylized frames back into a video. TODO
    pass