# Image Segmentation and Stylization
## with Fast Artistic Videos by Ruder & Dosovitskiy
A thesis by Paul Galatic.

## Background

TODO

Some examples of this work can be found in the "results" directory. They are found from YouTube and I make no credit of original ownership.

## Installation

Some elements of what is required are included in requirements.txt.
```
pip install -r requirements.txt
```
Additional dependencies include:
* A video processing tool like [FFMPEG](https://www.ffmpeg.org/)
* A remote file system mount like [SFTP Drive V2](https://www.nsoftware.com/sftp/drive/download.aspx)


### Setting up a Shared Directory

This implementation is focused more on parallelization and cluster computing rather than networking. The simplest solution is to have a file system mount that appears as though it is local to all the machines involved.

In my preliminary experiments, I used two Windows machines (with Windows Subsystem for Linux, or WSL) and one remote Linux machine. Because my setup was a bit nontraditional, to say the least, I used STFP Drive V2 to get started. However, the program should function the same as long as the directory where the image files is stored is remotely accessible to all computers. Here's what I did:

1. Log in to all the requisite computers. Designate one computer as Master and create a folder that will be mounted by the other computers.
1. Go to a non-Master machine and mount the Master drive. I recommend using a public/private RSA key for this, shared between all computers.
1. If you're using WSL, you cannot directly access a remote directory mounted to a letter drive (so far as I know). A way around this creating a symbolic link. Here is the command I use in WSL to link the `O:` drive to a folder I created, `/mnt/o`. If it fails, first double-check that your link is active and that you can transfer files manually between your local computer and the remote system.
```
sudo mount -t drvfs 'O:' /mnt/o
```

## How to Use

TODO

## Known Issues / Future Work

* Because of an interaction between Python's subprocess and the optical flow calculations, a benign message `error: unexpected parameter '|'` is often printed.
* If the shared filesystem runs out of memory, the program may loop endlessly trying to create the same optical flow or stylization images, because Python's open(fname, 'x') will execute successfully.

## References

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