# author: Paul Galatic
#
# This module handles optical flow calculations.

# STD LIB
import os
import sys
import pdb
import glob
import time
import shutil
import platform
import threading
import subprocess

# EXTERNAL LIB

# LOCAL LIB
from const import *

def most_recent_optflo(flow, resolution):
    # Check to see if the optical flow folder exists.
    if not os.path.isdir(str(flow)):
        # If it doesn't exist, then there are no optflow files, and we start from scratch.
        return 1

    # The most recent frame half the number of placeholder files plus one.
    return len(glob.glob1(str(flow), '*.plc')) + 1

def claim_job(dirname, flow, local, resolution, num_frames):
    # Check the most recent available job.
    next_job = most_recent_optflo(flow, resolution)
    
    # In order for an optflow job to be possible, there needs to be a valid pair of frames.
    if next_job >= num_frames:
        return None
    
    # Loop while there may yet still be jobs to do.
    while next_job < num_frames:
        
        # Try to create a placeholder. If this fails, return False.
        placeholder = str(flow / (os.path.splitext(FRAME_NAME)[0] % next_job + '.plc'))
        try:
            # This will only succeed if this program successfully created the placeholder.
            with open(placeholder, 'x') as handle:
                handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
            
            # Download the files required for the job, if necessary.
            start_local = str(local / (FRAME_NAME % next_job))
            start_remote = str(dirname / (FRAME_NAME % next_job))
            end_local = str(local / (FRAME_NAME % (next_job + 1)))
            end_remote = str(dirname / (FRAME_NAME % (next_job + 1)))
            
            if not os.path.exists(start_local): shutil.copy(start_remote, start_local)
            if not os.path.exists(end_local):   shutil.copy(end_remote, end_local)
            
            print('Job claimed: {job}'.format(job=next_job))
            return next_job
        except FileExistsError:
            # We couldn't claim that job, so try the next one.
            next_job += 1
    
    # There are no more jobs.
    return None

def complete_job(fnames, dst):
    for fname in fnames:
        shutil.copyfile(fname, str(dst / os.path.basename(fname)))

def run_job(job, dirname, flow, local, downsamp_factor, put_thread):
    if job == None or job < 0:
        raise Exception('Bad job passed to run_job: {job}'.format(job=job))
    
    start_local = str(local / (FRAME_NAME % job))
    start_remote = str(dirname / (FRAME_NAME % job))
    end_local = str(local / (FRAME_NAME % (job + 1)))
    end_remote = str(dirname / (FRAME_NAME % (job + 1)))
    forward_name = str(local / 'forward_{i}_{j}.flo'.format(i=job, j=job+1))
    backward_name = str(local / 'backward_{j}_{i}.flo'.format(i=job, j=job+1))
    reliable_forward = str(local / 'reliable_{i}_{j}.pgm'.format(i=job, j=job+1))
    reliable_backward = str(local / 'reliable_{j}_{i}.pgm'.format(i=job, j=job+1))
        
    # Compute forward optical flow.
    print('Computing forward optical flow for job {job}.'.format(job=job))
    forward_dm = subprocess.Popen([
        './core/deepmatching-static', start_local, end_local, '-nt', '0', '-downscale', downsamp_factor
    ], stdout=subprocess.PIPE)
    forward_df = subprocess.run([
        './core/deepflow2-static', start_local, end_local, forward_name, '-match'
    ], stdin=forward_dm.stdout)
    
    # Compute backward optical flow.
    # print('Computing backward optical flow for job {job}.'.format(job=job))
    backward_dm = subprocess.Popen([
        './core/deepmatching-static', end_local, start_local, '-nt', '0', '-downscale', downsamp_factor, '|',
    ], stdout=subprocess.PIPE)
    backward_df = subprocess.run([
        './core/deepflow2-static', end_local, start_local, backward_name, '-match'
    ], stdin=backward_dm.stdout)
    
    # Compute consistency check for forwards optical flow.
    # print('Computing consistency check for forwards optical flow.')
    con1 = subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        forward_name, backward_name, reliable_forward, start_local
    ])
    
    # Compute consistency check for backwards optical flow.
    # print('Computing consistency check for backwards optical flow.')
    con2 = subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        backward_name, forward_name, reliable_backward, end_local
    ])
    
    # Spawn a thread to put the produced files in the remote directory.
    fnames = [forward_name, backward_name, reliable_forward, reliable_backward]
    production = threading.Thread(target=complete_job, args=(fnames, flow))
    put_thread.append(production)
    production.start()

def optflow(resolution, downsamp_factor, num_frames, dirname, local): 
    print('Starting optical flow calculations...')
    
    flow = dirname / ('flow_' + resolution + '/')
    if not os.path.isdir(str(flow)):
        os.mkdir(str(flow))
    
    # Get a job! We need our first job before we can start threading.
    job = claim_job(dirname, flow, local, resolution, num_frames)
    running = []
    completing = []
    while job is not None:
        # If there isn't room in the jobs list, wait for a thread to finish.
        while len(running) > MAX_OPTFLOW_JOBS:
            running = [thread for thread in running if thread.isAlive()]
            time.sleep(1)
        # Spawn a thread to complete that job, then get the next one.
        running.append(threading.Thread(target=run_job, 
            args=(job, dirname, flow, local, downsamp_factor, completing)))
        running[-1].start()
        job = claim_job(dirname, flow, local, resolution, num_frames)
        
    # Uncomment these two lines to discard placeholders when optical flow calculations are finished.
    # files = glob.glob1(flow, '*.plc')
    # for fname in files: os.remove(flow / fname)
    
    # Join all remaining threads.
    print('Wrapping up threads...')
    for thread in running:
        thread.join()
    for thread in completing:
        thread.join()

    print('...optical flow calculations are finished.')