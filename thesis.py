# author: Paul Galatic
#
# Python wrapper for my thesis, "Divide and Conquer in Video Style Transfer,"
# which is based on the work Fast Artistic Videos by Manuel Ruder and Alexey 
# Dosovitskiy.

# STD LIB
import os
import pdb
import sys
import glob
import time
import shutil
import logging
import pathlib
import argparse
import threading

# EXTERNAL LIB
import numpy as np

# LOCAL LIB
import common
import video
import optflow
import cut
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
    ap.add_argument('--test', action='store_true',
        help='Test the algorithm by stylizing only a few frames of the video, rather than all of the frames.')
    ap.add_argument('--local', type=str, nargs='?', default='.',
        help='The local directory where files will temporarily be stored during processing, to cut down on communication costs over NFS. By defualt, local files will be stored in a folder at the same level of the repository [.].')
    ap.add_argument('--local_video', type=str, nargs='?', default=None,
        help='The local path to the stylization target. If this argument is specified, the video will be copied to the remote directory. If left unspecified and the program finds no video of the given name present at the remote directory, the program will wait for another node to upload the video [None].')
    ap.add_argument('--local_style', type=str, nargs='?', default=None,
        help='Same as --local_video, but for the model used for feed-forward stylization [None].')
    ap.add_argument('--processor', type=str, nargs='?', default='ffmpeg',
        help='The video processer to use, either ffmpeg (preferred) or avconv (untested) [ffmpeg].')
    ap.add_argument('--downsamp_factor', type=str, nargs='?', default='2',
        help='The downsampling factor for optical flow calculations. Increase this slightly if said calculations are too slow or memory-intense for your machine [2].')    
    ap.add_argument('--no_cuts', action='store_true',
        help='If a video has no cuts, use this to parallelize only the optical flow calculations.')
    ap.add_argument('--read_cuts', type=str, nargs='?', default=None,
        help='The .csv file containing frames that denote cuts. Computing cuts manually is always more accurate than an automatic assessment, if time permits. Use video.py to split frames for manual inspection. [None]')
    ap.add_argument('--write_cuts', type=str, nargs='?', default=None,
        help='The .csv file in which to write automatically computed cuts for later reading [None].')
    
    return ap.parse_args()

def main():
    '''Driver program.'''
    t_start = time.time()
    args = parse_args()
    logging.basicConfig(filename=LOGFILE, filemode='a', format=LOGFORMAT, level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info('\n-----START-----')
    
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
        if not os.path.exists(str(reel)):
            shutil.copyfile(args.local_video, str(reel))
    elif not os.path.exists(str(reel)):
        common.wait_for(args.video)
        shutil.copyfile(args.video, str(reel))
    
    if args.local_style:
        # Only upload if strictly necessary.
        if not os.path.exists(args.style):
            common.upload_files([args.local_style], args.style, absolute_path=True)
        if not os.path.exists(str(model)):
            shutil.copyfile(args.local_style, str(model))
    elif not os.path.exists(str(model)):
        common.wait_for(args.style)
        shutil.copyfile(args.style, str(model))
    
    num_frames = video.split_frames(args.processor, reel, local)
    # Split video into individual frames
    frames = sorted([str(local / frame) for frame in glob.glob1(str(local), '*.ppm')])
    
    if args.test:
        num_frames = NUM_FRAMES_FOR_TEST
        frames = frames[:NUM_FRAMES_FOR_TEST]
    
    # Record the time between the start of the program and preliminary setup.
    t_prelim = time.time()
    logging.info('{} seconds\tpreliminary setup'.format(round(t_prelim - t_start, 3)))
    
    # Spawn a thread for optical flow calculation.
    optflow_thread = threading.Thread(target=optflow.optflow,
        args=(args.downsamp_factor, num_frames, remote, local))
    optflow_thread.start()
    
    # Either read the cuts from disk or compute them manually (if applicable).
    if args.no_cuts:
        partitions = [frames]
    elif args.read_cuts:
        partitions = cut.read_cuts(args.read_cuts, frames)
    elif args.test:
        midpoint = NUM_FRAMES_FOR_TEST // 2
        partitions = [frames[:midpoint], frames[midpoint:]]
    else:
        partitions = common.wait_complete(DIVIDE_TAG, cut.divide, [frames, args.write_cuts], remote)
    
    # FIXME: Right now, the Torch stylization procedure crashes when it tries to use an incomplete file.
    # As a result, we have to join the thread in order to perform stylization.
    optflow_thread.join()
    
    # Record the time between the preliminary setup and optflow calculations.
    # Calculating the frames is rolled into this, but that is so quick proportional to the video size that we can essentially ignore it.
    t_optflow = time.time()
    logging.info('{} seconds\toptical flow calculations'.format(round(t_optflow - t_prelim, 3)))
    
    # Compute neural style transfer.
    stylize.stylize(model, partitions, remote, local)
    
    # Record the time between the optflow calculations and completing stylization.
    t_stylize = time.time()
    logging.info('{} seconds\tstylization'.format(round(t_stylize - t_prelim, 3)))
    
    # Combining frames into a final video won't work if we're testing on only a portion of the frames.
    if not args.test:
        video.combine_frames(args.processor, reel, remote, local)
    
    # Clean up any lingering files.
    if os.path.exists(DIVIDE_TAG):
        os.remove(DIVIDE_TAG)
    
    # Log all the times for good measure.
    t_end = time.time()
    logging.info('====TIMES====')
    logging.info('{} seconds\tpreliminary setup'.format(round(t_prelim - t_start, 3)))
    logging.info('{} seconds\toptical flow calculations'.format(round(t_optflow - t_prelim, 3)))
    logging.info('{} seconds\tstylization'.format(round(t_stylize - t_prelim, 3)))
    logging.info('{} seconds\twrapping up'.format(round(t_end - t_stylize, 3)))
    logging.info('{} seconds\tTOTAL'.format(round(t_end - t_start, 3)))
    logging.info('=============')
    logging.info('\n------END-----\n')

if __name__ == '__main__':  
    main()
