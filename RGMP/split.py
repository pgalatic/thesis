# author: Paul Galatic
#
# Program to

# STD LIB
import os
import time
import argparse

# REQUIRED LIB
import shutil
import cv2 as cv

# PROJECT LIB

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'

def log(s):
    '''More informative print debugging'''
    print('[%s]: %s' % (time.strftime(TIME_FORMAT, time.localtime()), str(s)))

def parse_args():
    '''Parses arguments'''
    parser = argparse.ArgumentParser()
    
    parser.add_argument('path', help='path to video')
    parser.add_argument('--invert', action='store_true', help='invert order of frames')
    
    return parser.parse_args()
    
def main():
    '''Driver program'''
    args = parse_args()
    log('Starting...')

    name = 'v_' + os.path.basename(args.path).split('.')[0]
    if not os.path.isdir(name):
        os.mkdir(name)
    cap = cv.VideoCapture(args.path)
    is_frame, frame = cap.read()
    count = 0
    while is_frame:
        cv.imwrite(os.path.join(name, f'{count:05}.png'), frame)
        is_frame, frame = cap.read()
        count += 1
    
    if args.invert:
        temp = 'temp'
        if not os.path.isdir(temp): os.mkdir(temp)
        frames = list(reversed([os.path.join(name, frame) for frame in os.listdir(name)]))
        for idx in range(len(frames)):
            os.rename(frames[idx], os.path.join(temp, f'{idx:05}.png'))
        frames = [os.path.join(temp, frame) for frame in os.listdir(temp)]
        for idx in range(len(frames)):
            os.rename(frames[idx], os.path.join(name, f'{idx:05}.png'))
        shutil.rmtree(temp)
    
    log('...finished.')
    return 0

if __name__ == '__main__':
    main()