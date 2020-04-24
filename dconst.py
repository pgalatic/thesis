# author: Paul Galatic
# 
# Stores constants for use in distribute.py.
#

# These are names of functions that only one computer should complete while the 
# others wait.
DIVIDE_TAG = 'divide.pkl'
SPLIT_TAG = 'split.pkl'
COMBINE_TAG = 'combine.pkl'

# The name of the file in which logs are stored, and the format of displaying messages.
LOGFILE = 'thesis.log'
LOGFORMAT = '%(asctime)s %(name)s:%(levelname)s -- %(message)s'

# When testing the algorithm, it is not immediately necessary to test it on a
# full video; instead, it can be tested with the first few frames of a video.
NUM_FRAMES_FOR_TEST = 15

# Increasing this is not recommended unless you have an extremely powerful computer.
MAX_STYLIZATION_JOBS = 1