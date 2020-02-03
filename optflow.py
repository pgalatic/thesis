# author: Paul Galatic
#
# This module handles optical flow calculations.

# STD LIB
import os
import sys
import pdb
import glob
import shutil
import platform
import threading
import subprocess

# EXTERNAL LIB

# LOCAL LIB
from const import *

def most_recent_optflo(flow, resolution):
    # Check to see if the optical flow folder exists.
    if not os.path.isdir(flow):
        # If it doesn't exist, then there are no optflow files, and we start from scratch.
        return 1

    # The most recent frame half the number of placeholder files plus one.
    return len(glob.glob1(flow, '*.plc')) + 1

def claim_job(flow, resolution, num_frames):
    # Check the most recent available job.
    next_job = most_recent_optflo(flow, resolution)
    
    # In order for an optflow job to be possible, there needs to be a valid pair of frames.
    if next_job >= num_frames:
        return None
    
    # Loop while there may yet still be jobs to do.
    while next_job < num_frames:
        
        # Try to create a placeholder. If this fails, return False.
        placeholder = flow / (os.path.splitext(FRAME_NAME)[0] % next_job + '.plc')
        try:
            # This will only succeed if this program successfully created the placeholder.
            with open(placeholder, 'x') as handle:
                handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
            return next_job
        except FileExistsError:
            # We couldn't claim that job, so try the next one.
            next_job += 1
    
    # There are no more jobs.
    return None

def complete_job(fnames, dst):
    for fname in fname:
        shutil.copyfile(fname, dst / os.path.basename(fname))

def run_job(job, dirname, flow, local, downsamp_factor):
    if job == None or job < 0:
        raise Exception('Bad job passed to run_job: {job}'.format(job=job))
    
    start_local = local / (FRAME_NAME % job)
    start_remote = dirname / (FRAME_NAME % job)
    end_local = local / (FRAME_NAME % (job + 1))
    end_remote = dirname / (FRAME_NAME % (job + 1))
    forward_name = local / 'forward_{i}_{j}.flo'.format(i=job, j=job+1)
    backward_name = local / 'backward_{j}_{i}.flo'.format(i=job, j=job+1)
    reliable_forward = local / 'reliable_{i}_{j}.pgm'.format(i=job, j=job+1)
    reliable_backward = local / 'reliable_{j}_{i}.pgm'.format(i=job, j=job+1)
    
    # Move the files to the local directory, if necessary.
    if not os.path.exists(start_local): shutil.copy(start_remote, start_local)
    if not os.path.exists(end_local):   shutil.copy(end_remote, end_local)
        
    # Compute forward optical flow.
    print('Computing forward optical flow for job {job}.'.format(job=job))
    forward_dm = subprocess.Popen([
        './core/deepmatching-static', start_local, end_local, '-nt', '0', '-downscale', downsamp_factor
    ], stdout=subprocess.PIPE)
    forward_df = subprocess.run([
        './core/deepflow2-static', start_local, end_local, forward_name, '-match'
    ], stdin=forward_dm.stdout)
    
    # Compute backward optical flow.
    print('Computing backward optical flow for job {job}.'.format(job=job))
    backward_dm = subprocess.Popen([
        './core/deepmatching-static', end_local, start_local, '-nt', '0', '-downscale', downsamp_factor, '|',
    ], stdout=subprocess.PIPE)
    backward_df = subprocess.run([
        './core/deepflow2-static', end_local, start_local, backward_name, '-match'
    ], stdin=backward_dm.stdout)
    
    # Compute consistency check for forwards optical flow.
    print('Computing consistency check for forwards optical flow.')
    con1 = subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        forward_name, backward_name, reliable_forward, start_local
    ])
    
    # Compute consistency check for backwards optical flow.
    print('Computing consistency check for backwards optical flow.')
    con2 = subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        backward_name, forward_name, reliable_backward, end_local
    ])
    
    # Put the produced files in the remote directory.
    shutil.copyfile(forward_name, flow / os.path.basename(forward_name))
    shutil.copyfile(backward_name, flow / os.path.basename(backward_name))
    shutil.copyfile(reliable_forward, flow / os.path.basename(reliable_forward))
    shutil.copyfile(reliable_backward, flow / os.path.basename(reliable_backward))

def optflow(resolution, downsamp_factor, num_frames, dirname, local):    
    flow = dirname / ('flow_' + resolution + '/')
    if not os.path.isdir(flow):
        os.mkdir(flow)
    
    job = claim_job(flow, resolution, num_frames)
    while job is not None:
        print('Searching for a job...')
        run_job(job, dirname, flow, local, downsamp_factor)
        # Get a job!
        job = claim_job(flow, resolution, num_frames)
    
    # Discard placeholders.
    files = glob.glob1(flow, '*.plc')
    for fname in files: os.remove(fname)
