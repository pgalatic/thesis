# author: Paul Galatic
#
# Program to

# STD LIB
import time
import argparse

# REQUIRED LIB
import os

# PROJECT LIB

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'

def log(s):
    '''More informative print debugging'''
    print('[%s]: %s' % (time.strftime(TIME_FORMAT, time.localtime()), str(s)))

def parse_args():
    '''Parses arguments'''
    parser = argparse.ArgumentParser()
    
    parser.add_argument('path', help='path to images to rename')
    
    return parser.parse_args()
    
def main():
    '''Driver program'''
    args = parse_args()
    log('Starting...')

    # This code ensures that the file names are in the exact format that DAVIS
    # and run.py require
    names = os.listdir(args.path)
    counter = 0
    for name in names:
        os.rename(os.path.join(args.path, name), os.path.join(args.path, '{:05d}.jpg'.format(counter)))
        counter += 1
    
    log('...finished.')
    return 0

if __name__ == '__main__':
    main()