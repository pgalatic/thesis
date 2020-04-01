# author: Paul Galatic
#
# Python wrapper for my thesis, "Divide and Conquer in Video Style Transfer,"
# which is based on the work Fast Artistic Videos by Manuel Ruder and Alexey 
# Dosovitskiy. It organizes and executes divide-and-conquer style transfer.

# STD LIB
import os
import pdb
import glob
import time
import pickle
import logging
import pathlib
import argparse
import platform
import threading

# EXTERNAL LIB

# LOCAL LIB
import cut
from const import *
from core import model, optflow, video, styutils

def wait_complete(tag, target, args, remote):
    '''
    A function used to ensure that only one of N nodes completes a given task.
    
    given:
        tag     -> (str) the name of the file results should be written to and
                    read from
        target  -> (func) the function that only one node should execute
        args    -> (list:Object) the arguments to feed into the target function
        remote  -> (pathlib.Path) the common directory where results should be 
                    written to and read from
    returns:
        (Object) the product of target given args, either as computed by the 
            current node or as read from the common directory
    '''
    # Try to create a placeholder so that two nodes don't try to do the same job at once.
    placeholder = str(remote / (tag + '.plc'))
    write_to = str(remote / tag)
    
    try:
        # If either of these exist, it means that the result is being worked on, and we should fall through.
        if os.path.exists(placeholder) or os.path.exists(write_to):
            raise FileExistsError('{} or {} already exist -- don\'t panic! Waiting for output...'.format(placeholder, write_to))
    
        # This will only succeed if this program successfully created the placeholder.
        with open(placeholder, 'x') as handle:
            handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
        
        logging.info('Job claimed: {}'.format(tag))
        # Run the function.
        result = target(*args)
        
        # Write the output to disk.
        with open(write_to, 'wb') as handle:
            if result != None:
                pickle.dump(result, handle)
            else:
                pickle.dump(tag, handle)
        
        return result
    except FileExistsError:
        # We couldn't claim that job, so WAIT until it's finished, then return None.
        logging.info('Job {} already claimed; waiting for output...'.format(tag))
        # Until the placeholder is gone, the file may still be incompletely uploaded.
        while os.path.exists(placeholder):
            time.sleep(1)
        
        try:
            with open(write_to, 'rb') as handle:
                return pickle.load(handle)
        except FileNotFoundError:
            # This error is more troublesome -- it means that the output file was 
            # deleted somehow. Still, we have to try and handle it gracefully, in 
            # case no file was needed in the first place.
            logging.error('ERROR! {} could not be loaded!'.format(write_to))
    finally:
        # Remove the placeholder in either case.
        if os.path.exists(placeholder):
            os.remove(placeholder)

def claim_job(remote, partitions):
    for idx, partition in enumerate(partitions):
        if len(partition) == 0:
            logging.error('Skipping a partition with length 0! Partition: {}'.format(idx))
            continue # Edge case; this shouldn't happen
    
        placeholder = str(remote / 'partition_{}.plc'.format(idx))
        # Check if someone has already claimed this partition.
        if not os.path.exists(placeholder):
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

def stylize(style, partitions, remote, fast):
    # Sort in descending order of length. This will mitigate the slowdown caused by very large partitions.
    # TODO Allow user to select sorting strategy
    partitions = sorted(partitions, key=lambda x: x[1] - x[0], reverse=True)
    
    running = []

    framefiles = sorted([str(remote / name) for name in glob.glob1(str(remote), '*.ppm')])
    stylizer = model.StylizationModel(weights_fname=str(style))
    partition = claim_job(remote, partitions)
    
    while partition is not None:
        frames_p = framefiles[partition[0]:partition[-1]]
        # Spawn a thread to complete that job, then get the next one.
        to_run = threading.Thread(
            target=stylizer.stylize, 
            args=(partition[0], frames_p, remote, fast))
        running.append(to_run)
        to_run.start()
        
        # If there isn't room in the jobs list, wait for a thread to finish.
        while len(running) >= MAX_STYLIZATION_JOBS:
            running = [thread for thread in running if thread.isAlive()]
            time.sleep(1)
        
        partition = claim_job(remote, partitions)
    
    # Finish any remaining optical flow, to help speed along other nodes, if necessary.
    if optflow.most_recent_optflow(remote) < styutils.count_files(remote, '.ppm'):
        for partition in partitions:
            frames_p = framefiles[partition[0]:partition[-1]]
            optflow.optflow(0, frames_p, remote, fast)
    
    # Join all remaining threads.
    logging.info('Wrapping up threads for stylization...')
    for thread in running:
        thread.join()

