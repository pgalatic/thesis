# author: Paul Galatic
# 
# Stores constants for the program.
#

# The format name to properly split frames. Changing this would require changes 
# in CORE.
FRAME_NAME = 'frame_%05d.ppm'

# The default resolution keyword, for videos that should be stylized at the 
# same resolution as their original resolution.
RESOLUTION_DEFAULT = 'default'

# The threshold at which to stop accepting new keyframes.
KNEE_THRESHOLD = 0.05

# The maximum number of threading jobs to run simultaneously.
MAX_STYLIZE_JOBS = 2
MAX_OPTFLOW_JOBS = 3
MAX_UPLOAD_JOBS = 8

# These are names of functions that only one computer should complete while the others wait.
DIVIDE_TAG = 'divide.pkl'