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
import logging
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

def claim_job(remote, partitions):
    for idx, partition in enumerate(partitions):
        if len(partition) == 0: continue # Edge case; this shouldn't happen
    
        placeholder = str(remote / 'partition_{}.plc'.format(idx))
        # Check if someone has already claimed this partition.
        if not os.path.isdir(placeholder):
            try:
                with open(placeholder, 'x') as handle:
                    handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
                
                logging.info('Partition claimed: {}:{}'.format(
                    os.path.basename(partition[0]), os.path.basename(partition[-1])))
                
                return idx, partition
                
            except FileExistsError:
                # We couldn't claim this partition, so try the next one.
                logging.debug('Already claimed: {}:{}; moving on...'.format(
                    os.path.basename(partition[0]), os.path.basename(partition[-1])))
                continue
    
    # There are no more jobs.
    return None, None

def run_job(idx, frames, resolution, style, remote, flow, local, put_thread):
    # Copy the relevant files into a local directory.
    # This is not efficient, but it makes working with the Torch script easier.
    processing = local / 'partition_{}'.format(idx)
    common.makedirs(processing)
    
    # Get a list of the indices of the frames we're manipulating.
    idys = sorted(list(map(int, [re.findall(r'\d+', os.path.basename(frame))[0] for frame in frames])))
    
    # Move all the frames to the processing folder.
    for frame in frames:
        newname = str(processing / os.path.basename(frame))
        shutil.copyfile(frame, newname)

    # The following are all arguments to be fed into the Torch script.
    
    # The pattern denoting the content images.
    input_pattern = str('..' / processing / FRAME_NAME)
    
    # The pattern denoting the optical flow images.
    # FIXME: Make sure that the optical flow files are transferred to the local partition.
    flow_pattern = str(flow / 'backward_[%d]_{%d}.flo')
    
    # The pattern denoting the consistency images (for handling potential occlusion).
    occlusions_pattern = str(flow / 'reliable_[%d]_{%d}.pgm')
    
    # The pattern denoting where and by what name the output PNG images should be deposited.
    output_prefix = str('..' / processing / OUTPUT_PREFIX)
    
    # Tell the algorithm to start at the beginning of this cut.
    continue_with = str(idys[0])

    # Run stylization.
    proc = subprocess.run([
        'th', 'fast_artistic_video.lua',
        '-input_pattern', input_pattern,
        '-flow_pattern', flow_pattern,
        '-occlusions_pattern', occlusions_pattern,
        '-output_prefix', output_prefix,
        '-model_vid', str('..' / style),
        '-continue_with', continue_with,
        '-new_cut', '1'
    ], cwd=str(pathlib.Path(os.getcwd()) / 'core'))
    logging.debug(' '.join(proc.args))
    
    # Upload the product of stylization to the remote directory.
    oldnames = sorted([str(processing / fname) for fname in glob.glob1(str(processing), '*.png')])
    newnames = [str(processing / (PREFIX_FORMAT % (idy))) for idy in idys]
    [shutil.move(oldname, newname) for oldname, newname in zip(oldnames, newnames)]
    
    logging.info('Uploading {} files...'.format(len(newnames)))
    complete = threading.Thread(target=common.upload_files, args=(newnames, remote))
    put_thread.append(complete)
    complete.start()

def stylize(resolution, style, partitions, remote, flow, local):
    # Sort in ascending order of length. This will mitigate the slowest-link effect of any weak nodes.
    # Sort in descending order of length. This will mitigate the slowdown caused by very large partitions.
    partitions = sorted(partitions, key=lambda x: len(x), reverse=True)
    
    running = []
    completing = []
    idx, partition = claim_job(remote, partitions)
    
    while partition is not None:
        # Style transfer is so computationally intense that threading it doesn't yield much time gain.
        run_job(idx, partition, resolution, style, remote, flow, local, completing)
        idx, partition = claim_job(remote, partitions)
    
    # Join all remaining threads.
    logging.info('Wrapping up threads for stylization...')
    for thread in completing:
        thread.join()
        