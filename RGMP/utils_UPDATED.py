from __future__ import division
import torch
from torch.autograd import Variable
from torch.utils import data

import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init
import torch.utils.model_zoo as model_zoo
from torchvision import models

# general libs
import cv2
# import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import math
import time
import tqdm
import os
import random
import argparse
import glob

def ToLabel(img):
    '''Converts an image into an image of labels.'''
    fgs = np.argmax(img, axis=0).astype(np.float32)
    return fgs.astype(np.uint8)

def ToCudaVariable(vars, volatile=False):
    '''Transform a set of variables into Cuda variables.'''
    if torch.cuda.is_available():
        return [Variable(var.cuda(), volatile=volatile) for var in vars]
    else:
        return [Variable(var, volatile=volatile) for var in vars]

def upsample(img, size):
    '''Applies linear interpolation to upscale an image.'''
    img = img.numpy()[0]
    dsize = (size[1], size[0])
    img = cv2.resize(img, dsize=dsize, interpolation=cv2.INTER_LINEAR)
    return torch.unsqueeze(torch.from_numpy(img), dim=0)

def downsample(imgs, scale):
    '''Applies linear interpolation to downscale images.'''
    if scale == 1:
        return imgs

    # find new size dividable by 32
    height = imgs[0].size()[2] 
    width = imgs[0].size()[3]
    
    # get the new dimensions of the downsampled image
    new_h = int(height * scale)
    new_w = int(width * scale) 
    new_h = new_h + 32 - new_h % 32
    new_w = new_w + 32 - new_w % 32

    # new dims
    dsize = (new_w, new_h)
    results = []
    
    # downsample each image according to the specs above
    for img in imgs:
        img = img.numpy()[0]
        if img.ndim == 3:
            img = np.transpose(img, [1,2,0])
            img = cv2.resize(img, dsize=dsize, interpolation=cv2.INTER_LINEAR)
            img = np.transpose(img, [2,0,1])
        else:
            img = cv2.resize(img, dsize=dsize, interpolation=cv2.INTER_LINEAR)

        results.append(torch.unsqueeze(torch.from_numpy(img), dim=0))

    return results


