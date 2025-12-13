#!/usr/bin/env python3
import sys
sys.path.append( "./cython")
try: 
    import mandelbrotCython
    cythonOK = True
except: 
    cythonOK = False

import numpy as np
import matplotlib.pyplot as plt 
import os
#
# for tiled worker
#
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

class TileWorker(QThread):

    # see remark in mandelbrot.py l.2164
    #finished = pyqtSignal(int, int, np.ndarray, np.ndarray)  # row, col, tile result

    def __init__(self, col, row):
        super().__init__()
        self.row, self.col = row, col

    @pyqtSlot(int, int, np.ndarray, np.ndarray)
    def collect( self, col, row, tile, zAbs): 
        with TileWorker.lock:
            w = int( float( self.width)/float( self.NCOL))
            h = int( float( self.width)/float( self.NROW))
            x0 = self.col*w
            y0 = self.row*h
            TileWorker.finalImage[ y0:y0+h, x0:x0+w] = tile
            TileWorker.finalZAbs[ y0:y0+h, x0:x0+w] = zAbs
            TileWorker.finished_count += 1
        return 

    def run(self):
        w = int( float( self.width)/float( self.NCOL))
        h = int( float( self.width)/float( self.NROW))
        x0 = self.col*w
        y0 = self.row*h
        #
        # notice self.xmin, etc. are class variables
        #
        xmin = self.xmin + (self.xmax - self.xmin) * x0 / self.width
        xmax = self.xmin + (self.xmax - self.xmin) * (x0 + w) / self.width
        ymin = self.ymin + (self.ymax - self.ymin) * y0 / self.width
        ymax = self.ymin + (self.ymax - self.ymin) * (y0 + h) / self.width
        if TileWorker.highPrec == "True":
            ( tile, zAbs) = mandelbrotCython.compute_mandelbrot_hp(
                w, h, xmin, xmax, ymin, ymax, 
                self.max_iter, self.horizon, 20)
        else:
            ( tile, zAbs) = mandelbrotCython.compute_mandelbrot(
                w, h, xmin, xmax, ymin, ymax, 
                self.max_iter, self.horizon, self.iConvTest)
        self.collect(self.col, self.row, tile, zAbs)
        #self.finished.emit(self.row, self.col, tile, zAbs)

class TileWorkerDz(QThread):

    # see comment above
    #finished = pyqtSignal(int, int, np.ndarray)  # row, col, tile result

    def __init__(self, col, row):
        super().__init__()
        self.row, self.col = row, col

    def collect( self, col, row, tile):
        
        with TileWorker.lock:
            TileWorkerDz.finished_count += 1                
            w = int( float( self.width)/float( self.NCOL))
            h = int( float( self.width)/float( self.NROW))
            x0 = self.col*w
            y0 = self.row*h
            TileWorkerDz.finalImage[ y0:y0+h, x0:x0+w] = tile
        return 

    def run(self):
        w = int( float( self.width)/float( self.NCOL))
        h = int( float( self.width)/float( self.NROW))
        x0 = self.col*w
        y0 = self.row*h
        #
        # notice self.xmin, etc. are class variables
        #
        xmin = self.xmin + (self.xmax - self.xmin) * x0 / self.width
        xmax = self.xmin + (self.xmax - self.xmin) * (x0 + w) / self.width
        ymin = self.ymin + (self.ymax - self.ymin) * y0 / self.width
        ymax = self.ymin + (self.ymax - self.ymin) * (y0 + h) / self.width

        x = np.linspace(xmin, xmax, w)
        y = np.linspace(ymin, ymax, w)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y

        # Compute smoothed Mandelbrot
        tile = mandelbrotCython.mandelbrot_dz(C, max_iter=TileWorkerDz.max_iter)
        self.collect( self.row, self.col, tile)
        #self.finished.emit(self.row, self.col, tile)

class TileWorkerJulia(QThread):

    def __init__(self, col, row):
        super().__init__()
        self.row, self.col = row, col

    @pyqtSlot(int, int, np.ndarray, np.ndarray)
    def collect( self, col, row, tile, zAbs): 
        with TileWorkerJulia.lock:
            w = int( float( self.width)/float( self.NCOL))
            h = int( float( self.width)/float( self.NROW))
            x0 = self.col*w
            y0 = self.row*h
            TileWorkerJulia.finalImage[ y0:y0+h, x0:x0+w] = tile
            TileWorkerJulia.finalZAbs[ y0:y0+h, x0:x0+w] = zAbs
            TileWorkerJulia.finished_count += 1
        return 

    def run(self):
        xmin = self.cxJ - self.deltaJ/2.
        xmax = self.cxJ + self.deltaJ/2.
        ymin = self.cyJ - self.deltaJ/2.
        ymax = self.cyJ + self.deltaJ/2.
        w = int( float( self.width)/float( self.NCOL))
        h = int( float( self.width)/float( self.NROW))
        x0 = self.col*w
        y0 = self.row*h
        #
        # notice self.xmin, etc. are class variables
        #
        xminTile = xmin + (xmax - xmin) * x0 / self.width
        xmaxTile = xmin + (xmax - xmin) * (x0 + w) / self.width
        yminTile = ymin + (ymax - ymin) * y0 / self.width
        ymaxTile = ymin + (ymax - ymin) * (y0 + h) / self.width

        real = np.linspace(xminTile, xmaxTile, w)
        imag = np.linspace(yminTile, ymaxTile, w)
        real_grid, imag_grid = np.meshgrid(real, imag)

        (tile, zAbs) = mandelbrotCython.compute_julia( real_grid, imag_grid, 
                                                       self.cxM, self.cyM, 
                                                       self.maxIterJ, self.horizon)
        self.collect(self.col, self.row, tile, zAbs)
