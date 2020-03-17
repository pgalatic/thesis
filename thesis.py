# author: Paul Galatic
#
# Python wrapper for my thesis, "Divide and Conquer in Video Style Transfer,"
# which is based on the work Fast Artistic Videos by Manuel Ruder and Alexey 
# Dosovitskiy.

# STD LIB
import os
import pdb
import glob
import time
import shutil
import logging
import pathlib
import argparse
import threading

# EXTERNAL LIB

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
        help='The path to the model used for stylization as it would appear on the common directory, e.g. \\mnt\\o\\foo\\bar.pth')
        
    # Optional arguments
    ap.add_argument('--test', action='store_true',
        help='Test the algorithm by stylizing only a few frames of the video, rather than all of the frames.')
    ap.add_argument('--local', type=str, nargs='?', default='out',
        help='The local directory where files will temporarily be stored during processing, to cut down on communication costs over NFS. By defualt, local files will be stored in a folder at the same level of the repository [out].')
    ap.add_argument('--local_video', type=str, nargs='?', default=None,
        help='The local path to the stylization target. If this argument is specified, the video will be copied to the remote directory. If left unspecified and the program finds no video of the given name present at the remote directory, the program will wait for another node to upload the video [None].')
    ap.add_argument('--local_style', type=str, nargs='?', default=None,
        help='Same as --local_video, but for the model used for feed-forward stylization [None].')
    ap.add_argument('--processor', type=str, nargs='?', default='ffmpeg',
        help='The video processer to use, either ffmpeg (preferred) or avconv (untested) [ffmpeg].')
    ap.add_argument('--no_cuts', action='store_true',
        help='If a video has no cuts, use this to parallelize only the optical flow calculations.')
    ap.add_argument('--read_cuts', type=str, nargs='?', default=None,
        help='The .csv file containing frames that denote cuts. Computing cuts manually is always more accurate than an automatic assessment, if time permits. Use video.py to split frames for manual inspection. [None]')
    ap.add_argument('--write_cuts', type=str, nargs='?', default=None,
        help='The .csv file in which to write automatically computed cuts for later reading [None].')
    ap.add_argument('--precompute', action='store_true',
        help='Set to True to precompute optical flow instead of computing as-needed. When this option is True, optical flow files will NOT be deleted. [False]')
    
    return ap.parse_args()

def main():
    '''Driver program.'''
    t_start = time.time()
    args = parse_args()
    common.start_logging()
    logging.info('\n-----START {} -----'.format(os.path.basename(args.video)))
    
    # Make output folder(s), if necessary
    remote = pathlib.Path(args.remote) / os.path.basename(os.path.splitext(args.video)[0])
    common.makedirs(remote)
    local = pathlib.Path(args.local) / os.path.basename(os.path.splitext(args.video)[0])
    common.makedirs(local)
    video_path = local / os.path.basename(args.video)
    style_path = local / os.path.basename(args.style)
    
    # This loop ensures all nodes have the prerequisite files and models.
    for src, cmn, dst in zip(
        [args.local_video, args.local_style],
        [args.video, args.style],
        [video_path, style_path]):
        if src:
            # We have the master copy, so we have to distribute it to the common drive.
            common.upload_files([src], cmn, absolute_path=True)
            if not os.path.exists(str(dst)):
                shutil.copyfile(src, str(dst))
        elif not os.path.exists(str(dst)):
            # We do not have the master copy, so we have to wait for it to be uploaded, then copy it locally.
            common.wait_for(cmn)
            shutil.copyfile(cmn, dst)
    
    num_frames = video.split_frames(args.processor, video_path, local)
    # Split video into individual frames
    frames = sorted([str(local / frame) for frame in glob.glob1(str(local), '*.ppm')])
    
    # Make sure we only test on a small number of files, if we are testing.
    if args.test:
        num_frames = NUM_FRAMES_FOR_TEST
        to_remove = frames[NUM_FRAMES_FOR_TEST:]
        frames = frames[:NUM_FRAMES_FOR_TEST]
        for frame in to_remove:
            os.remove(frame)
    
    # Record the time between the start of the program and preliminary setup.
    t_prelim = time.time()
    logging.info('{} seconds\tpreliminary setup'.format(round(t_prelim - t_start)))
    
    # Spawn a thread for optical flow calculation.
    optflow_thread = threading.Thread(target=optflow.optflow,
        args=(num_frames, remote, local))
    optflow_thread.start()
    
    # Either read the cuts from disk or compute them manually (if applicable).
    if args.no_cuts:
        partitions = [(0, None)]
    elif args.read_cuts:
        partitions = cut.read_cuts(args.read_cuts, frames)
    elif args.test:
        midpoint = NUM_FRAMES_FOR_TEST // 2
        partitions = [(0, midpoint), (midpoint, None)]
    else:
        partitions = common.wait_complete(DIVIDE_TAG, cut.divide, [frames, args.write_cuts], remote)
        
    # FIXME: Right now, the Torch stylization procedure crashes when it tries to use an incomplete file.
    # As a result, we have to join the thread in order to perform stylization.
    optflow_thread.join()
    logging.info('Waiting for other nodes to finish optical flow...')
    while len(glob.glob1(str(remote), '*.pgm')) + 1 < num_frames:
        time.sleep(1)
    
    # Record the time between the preliminary setup and optflow calculations.
    # Calculating the frames is rolled into this, but that is so quick proportional to the video size that we can essentially ignore it.
    t_optflow = time.time()
    logging.info('{} seconds\toptical flow calculations'.format(round(t_optflow - t_prelim)))
    
    # Compute neural style transfer.
    stylize.stylize(style_path, partitions, remote, local)
    # Wait until all output files are present.
    logging.info('Waiting for other nodes to finish stylization...')
    while len(glob.glob1(str(remote), '*.png') < num_frames:
        time.sleep(1)
    
    # Record the time between the optflow calculations and completing stylization.
    t_stylize = time.time()
    logging.info('{} seconds\tstylization'.format(round(t_stylize - t_prelim)))
    
    # Combining frames into a final video won't work if we're testing on only a portion of the frames.
    if not args.test:
        video.combine_frames(args.processor, video_path, remote, local)
    
    # Clean up any lingering files.
    if os.path.exists(DIVIDE_TAG):
        os.remove(DIVIDE_TAG)
    
    # Log all the times for good measure.
    t_end = time.time()
    logging.info('====TIMES====')
    logging.info('{} seconds\tpreliminary setup'.format(round(t_prelim - t_start)))
    logging.info('{} seconds\toptical flow calculations'.format(round(t_optflow - t_prelim)))
    logging.info('{} seconds\tstylization'.format(round(t_stylize - t_optflow)))
    logging.info('{} seconds\twrapping up'.format(round(t_end - t_stylize)))
    logging.info('{} seconds\tTOTAL'.format(round(t_end - t_start)))
    logging.info('=============')
    logging.info('\n------END-----\n')

if __name__ == '__main__':  
    main()
