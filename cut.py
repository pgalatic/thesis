# author: Paul Galatic
#
# Computes cuts given a video.

# STD LIB
import os
import csv
import pdb
import sys
import glob
import logging
import pathlib
import argparse

# EXTERNAL LIB
import cv2
import numpy as np
import scenedetect as sd

# LOCAL LIB
import common
from const import *

def divide(video_path, write_to=None):
    video_manager = sd.video_manager.VideoManager([str(video_path)])
    scene_manager = sd.scene_manager.SceneManager()
    scene_detector = sd.detectors.ContentDetector(threshold=45, min_scene_len=10)
    scene_manager.add_detector(scene_detector)
    base_timecode = video_manager.get_base_timecode()
    
    try:
        video_manager.set_downscale_factor()
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        
        scene_list = scene_manager.get_scene_list(base_timecode)
        partitions = []
        logging.info('Number of partitions: {}'.format(len(scene_list)))
        for idx, scene in enumerate(scene_list):
            start, end = scene[0].get_frames(), scene[1].get_frames()
            logging.info('Partition %2d frames: [%d:%d]' % (idx, start, end))
            partitions.append((start, end))
    
        # Write the keys to a .csv file, if applicable.
        if write_to:
            # Skip the last partition to stay consistent with manual format.
            write_cuts(write_to, partitions[:-1])
        
    finally:
        video_manager.release()

def read_cuts(fname):
    with open(fname, 'r') as f:
        rdr = csv.reader(f)
        keys = sorted([int(row[0]) for row in rdr])
        partitions = [(idx, idy) for idx, idy in zip([0] + keys, keys + [None])]
    
    logging.info('Number of partitions: {}'.format(len(partitions)))
    return partitions

def write_cuts(write_to, partitions):
    with open(write_to, 'w') as f:
        wtr = csv.writer(f)
        for partition in partitions:
            wtr.writerow([partition[1]])
    logging.info('...Wrote keys to {}.'.format(write_to))

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('reel', type=str,
        help='The path to the video to cut up.')
    
    # Optional arguments
    ap.add_argument('--extension', type=str, nargs='?', default='.ppm',
        help='The extension of the frames in src. Change this if you only have, say, .png files [.ppm].')
    ap.add_argument('--read_from', type=str, nargs='?', default=None,
        help='The .csv file containing frames that denote cuts. Determining cuts manually is always more accurate than an automatic assessment, if time permits. Use video.py to split frames for manual inspection. [None]')
    ap.add_argument('--write_to', type=str, nargs='?', default=None,
        help='The .csv file in which to write automatically computed cuts for later reading [None].')
    
    return ap.parse_args()

def main():
    args = parse_args()
    common.start_logging()
    
    if args.read_from:
        partitions = read_cuts(args.read_from)
    else:
        partitions = divide(args.reel, args.write_to)
    
    logging.info(partitions)

if __name__ == '__main__':
    main()