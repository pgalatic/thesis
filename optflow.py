# author: Paul Galatic
#
# This module handles optical flow calculations. These calculations are made using DeepMatching and
# DeepFlow. Future versions may use FlowNet2 or other, faster, better-quality optical flow 
# measures. The most important criteria is accuracy, and after that, speed.

# STD LIB
import os
import re
import pdb
import glob
import time
import logging
import pathlib
import argparse
import platform
import threading
import subprocess

# EXTERNAL LIB
import cv2
import numpy as np

# LOCAL LIB
import common
from const import *

def most_recent_optflo(remote):
    # Check to see if the optical flow folder exists.
    if not os.path.isdir(str(remote)):
        # If it doesn't exist, then there are no optflow files, and we start from scratch.
        return 1

    # The most recent frame is the most recent placeholder plus 1.
    placeholders = glob.glob1(str(remote), 'frame_*.plc')
    if len(placeholders) == 0: return 1
    
    return max(map(int, [re.findall(r'\d+', plc)[0] for plc in placeholders])) + 1

def claim_job(remote, local, num_frames):
    '''
    All nodes involved are assumed to share a common directory. In this directory, placeholders
    are created so that no two nodes work compute the same material. 
    '''
    # Check the most recent available job.
    next_job = most_recent_optflo(remote)
    
    # In order for an optflow job to be possible, there needs to be a valid pair of frames.
    if next_job >= num_frames:
        # Check to see if there are any more frames in the time since we began optflow calculations.
        num_frames = common.count_files(local, '.ppm')
        if next_job >= num_frames:
            return None
    
    # Loop while there may yet still be jobs to do.
    while next_job < num_frames:
        
        # Try to create a placeholder.
        placeholder = str(remote / (os.path.splitext(FRAME_NAME)[0] % next_job + '.plc'))
        try:
            # This will only succeed if this program successfully created the placeholder.
            with open(placeholder, 'x') as handle:
                handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
            
            logging.debug('Job claimed: {}'.format(next_job))
            return next_job
        except FileExistsError:
            # We couldn't claim that job, so try the next one.
            next_job += 1
    
    # There are no more jobs.
    return None

def write_flow(fname, flow):
    """Write optical flow to a .flo file
    Args:
        flow: optical flow
        dst_file: Path where to write optical flow
    """
    # Save optical flow to disk
    with open(fname, 'wb') as f:
        np.array(202021.25, dtype=np.float32).tofile(f)
        height, width = flow.shape[:2]
        np.array(width, dtype=np.uint32).tofile(f)
        np.array(height, dtype=np.uint32).tofile(f)
        flow.astype(np.float32).tofile(f)

def farneback(start_name, end_name, forward_name, backward_name):
    start = cv2.cvtColor(cv2.imread(start_name), cv2.COLOR_BGR2GRAY)
    end = cv2.cvtColor(cv2.imread(end_name), cv2.COLOR_BGR2GRAY)
    
    # Compute forward optical flow.
    forward = cv2.calcOpticalFlowFarneback(start, end, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    # Compute backward optical flow.
    backward = cv2.calcOpticalFlowFarneback(end, start, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    
    write_flow(forward_name, forward)
    write_flow(backward_name, backward)

def deepflow(start_name, end_name, forward_name, backward_name, downsamp_factor='2'):
    # Compute forward optical flow.
    forward_dm = subprocess.Popen([
        './core/deepmatching-static', start_name, end_name, '-nt', '0', '-downscale', downsamp_factor
    ], stdout=subprocess.PIPE)
    subprocess.run([
        './core/deepflow2-static', start_name, end_name, forward_name, '-match'
    ], stdin=forward_dm.stdout)
    
    # Compute backward optical flow.
    backward_dm = subprocess.Popen([
        './core/deepmatching-static', end_name, start_name, '-nt', '0', '-downscale', downsamp_factor, '|',
    ], stdout=subprocess.PIPE)
    subprocess.run([
        './core/deepflow2-static', end_name, start_name, backward_name, '-match'
    ], stdin=backward_dm.stdout)

def run_job(job, remote, local, put_thread, fast=False):
    if job == None or job < 0:
        raise Exception('Bad job passed to run_job: {}'.format(job))
    
    logging.info('Computing optical flow for job {}.'.format(job))
    
    start_name = str(local / (FRAME_NAME % job))
    end_name = str(local / (FRAME_NAME % (job + 1)))
    forward_name = str(local / 'forward_{i}_{j}.flo'.format(i=job, j=job+1))
    backward_name = str(local / 'backward_{j}_{i}.flo'.format(i=job, j=job+1))
    reliable_name = str(local / 'reliable_{j}_{i}.pgm'.format(i=job, j=job+1))
    
    if fast:
        farneback(start_name, end_name, forward_name, backward_name)
    else:
        deepflow(start_name, end_name, forward_name, backward_name)
    
    # Compute consistency check for backwards optical flow.
    logging.debug('Job {}: Consistency check.'.format(job))
    subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        backward_name, forward_name, reliable_name, end_name
    ])
    
    # Spawn a thread to put the produced files in the remote directory.
    # TODO: Reduce thread creation overhead by having one background thread operating on a list?
    # TODO: Look at thread pools.
    fnames = [forward_name, backward_name, reliable_name]
    complete = threading.Thread(target=common.upload_files, args=(fnames, remote))
    put_thread.append(complete)
    complete.start()

def optflow(num_frames, remote, local): 
    logging.info('Starting optical flow calculations...')
        
    # Get a job! We need our first job before we can start threading.
    job = claim_job(remote, local, num_frames)
    running = []
    completing = []
    
    # FIXME: If optflow starts before the frames are entirely split, then the program will end early.
    while job is not None:
        # Spawn a thread to complete that job, then get the next one.
        running.append(threading.Thread(target=run_job, 
            args=(job, remote, local, completing)))
        running[-1].start()
        
        # If there isn't room in the jobs list, wait for a thread to finish.
        while len(running) >= MAX_OPTFLOW_JOBS:
            running = [thread for thread in running if thread.isAlive()]
            time.sleep(1)
        
        job = claim_job(remote, local, num_frames)
    
    # Join all remaining threads.
    logging.info('Wrapping up threads for optical flow calculation...')
    for thread in running:
        thread.join()
    for thread in completing:
        thread.join()

    logging.info('...optical flow calculations are finished.')

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    ap.add_argument('src', type=str,
        help='The directory in which the .ppm files are stored.')
    ap.add_argument('dst', type=str,
        help='The directory in which to place the .flo, .pgm files.')
    
    # Optional arguments
    ap.add_argument('--test', action='store_true',
        help='Compute optical flow over only a few frames to test functionality.')
    
    return ap.parse_args()

def main():
    args = parse_args()
    common.start_logging()
    
    src = pathlib.Path(args.src)
    dst = pathlib.Path(args.dst)
    
    if args.test:
        num_frames = NUM_FRAMES_FOR_TEST
    else:
        num_frames = len(glob.glob1(str(src), '*.ppm'))
    
    optflow(num_frames, dst, src)

if __name__ == '__main__':
    main()