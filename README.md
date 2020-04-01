# Divide and Conquer in Neural Video Stylization
A thesis by Paul Galatic, a graduate student at the Rochester Institute of Technology (RIT) in New York State.

## Background

Neural Style Transfer is the process of replacing the texture of one image with the texture of another image. While there are many implementation of neural style transfer for images, there are few that can do the same for video without introducing undesireable flickering effects and other artifacts. Even fewer can stylize a video in a reasonable amount of time.



## Installation

1. Ensure all computers involved have at least Ubuntu >= 16.04 (see [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10) if using Windows)
1. Clone this repository
1. Run `install.sh`

Prerequisites like Python >= 3.5.6 and [FFMPEG](https://www.ffmpeg.org/) are installed automatically. Make sure that your FFMPEG installation supports libx264.

## Usage Guide

There are three required arguments in order to run the program. You can also run `python stylize.py -h` for more details as well as descriptions of optional arguments.
1. `remote` -- the path to the directory common to all participating nodes, also known as the **shared directory.**
1. `video` -- the path to the video you desire to stlyize as it appears on the **shared directory.** See `--local_video` for how to automatically distribute a video. You can also place the video on the shared directory manually.
1. `style` -- the path to the neural model used for feed-forward stylization as it appears on the **shared directory**, the same as `video` above.

Consider the following example: I have four nodes, my common directory is `out/` and I want to stylize a video called `eggdog.mp4` with the neural model `candy.pth`. I would move `eggdog.mp4` and `candy.pth` to the common directory `out/` and run this command on all of them:
```
python stylize.py out/ out/eggdog.mp4 out/candy.pth
```

Other options can be shown by running
```
python stylize.py -h
```
In particular, consider enabling `--fast`, which uses Farneback optical flow calculations. They aren't as accurate as DeepFlow2, but they are an order of magnitude faster, and perform adequately in most circumstances.

## Procedure Description 

Nodes are assumed to be of roughly equivalent computation power. The program operates in the following steps:
1. One node splits the video into frames, placing those frames in the common directory.
1. All nodes coordinate stylization and move the results to the common directory.
1. One node combines the stylized frames into a stylized video.

## Credits

This work is based on the implementation of [Ruder et al.](https://github.com/manuelruder/fast-artistic-videos) from 2018. This repository is an effort to simply their implementation and extend it to work on a distributed computing cluster.

If you use my code, please link back to this repository. If you use it for research, please include this citation.

```
@mastersthesis{Galatic2020Dav
author  = "Paul Galatic",
title   = "Divide and Conquer in Video Style Transfer",
school  = "Rochester Institute of Technology - RIT",
year    = "2020",
url     = "https://github.com/pgalatic/thesis"
}
```

## Known Issues / Future Work

Known issues:
* If the shared filesystem runs out of memory, the program may loop endlessly trying to create the same optical flow or stylization images, because Python's open(fname, 'x') will execute successfully even though the file is not created.

Future work:
* Enabling CUDA/CUDNN is an important priority, and now that the repository uses pyTorch instead of Torch, this upgrade should be relatively simple, though it must wait until my thesis is published.
* Fully recreating the evaluation and training mechanisms of the core program, or replacing it with an alternative, is the next most important step
