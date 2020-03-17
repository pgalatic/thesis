# author: Paul Galatic
#
# Organizes and executes divide-and-conquer style transfer.

# STD LIB
import re
import os
import pdb
import glob
import time
import logging
import pathlib
import argparse
import platform
import threading

# EXTERNAL LIB

# LOCAL LIB
import cut
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

def doublesort(fnames):
    # End me.
    return sorted(sorted(fnames), key=lambda y: len(y) if y else -1)

def stylize(style, partitions, remote, local):
    # Sort in ascending order of length. This will mitigate the slowest-link effect of any weak nodes.
    # Sort in descending order of length. This will mitigate the slowdown caused by very large partitions.
    # Don't sort at all.
    # partitions = sorted(partitions, key=lambda x: len(x), reverse=True)
    
    running = []
    completing = []
    framefiles = sorted([str(local / name) for name in glob.glob1(str(local), '*.ppm')])
    # First flow/cert doesn't exist, so use None as a placeholder
    flowfiles = [None] + doublesort([str(remote / name) for name in glob.glob1(str(remote), 'backward*.flo')])
    certfiles = [None] + doublesort([str(remote / name) for name in glob.glob1(str(remote), 'reliable*.pgm')])
    
    # Sanity checks
    assert(len(framefiles) > 0 and len(flowfiles) > 0 and len(certfiles) > 0 
            and len(framefiles) == len(flowfiles) and len(flowfiles) == len(certfiles))
    
    stylizer = core.StylizationModel(str(style))
    partition = claim_job(remote, partitions)
    
    while partition is not None:
        frames_p = framefiles[partition[0]:partition[-1]]
        flows_p = flowfiles[partition[0]:partition[-1]]
        certs_p = certfiles[partition[0]:partition[-1]]
        pdb.set_trace()
        
        # Spawn a thread to complete that job, then get the next one.
        to_run = threading.Thread(
            target=run_job, 
            args=(stylizer, frames_p, flows_p, certs_p, remote, local, completing))
        running.append(to_run)
        to_run.start()
        
        # If there isn't room in the jobs list, wait for a thread to finish.
        while len(running) >= MAX_STYLIZATION_JOBS:
            running = [thread for thread in running if thread.isAlive()]
            time.sleep(1)
        
        partition = claim_job(remote, partitions)
    
    # Join all remaining threads.
    logging.info('Wrapping up threads for stylization...')
    for thread in completing:
        thread.join()

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    ap.add_argument('src', type=str,
        help='The directory in which the .ppm files are stored.')
    ap.add_argument('dst', type=str,
        help='The directory in which to place the .flo, .pgm files.')
    ap.add_argument('style', type=str,
        help='The path to the model used for stylization as it would appear on the common directory, e.g. \\mnt\\o\\foo\\bar.pth')
        
    # Optional arguments
    ap.add_argument('--no_cuts', action='store_true',
        help='Use for videos that have no cuts.')
    ap.add_argument('--read_cuts', type=str, nargs='?', default=None,
        help='The .csv file containing frames that denote cuts. Computing cuts manually is always more accurate than an automatic assessment, if time permits. Use video.py to split frames for manual inspection. [None]')
    
    return ap.parse_args()

def main():
    args = parse_args()
    common.start_logging()
    
    src = pathlib.Path(args.src)
    dst = pathlib.Path(args.dst)
    style = pathlib.Path(args.style)
    
    frames = sorted([str(src / frame) for frame in glob.glob1(str(src), '*.ppm')])
    
    # Either read the cuts from disk or compute them manually (if applicable).
    if args.no_cuts:
        partitions = [(0, None)]
    elif args.read_cuts:
        partitions = cut.read_cuts(args.read_cuts, frames)
    elif args.test:
        midpoint = NUM_FRAMES_FOR_TEST // 2
        partitions = [(0, midpoint), (midpoint, None)]
    else:
        partitions = cut.divide(frames, args.write_cuts)
    
    stylize(args.style, partitions, dst, src)

if __name__ == '__main__':
    main()
