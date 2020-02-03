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
import optflow
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

def check_deps(processor):
    check = shutil.which(processor)
    if not check:
        print('Video processor {p} not installed. Aborting'.format(p=processor))
        sys.exit(1)
    
    if not (os.path.exists('core/deepmatching-static') and os.path.exists('core/deepflow2-static')):
        print('Deepmatching/Deepflow static binaries are missing. Aborting')
        sys.exit(1)
    else:
        # Ensure that Deepmatching/Deepflow can be executed.
        subprocess.Popen(['chmod', '+x', 'core/deepmatching-static'])
        subprocess.Popen(['chmod', '+x', 'core/deepflow2-static'])

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

def most_recent_stylize(dirname):
    # Count the number of output files and return.
    return len(glob.glob1(dirname, '*.png'))

def main():
    '''Driver program'''
    args = parse_args()
    
    # Make output folder(s), if necessary
    dirname = pathlib.Path(args.nfs) / os.path.basename(os.path.splitext(args.content)[0])
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    local = pathlib.Path(args.local) / os.path.basename(os.path.splitext(args.content)[0])
    if not os.path.exists(local):
        os.mkdir(local)
        
    # Preliminary operations to make sure that the environment is set up properly.
    check_deps(args.processor)
    
    # Split video into individual frames
    num_frames = split_frames(args.processor, args.content, args.resolution, dirname)
        
    # Find the most recent stylization and optical flow calculation.
    continue_with = most_recent_stylize(dirname) + 1
        
    # Begin optical flow calculation.
    optflow.optflow(args.resolution, args.downsamp_factor, num_frames, dirname, local)
    
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
