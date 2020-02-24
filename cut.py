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
from statistics import mean

# EXTERNAL LIB
import numpy as np
from PIL import Image

# LOCAL LIB
import common
from const import *

# TODO: https://pyscenedetect.readthedocs.io/en/latest/examples/usage-example/

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('src', type=str,
        help='The path to the folder in which the frames are contained.')
    
    # Optional arguments
    ap.add_argument('--extension', type=str, nargs='?', default='.ppm',
        help='The extension of the frames in src. Change this if you only have, say, .png files [.ppm].')
    ap.add_argument('--read_from', type=str, nargs='?', default=None,
        help='The .csv file containing frames that denote cuts. Determining cuts manually is always more accurate than an automatic assessment, if time permits. Use video.py to split frames for manual inspection. [None]')
    ap.add_argument('--write_to', type=str, nargs='?', default=None,
        help='The .csv file in which to write automatically computed cuts for later reading [None].')
    
    return ap.parse_args()

def kl_dist(frame1, frame2):
    # Uses Kullback-Liebler divergence as in Courbon et al. (2010).
    # http://www.sciencedirect.com/science/article/pii/S0967066110000808
    array1 = np.asarray(Image.open(frame1)).astype(np.float64) / 255.
    array2 = np.asarray(Image.open(frame2)).astype(np.float64) / 255.
    
    hist1 = array1.mean(axis=2).flatten()
    hist2 = array2.mean(axis=2).flatten()
    
    # Add EPSILON everywhere to avoid dividing by zero.
    p = (hist1 + EPSILON) / np.sum(hist1)
    q = (hist2 + EPSILON) / np.sum(hist2)
    
    # As implemented in "KL Divergence Python Example" by Cory Malkin (2019).
    # https://towardsdatascience.com/kl-divergence-python-example-b87069e4b810
    return np.sum(p * np.log(p / (q)))

def get_dists(frames, dist_func):
    # Iterate over all consecutive pairs and find the distances between them.
    dists = []
    for idx, (frame1, frame2) in enumerate(zip(frames, frames[1:])):
        # Store the names of the frames, their location in the sequence, and the distance between them.
        dists.append((idx, dist_func(frame1, frame2)))
    # Sort in descending order by the distance between frames.
    return sorted(dists, key=lambda x: x[-1], reverse=True)

def assess_partitions(partitions):
    assert(len(partitions) == len(keys) + 1)

    logging.info('Number of partitions: {}'.format(len(partitions)))
    logging.info('Average partition length: {}'.format(mean([len(partition) for partition in partitions])))

def divide(frames, write_to=None):
    distpairs = get_dists(frames, kl_dist) # Change the second parameter to change the distance metric.
    # Ignore any distances that aren't significantly above the average as defined by MIN_DIST_FACTOR.
    dists = np.array([pair[-1] for pair in distpairs])
    mean_dist = np.mean(dists)
    distpairs = [pair for pair in distpairs if pair[-1] > MIN_DIST_FACTOR * mean_dist]
    
    # Loop until the "knee point" where keyframe candidates become more similar is reached.
    total_divergence = EPSILON
    keys = []
    for pair in distpairs:
        if pair[-1] / total_divergence < KNEE_THRESHOLD:
            break
        total_divergence += pair[-1]
        keys.append(pair[0])
    # Use the keys to compute partitions, then return the partitions.
    keys = sorted(keys)
    
    # Write the keys to a .csv file, if applicable.
    if write_to:
        with open(write_to, 'w') as f:
            wtr = csv.writer(f)
            for key in keys:
                wtr.writerow([key])
        logging.info('...Wrote keys to {}.'.format(write_to))
    
    # Partitions are a list of lists of frame filenames.
    partitions = [frames[idx:idy] for idx, idy in zip([0] + keys, keys + [None])]
    
    assess_partitions(partitions)
    
    return partitions

def read_cuts(fname, frames):
    with open(fname, 'r') as f:
        rdr = csv.reader(f)
        keys = sorted([int(row[0]) for row in rdr])
        partitions = [frames[idx:idy] for idx, idy in zip([0] + keys, keys + [None])]
    
    assess_partitions(partitions)
    
    return partitions

def main():
    args = parse_args()
    
    src = pathlib.Path(args.src)
    frames = [str(src / name) for name in glob.glob1(str(src), '*{}'.format(args.extension))]
    
    if len(frames) == 0:
        sys.exit('There are no frames of extension {} -- exiting.'.format(args.extension))
    
    if args.read_from:
        partitions = read_cuts(args.read_from, frames)
    else:
        partitions = divide(frames, args.write_to)
    
    pdb.set_trace() # This main() is used principally for debugging.

if __name__ == '__main__':
    main()