class DAVIS(data.Dataset):
    '''
    Loads the DAVIS dataset, and only the DAVIS dataset. Not any other dataset.
    If you want to use this program, you better figure out the DAVIS dataset 
    and make your data blend with the DAVIS dataset like a clown at clown 
    college.
    '''
    def __init__(self, root, imset='2016/val.txt', resolution='480p', multi_object=False):
        # There are three folders we pay attention to: Annotations, 
        # JPEGImages, and ImageSets.
        self.root = root
        self.mask_dir = os.path.join(root, 'Annotations', resolution)
        self.image_dir = os.path.join(root, 'JPEGImages', resolution)
        _imset_dir = os.path.join(root, 'ImageSets')
        _imset_f = os.path.join(_imset_dir, imset)
        # Annotations contains folders. Each folder contains a sequence of .jpg
        # files that are the ground-truth segmentation masks of the data.
        
        # JPEGImages contains folders. Each folder contains a sequence of .jpg 
        # files, each one a frame in a video.
        
        # ImageSets contains three files that denote which folders in 
        # Annotations and JPEGImages are training, test, and validation.
        self.videos = []
        self.num_frames = {}
        self.num_objects = {}
        self.shape = {}
        # This code grabs all that info and tosses it into one big 'ol 
        # dictionary.
        with open(os.path.join(_imset_f), "r") as lines:
            for line in lines:
                _video = line.rstrip('\n')
                self.videos.append(_video)
                self.num_frames[_video] = len(glob.glob(os.path.join(self.image_dir, _video, '*.jpg')))
                _mask = np.array(Image.open(os.path.join(self.mask_dir, _video, '00000.png')).convert("P"))
                self.num_objects[_video] = np.max(_mask)
                self.shape[_video] = np.shape(_mask)
        
        # I can't believe this warning wasn't in place when I got here!
        # If the frames aren't in the PRECISELY CORRECT FORMAT, they will be
        # skipped, which will cause a bizarre tensor size error later.
        for key in self.num_frames.keys():
            if self.num_frames[key] < 1:
                print('WARN: {key} does not have any frames.'.format(key=key))

        self.MO = multi_object

    def __len__(self):
        return len(self.videos)

    def __getitem__(self, index):
        # The dataset is organized into layers, which each layer being a 
        # different set of frames and its annotated masks. This function gets 
        # the next set of frames/mask(s) and returns them.
        video = self.videos[index]
        info = {}
        info['name'] = video
        info['num_frames'] = self.num_frames[video]
        if self.MO:
            num_objects = self.num_objects[video]
        else:
            num_objects = 1
        info['num_objects'] = num_objects

        # Convert the frames and masks into a format/size that is usable by the
        # rest of the program, particularly the artificial neural network.
        raw_frames = np.empty((self.num_frames[video],)+self.shape[video]+(3,), dtype=np.float32)
        raw_masks = np.empty((self.num_frames[video],)+self.shape[video], dtype=np.uint8)
        
        # For each frame, convert it into a usable format.
        for frame in range(self.num_frames[video]):
            img_file = os.path.join(self.image_dir, video, '{:05d}.jpg'.format(frame))
            try:
                raw_frames[frame] = np.array(Image.open(img_file).convert('RGB'))/255.
            except ValueError:
                # We can't process files that are too big or are otherwise lopsided.
                img = Image.open(img_file).resize((360, 640))
                raw_frames[frame] = np.array(img.convert('RGB'))/255.

            try:
                # always return first frame mask
                mask_file = os.path.join(self.mask_dir, video, '{:05d}.png'.format(frame))
                raw_mask = np.array(Image.open(mask_file).convert('P'), dtype=np.uint8)
            except:
                mask_file = os.path.join(self.mask_dir, video, '00000.png')
                raw_mask = np.array(Image.open(mask_file).convert('P'), dtype=np.uint8)

            # Depending on whether or not we are using multi object 
            # segmentation, format the mask slightly differently
            if self.MO:
                raw_masks[frame] = raw_mask
            else:
                raw_masks[frame] = (raw_mask != 0).astype(np.uint8)
            
        # make One-hot channel is object index
        oh_masks = np.zeros((self.num_frames[video],)+self.shape[video]+(num_objects,), dtype=np.uint8)
        for o in range(num_objects):
            oh_masks[:,:,:,o] = (raw_masks == (o+1)).astype(np.uint8)

        # padding size to be divide by 32
        _, height, width, _ = oh_masks.shape
        new_h = height + 32 - height % 32
        new_w = width + 32 - width % 32
        # Add padding according to necessity
        # lhp -- lower height padding
        # uhp -- upper height padding
        # lwp -- lower width padding
        # uwp -- upper width padding
        lhp, uhp = (new_h-height) / 2, (new_h-height) / 2 + (new_h-height) % 2
        lwp, uwp = (new_w-width) / 2, (new_w-width) / 2 + (new_w-width) % 2
        lhp, uhp, lwp, uwp = int(lhp), int(uhp), int(lwp), int(uwp)
        pad_masks = np.pad(oh_masks, ((0, 0), (lhp,uhp), (lwp, uwp), (0, 0)), mode='constant')
        pad_frames = np.pad(raw_frames, ((0, 0), (lhp,uhp), (lwp, uwp), (0, 0)), mode='constant')
        info['pad'] = ((lhp, uhp), (lwp, uwp))

        th_frames = torch.unsqueeze(torch.from_numpy(np.transpose(pad_frames, (3, 0, 1, 2)).copy()).float(), 0)
        th_masks = torch.unsqueeze(torch.from_numpy(np.transpose(pad_masks, (3, 0, 1, 2)).copy()).long(), 0)
        
        return th_frames, th_masks, info