# Image Segmentation and Stylization with Fast Artistic Videos by Ruder & Dosovitskiy
A thesis by Paul Galatic, a graduate student at the Rochester Institute of Technology (RIT) in New York State.

## Background

Neural Style Transfer is the process of replacing the texture of one image with the texture of another image. While there are many implementation of neural style transfer that can stylize a video in a relatively short amount of time, there are few that account for the differences between frames in order to create a smooth and consistent final product. 

This work is based on an implementation of [Ruder et al.](https://github.com/manuelruder/fast-artistic-videos) in 2018. Please site their work if you use this repository as part of your project or research. This repository is an effort to simply their implementation and extend it to work on a distributed computing cluster.

```
@Article{Ruder18,
author       = "M. Ruder and A. Dosovitskiy and T. Brox",
title        = "Artistic style transfer for videos and spherical images",
journal      = "International Journal of Computer Vision",
number       = "11",
volume       = "126",
pages        = "1199-1219",
month        = "Nov",
year         = "2018",
note         = "online first",
url          = "http://lmb.informatik.uni-freiburg.de/Publications/2018/RDB18"
}
```

## Installation

All nodes involved in computation should have the following priors:
* This respository
* Ubuntu >= 16.04 (see [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10) if using Windows)
* Python >= 3.5.6
* A video processing tool like [FFMPEG](https://www.ffmpeg.org/) that supports libx264

Once those are installed, run the following two commands on each node to install the rest.
```
bash install.sh
pip install -r requirements.txt
```

Optional programs that may be useful:
* A remote file system mount like [SFTP Drive V2](https://www.nsoftware.com/sftp/drive/download.aspx)

### Setting up a Shared Directory with SFTP Drive V2

This implementation is focused more on parallelization and cluster computing rather than networking. The simplest solution is to have a file system mount that appears as though it is local to all the machines involved. Many computing clusters have this set up natively, but it should also work for any number of computers that participate by implicitly communicating with a central node. A tool I found useful for this purpose is SFTP Drive V2.

In my preliminary experiments, I used two Windows machines (with Windows Subsystem for Linux, or WSL) and one remote Linux machine. Because my setup was a bit nontraditional to say the least, I used STFP Drive V2 to get started. However, the program should function the same as long as the path specified by the argument `nfs` is remotely accessible to all computers. Here's what I did:

1. Log in to all the requisite computers. Designate one computer as Master and create a folder there that will be mounted by the other computers.
1. Go to each non-Master machine and mount the Master drive. I recommend using a public/private RSA key for this that is distributed manually between all computers.
1. If you're using WSL, you cannot directly access a remote directory mounted to a letter drive (so far as I know). A way around this creating a symbolic link. Here is the command I use in WSL to link the `O:` drive to a folder I created, `/mnt/o`. If it fails, first double-check that your link is active and that you can transfer files manually between your local computer and the remote system.
```
sudo mount -t drvfs 'O:' /mnt/o
```

## Usage Guide

There are three required arguments in order to run the program. You can also run `python thesis.py -h` for more details as well as descriptions of optional arguments.
1. `remote` -- the path to the directory common to all participating nodes, also known as the **shared directory.**
1. `video` -- the path to the video you desire to stlyize as it appears on the **shared directory.** See `--local_video` for how to automatically distribute a video. You can also place the video on the shared directory manually.
1. `style` -- the path to the neural model used for feed-forward stylization as it appears on the **shared directory**, the same as `video` above.

Consider the following example: I have three nodes, my common directory is `/mnt/o/foo/` and I want to stylize a video called `eggdog.mp4` which I have stored on Node 0 with the neural model `candy.t7` that is also stored on Node 0. `eggdog.mp4` is conveniently stored at the same level as `thesis.py` and `candy.t7` is in the `/models/` directory. I would run the following command on Node 0:
```
python thesis.py /mnt/o/foo/ /mnt/o/foo/eggdog.mp4 /mnt/o/foo/candy.t7 --local_video eggdog.mp4 --local_style models/candy.t7
```
I would run this command on Nodes 1 and 2. These commands can all be run at the same time, as Nodes 1 and 2 will wait until Node 0 has finished uploading its file.
```
python thesis.py /mnt/o/foo/ /mnt/o/foo/eggdog.mp4 /mnt/o/foo/candy.t7
```

## Procedure Description 

Nodes are assumed to be of roughly equivalent computation power. The program operates in the following steps:
1. All nodes download the remote video and model.
1. Each node locally splits the video into frames to save on communication costs with the common directory.
1. All nodes coordinate optical flow computation and move the results to the common directory.
1. One node computes the optimal keyframes based on the frames of the video and report the results.
1. All nodes coordinate stylization and move the results to the common directory.
1. Each node downloads the resulting frames and locally stitches together the output video.

## Known Issues / Future Work

Known issues:
* Because of an interaction between Python's subprocess and the optical flow calculations, a benign message `error: unexpected parameter '|'` is often printed.
* If the shared filesystem runs out of memory, the program may loop endlessly trying to create the same optical flow or stylization images, because Python's open(fname, 'x') will execute successfully even though the file is not created.
* If the program produces images that are mostly or entirely blank, that means that the Torch installation is faulty. It is very particular. I fixed this issue by uninstalling Torch, cloning an old (Torch distro)[https://github.com/torch/distro], running install-deps, install.sh, and using Luarocks to install [torch, nn, image, lua-cjson]. Then, I ran update.sh and the problem was fixed. 

Future work:
* Enabling CUDA/CUDNN is an important priority, and is unfortunately more difficult due to circumstances involving the core implementation of this program. The core program is currently implemented in Torch. As noted in [Issue #7](https://github.com/manuelruder/fast-artistic-videos/issues/7), Torch's CUDA/CUDNN hooks are extremely finicky and often result in unusable outputs. I have tried many different version of Torch and CUDA/CUDNN with no success resolving this issue, and it will probably involve a conversion of the core implementation to pyTorch, an avenue I am pursuing as another part of my graduate work.
