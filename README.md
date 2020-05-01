# Divide and Conquer in Neural Video Stylization
A thesis by Paul Galatic, a graduate student at the Rochester Institute of Technology (RIT) in New York State.

## Background

Neural Style Transfer is the process of redrawing one image in the style of another image. While there are many implementation of neural style transfer for single images, there are few that can do the same for video without introducing undesireable flickering effects and other artifacts. Even fewer can stylize a video in a reasonable amount of time.

This work addresses several weaknesses of its predecessor, [Fast Artistic Videos](https://github.com/manuelruder/fast-artistic-videos) by Ruder et al. (2018) while preserving all of its strengths. Much of the improvement is gained by converting from Lua Torch to pyTorch, which cuts overall runtime by over 50% with no reduction in output quality. Further speedup can be gained by using this repository to split the work of stylization across multiple computers.

If you intend to run stylization on only one computer, use [this repository](https://github.com/pgalatic/fast-artistic-videos-pytorch) instead.

## Installation

1. Ensure all computers involved have at least Ubuntu >= 16.04 (see [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10) if using Windows), Python >= 3.6.1, and that they have an FFMPEG installation compiled with libx264.
1. Clone this repository
1. Run `bash install.sh`

## Usage Guide

There are three required arguments in order to run the program.
1. `remote` -- the path to the directory common to all participating nodes.
1. `video` -- the path where the node can find the video
1. `style` -- the path where the node can find the stylization model

Consider the following example: I have four nodes, my common directory is `common/` and I want to stylize a video called `eggdog.mp4` with the neural model `candy.pth`. I move `eggdog.mp4` and `candy.pth` to `common/` and run this command on all four nodes:
```
python distribute.py common/ common/eggdog.mp4 common/candy.pth
```

Other options can be shown by running
```
python distribute.py -h
```
By default, this algorithm uses the [SPyNet](https://arxiv.org/abs/1611.00850) architecture to calculate optical flow, which is the best balance between speed and quality when running on a CPU. Please read the help message carefully so that you are aware of all the options available in the latest release, as the choice of optical flow calculator will dramatically affect both the quality of the final stylized video and the total processing time.

## Procedure Description 

Nodes are assumed to be of roughly equivalent computation power. The program operates in the following steps:
1. One node splits the video into frames, placing those frames in the common directory.
1. All nodes coordinate stylization and move the results to the common directory.
1. One node combines the stylized frames into a stylized video.

## Credits

This work is based on [Fast Artistic Videos](https://github.com/manuelruder/fast-artistic-videos). It relies on static binaries of [DeepMatching](https://thoth.inrialpes.fr/src/deepmatching/) and [Deepflow2](https://thoth.inrialpes.fr/src/deepflow/), among other external libraries.

If you use my code, please include a link back to this repository. If you use it for research, please include this citation.

```
@mastersthesis{Galatic2020Divide
  author  = "Paul Galatic",
  title   = "Divide and Conquer in Video Style Transfer",
  school  = "Rochester Institute of Technology - RIT",
  year    = "2020",
  url     = "https://github.com/pgalatic/thesis"
}
```

## Known Issues

* Any known issues in in the [core respository](https://github.com/pgalatic/fast-artistic-videos-pytorch).
* Installation may fail to install requirements on the first pass depending on your setup. Do NOT try to install with `sudo`. Instead, run `pip3 install -r requirements.txt` on all the requirements.txt files in the repository and subrepositories.

## Future Work

See the Future Work section in the [core repository](https://github.com/pgalatic/fast-artistic-videos-pytorch).
