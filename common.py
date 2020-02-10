# author: Paul Galatic
# 
# Stores common functionality for the program.
#

# STD LIB
import os
import pdb
import time
import pickle
import pathlib
import threading

# EXTERNAL LIB

# LOCAL LIB
from const import *

def wait_complete(tag, target, args, remote):
    # Try to create a placeholder.
    placeholder = str(remote / (tag +'.plc'))
    try:
        # This will only succeed if this program successfully created the placeholder.
        with open(placeholder, 'x') as handle:
            handle.write('PLACEHOLDER CREATED BY {name}'.format(name=platform.node()))
        
        print('Job claimed: {}'.format(tag))
        # Run the function.
        result = target(*args)
        
        # Write the output to disk.
        with open(tag, 'wb') as handle:
            pickle.dump(result, handle)
        
        # Remove the placeholder.
        os.remove(placeholder)
    except FileExistsError:
        # We couldn't claim that job, so WAIT until it's finished, then return None.
        while os.path.exists(placeholder):
            time.sleep(1)

def read_tag(tag, remote):
    # Read data from a common tag.
    fname = str(remote / tag)
    with open(fname, 'rb') as handle:
        return pickle.load(handle)

def upload_files(fnames, dst, absolute_path=False):
    # Upload frames from the local directory to the shared directory.
    # Uses file-objects to help guard against race conditions.
    running = []
    
    for fname in fnames:
        # print('\nUploading {}...'.format(fname))
        try:
            # This function should handle both PosixPath as well as string destinations.
            if absolute_path:
                newname = dst
            else:
                newname = str(pathlib.Path(dst) / os.path.basename(fname))
            
            # In case anyone is waiting on a file, "label" it as incomplete.
            partname = newname + '.part'
            # This will only succeed if this program successfully created the file.
            with open(partname, 'xb') as handle:
                with open(str(fname), 'rb') as alt:
                    content = alt.read()
                    # Check to make sure we're not running too many threads.
                    if len(running) > MAX_UPLOAD_JOBS:
                        running = [thread for thread in running if thread.isAlive()]
                        time.sleep(1)
                    # Upload the data.
                    handle.write(content)
            # Remove the incomplete "label".
            os.rename(partname, newname)
        except FileExistsError:
            # Try to upload the next file.
            print('\nFile already exists!')
            pass

def wait_for(fname):
    # If you wish upon a star...
    while not os.path.exists(fname):
        time.sleep(1)