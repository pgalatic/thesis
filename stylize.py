# author: Paul Galatic
#
# Organizes and executes divide-and-conquer style transfer.

# STD LIB
import pdb
import subprocess

# EXTERNAL LIB
import cv2
import numpy as np
from PIL import Image

# LOCAL LIB
import common
from const import *

def kl_divergence(p, q):
    # As implemented in "KL Divergence Python Example" by Cory Malkin (2019).
    # https://towardsdatascience.com/kl-divergence-python-example-b87069e4b810
    return np.sum(np.where(p != 0, p * np.log(p / q), 0))

def kl_dist(array1, array2):
    # Uses Kullback-Liebler divergence as in Courbon et al. (2010).
    # http://www.sciencedirect.com/science/article/pii/S0967066110000808
    
    array1 = np.asarray(Image.open(frame1))
    array2 = np.asarray(Image.open(frame2))
    
    hist1 = array1.mean(axis=2).flatten()
    hist2 = array2.mean(axis=2).flatten()
    
    return kl_divergence(hist1, hist2)

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
    pdb.set_trace() # Check to see if the keyframes in the dists are legitimate.
    # Loop until the "knee point" where keyframe candidates become more similar is reached.
    total_divergence = 0
    partitions = []
    for dist in dists:
        if dist[-1] / total_divergence < KNEE_THRESHOLD:
            break
        total_divergence += dist[-1]
        keyframes.append(dist[2])
    # Use the keyframes to compute partitions, then return the partitions.
    keyframes = sorted(keyframes)
    # Partitions are a tuple of (start, end, [frames]).
    partitions = [(idx, idy, frames[idx:idy]) for idx, idy in zip([0] + keyframes, keyframes + [None])]
    pdb.set_trace() # DEBUG Verify that these partitions are legitimate.
    return partitions

def claim_job(start_at, partitions):
    for idx, partition in enumerate(partitions[start_at:]):
        placeholder = 'partition_{}.plc'.format(idx)
        try:
            with open(placeholder, 'x') as handle:
                handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
            
            return idx, partition
            
        except FileExistsError:
            # We couldn't claim this partition, so try the next one.
            continue
    
    # There are no more jobs.
    return None, None

def run_job(start, end, resolution, remote, local):
    # The following are all arguments to be fed into the Torch script.
    input_pattern = str('..' / local / FRAME_NAME)
    flow_pattern = str('..' / remote / ('flow_' + resolution) / 'backward_[%d]_{%d}.flo')
    occlusions_pattern = str('..' / remote / ('flow_' + resolution) / 'reliable_[%d]_{%d}.pgm')
    output_prefix = str('..' / local / 'out')
    backend = 'nn'
    use_cudnn = '0'
    # TODO: GPU/CUDA support
    # backend = args.gpu_lib if int(args.gpu_num) > -1 else 'nn'
    # use_cudnn = '1' if args.gpu_lib == 'cudnn' and int(args.gpu_num) > -1 else '0'

    # Run stylization.
    proc = subprocess.Popen([
        'th', 'fast_artistic_video.lua',
        '-start_at', str(start),
        '-end_at', str(end),
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
    
    # Upload the product of stylization to the remote directory.
    fnames = [str(local / fname) for fname in glob.glob1(str(local), '*.png')]
    threading.Thread(target=common.upload_files, args=(fnames, remote)).start()

def stylize(resolution, remote, local):
    # Find keyframes and use those as delimiters.
    frames = [str(local / frame) for frame in glob.glob1(str(local), '*.ppm')]
    common.wait_complete(DIVIDE_TAG, divide, frames, remote)
    partitions = common.read_tag(DIVIDE_TAG, remote)
    
    running = []
    last_partition, job = claim_job(0, partitions)
    
    while job is not None:
        # If there isn't room in the jobs list, wait for a thread to finish.
        while len(running) > MAX_STYLIZE_JOBS:
            running = [thread for thread in running if thread.isAlive()]
            time.sleep(1)
        # Spawn a thread to complete that job, then get the next one.
        running.append(threading.Thread(target=run_job, 
            args=(job[0], job[1], resolution, remote, local)))
        running[-1].start()
        last_partition, job = claim_job(last_partition, partitions)
        