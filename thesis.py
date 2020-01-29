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
import errno
import shutil
import pathlib
import argparse
import platform
import threading
import subprocess
import numpy as np

# EXTERNAL LIB

# LOCAL LIB
from const import *

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'

def parse_args():
    '''Parses arguments'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('content', type=str,
        help='The path to the video to stylize.')
    ap.add_argument('style', type=str,
        help='The path to the model used for stylization')
    ap.add_argument('nfs', type=str,
        help='The directory of the mounted NFS file server where images are to be shared.')
        
    # Optional arguments
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

def check_deps(processor):
    check = shutil.which(processor)
    if not check:
        print('Video processor {p} not installed. Aborting'.format(p=processor))
        sys.exit(1)
    
    if not (os.path.exists('deepmatching-static') and os.path.exists('deepflow2-static')):
        print('Deepmatching/Deepflow static binaries are missing. Aborting')
        sys.exit(1)
    else:
        # Ensure that Deepmatching/Deepflow can be executed.
        subprocess.Popen(['chmod', '+x', 'deepmatching-static'])
        subprocess.Popen(['chmod', '+x', 'deepflow2-static'])

def split_frames(processor, content, resolution, dirname):    
    # Don't split the video if we've already done so.
    if not os.path.isfile(dirname / 'frame_00001.ppm'):
        if not resolution == RESOLUTION_DEFAULT:
            subprocess.Popen([processor, '-i', content, '-vf', 'scale=' + resolution, 
                str(dirname / FRAME_NAME)])
        else:
            subprocess.Popen([processor, '-i', content, str(dirname / FRAME_NAME)])
    
    # Return the number of frames.
    return len(glob.glob1(dirname, '*.ppm'))

def most_recent_optflo(dirname, resolution):
    # Check to see if the optical flow folder exists.
    flow = str(dirname / ('flow_' + resolution + '/'))
    if not os.path.isdir(flow):
        # If it doesn't exist, then there are no optflow files, and we start from scratch.
        return 1

    # The most recent frame half the number of .flo files (as there are two for each frame) plus one.
    return (len(glob.glob1(flow, '*.flo')) // 2) + 1

def most_recent_stylize(dirname):
    # Count the number of output files and return.
    return len(glob.glob1(dirname, '*.png'))

def get_job(dirname, resolution, num_frames):
    next_job = most_recent_optflo(dirname, resolution)
    # In order for an optflow job to be possible, there needs to be a valid pair of frames.
    if next_job >= num_frames:
        return None
    return next_job

def claim_job(job, flow, placeholder):
    # Try to create a placeholder. If this fails, return False.
    try:
        with open(placeholder, 'x') as handle:
            handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
    except FileExistsError:
        return False
    return True

def run_job(job, dirname, flow, downsamp_factor):
    if not job or job < 0:
        raise Exception('Bad job passed to run_job: {job}'.format(job=job))
    
    placeholder = flow / (os.path.splitext(FRAME_NAME)[0] % job + '.plc')
    
    # Create a placeholder for this job. If the claim fails, return.
    if not claim_job(job, flow, placeholder): return False
    
    start = dirname / (FRAME_NAME % job)
    end = dirname / (FRAME_NAME % (job + 1))
    forward_name = flow / 'forward_{i}_{j}.flo'.format(i=job, j=job+1)
    backward_name = flow / 'backward_{j}_{i}.flo'.format(i=job, j=job+1)
    reliable_forward = flow / 'reliable_{i}_{j}.pgm'.format(i=job, j=job+1)
    reliable_backward = flow / 'reliable_{j}_{i}.pgm'.format(i=job, j=job+1)
    
    # FIXME: These programs are extremely slow. We should pull to local for calculations.
    
    # Compute forward optical flow.
    print('Computing forward optical flow for job {job}.'.format(job=job))
    forward_dm = subprocess.Popen([
        './deepmatching-static', start, end, '-nt', '0', '-downscale', downsamp_factor
    ], stdout=subprocess.PIPE)
    forward_df = subprocess.run([
        './deepflow2-static', start, end, forward_name, '-match'
    ], stdin=forward_dm.stdout)
    
    # Compute backward optical flow.
    print('Computing backward optical flow for job {job}.'.format(job=job))
    backward_dm = subprocess.Popen([
        './deepmatching-static', end, start, '-nt', '0', '-downscale', downsamp_factor, '|',
    ], stdout=subprocess.PIPE)
    backward_df = subprocess.run([
        './deepflow2-static', end, start, backward_name, '-match'
    ], stdin=backward_dm.stdout)
    
    # Compute consistency check for forwards optical flow.
    print('Computing consistency check for forwards optical flow.')
    con1 = subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        forward_name, backward_name, reliable_forward, start
    ])
    
    # Compute consistency check for backwards optical flow.
    print('Computing consistency check for backwards optical flow.')
    con2 = subprocess.run([
        './core/consistencyChecker/consistencyChecker',
        backward_name, forward_name, reliable_backward, end
    ])
    
    # Now that the .flo files have been created, there's no reason to keep the placeholder.
    os.remove(placeholder)
    sys.exit(0)
    
    return True

def optflow(resolution, downsamp_factor, num_frames, dirname):    
    flow = dirname / ('flow_' + resolution + '/')
    if not os.path.isdir(flow):
        os.mkdir(flow)
    
    job = get_job(dirname, resolution, num_frames)
    while job is not None:
        print('Searching for a job...')
        success = run_job(job, dirname, flow, downsamp_factor)
        if success:
            # If we finished our job, other jobs may have completed in the 
            # meantime, so we should check from scratch.
            job = get_job(dirname, resolution, num_frames)
        else:
            # We narrowly missed our chance to complete a job, so we should 
            # try the next one available.
            job += 1

def main():
    '''Driver program'''
    args = parse_args()
    
    # Make output folder(s), if necessary
    dirname = pathlib.Path(args.nfs) / os.path.basename(os.path.splitext(args.content)[0])
    if not os.path.exists(dirname):
        os.mkdir(dirname)
        
    # Preliminary operations to make sure that the environment is set up properly.
    check_deps(args.processor)
    
    # Split video into individual frames
    num_frames = split_frames(args.processor, args.content, args.resolution, dirname)
        
    # Find the most recent stylization and optical flow calculation.
    continue_with = most_recent_stylize(dirname) + 1
        
    # Begin optical flow calculation.
    optflow(args.resolution, args.downsamp_factor, num_frames, dirname)
    
    # The following are all arguments to be fed into the Torch script.
    input_pattern = str('..' / dirname / FRAME_NAME)
    flow_pattern = str('..' / dirname / ('flow_' + args.resolution) / 'backward_[%d]_{%d}.flo')
    occlusions_pattern = str('..' / dirname / ('flow_' + args.resolution) / 'reliable_[%d]_{%d}.pgm')
    output_prefix = str('..' / dirname / 'out')
    backend = args.gpu_lib if int(args.gpu_num) > -1 else 'nn'
    use_cudnn = '1' if args.gpu_lib == 'cudnn' and int(args.gpu_num) > -1 else '0'
    
    # Run stylization.
    subprocess.Popen([
        'th', 'fast_artistic_video.lua',
        '-continue_with', str(continue_with),
        '-input_pattern', input_pattern,
        '-flow_pattern', flow_pattern,
        '-occlusions_pattern', occlusions_pattern,
        '-output_prefix', output_prefix,
        '-use_cudnn', use_cudnn,
        '-gpu', args.gpu_num,
        '-model_vid', '../' + args.style,
        '-model_img', 'self'
    ], cwd=pathlib.Path(os.getcwd()) / 'core')

if __name__ == '__main__':
    main()
