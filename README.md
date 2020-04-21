# Divide and Conquer in Fast Artistic Videos
A thesis by Paul Galatic, a graduate student at the Rochester Institute of Technology (RIT) in New York State.

# NOTICE

This is the **reproducibility** branch. If you use this code, know that it is much less efficient than the current master branch. If you are trying to reproduce my results and you are having trouble, raise an issue. Otherwise, please try to use the current master before you point out any flaws.

## Background

Neural Style Transfer is the process of redrawing one image in the style of another image. While there are many implementation of neural style transfer for single images, there are few that can do the same for video without introducing undesirable flickering effects and other artifacts. Even fewer can stylize a video in a reasonable amount of time.

This work addresses several weaknesses of its predecessor, [Fast Artistic Videos](https://github.com/manuelruder/fast-artistic-videos) by Ruder et al. (2018) while preserving all of its strengths. Installation is far faster and easier, and runtime is cut by over 50%. 

That said, runtime in this implementation will still run into the hours on any video longer than a few seconds due to inefficiencies in the code that are left unfixed intentionally for the purpose of reproducibility.

## Installation

All nodes involved in computation should have the following priors:
* This respository
* Ubuntu >= 16.04 (see [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10) if using Windows)
* Python >= 3.5.6
* A video processing tool like [FFMPEG](https://www.ffmpeg.org/) that supports libx264

Once those are installed, run the following command on each node to install the rest.
```
bash install.sh
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
* If the filesystem runs out of memory, which is very likely with any HD video larger than a minute, the program may loop endlessly trying to create the same optical flow or stylization files, because Python's open(fname, 'x') will execute successfully even though the file is not created.

Future work:
* Because this is the reproducibility repository, it will never be updated beyond fixing crashes and updating documentation.
