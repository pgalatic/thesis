from __future__ import division

# general libs
import cv2
from PIL import Image
import numpy as np
import argparse
import os
import time

# torch libs
import torch
from torch.autograd import Variable
from torch.utils import data
import torch.nn as nn
import torch.nn.functional as functional
import torch.nn.init as init
import torch.utils.model_zoo as model_zoo
from torchvision import models

# custom libs
from model import RGMP
from utils import ToCudaVariable, ToLabel, DAVIS, upsample, downsample

# set paths
DAVIS_ROOT = 'davis-2017/data/DAVIS/'
palette = Image.open(DAVIS_ROOT + 'Annotations/480p/bear/00000.png').getpalette()

def get_arguments():
    parser = argparse.ArgumentParser(description="RGMP")
    parser.add_argument("-multi", action="store_true", help="Multi-object")
    return parser.parse_args()
    
def Encode_MS(curr, prev, scales):
    '''
    This function encodes the mask of the first frame so that it is usable by
    the rest of the program (as a reference, or 'ref').
    '''
    ref = {}
    # For each scale, apply downsampling (if necessary) and then convert to an 
    # encoded CUDA variable.
    for scale in scales:
        if scale != 1.0:
            curr_m, prev_m = downsample([curr, prev], scale)
            curr_m, prev_m = ToCudaVariable([curr_m, prev_m], volatile=True)
            ref[scale] = model.module.Encoder(curr_m, prev_m)[0]
        else:
            curr_m, prev_m = ToCudaVariable([curr, prev], volatile=True)
            ref[scale] = model.module.Encoder(curr_m, prev_m)[0]

    return ref

def Propagate_MS(ref, curr, prev, scales):
    '''
    This function uses the mathematics described in the paper to propagate the
    mask from the previous frame to the new frame.
    '''
    height, width = curr.size()[2], curr.size()[3]
    result_vals = {}
    # We apply the algorithm to several scales (all <= 1.0) and apply 
    # downsampling as necessary to achieve desired results.
    for scale in scales:
        if scale != 1.0:
            # downsample both frames and store them in a temporary variable
            curr_m, prev_m = downsample([curr, prev], scale)
            # turn them into tensors
            curr_m, prev_m = ToCudaVariable([curr_m, prev_m], volatile=True)
            # use the custom Encoder class to perform convolutions
            r_512, r_256, r_128, r_64 = model.module.Encoder(curr_m, prev_m)
            # use the custom Decoder class to get a preliminary result
            preliminary = model.module.Decoder(r_512, ref[scale], r_256, r_128, r_64)
            # set the result value for the scale we're working with
            result_vals[scale] = upsample(functional.softmax(preliminary[0], dim=1)[:,1].data.cpu(), (height, width))
        else:
            # same as above, but with the scale at 1.0
            curr_m, prev_m = ToCudaVariable([curr, prev], volatile=True)
            r_512, r_256, r_128, r_64 = model.module.Encoder(curr_m, prev_m)
            preliminary = model.module.Decoder(r_512, ref[scale], r_256, r_128, r_64)
            result_vals[scale] = functional.softmax(preliminary[0], dim=1)[:,1].data.cpu()

    # Create a tensor and fill it with the average of the results
    result = torch.zeros(prev.size())
    for scale in scales:
        result += result_vals[scale]
    result /= len(scales)
    return result


def Infer_SO(frames, masks, num_frames, scales=[0.5, 0.75, 1.0]):

    # Create a tensor with the same shape as the frames we're analyzing, 
    # because when we segment the image we want the result to be the same size
    # as our input
    results = torch.zeros(masks.size())
    results[:,:,0] = masks[:,:,0]

    # Encode the mask of the frames
    ref = Encode_MS(frames[:,:,0], results[:,0,0], scales)
    
    # For each frame, propagate the mask over the image according to the
    # algorithm's perception of how the target is moving
    for frame in range(0, num_frames-1):
        results[:,0,frame+1] = Propagate_MS(ref, frames[:,:,frame+1], results[:,0,frame], scales)

    return results

