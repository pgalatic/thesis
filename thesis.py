# author: Paul Galatic
#
# Python wrapper for my thesis, "Divide and Conquer in Video Style Transfer,"
# which is based on the work Fast Artistic Videos by Manuel Ruder and Alexey 
# Dosovitskiy.

# STD LIB
import os
import pdb
import sys
import shutil
import pathlib
import argparse
import threading

# EXTERNAL LIB
import numpy as np

# LOCAL LIB
import common
import video
import optflow
import stylize
from const import *

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('remote', type=str,
        help='The directory common to all nodes, e.g. \\mnt\\o\\foo\\.')
    ap.add_argument('video', type=str,
        help='The path to the stylization target as it would appear on the common directory, e.g. \\mnt\\o\\foo\\bar.mp4\\')
    ap.add_argument('style', type=str,
        help='The path to the model used for stylization as it would appear on the common directory, e.g. \\mnt\\o\\foo\\bar.t7\\')
        
    # Optional arguments
    ap.add_argument('--local', type=str, nargs='?', default='.',
        help='The local directory where files will temporarily be stored during processing, to cut down on communication costs over NFS. By defualt, local files will be stored in a folder at the same level of the repository [.].')
    ap.add_argument('--local_video', type=str, nargs='?', default=None,
        help='The local path to the stylization target. If this argument is specified, the video will be copied to the remote directory. If left unspecified and the program finds no video of the given name present at the remote directory, the program will wait for another node to upload the video [None].')
    ap.add_argument('--local_style', type=str, nargs='?', default=None,
        help='Same as --local_video, but for the model used for feed-forward stylization [None].')
    ap.add_argument('--processor', type=str, nargs='?', default='ffmpeg',
        help='The video processer to use, either ffmpeg (preferred) or avconv (untested) [ffmpeg].')
    ap.add_argument('--resolution', type=str, nargs='?', default=RESOLUTION_DEFAULT,
        help='The width to process the video at in the format w:h [Original resolution].')
    ap.add_argument('--downsamp_factor', type=str, nargs='?', default='2',
        help='The downsampling factor for optical flow calculations. Increase this slightly if said calculations are too slow or memory-intense for your machine [2].')    
    
    return ap.parse_args()

def main():
    '''Driver program.'''
    args = parse_args()
    
    # Make output folder(s), if necessary
    remote = pathlib.Path(args.remote) / os.path.basename(os.path.splitext(args.video)[0])
    common.makedirs(remote)
    local = pathlib.Path(args.local) / os.path.basename(os.path.splitext(args.video)[0])
    common.makedirs(local)
    reel = local / os.path.basename(args.video)
    model = local / os.path.basename(args.style)
    
    # Upload the video to the remote system, if it was specified, otherwise wait for the video to be uploaded.
    if args.local_video:
        # Only upload if strictly necessary.
        if not os.path.exists(args.video):
            common.upload_files([args.local_video], args.video, absolute_path=True)
        shutil.copyfile(args.local_video, str(reel))
    else:
        common.wait_for(args.video)
        shutil.copyfile(args.video, str(reel))
    
    if args.local_style:
        # Only upload if strictly necessary.
        if not os.path.exists(args.style):
            common.upload_files([args.local_style], args.style, absolute_path=True)
        shutil.copyfile(args.local_style, str(model))
    else:
        common.wait_for(args.style)
        shutil.copyfile(args.style, str(model))
    
    # Split video into individual frames
    num_frames = video.split_frames(args.processor, args.resolution, reel, local)
            
    # Spawn a thread for optical flow calculation.
    optflow_thread = threading.Thread(target=optflow.optflow,
        args=(args.resolution, args.downsamp_factor, num_frames, remote, local))
    optflow_thread.start()
    # FIXME: Right now, the Torch stylization procedure crashes when it tries to use an incomplete file.
    # As a result, we have to join the thread in order to continue.
    optflow_thread.join()
        
    # Compute neural style transfer.
    stylize.stylize(args.resolution, model, remote, local)
    
    sys.exit(1)
    
    video.combine_frames(args.processor)

if __name__ == '__main__':
    main()
