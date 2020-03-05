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
from core import core
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
                
                logging.info(str(remote / 'partition_{}.plc claimed\t[{}:{}]'.format(
                    idx, partition[0], partition[1])))
                return partition
                
            except FileExistsError:
                # We couldn't claim this partition, so try the next one.
                logging.debug('Partition {} alraedy claimed; moving on...'.format(idx))
                continue
    
    # There are no more jobs.
    return None

def run_job(stylizer, framefiles, flowfiles, certfiles, remote, local, completing):
    idys = sorted(list(map(int, [re.findall(r'\d+', os.path.basename(fname))[0] for fname in framefiles])))
    
    stylizer.stylize(framefiles, flowfiles, certfiles, out_dir=str(local))
    
    # Upload the product of stylization to the remote directory as necessary.
    products = [str(local / (OUTPUT_FORMAT % (idy))) for idy in idys]
    
    logging.info('Uploading {} files...'.format(len(products)))
    complete = threading.Thread(target=common.upload_files, args=(products, remote))
    completing.append(complete)
    complete.start()

def stylize(style, partitions, remote, local):
    # Sort in ascending order of length. This will mitigate the slowest-link effect of any weak nodes.
    # Sort in descending order of length. This will mitigate the slowdown caused by very large partitions.
    partitions = sorted(partitions, key=lambda x: len(x), reverse=True)
    
    running = []
    completing = []
    framefiles = sorted([str(local / name) for name in glob.glob1(str(local), '*.ppm')])
    # First flow/cert doesn't exist, so use None as a placeholder
    flowfiles = [None] + sorted([str(remote / name) for name in glob.glob1(str(remote), 'backward*.flo')])
    certfiles = [None] + sorted([str(remote / name) for name in glob.glob1(str(remote), 'reliable*.pgm')])
    stylizer = core.StylizationModel(str(style))
    
    partition = claim_job(remote, partitions)
    
    while partition is not None:
        frames_p = framefiles[partition[0]:partition[-1]]
        flows_p = flowfiles[partition[0]:partition[-1]]
        certs_p = certfiles[partition[0]:partition[-1]]
        
        # Spawn a thread to complete that job, then get the next one.
        running.append(threading.Thread(
            target=run_job, 
            args=(stylizer, frames_p, flows_p, certs_p, remote, local, completing)))
        running[-1].start()
        
        # If there isn't room in the jobs list, wait for a thread to finish.
        while len(running) >= MAX_STYLIZATION_JOBS:
            running = [thread for thread in running if thread.isAlive()]
            time.sleep(1)
        
        partition = claim_job(remote, partitions)
    
    # Join all remaining threads.
    logging.info('Wrapping up threads for stylization...')
    for thread in completing:
        thread.join()
        