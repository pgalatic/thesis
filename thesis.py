# author: Paul Galatic
#
# Python wrapper for my thesis, "Divide and Conquer in Video Style Transfer,"
# which is based on the work Fast Artistic Videos by Manuel Ruder and Alexey 
# Dosovitskiy.

# STD LIB
import os
import pdb
import pathlib
import argparse
import threading

# EXTERNAL LIB
import numpy as np

# LOCAL LIB
import optflow
import stylize
from const import *

def parse_args():
    '''Parses arguments'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('video', type=str,
        help='The path to the video to stylize.')
    ap.add_argument('style', type=str,
        help='The path to the model used for stylization')
    ap.add_argument('nfs', type=str,
        help='The directory of the mounted NFS file server where images are to be shared.')
        
    # Optional arguments
    ap.add_argument('local', type=str, nargs='?', default='.',
        help='The local directory where files will temporarily be stored during processing, to cut down on communication costs over NFS. [.]')
    ap.add_argument('--processor', type=str, nargs='?', default='ffmpeg',
        help='The video processer to use, either ffmpeg (preferred) or avconv (experimental) [ffmpeg]')
    ap.add_argument('--gpu_num', type=str, nargs='?', default='-1',
        help='The zero-indexed ID of the GPU to use, or -1 to use CPU [-1]')
    ap.add_argument('--gpu_lib', type=str, nargs='?', default='cudnn',
        help='The framework to use to run GPU acceleration. This argument is ignored if gpu_num=-1 [cudnn]')
    ap.add_argument('--resolution', type=str, nargs='?', default=RESOLUTION_DEFAULT,
        help='The width to process the video at in the format w:h [Original resolution]')
    ap.add_argument('--downsamp_factor', type=str, nargs='?', default='2',
        help='The downsampling factor for optical flow calculations. Increase this slightly if said calculations are too slow or memory-intense for your machine. [2]')    
    
    return ap.parse_args()

def main():
    '''Driver program'''
    args = parse_args()
    
    # Make output folder(s), if necessary
    remote = pathlib.Path(args.nfs) / os.path.basename(os.path.splitext(args.video)[0])
    if not os.path.exists(str(remote)):
        os.makedirs(str(remote))
    local = pathlib.Path(args.local) / os.path.basename(os.path.splitext(args.video)[0])
    if not os.path.exists(str(local)):
        os.makedirs(str(local))
    
    # Split video into individual frames
    num_frames = video.split_frames(args.processor, args.video, args.resolution, remote)
    
    pdb.set_trace() # Did video.split_frames() work?
        
    # Spawn a thread for optical flow calculation.
    optflow_thread = threading.Thread(target=optflow.optflow,
        args=(args.resolution, args.downsamp_factor, num_frames, remote, local))
    optflow_thread.start()
    # FIXME: Right now, the Torch stylization procedure crashes when it tries to use an incomplete file.
    # As a result, we have to join the thread in order to continue.
    optflow_thread.join()
    
    pdb.set_trace() # Did optflow.optflow() work?
    
    # Compute neural style transfer.
    stylize.stylize(args.resolution, remote, local)
    
    pdb.set_trace() # Did stylize.stylize() work?
    
    video.combine_frames(args.processor)

if __name__ == '__main__':
    main()