def Infer_MO(frames, masks, num_frames, num_objects, scales=[0.5, 0.75, 1.0]):
    
    # If the number of objects we're segmenting is 1, then we don't need to do 
    # any new-fangled multi-object segmentation. Stick with single-object 
    
    if num_objects == 1:
        result = Infer_SO(frames, masks, num_frames, scales=scales) #1,1,t,h,w
        return torch.cat([1 - result, result], dim=1)

    # Create a tensor with the same size as the image
    _, num_obj, time, height, width = masks.size()
    results = torch.zeros((1, num_obj+1, time, height, width))
    results[:,1:,0] = masks[:,:,0]
    results[:,0,0] = 1 - torch.sum(masks[:,:,0], dim=1)

    ref_bg = Encode_MS(frames[:,:,0], torch.sum(results[:,1:,0], dim=1), scales)
    refs = []
    for obj in range(num_objects):
        refs.append(Encode_MS(frames[:,:,0], results[:,obj+1,0], scales))

    for frame in range(0, num_frames-1):
        # 1 - all 
        results[:,0,frame+1] = 1-Propagate_MS(ref_bg, frames[:,:,frame+1], torch.sum(results[:,1:,frame], dim=1), scales)
        for obj in range(num_objects):
            results[:,obj+1,frame+1] = Propagate_MS(refs[obj], frames[:,:,frame+1], results[:,obj+1,frame], scales)

        # Normalize by softmax
        results[:,:,frame+1] = torch.clamp(results[:,:,frame+1], 1e-7, 1-1e-7)
        results[:,:,frame+1] = torch.log((results[:,:,frame+1] /(1-results[:,:,frame+1])))
        results[:,:,frame+1] = functional.softmax(Variable(results[:,:,frame+1]), dim=1).data

    return results

if __name__ == '__main__':
    args = get_arguments()

    # There are two options: Segment on just one object, or segment on several
    # objects at the same time. Either way, we use a special method to load the
    # DAVIS dataset and then move on.
    if args.multi:
        print('Multi-object VOS on DAVIS-2017 valildation')
        Testset = DAVIS(DAVIS_ROOT, imset='2017/test-dev.txt', multi_object=True)
        Testloader = data.DataLoader(Testset, batch_size=1, shuffle=False, num_workers=2, pin_memory=True)
    else:
        print('Single-object VOS on DAVIS-2017 valildation')
        Testset = DAVIS(DAVIS_ROOT, imset='2017/test-dev.txt')
        Testloader = data.DataLoader(Testset, batch_size=1, shuffle=False, num_workers=2, pin_memory=True)

    # if we can, use the most efficient hardware
    model = nn.DataParallel(RGMP())
    if torch.cuda.is_available():
        model.cuda()

    # load the model, using the CPU because I'm not rich
    model.load_state_dict(torch.load('weights.pth', map_location='cpu'))
    print('Model loaded')

    model.eval() # turn-off BN
    
    # Enumerate through all of the sets of training data
    for seq, (frames, masks, info) in enumerate(Testloader):
        # Extract from the enumeration the information we need to perform the 
        # evaluation
        frames, masks = frames[0], masks[0]
        video_name = info['name'][0]
        num_frames = info['num_frames'][0]
        num_objects = info['num_objects'][0]
        print(video_name)

        # Use the model to segment the video frame-by-frame
        start = time.time()
        results = Infer_MO(frames, masks, num_frames, num_objects, scales=[0.5, 0.75, 1.0])
        print('{} | num_objects: {}, FPS: {}'.format(video_name, num_objects, (time.time() - start)/num_frames))

        # Save results for quantitative eval
        if args.multi:
            folder = 'results/MO'
        else:
            folder = 'results/SO'
        
        test_path = os.path.join(folder, video_name)
        if not os.path.exists(test_path):
            os.makedirs(test_path)

        # Save each frame to the designated directory
        for frame in range(num_frames):
            result = results[0,:,frame].numpy()
            # make hard label
            result = ToLabel(result)
            
            # Add padding if necessary
            (lhp,uhp), (lwp,uwp) = info['pad']
            result = result[lhp[0]:-uhp[0], lwp[0]:-uwp[0]]

            result_img = Image.fromarray(result)
            # put a standard palatte on the mask (to make it easier to read)
            result_img.putpalette(palette)
            result_img.save(os.path.join(test_path, '{:05d}.png'.format(frame)))