def parse_args():
    '''Parses arguments.'''
    ap = argparse.ArgumentParser()
    
    # Required arguments
    ap.add_argument('remote', type=str,
        help='The directory common to all nodes, e.g. out/.')
    ap.add_argument('video', type=str,
        help='The path to the stylization target, e.g. out/foo.mp4')
    ap.add_argument('style', type=str,
        help='The path to the model used for stylization, e.g. out/bar.pth')
    
    # Optional arguments
    ap.add_argument('--test', action='store_true',
        help='Test the algorithm by stylizing only a few frames of the video, rather than all of the frames.')
    ap.add_argument('--fast', action='store_true',
        help='Use Farneback optical flow, which is faster than the default, DeepFlow2.')
    ap.add_argument('--no_cuts', action='store_true',
        help='If a video has no cuts, use this to denote that and skip unnecessary computation.')
    ap.add_argument('--read_cuts', type=str, nargs='?', default=None,
        help='The .csv file containing frames that denote cuts. Computing cuts manually is always more accurate than an automatic assessment, if time permits. Use video.py to split frames for manual inspection. Use cut.py to compute and write cuts to disk. [None]')
    
    return ap.parse_args()

def main():
    '''Driver program.'''
    t_start = time.time()
    args = parse_args()
    styutils.start_logging()
    logging.info('\n-----START {} -----'.format(os.path.basename(args.video)))
    
    # Make output folder(s), if necessary
    remote = pathlib.Path(args.remote) / os.path.basename(os.path.splitext(args.video)[0])
    styutils.makedirs(remote)
    
    # Split video into individual frames
    wait_complete(SPLIT_TAG, video.split_frames, [args.video, remote], remote)
    frames = sorted([str(remote / frame) for frame in glob.glob1(str(remote), '*.ppm')])
    
    # Make sure we only test on a small number of files, if we are testing.
    if args.test:
        to_remove = frames[NUM_FRAMES_FOR_TEST:]
        frames = frames[:NUM_FRAMES_FOR_TEST]
        for frame in to_remove:
            os.remove(frame)
    
    # Either read the cuts from disk or compute them manually (if applicable).
    if args.no_cuts:
        partitions = [(0, len(frames))]
    elif args.read_cuts:
        partitions = cut.read_cuts(args.read_cuts, len(frames))
    elif args.test:
        # use different-size partitions to test sorting
        q1 = (NUM_FRAMES_FOR_TEST // 4) 
        q2 = (NUM_FRAMES_FOR_TEST // 3)
        q3 = (NUM_FRAMES_FOR_TEST // 2)
        partitions = [(0, q1), (q1, q2), (q2, q3), (q3, None)]
    else:
        partitions = wait_complete(DIVIDE_TAG, cut.divide, [args.video, len(frames)], remote)
    
    # Record the time between the start of the program and preliminary setup.
    t_prelim = time.time()
    logging.info('{} seconds\tpreliminary setup'.format(round(t_prelim - t_start)))
    
    # Compute neural style transfer.
    stylize(args.style, partitions, remote, args.fast)
    # Wait until all output files are present.
    logging.info('Waiting for other nodes to finish stylization...')
    while len(glob.glob1(str(remote), '*.png')) < len(frames):
        time.sleep(1)
    
    # Record the time between the optflow calculations and completing stylization.
    t_stylize = time.time()
    logging.info('{} seconds\tstylization'.format(round(t_stylize - t_prelim)))
    
    # Combining frames into a final video won't work if we're testing on only a portion of the frames.
    if not args.test:
        wait_complete(COMBINE_TAG, video.combine_frames, [args.video, remote], remote)
    
    # Clean up any lingering files.
    for fname in [str(remote / name) for name in glob.glob1(str(remote), '*.pkl')]:
        os.remove(fname)
    for fname in [str(remote / name) for name in glob.glob1(str(remote), '*.ppm')]:
        os.remove(fname)
    #for fname in [str(remote / name) for name in glob.glob1(str(remote), '*.plc')]:
    #    os.remove(fname)
    #for fname in [str(remote / name) for name in glob.glob1(str(remote), '*.png')]:
    #    os.remove(fname)
    
    # Log all the times for good measure.
    t_end = time.time()
    logging.info('====TIMES====')
    logging.info('{} seconds\tpreliminary setup'.format(round(t_prelim - t_start)))
    logging.info('{} seconds\tstylization'.format(round(t_stylize - t_prelim)))
    logging.info('{} seconds\twrapping up'.format(round(t_end - t_stylize)))
    logging.info('{} seconds\tTOTAL'.format(round(t_end - t_start)))
    logging.info('=============')
    logging.info('\n------END-----\n')

if __name__ == '__main__':  
    main()