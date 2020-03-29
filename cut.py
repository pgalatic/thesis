# author: Paul Galatic
#
# Computes cuts given a video.

# STD LIB
import os
import csv
import pdb
import logging
import argparse

# EXTERNAL LIB
import ffprobe3
import scenedetect as sd
from scipy import stats

# LOCAL LIB
import common

def divide(video_path, write_to=None):
    video_manager = sd.video_manager.VideoManager([str(video_path)])
    scene_manager = sd.scene_manager.SceneManager()
    scene_detector = sd.detectors.ContentDetector(threshold=45, min_scene_len=10)
    scene_manager.add_detector(scene_detector)
    base_timecode = video_manager.get_base_timecode()
    
    partitions = []
    
    try:
        video_manager.set_downscale_factor()
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        
        scene_list = scene_manager.get_scene_list(base_timecode)
        logging.info('Number of partitions: {}'.format(len(scene_list)))
        for idx, scene in enumerate(scene_list):
            start, end = scene[0].get_frames(), scene[1].get_frames()
            logging.info('Partition %2d frames: [%d:%d]' % (idx, start, end))
            partitions.append((start, end))
        
    finally:
        video_manager.release()
    
    return partitions

def read_cuts(fname, num_frames):
    with open(fname, 'r') as f:
        rdr = csv.reader(f)
        keys = sorted([int(row[0]) for row in rdr])
        partitions = [(idx, idy) for idx, idy in zip([0] + keys, keys + [num_frames])]
    
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

def sfp(reel, partitions=None):
    probe = ffprobe3.FFProbe(str(reel))
    num_frames = int(probe.streams[0].nb_frames)
    if not partitions: return num_frames
    partitions[-1] = (partitions[-1][0], num_frames)
    norm_partitions = [(partition[1] - partition[0]) / num_frames for partition in partitions]
    entropy = stats.entropy(norm_partitions, base=len(partitions))
    
    return num_frames / (1 + ((len(partitions) - 1) * entropy**2))

def main():
    args = parse_args()
    common.start_logging()
    
    probe = ffprobe3.FFProbe(str(args.reel))
    num_frames = int(probe.streams[0].nb_frames)
    
    if args.read_from:
        partitions = read_cuts(args.read_from, num_frames)
    else:
        partitions = divide(args.reel, num_frames, args.write_to)
    
    logging.info(partitions)

if __name__ == '__main__':
    main()
    