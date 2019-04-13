#!/usr/bin/env python

'''
Watershed segmentation

Source: https://github.com/opencv/opencv/tree/master/samples/python
=========
This program demonstrates the watershed segmentation algorithm
in OpenCV: watershed().
Usage
-----
watershed.py [image filename]
Keys
----
  1-7   - switch marker color
  SPACE - update segmentation
  r     - reset
  a     - toggle autoupdate
  ESC   - exit
'''

# Python 2/3 compatibility
from __future__ import print_function

import numpy as np
import cv2 as cv
from skimage import morphology as skmorph

WINDOW_IMG = 'img'
WINDOW_CV = 'opencv watershed'
WINDOW_SK = 'skimage watershed'

class Sketcher:
    '''
    The Sketcher class is responsible for drawing colored dots on the image 
    window.
    '''
    def __init__(self, windowname, dests, colors_func):
        # The last point drawn. This is used to draw lines.
        self.prev_pt = None
        # The name of the window to draw on.
        self.windowname = windowname
        # These are the points that the Sketcher is responsible for.
        self.dests = dests
        # The function used to determine which color should be drawn.
        self.colors_func = colors_func
        # Whether or not the sketch has been edited recently. This is a "dirty
        # flag" that signals to anything using the Sketcher that updates are 
        # necessary.
        self.dirty = False
        
        # Finish initialization by displaying the window.
        self.show()
        cv.setMouseCallback(self.windowname, self.on_mouse)

    def show(self):
        '''For initialization, updates, and refreshing the window.'''
        cv.imshow(self.windowname, self.dests[0])

    def on_mouse(self, event, x, y, flags, param):
        '''
        Mouse event callback. Takes the current 
        '''
        pt = (x, y)
        # On left clicks, draw a point (or continue a line).
        if event == cv.EVENT_LBUTTONDOWN:
            self.prev_pt = pt
        # Otherwise, stop drawing.
        elif event == cv.EVENT_LBUTTONUP:
            self.prev_pt = None

        if self.prev_pt and flags & cv.EVENT_FLAG_LBUTTON:
            # As long as the previous point exists, keep drawing lines.
            for dst, color in zip(self.dests, self.colors_func()):
                cv.line(dst, self.prev_pt, pt, color, 5)
            # Let it be known that the updates are required.
            self.dirty = True
            self.prev_pt = pt
            # Update.
            self.show()

class App:
    def __init__(self, fn):
        # Read the image, if it exists.
        self.img = cv.imread(fn)
        if self.img is None:
            raise Exception('Failed to load image file: %s' % fn)

        # Set up the height, width, and markers array.
        height, width = self.img.shape[:2]
        
        # Make sure the image is viewable.
        while height > 800:
            self.img = cv.resize(self.img, (0, 0), fx=0.5, fy=0.5)
            height, width = self.img.shape[:2]
        
        self.markers = np.zeros((height, width), np.int32)
        self.markers_vis = self.img.copy()
        self.cur_marker = 1
        self.colors = np.int32(list(np.ndindex(2, 2, 2))) * 255

        # When set to true, automatically update the "results" window.
        self.auto_update = True
        
        # Initialize the Sketcher, which will draw our markers over the 
        # original image.
        self.sketch = Sketcher(WINDOW_IMG, [self.markers_vis, self.markers], self.get_colors)

    def get_colors(self):
        '''
        This function is a callback used to get the color of the current 
        marker.
        '''
        return list(map(int, self.colors[self.cur_marker])), self.cur_marker

    def watershed(self):
        # Copy the existing markers and use them to apply both watershed 
        # algorithms to the original image.
        m = self.markers.copy()
        cv.watershed(self.img, m) # opencv
        
        # Use the watershed segmentation to set up an overlay of the original
        # image. This will be used to more clearly denote which segments were 
        # caused by which marker.
        overlay_cv = self.colors[np.maximum(m, 0)]
        overlay_cv = (255 - overlay_cv)
        cv.imwrite('out.png', overlay_cv)
        
        vis_cv = cv.addWeighted(self.img, 0.5, overlay_cv, 0.5, 0.0, dtype=cv.CV_8UC3)
        cv.imshow(WINDOW_CV, vis_cv)

    def run(self):
        # This will run until the windows are closed or ESC is pressed.
        while  (cv.getWindowProperty(WINDOW_IMG, 0) != -1 or 
                cv.getWindowProperty(WINDOW_CV, 0) != -1 or
                cv.getWindowProperty(WINDOW_SK, 0) != -1):
            chx = cv.waitKey(50)
            # If the user doesn't provide input, the program doesn't act.
            if chx == 27:
                break
            # Keys 1 - 7 are used to change the color of the marker.
            if chx >= ord('0') and chx <= ord('7'):
                self.cur_marker = chx - ord('0')
                print('marker: ', self.cur_marker)
            # If auto-update is turned off, then space is used to update the
            # segmentation. Otherwise, update it whenever the Sketcher throws 
            # up its "dirty" flag.
            if chx == ord(' ') or (self.sketch.dirty and self.auto_update):
                self.watershed()
                self.sketch.dirty = False
            # Toggle auto-updating.
            if chx in [ord('a'), ord('A')]:
                self.auto_update = not self.auto_update
                print('auto_update if', ['off', 'on'][self.auto_update])
            # Clear all markers and reset the sketcher.
            if chx in [ord('r'), ord('R')]:
                self.markers[:] = 0
                self.markers_vis[:] = self.img
                self.sketch.show()
        
        # Once the user is finished, close all windows.
        cv.destroyAllWindows()


if __name__ == '__main__':
    import sys
    try:
        fn = sys.argv[1]
    except:
        fn = 'fruits.jpg'
    print(__doc__)
    App(cv.samples.findFile(fn)).run()