# author: Paul Galatic
#
# Handles initial task of splitting video and uploading frames to the shared system.

# STD LIB
import os
import pdb
import sys
import glob
import time
import shutil
import pathlib
import argparse
import threading
import subprocess

# EXTERNAL LIB
import ffprobe3

# LOCAL LIB
import common
from const import *

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('mode', type=str,
        help='Whether or not to split or combine frames. Options: (s)plit, (c)ombine')
    ap.add_argument('reel', type=str,
        help='The name of the video (locally, on disk).')
    
    # Optional arguments
    ap.add_argument('--src', type=str, nargs='?', default=None,
        help='The path to the folder in which the frames are contained, if combining them.')
    ap.add_argument('--dst', type=str, default=None,
        help='The path to the folder in which the product(s) of the operation will be placed. By default, it will place products in a folder derived from the name of the reel.')
    ap.add_argument('--extension', type=str, nargs='?', default='.ppm',
        help='The extension used for the frames of a split video. If performing manual cuts, set this to .png [.ppm].')
    ap.add_argument('--processor', type=str, nargs='?', default='ffmpeg',
        help='The video processer to use, either ffmpeg (preferred) or avconv (untested) [ffmpeg].')
    ap.add_argument('--lossless', action='store_true',
        help='Set in order to use a lossless video encoding, which will create an extremely large video file.')
    
    return ap.parse_args()

def check_deps(processor):
    check = shutil.which(processor)
    if not check:
        sys.exit('Video processor {} not installed. Aborting'.format(processor))
    if not (os.path.exists('core/deepmatching-static') and os.path.exists('core/deepflow2-static')):
        sys.exit('Deepmatching/Deepflow static binaries are missing. Aborting')
    else:
        # Ensure that Deepmatching/Deepflow can be executed.
        subprocess.Popen(['chmod', '+x', 'core/deepmatching-static'])
        subprocess.Popen(['chmod', '+x', 'core/deepflow2-static'])

def split_frames(processor, reel, local, extension='.ppm'):
    # Preliminary operations to make sure that the environment is set up properly.
    check_deps(processor)

    # Split video into a collection of frames. It's necessary to have a local copy of the frames.
    # Don't split the video if we've already done so.
    if not os.path.isfile(str(local / 'frame_00001{}'.format(extension))):
        # This line is to account for extensions other than the default.
        frame_name = os.path.splitext(FRAME_NAME)[0] + extension
        proc = subprocess.Popen([processor, '-i', str(reel), str(local / frame_name)])
    
        # Wait until splitting the frames is finished, so we know how many there are.
        proc.wait()
    
    # Spawn a thread to upload the files to the common area (is this necessary?).
    # threading.Thread(target=common.upload_frames...
    
    # Return the number of frames.
    return len(glob.glob1(str(local), '*.ppm'))

def combine_frames(processor, reel, src, dst, extension='.avi', lossless=False):
    # Preliminary operations to make sure that the environment is set up properly.
    check_deps(processor)

    # Get the original video's length. This will be necessary to properly reconstruct it.
    probe = ffprobe3.FFProbe(str(reel))
    duration = probe.streams[-1].duration
    num_frames = str(probe.streams[0].nb_frames)
    
    basename = os.path.splitext(os.path.basename(reel))[0]
    
    # Combine stylized frames into video.
    no_audio = str(dst / ('{}_no_audio{}'.format(basename, extension)))
    audio = str(dst / ('{}_stylized{}'.format(basename, extension)))
    
    if lossless:
        subprocess.run([
            processor, '-i', str(src / PREFIX_FORMAT),
            '-c:v', 'huffyuv',
            '-filter:v', 'setpts={}/{}*N/TB'.format(duration, num_frames),
            '-r', '{}/{}'.format(num_frames, duration),
            no_audio
        ])
    else:
        subprocess.run([
            processor, '-i', str(src / PREFIX_FORMAT),
            '-filter:v', 'setpts={}/{}*N/TB'.format(duration, num_frames),
            '-r', '{}/{}'.format(num_frames, duration),
            no_audio
        ])
     
    # Add audio to that video.
    subprocess.run([
        processor, '-i', no_audio, '-i', reel,
        '-c', 'copy', '-map', '0:0', '-map', '1:1',
        audio
    ])

def main():
    args = parse_args()

    dst = args.dst
    if dst == None:
        dst = os.path.basename(os.path.splitext(args.reel)[0])
    dst = pathlib.Path(dst)
    common.makedirs(dst)

    if args.mode == 's' or args.mode == 'split':
        split_frames(args.processor, args.reel, dst, args.extension)
    elif args.mode == 'c' or args.mode == 'combine':
        if not args.src:
            sys.exit('Please specify a source directory.')
        combine_frames(args.processor, args.reel, pathlib.Path(args.src), dst, lossless=args.lossless)
    else:
        sys.exit('Mode {} not recognized; please try again.'.format(args.mode))

if __name__ == '__main__':
    main()
