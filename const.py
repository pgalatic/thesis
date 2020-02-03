# author: Paul Galatic
# 
# Stores constants for the program
#

import os

# The format name to properly split frames. Changing this would require changes 
# in CORE.
FRAME_NAME = 'frame_%05d.ppm'

# The default resolution keyword, for videos that should be stylized at the 
# same resolution as their original resolution.
RESOLUTION_DEFAULT = 'default'

# The maximum number of Optflow jobs to run simultaneously.
MAX_OPTFLOW_JOBS = 2