# author: Paul Galatic
#
# Organizes and executes divide-and-conquer style transfer.

# STD LIB
import re
import os
import pdb
import glob
import time
import shutil
import pathlib
import platform
import threading
import subprocess

# EXTERNAL LIB
import numpy as np
from PIL import Image

# LOCAL LIB
import common
from const import *

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
        dists.append((frame1, frame2, idx, dist_func(frame1, frame2)))
    # Sort in descending order by the distance between frames.
    return sorted(dists, key=lambda x: x[-1], reverse=True)

def divide(frames):
    dists = get_dists(frames, kl_dist) # Change the second parameter to change the distance metric.
    # Loop until the "knee point" where keyframe candidates become more similar is reached.
    total_divergence = EPSILON
    keyframes = []
    for dist in dists:
        if dist[-1] / total_divergence < KNEE_THRESHOLD:
            break
        total_divergence += dist[-1]
        keyframes.append(dist[2])
    # Use the keyframes to compute partitions, then return the partitions.
    keyframes = sorted(keyframes)
    # Partitions are a list of lists of frame filenames.
    partitions = [frames[idx:idy] for idx, idy in zip([0] + keyframes, keyframes + [None])]
    return partitions

def claim_job(remote, start_at, partitions):
    for idx, partition in enumerate(partitions[start_at:]):
        if len(partition) == 0: continue
    
        placeholder = str(remote / 'partition_{}.plc'.format(idx))
        try:
            with open(placeholder, 'x') as handle:
                handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
            
            print('Partition claimed: {}:{}'.format(
                os.path.basename(partition[0]), os.path.basename(partition[-1])))
            
            return idx, partition
            
        except FileExistsError:
            # We couldn't claim this partition, so try the next one.
            continue
    
    # There are no more jobs.
    return None, None

def run_job(idx, frames, style, resolution, remote, local):
    # Copy the relevant files into a local directory.
    # This is not efficient, but it makes working with the Torch script easier.
    processing = local / 'processing_{}'.format(idx)
    idys = list(map(int, [re.findall(r'\d+', frame)[0] for frame in frames]))
    if not os.path.isdir(str(processing)):
        os.makedirs(str(processing))
    for idy, frame in enumerate(frames):
        newname = str(processing / (FRAME_NAME % (idy + 1)))
        shutil.copyfile(frame, newname)

    # The following are all arguments to be fed into the Torch script.
    
    # The pattern denoting the content images.
    input_pattern = str('..' / processing / FRAME_NAME)
    
    # The pattern denoting the optical flow images.
    flow_pattern = str('..' / remote / ('flow_' + resolution) / 'backward_[%d]_{%d}.flo')
    
    # The pattern denoting the consistency images (for handling potential occlusion).
    occlusions_pattern = str('..' / remote / ('flow_' + resolution) / 'reliable_[%d]_{%d}.pgm')
    
    # The pattern denoting where and by what name the output PNG images should be deposited.
    output_prefix = str('..' / processing / OUTPUT_PREFIX)
    
    # We are using the default, slow backend for now.
    backend = 'nn'
    use_cudnn = '0'
    gpu_num = '-1'
    # TODO: GPU/CUDA support
    # backend = args.gpu_lib if int(args.gpu_num) > -1 else 'nn'
    # use_cudnn = '1' if args.gpu_lib == 'cudnn' and int(args.gpu_num) > -1 else '0'

    # Run stylization.
    proc = subprocess.Popen([
        'th', 'fast_artistic_video.lua',
        '-input_pattern', input_pattern,
        '-flow_pattern', flow_pattern,
        '-occlusions_pattern', occlusions_pattern,
        '-output_prefix', output_prefix,
        '-use_cudnn', use_cudnn,
        '-gpu', gpu_num,
        '-model_vid', '../' + style,
        '-model_img', 'self'
    ], cwd=str(pathlib.Path(os.getcwd()) / 'core'))
    # print(' '.join(proc.args))
    proc.wait()
    
    status = proc.wait(TIMEOUT)
    # Upload the product of stylization to the remote directory every TIMEOUT seconds.
    oldnames = sorted([str(processing / fname) for fname in glob.glob1(str(processing), '*.png')])
    newnames = [str(processing / (PREFIX_FORMAT % (idy + 1))) for idy in idys]
    [shutil.move(oldname, newname) for oldname, newname in zip(oldnames, newnames)]
    
    print('Uploading {} files...'.format(len(newnames)))
    threading.Thread(target=common.upload_files, args=(newnames, remote)).start()

def stylize(style, resolution, remote, local):
    # Find keyframes and use those as delimiters.
    frames = [str(local / frame) for frame in glob.glob1(str(local), '*.ppm')]
    partitions = common.wait_complete(DIVIDE_TAG, divide, [frames], remote)
    
    running = []
    last_idx, partition = claim_job(remote, 0, partitions)
    
    while partition is not None:
        # Style transfer is so computationally intense that threading it doesn't yield much time gain.
        run_job(last_idx, partition, style, resolution, remote, local)
        last_idx, partition = claim_job(remote, last_idx, partitions)
    
    # Remove the partitioning file if it still exists (is this necessary?).
    if os.path.exists(DIVIDE_TAG):
        os.remove(DIVIDE_TAG)
        