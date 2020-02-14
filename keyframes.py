# author: Paul Galatic
#
# Computes keys given a video.

# STD LIB
import os
import pdb
import sys
import glob
import pathlib
import argparse
from statistics import mean

# EXTERNAL LIB
import numpy as np
from PIL import Image

# LOCAL LIB
import common
from const import *

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('src', type=str, nargs='?', default=None,
        help='The path to the folder in which the frames are contained.')
    
    # Optional arguments
    
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

def divide(frames):
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
    # Partitions are a list of lists of frame filenames.
    partitions = [frames[idx:idy] for idx, idy in zip([0] + keys, keys + [None])]
    
    print('Number of partitions: {}'.format(len(partitions)))
    print('Average partition length: {}'.format(mean([len(partition) for partition in partitions])))
    
    return partitions

def main():
    args = parse_args()
    
    src = pathlib.Path(args.src)
    
    frames = [str(src / name) for name in glob.glob1(str(src), '*.ppm')]
    partitions = divide(frames)
    
    pdb.set_trace() # This main() is used principally for debugging.

if __name__ == '__main__':
    main()