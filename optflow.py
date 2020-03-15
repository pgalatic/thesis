# author: Paul Galatic
#
# This module handles optical flow calculations.

# STD LIB
import os
import re
import sys
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
import torch
import numpy as np

from PIL import Image

# LOCAL LIB
import common
from const import *

def most_recent_optflo(remote):
    # Check to see if the optical flow folder exists.
    if not os.path.isdir(str(remote)):
        # If it doesn't exist, then there are no optflow files, and we start from scratch.
        return 1

    # The most recent frame is the most recent placeholder plus 1.
    placeholders = glob.glob1(str(remote), 'frame*.plc')
    if len(placeholders) == 0: return 1
    
    return max(map(int, [re.findall(r'\d+', plc)[0] for plc in placeholders])) + 1

def claim_job(remote, local, num_frames):
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

def load_and_preprocess(fname):
    load = cv2.cvtColor(cv2.imread(fname), cv2.COLOR_RGB2GRAY)
    return load

def write_flo(fname, tensor):
    out = open(fname, 'wb')
    np.array([ 80, 73, 69, 72 ], np.uint8).tofile(out)
    np.array([ tensor.shape[0], tensor.shape[1] ], np.int32).tofile(out)
    tensor.tofile(out)
    out.close()

def run_job(job, net, remote, local, completing):
    if job == None or job < 0:
        raise Exception('Bad job passed to run_job: {}'.format(job))
    
    time_start = time.time()
    
    logging.info('Computing optical flow for job {}.'.format(job))
    start_name = str(local / (FRAME_NAME % job))
    end_name = str(local / (FRAME_NAME % (job + 1)))
    forward_name = str(local / 'forward_{i}_{j}.flo'.format(i=job, j=job+1))
    backward_name = str(local / 'backward_{j}_{i}.flo'.format(i=job, j=job+1))
    reliable_name = str(local / 'reliable_{j}_{i}.pgm'.format(i=job, j=job+1))
    
    start = load_and_preprocess(start_name)
    end = load_and_preprocess(end_name)
    
    # Compute forward and backward optical flow.
    logging.debug('Job {}: Forward optical flow.'.format(job))
    forward = cv2.calcOpticalFlowFarneback(
        start, end, None, 0.5, 5, 30, 7, 7, 1.5, cv2.OPTFLOW_FARNEBACK_GAUSSIAN)
    write_flo(forward_name, forward)
    logging.debug('Job {}: Backward optical flow.'.format(job))
    backward = cv2.calcOpticalFlowFarneback(
        end, start, None, 0.5, 3, 15, 3, 5, 1.1, cv2.OPTFLOW_FARNEBACK_GAUSSIAN)
    write_flo(backward_name, backward)
    
    # Compute consistency check for backwards optical flow.
    logging.debug('Job {}: Consistency check.'.format(job))
    con2 = subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        backward_name, forward_name, reliable_name, end_name
    ])
    
    logging.info(
            'Elapsed time for computing optical flow: {}'.format(round(time.time() - time_start, 3)))
    
    # Spawn a thread to put the produced files in the remote directory.
    # TODO: Reduce thread creation overhead by having one background thread operating on a list?
    # TODO: Look at thread pools.
    # TODO: Assess time taken in various section of program (threads vs. bash commands?)
    # TODO: Determine which bash commands can be executed in parallel.
    if remote != local:
        fnames = [forward_name, backward_name, reliable_name]
        complete = threading.Thread(target=common.upload_files, args=(fnames, remote))
        completing.append(complete)
        complete.start()

def optflow(num_frames, net_name, remote, local): 
    logging.info('Starting optical flow calculations...')
    
    # Get a job! We need our first job before we can start threading.
    job = claim_job(remote, local, num_frames)
    running = []
    completing = []
    
    while job is not None:
        # Spawn a thread to complete that job, then get the next one.
        to_run = threading.Thread(target=run_job, 
            args=(job, net, remote, local, completing))
        running.append(to_run)
        to_run.start()
        
        # If there isn't room in the jobs list, wait for a thread to finish.
        while len(running) >= MAX_OPTFLOW_JOBS:
            running = [thread for thread in running if thread.isAlive()]
            time.sleep(1)
        
        job = claim_job(remote, local, num_frames)
            
    # Uncomment these two lines to discard placeholders when optical flow calculations are finished.
    # files = glob.glob1(str(remote), '*.plc')
    # for fname in files: os.remove(str(remote / fname))
    
    # Join all remaining threads.
    logging.info('Wrapping up threads for optical flow calculation...')
    for thread in running:
        thread.join()
    for thread in completing:
        thread.join()

    logging.info('...optical flow calculations are finished.')

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser(epilog='Specify image1 and image2 to compute optical flow between images. Otherwise, specify just \'dir\' to compute optical flow between all adjacent pairs of images in \'dir\'.\n\nDo not specify the full paths of image1 or image2!')
    
    ap.add_argument('dir',
        help='The directory containing the optical flow files.')
    ap.add_argument('net_name',
        help='The path to the model used for computing optical flow.')
    ap.add_argument('image1', nargs='?', default=None,
        help='The name of the .ppm image to compute optical flow FROM')
    ap.add_argument('image2', nargs='?', default=None,
        help='The name of the .ppm image to compute optical flow TO')
    ap.add_argument('outname', nargs='?', default='out.flo',
        help='The name of the output file, if image1 and image2 are specified')
    
    return ap.parse_args()

def main():
    args = parse_args()
    common.start_logging()
    
    dir = pathlib.Path(args.dir)
    
    if args.image1 and args.image2:
        pass # implement this later
    else:
        num_frames = len([str(dir / frame) for frame in glob.glob1(str(dir), '*.ppm')])
        optflow(num_frames, args.net_name, dir, dir)

if __name__ == '__main__':
    main()