# author: Paul Galatic
#
# Program to assemble frames produced by other algorithms

# STD LIB
import os
import time
import argparse
from pathlib import Path

# REQUIRED LIB
import cv2 as cv
import numpy as np

# PROJECT LIB

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'
ORIG = 'original'
MASK = 'mask'
STYL = 'style'
OUT = 'output'
ZERO = np.array([0, 0, 0])

def log(*args):
    '''More informative print debugging'''
    t = time.strftime(TIME_FORMAT, time.localtime())
    s = ' '.join([str(arg) for arg in args])
    print(f'[{t}]: {s}')

def parse_args():
    '''Parses arguments'''
    ap = argparse.ArgumentParser()
    
    ap.add_argument('src', help='source directory (contains original, masks, and stylized)')
    
    return ap.parse_args()
    
def main():
    '''Driver program'''
    args = parse_args()
    log('Starting...')
    
    DIR = Path(args.src)
    valid = (   os.path.isdir(str(DIR/ORIG)) and 
                os.path.isdir(str(DIR/MASK)) and 
                os.path.isdir(str(DIR/STYL)) )
    if not valid:
        raise Exception('A directory is missing in the src folder!')
    DIR_ORIG = DIR / ORIG
    DIR_MASK = DIR / MASK
    DIR_STYL = DIR / STYL
    DIR_OUT = DIR / OUT
    if not os.path.isdir(str(DIR_OUT)):
        os.mkdir(str(DIR_OUT))
    
    orig_fs = [str(DIR_ORIG / name) for name in os.listdir(str(DIR_ORIG))]
    mask_fs = [str(DIR_MASK / name) for name in os.listdir(str(DIR_MASK))]
    styl_fs = [str(DIR_STYL / name) for name in os.listdir(str(DIR_STYL))]
    
    assert(len(orig_fs) == len(mask_fs) == len(styl_fs))
    for idx in range(len(orig_fs)):
        orig = cv.imread(orig_fs[idx])
        mask = cv.imread(mask_fs[idx])
        styl = cv.imread(styl_fs[idx])
        assert(orig.shape == mask.shape == styl.shape)
        
        log(f'\tout_{idx:05}.png...')
        
        out = np.zeros(orig.shape)
        for row in range(len(out)):
            for col in range(len(out[0])):
                if not np.any(mask[row][col]):
                    # take pixel from style image
                    out[row][col] = styl[row][col]
                else:
                    # take pixel from original image
                    out[row][col] = orig[row][col]
        
        cv.imwrite(str(DIR_OUT / f'out_{idx:05}.png'), out)
    
    log('...finished.')
    return 0

if __name__ == '__main__':
    main()