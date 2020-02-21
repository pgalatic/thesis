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
    ap.add_argument('--resolution', type=str, nargs='?', default=RESOLUTION_DEFAULT,
        help='The width to process the video at in the format w:h [Original resolution].')
    
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

def split_frames(processor, resolution, reel, local, extension='.ppm'):
    # Preliminary operations to make sure that the environment is set up properly.
    check_deps(processor)

    # Split video into a collection of frames. It's necessary to have a local copy of the frames.
    # Don't split the video if we've already done so.
    if not os.path.isfile(str(local / 'frame_00001{}'.format(extension))):
        # This line is to account for extensions other than the default.
        frame_name = os.path.splitext(FRAME_NAME)[0] + extension
        if resolution == RESOLUTION_DEFAULT:
            proc = subprocess.Popen([processor, '-i', str(reel), str(local / frame_name)])
        else:
            proc = subprocess.Popen([processor, '-i', str(reel), '-vf', 'scale=' + resolution, 
                str(local / frame_name)])
    
        # Wait until splitting the frames is finished, so we know how many there are.
        proc.wait()
    
    # Spawn a thread to upload the files to the common area (is this necessary?).
    # threading.Thread(target=common.upload_frames...
    
    # Return the number of frames.
    return len(glob.glob1(str(local), '*.ppm'))

def combine_frames(processor, reel, remote, local):
    # Preliminary operations to make sure that the environment is set up properly.
    check_deps(processor)

    # Get the stylized frames from remote and move them to local for ease of processing.
    fnames = glob.glob1(str(remote), '*.png.')
    oldnames = [str(remote / name) for name in fnames]
    newnames = [str(local / name) for name in fnames]
    
    for oldname, newname in zip(oldnames, newnames):
        shutil.copyfile(oldname, newname)

    # Get the original video's length. This will be necessary to properly reconstruct it.
    probe = ffprobe.FFProbe(reel)
    duration = probe.streams[-1].duration
    num_frames = str(probe.streams[0].nb_frames)
    
    stylized = str(local / ('stylized_' + os.path.basename(reel)))
    stylized_audio = str(local / ('stylized_audio_' + os.path.basename(reel)))
    stylized_final = str(local / ('stylized_final_' + os.path.basename(reel)))
    
    # Combine stylized frames into video.
    subprocess.run([
        processor, '-i', str(local / PREFIX_FORMAT), 
        '-filter:v', 'setpts={}/{}*N/TB'.format(duration, num_frames),
        '-r', '{}/{}'.format(num_frames, duration),
        stylized
    ])
    
    # Add audio to that video.
    subprocess.run([
        processor, '-i', stylized, '-i', reel,
        '-c', 'copy', '-map', '0:0', '-map', '1:1',
        stylized_audio
    ])
    
    # Re-encode so that the video is accessible on more platforms (otherwise, it will be corrupted when played in Google Chrome).
    subprocess.run([
        processor, '-i', stylized_audio,
        '-pix_fmt', 'yuv420p',
        stylized_final
    ])

def main():
    args = parse_args()

    dst = args.dst
    if dst == None:
        dst = os.path.basename(os.path.splitext(args.reel)[0])
    dst = pathlib.Path(dst)
    common.makedirs(dst)

    if args.mode == 's' or args.mode == 'split':
        split_frames(args.processor, args.resolution, args.reel, dst, args.extension)
    elif args.mode == 'c' or args.mode == 'combine':
        if not args.src:
            sys.exit('Please specify a source directory.')
        combine_frames(args.processor, args.reel, pathlib.Path(args.src), dst)
    else:
        sys.exit('Mode {} not recognized; please try again.'.format(args.mode))

if __name__ == '__main__':
    main()
