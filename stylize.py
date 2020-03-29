# author: Paul Galatic
#
# Python wrapper for my thesis, "Divide and Conquer in Video Style Transfer,"
# which is based on the work Fast Artistic Videos by Manuel Ruder and Alexey 
# Dosovitskiy. It organizes and executes divide-and-conquer style transfer.

# STD LIB
import re
import os
import pdb
import glob
import time
import logging
import pathlib
import argparse
import platform
import threading

# EXTERNAL LIB

# LOCAL LIB
import cut
import video
import common
from const import *
from core import model, optflow

def most_recent_partition(remote):
    # Check to see if the optical flow folder exists.
    if not os.path.isdir(str(remote)):
        # If it doesn't exist, then there are no optflow files, and we start from scratch.
        return 1

    # The most recent partition is the most recent placeholder plus 1.
    placeholders = glob.glob1(str(remote), 'partition_*.plc')
    if len(placeholders) == 0: return 1
    
    return max(map(int, [re.findall(r'\d+', plc)[0] for plc in placeholders])) + 1

def claim_job(remote, partitions):
    for idx, partition in enumerate(partitions):
        if len(partition) == 0:
            logging.error('Skipping a partition with length 0! Partition: {}'.format(idx))
            continue # Edge case; this shouldn't happen
    
        placeholder = str(remote / 'partition_{}.plc'.format(idx))
        # Check if someone has already claimed this partition.
        if not os.path.exists(placeholder):
            try:
                with open(placeholder, 'x') as handle:
                    handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
                
                logging.info(str(remote / 'partition_{}.plc claimed\t[{}:{}]'.format(
                    idx, partition[0], partition[1])))
                return partition
                
            except FileExistsError:
                # We couldn't claim this partition, so try the next one.
                logging.debug('Partition {} alraedy claimed; moving on...'.format(idx))
                continue
    
    # There are no more jobs.
    return None

def stylize(style, partitions, remote):
    # Sort in ascending order of length. This will mitigate the slowest-link effect of any weak nodes.
    # Sort in descending order of length. This will mitigate the slowdown caused by very large partitions.
    # TODO Allow user to select sorting strategy
    # partitions = sorted(partitions, key=lambda x: -(x[1] - x[0]) if x[1] else -99999)
    
    running = []

    framefiles = sorted([str(remote / name) for name in glob.glob1(str(remote), '*.ppm')])
    stylizer = model.StylizationModel(weights_fname=str(style))
    partition = claim_job(remote, partitions)
    
    while partition is not None:
        frames_p = framefiles[partition[0]:partition[-1]]
        # Spawn a thread to complete that job, then get the next one.
        to_run = threading.Thread(
            target=stylizer.stylize, 
            args=(partition[0], frames_p, remote))
        running.append(to_run)
        to_run.start()
        
        # If there isn't room in the jobs list, wait for a thread to finish.
        while len(running) >= MAX_STYLIZATION_JOBS:
            running = [thread for thread in running if thread.isAlive()]
            time.sleep(1)
        
        partition = claim_job(remote, partitions)
    
    # Finish any remaining optical flow, to help speed along other nodes, if necessary.
    if most_recent_partition(remote) < len(partitions):
        for partition in partitions:
            frames_p = framefiles[partition[0]:partition[-1]]
            optflow.optflow(0, frames_p, remote)
    
    # Join all remaining threads.
    logging.info('Wrapping up threads for stylization...')
    for thread in running:
        thread.join()

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('remote', type=str,
        help='The directory common to all nodes, e.g. \\mnt\\o\\foo\\.')
    ap.add_argument('video', type=str,
        help='The path to the stylization target, e.g. \\mnt\\o\\foo\\bar.mp4\\')
    ap.add_argument('style', type=str,
        help='The path to the model used for stylization, e.g. \\mnt\\o\\foo\\bar.pth')
    
    # Optional arguments
    ap.add_argument('--test', action='store_true',
        help='Test the algorithm by stylizing only a few frames of the video, rather than all of the frames.')
    ap.add_argument('--no_cuts', action='store_true',
        help='If a video has no cuts, use this to parallelize only the optical flow calculations.')
    ap.add_argument('--read_cuts', type=str, nargs='?', default=None,
        help='The .csv file containing frames that denote cuts. Computing cuts manually is always more accurate than an automatic assessment, if time permits. Use video.py to split frames for manual inspection. [None]')
    
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
    
    video.split_frames(args.video, remote)
    # Split video into individual frames
    frames = sorted([str(remote / frame) for frame in glob.glob1(str(remote), '*.ppm')])
    
    # Make sure we only test on a small number of files, if we are testing.
    if args.test:
        to_remove = frames[NUM_FRAMES_FOR_TEST:]
        frames = frames[:NUM_FRAMES_FOR_TEST]
        for frame in to_remove:
            os.remove(frame)
    
    # Either read the cuts from disk or compute them manually (if applicable).
    if args.no_cuts:
        partitions = [(0, len(frames))]
    elif args.read_cuts:
        partitions = cut.read_cuts(args.read_cuts, len(frames))
    elif args.test:
        # use different-size partitions to test sorting
        q1 = (NUM_FRAMES_FOR_TEST // 4) 
        q2 = (NUM_FRAMES_FOR_TEST // 3)
        q3 = (NUM_FRAMES_FOR_TEST // 2)
        partitions = [(0, q1), (q1, q2), (q2, q3), (q3, None)]
    else:
        partitions = common.wait_complete(
            DIVIDE_TAG, cut.divide, [args.video, len(frames)], remote)
    
    # Record the time between the start of the program and preliminary setup.
    t_prelim = time.time()
    logging.info('{} seconds\tpreliminary setup'.format(round(t_prelim - t_start)))
    
    # Compute neural style transfer.
    stylize(args.style, partitions, remote)
    # Wait until all output files are present.
    logging.info('Waiting for other nodes to finish stylization...')
    while len(glob.glob1(str(remote), '*.png')) < len(frames):
        time.sleep(1)
    
    # Record the time between the optflow calculations and completing stylization.
    t_stylize = time.time()
    logging.info('{} seconds\tstylization'.format(round(t_stylize - t_prelim)))
    
    # Combining frames into a final video won't work if we're testing on only a portion of the frames.
    if not args.test:
        video.combine_frames(args.video, remote)
    
    # Clean up any lingering files.
    if os.path.exists(DIVIDE_TAG):
        os.remove(DIVIDE_TAG)
    #for fname in [str(remote / name) for name in glob.glob1(str(remote), '*.plc')]:
    #    os.remove(fname)
    #for fname in [str(remote / name) for name in glob.glob1(str(remote), '*.png')]:
    #    os.remove(fname)
    
    # Log all the times for good measure.
    t_end = time.time()
    logging.info('====TIMES====')
    logging.info('{} seconds\tpreliminary setup'.format(round(t_prelim - t_start)))
    logging.info('{} seconds\tstylization'.format(round(t_stylize - t_prelim)))
    logging.info('{} seconds\twrapping up'.format(round(t_end - t_stylize)))
    logging.info('{} seconds\tTOTAL'.format(round(t_end - t_start)))
    logging.info('=============')
    logging.info('\n------END-----\n')

if __name__ == '__main__':  
    main()