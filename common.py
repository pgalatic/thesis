# author: Paul Galatic
# 
# Stores common functionality for the program.
#

# STD LIB
import os
import pdb
import sys
import glob
import time
import pickle
import logging
import pathlib
import platform
import threading

# EXTERNAL LIB

# LOCAL LIB
from const import *

def makedirs(dirname):
    # Convert from pathlib.Path to string if necessary.
    dirname = str(dirname)
    if not os.path.isdir(dirname):
        try:
            os.makedirs(dirname)
        except FileExistsError:
            pass # The directory was created just before we tried to create it.
        except PermissionError:
            logging.warning('Directory {} creation failed! Are you sure that the common folder is accessible/mounted?'.format(dirname))
            raise

def count_files(dir, extension):
    return len(glob.glob1(str(dir), '*{}'.format(extension)))

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
            pickle.dump(result, handle)
        
        return result
    except FileExistsError:
        # We couldn't claim that job, so WAIT until it's finished, then return None.
        logging.info('Job {} already claimed; waiting for output...'.format(tag))
        # Until the placeholder is gone, the file may still be incompletely uploaded.
        while os.path.exists(placeholder):
            time.sleep(1)
            write_to = str(remote / tag)
        
        with open(write_to, 'rb') as handle:
            return pickle.load(handle)
    finally:
        # Remove the placeholder in either case.
        if os.path.exists(placeholder):
            os.remove(placeholder)

def upload_files(fnames, dst, absolute_path=False):
    '''
    Upload frames from the local directory to the shared directory.
    
    given:
        fnames  -> (list:str) the names of the files to upload
        dst     -> (str) either the folder that the files should be deposited 
                    in (usually the common directory) or the absolute path to
                    which the files should be copied (the length of fnames must
                    be 1 in that case)
    optional:
        absolute_path   -> (bool) set to True when copying only one file to an 
                            absolute destination
    returns:
        None
    '''
    running = []
    
    for fname in fnames:
    
        # logging.info('\nUploading {}...'.format(fname))
        # This function should handle both PosixPath as well as string destinations.
        if absolute_path:
            newname = dst
        else:
            newname = str(pathlib.Path(dst) / os.path.basename(fname))
            
        # Only upload if the file doesn't already exist.
        if os.path.exists(newname):
            continue

        # In case anyone is waiting on a file, "label" it as incomplete.
        partname = newname + '.part'
        try:
            # This will only succeed if this program successfully created the file.
            # Uses file-objects to help guard against race conditions.
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
            logging.warning('\nFailed uploading -- file {} already exists!'.format(fname))
        except OSError:
            # The file path specified is incorrect, or there was another error.
            logging.error('\nFailed uploading {} -- OSError!'.format(fname), exc_info=True)
        finally:
            if os.path.exists(partname):
                os.remove(partname)
            
def wait_for(fname):
    '''
    WAIT until a file exists.
    '''
    # If you wish upon a star...
    logging.debug('Waiting for {}...'.format(fname))
    while not os.path.exists(fname):
        time.sleep(1)
    logging.debug('...{} found!'.format(fname))