# author: Paul Galatic
#
# Program to convert legacy Torch models to proper Pytorch models. This will only work with specific Torch models.

# STD LIB
import sys
import argparse

# EXTERNAL LIB
import torch # REQUIRES TORCH==0.4.1
import torch.nn as nn
import torch.nn.functional as F
try:
    from torch.utils import serialization
except Import Error:
    print('Importing Torch legacy functions failed--are you using the right version of pyTorch (0.4.1)?')
    sys.exit(1)

# LOCAL LIB

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'

class New(nn.Module):
    
    def __init__(self):
        super(New, self).__init__()
        
        self.padding_1 = nn.ReflectionPad2d(40) # https://pytorch.org/docs/master/nn.html#torch.nn.ReflectionPad2d
        self.spaital_1 = nn.Conv2d(7, 32, 9, 1, 4) # https://pytorch.org/docs/master/nn.html#torch.nn.Conv2d
        self.insnorm_1 = nn.Modules.InstanceNorm2d(32)
    
    def forward(self, x):
        pass
        

def parse_args():
    '''Parses arguments'''
    ap = argparse.ArgumentParser()
    
    ap.add_argument('model', type=str,
        help='The model to convert')
    ap.add_argument('name', type=str,
        help='The name of the converted model.')
    
    return ap.parse_args()
    
def main():
    '''Driver program'''
    args = parse_args()
    
    old = seralization.load_lua(args.model)
    
    # new = New()
    # new.load_state_dict(old.state_dict())
    # torch.save(new, args.name)
    

if __name__ == '__main__':
    main()