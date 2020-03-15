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
import platform
import threading
import subprocess

# EXTERNAL LIB

# LOCAL LIB
import common
from const import *

def most_recent_optflo(remote):
    # Check to see if the optical flow folder exists.
    if not os.path.isdir(str(remote)):
        # If it doesn't exist, then there are no optflow files, and we start from scratch.
        return 1

    # The most recent frame is the most recent placeholder plus 1.
    placeholders = glob.glob1(str(remote), '*.plc')
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

def run_job(job, remote, local, put_thread, downsamp_factor='2'):
    if job == None or job < 0:
        raise Exception('Bad job passed to run_job: {}'.format(job))
    
    logging.info('Computing optical flow for job {}.'.format(job))
    
    start_local = str(local / (FRAME_NAME % job))
    end_local = str(local / (FRAME_NAME % (job + 1)))
    forward_name = str(local / 'forward_{i}_{j}.flo'.format(i=job, j=job+1))
    backward_name = str(local / 'backward_{j}_{i}.flo'.format(i=job, j=job+1))
    reliable_forward = str(local / 'reliable_{i}_{j}.pgm'.format(i=job, j=job+1))
    reliable_backward = str(local / 'reliable_{j}_{i}.pgm'.format(i=job, j=job+1))
        
    # Compute forward optical flow.
    logging.debug('Job {}: Forward optical flow'.format(job))
    forward_dm = subprocess.Popen([
        './core/deepmatching-static', start_local, end_local, '-nt', '0', '-downscale', downsamp_factor
    ], stdout=subprocess.PIPE)
    forward_df = subprocess.run([
        './core/deepflow2-static', start_local, end_local, forward_name, '-match'
    ], stdin=forward_dm.stdout)
    
    # Compute backward optical flow.
    logging.debug('Job {}: Backward optical flow'.format(job))
    backward_dm = subprocess.Popen([
        './core/deepmatching-static', end_local, start_local, '-nt', '0', '-downscale', downsamp_factor, '|',
    ], stdout=subprocess.PIPE)
    backward_df = subprocess.run([
        './core/deepflow2-static', end_local, start_local, backward_name, '-match'
    ], stdin=backward_dm.stdout)
    
    # Compute consistency check for backwards optical flow.
    logging.debug('Job {}: Consistency check.'.format(job))
    con = subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        backward_name, forward_name, reliable_backward, end_local
    ])
    
    # Spawn a thread to put the produced files in the remote directory.
    # TODO: Reduce thread creation overhead by having one background thread operating on a list?
    # TODO: Look at thread pools.
    # TODO: Assess time taken in various section of program (threads vs. bash commands?)
    # TODO: Determine which bash commands can be executed in parallel.
    fnames = [forward_name, backward_name, reliable_backward]
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