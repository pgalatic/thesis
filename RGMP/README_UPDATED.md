# Fast Video Object Segmentation by Reference-Guided Mask Propagation
#### Seoung Wug Oh, Joon-Young Lee, Kalyan Sunkavalli, Seon Joo Kim
#### CVPR 2018
#### Edited by Paul Galatic

This is the official demo code for the paper. [PDF](http://openaccess.thecvf.com/content_cvpr_2018/CameraReady/1029.pdf)
___
## Test Environment
- Ubuntu 
- python 3.6
- Pytorch 0.3.1
  + If you want to run on a GPU, install with CUDA.

## How to Run
1) Download [DAVIS-2017](https://davischallenge.org/davis2017/code.html).
  + If you need to install Boost, do so with `sudo apt-get install libboost-all-dev`
2) Use the file `davis-2017/data/get_davis.sh` to download and extract the DAVIS folder.
3) Edit path for `DAVIS_ROOT` in run.py to be the DAVIS folder.
``` python
DAVIS_ROOT = '<Your DAVIS path>'
```
4) Download [weights.pth](https://www.dropbox.com/s/gt0kivrb2hlavi2/weights.pth?dl=0) and place it the same folde as run.py.
5) Split your video into frames. Place a copy of the frames in '<Your DAVIS path>/data/DAVIS/JPEGImages/480p/<your video name>'
6) Create a mask for your first frame (colors 6 and 7 of watershed_driver.py should be fine). Place this mask in '<Your DAVIS path>/data/DAVIS/Annotations/480p/<your video name>'. Note: This requires the target of segmentation to be visible on the first frame.
7) Edit the files in '<Your DAVIS path>/data/DAVIS/ImageSets/2017' to contain <your video name>. 
8) To run single-object video object segmentation on DAVIS-2016 validation.
``` 
python run.py
```
9) To run multi-object video object segmentation on DAVIS-2017 validation (assuming your mask has more than two colors).
``` 
python run.py -MO
```
10) Results will be saved in `./results/SO` or `./results/MO`.

## Use
#### This software is for Non-commercial Research Purposes only.

If you use this code please cite:
```
@InProceedings{oh2018fast,
author = {Oh, Seoung Wug and Lee, Joon-Young and Sunkavalli, Kalyan and Kim, Seon Joo},
title = {Fast Video Object Segmentation by Reference-Guided Mask Propagation},
booktitle = {The IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
year = {2018}
}
```
