# author: Paul Galatic
#
# Python wrapper for my thesis, "Divide and Conquer in Video Style Transfer,"
# which is based on the work Fast Artistic Videos by Manuel Ruder and Alexey 
# Dosovitskiy.

# STD LIB
import os
import sys
import time
import argparse
import subprocess

# EXTERNAL LIB

# LOCAL LIB

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'

def log(*args, nostamp=False):
    '''More informative print debugging'''
    t = time.strftime(TIME_FORMAT, time.localtime())
    s = '\t'.join([str(arg) for arg in args])
    if not nostamp: s = f'[{t}]: ' + s
    print(s)

def parse_args():
    '''Parses arguments'''
    ap = argparse.ArgumentParser()
    
    ap.add_argument('target', type=str,
        help='The path to the video to stylize.')
    ap.add_argument('style', type=str,
        help='The path to the model used for stylization')
    
    return ap.parse_args()
    
def main():
    '''Driver program'''
    args = parse_args()
    log('Starting...')

    workdir = os.getcwd() # remember our original working directory
    os.chdir(os.path.join(os.path.abspath(sys.path[0]), 'core/'))
    subprocess.call(['stylizeVideo.sh', '../' + args.target, '../' + args.style])
    os.chdir(workdir) # change back after executing the script
    
    log('...finished.')
    return 0

if __name__ == '__main__':
    main()