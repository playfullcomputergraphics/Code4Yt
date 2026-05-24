#!/usr/bin/env python3

import numpy as np
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numexpr as ne
import mandelbrotTiled
import utils
import threading
import PGViewer

LOG_HELPER = 0.001
NROW = 5
NCOL = 5

class FractalEngine( QWidget):
    """
    """
    
    MBSUpdated = pyqtSignal(np.ndarray)
    JuliaSetUpdated = pyqtSignal(np.ndarray)
    
    def __init__(self, parent=None, colorPars = None):
        super().__init__(parent)
        self.name = "FractalEngine" 
        self.parent = parent
        self.colorPars = colorPars
        return 

    def calcMandelbrotSet( self, display = True):
        """
        calculates self.dataMandelbrotSet
        """
        #print( "%s.calcMandelbrotSet" % self.name)
        
        if self.parent.widthM == 256:
            self.parent.vmax = CMAP_MAX - 1
            self.parent.setCurrentIndices()
            self.parent.dataMandelbrotSet = np.tile(np.arange(256), (256, 1))
            self.MBSUpdated.emit( self.parent.dataMandelbrotSet)
            return 

        #if self.parent.operatorWidget is not None:
        #    self.parent.operatorWidget.logWidget.append( "calcMBS")
        
        self.parent.isFilteredM = False
        
        if self.colorPars.smooth == "DZ": 
            if self.parent.cython == "True":
                return self.calcMandelbrotSetDzCython()
            else: 
                return self.calcMandelbrotSetDZ()

        if self.parent.cython == "True": 
            return self.calcMandelbrotSetCython()

        if self.parent.numba == "True": 
            return self.calcMandelbrotSetNumba()

        if self.parent.scalar == "True": 
            return self.calcMandelbrotSetScalar()

        if self.parent.numpy == "False":
            if cythonOK: 
                self.parent.cython = "True"
                self.parent.cythonAction.setChecked( self.parent.cython == "True")
                return self.calcMandelbrotSetCython()
            self.parent.logWidget.append( "calcMandelbrotSet: select a method")
            return 

        return self.calcMandelbrotSetNumpy()
    
    def calcMandelbrotSetNumpy( self, display = True):

        #print( "FractalEngine.calcMBSNumpy: cx %g cy %g delta %g width %d maxIter %d " % 
        #       ( self.parent.cxM, self.parent.cyM, 
        #         self.parent.deltaM, self.parent.widthM, self.parent.maxIterM))
        cx = self.parent.cxM
        cy = self.parent.cyM
        delta = self.parent.deltaM
        width = self.parent.widthM
        maxIter = self.parent.maxIterM
        dataNorm = utils.DATA_NORM
        
        if display: 
            self.parent.progressLbl.show()
            self.parent.progressLbl.setText( "Progress: 0/%4d M" % (maxIter))

        if self.parent.viewerMain.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        log_horizon = np.log2(np.log(horizon))
            
        x = np.linspace( cx - delta/2., cx + delta/2., width, dtype=np.float64)
        y = np.linspace( cy - delta/2., cy + delta/2., width, dtype=np.float64)
        
        c = x + y[:,None]*1j
        self.parent.progressLbl.setStyleSheet("background-color:lightblue")
        self.parent.app.processEvents()

        z = np.zeros(c.shape, np.complex128)

        escapeCount = np.zeros(c.shape) 
        
        startTime = time.time()
        for it in range( maxIter):
            notdone = ne.evaluate('z.real*z.real + z.imag*z.imag < %g' % float( horizon))
            #
            # escapeCount is set to it at the positions where notdone is true
            #
            escapeCount[notdone] = it
            z = ne.evaluate('where(notdone,z**2+c,z)')
            if (it % 100) == 0 and display:
                self.parent.progressLbl.setText( "Progress: %4d/%4d M" % ( it, maxIter))
                self.parent.app.processEvents()
                self.MBSUpdated.emit( escapeCount)
                
            if self.parent.stopRequested:
                break

        if escapeCount.shape[0] == 10: 
            print( "calcMandelbrotSet-0: corr %g escapeCount %s" %
                   ( dataNorm/float( maxIter), repr( escapeCount)))

        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= (dataNorm-1)/float( maxIter-1)
        #
        # smoothing algorithm from 
        # https://linas.org/art-gallery/escape/smooth.html
        #
        if self.parent.viewerMain.smooth == "DistEst": 
            temp = np.log( abs(z))
            temp[ temp <= 0.] = LOG_HELPER
            escapeCount = np.nan_to_num( escapeCount + 1 - np.log2( temp) + log_horizon)
            
        if escapeCount.shape[0] == 10: 
            print( "calcMandelbrotSet: escapeCount %s" % repr( escapeCount))

        self.parent.dataMandelbrotSet = escapeCount
        self.MBSUpdated.emit( self.parent.dataMandelbrotSet)
        
        if self.parent.debugSpeed == "True": 
            self.parent.logWidget.append( "M: %5.3f s, Numpy/Numexpr" % 
                                   (( time.time() - startTime)))

        if display: 
            self.parent.progressLbl.setText( "Progress: %4d/%4d M" % ( it, maxIter))
            self.parent.progressLbl.setStyleSheet("background-color:%s" % self.parent.backgroundColor)
            self.parent.progressLbl.hide()

        return 

    def calcMandelbrotSetCython( self):
        # 
        #print( "FractalEngine.calcMBSCython: cx %g cy %g delta %g width %d maxIter %d " % 
        #       ( self.parent.cxM, self.parent.cyM, 
        #         self.parent.deltaM, self.parent.widthM, self.parent.maxIterM))

        if self.parent.tiled == "True": 
            self.calcMandelbrotSetCythonTiled()
            return
        
        startTime = time.time()
        if self.parent.viewerMain.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        log_horizon = np.log2(np.log(horizon))
        
        (escapeCount, zAbs) = mandelbrotCython.compute_mandelbrot( 
            self.parent.widthM, self.parent.widthM, 
            self.parent.cxM - self.parent.deltaM/2., 
            self.parent.cxM + self.parent.deltaM/2., 
            self.parent.cyM - self.parent.deltaM/2., 
            self.parent.cyM + self.parent.deltaM/2., 
            self.parent.maxIterM, horizon)

        corr = (utils.DATA_NORM-1)/float( self.parent.maxIterM - 1)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr

        if self.parent.debugSpeed == "True": 
            self.parent.logWidget.append( "M: %5.3f s, Cython, not tiled, prange() %s" % 
                                   (( time.time()-startTime)))

        if self.parent.viewerMain.smooth == "DistEst":
            zAbs[ zAbs <= 0.] = LOG_HELPER
            temp = np.log( zAbs)
            temp[ temp <= 0.] = LOG_HELPER
            output = escapeCount
            corr = np.nan_to_num( escapeCount + 
                                  1 - np.log2( temp)*corr + log_horizon)
            self.parent.dataMandelbrotSet = np.where(output != 0, corr, output)
        else:
            self.parent.dataMandelbrotSet = escapeCount

        self.MBSUpdated.emit( self.parent.dataMandelbrotSet)
            
        return 

    def calcMandelbrotSetCythonTiled( self):
        # 
        #print( "FractalEngine.calcMBSCythonTiled: cx %g cy %g delta %g width %d maxIter %d " % 
        #       ( self.parent.cxM, self.parent.cyM, 
        #         self.parent.deltaM, self.parent.widthM, self.parent.maxIterM))
        
        if self.colorPars.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        width = self.parent.widthM
        
        mandelbrotTiled.TileWorker.NCOL = NCOL
        mandelbrotTiled.TileWorker.NROW = NROW
        mandelbrotTiled.TileWorker.width = width
        mandelbrotTiled.TileWorker.finalImage = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorker.finalZAbs = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorker.xmin = self.parent.cxM - self.parent.deltaM/2.
        mandelbrotTiled.TileWorker.xmax = self.parent.cxM + self.parent.deltaM/2.
        mandelbrotTiled.TileWorker.ymin = self.parent.cyM - self.parent.deltaM/2.
        mandelbrotTiled.TileWorker.ymax = self.parent.cyM + self.parent.deltaM/2.
        mandelbrotTiled.TileWorker.max_iter = self.parent.maxIterM
        mandelbrotTiled.TileWorker.horizon = horizon
        mandelbrotTiled.TileWorker.finished_count = 0
        mandelbrotTiled.TileWorker.total_tiles = NROW*NCOL
        
        #
        # to ensure that collect() is thread-safe 
        # if the GUI is updated from collect, signals have to used
        # because direct GUI updates from threads are unsafe
        #
        mandelbrotTiled.TileWorker.lock = threading.Lock()
        
        startTime = time.time()
        workers = []

        for row in range( NROW): 
            for col in range( NCOL): 
                worker = mandelbrotTiled.TileWorker( col, row)
                workers.append( worker)
                worker.start()

        while mandelbrotTiled.TileWorker.finished_count < NROW*NCOL:
            self.parent.app.processEvents()

        #
        # make sure that there is not left-over
        #
        for elm in workers:
            elm.quit()

        escapeCount = mandelbrotTiled.TileWorker.finalImage
        zAbs = mandelbrotTiled.TileWorker.finalZAbs
        #
        # nongil cython code has no sqrt()
        #
        #zAbs = np.sqrt( zAbs) 
        
        corr = (utils.DATA_NORM-1)/float( self.parent.maxIterM - 1)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr

        if self.colorPars.smooth == "DistEst":
            zAbs[ zAbs <= 0.] = LOG_HELPER
            temp = np.log( zAbs)
            temp[ temp <= 0.] = LOG_HELPER
            output = escapeCount
            log_horizon = np.log2(np.log(horizon))
            corr = np.nan_to_num( escapeCount + 
                                  1 - np.log2( temp)*corr + log_horizon)
            self.parent.dataMandelbrotSet = np.where(output != 0, corr, output)
        else:
            self.parent.dataMandelbrotSet = escapeCount

        if self.parent.debugSpeed == "True": 
            if not self.parent.isAnimating: 
                self.parent.logWidget.append( "M: %5.3f s, Cython, tiled, CardioidBulb %s, prange() %s" % 
                                       (( time.time() - startTime), repr( self.parent.cardioidBulb), repr( self.parent.prange))) 


        if self.parent.execDynOp == "True": 
            if self.parent.operatorWidget is not None: 
                self.parent.operatorWidget.cb_runOp()

        self.MBSUpdated.emit( self.parent.dataMandelbrotSet)

        return

    def calcMandelbrotSetDzCython( self):

        if self.parent.tiled == "True": 
            self.calcMandelbrotSetDzCythonTiled()
            return
        
        width = self.parent.widthM
        xmin = self.parent.cxM - self.parent.deltaM/2.
        xmax = self.parent.cxM + self.parent.deltaM/2.
        ymin = self.parent.cyM - self.parent.deltaM/2.
        ymax = self.parent.cyM + self.parent.deltaM/2.

        max_iter = self.parent.maxIterM

        x = np.linspace(xmin, xmax, width)
        y = np.linspace(ymin, ymax, width)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y
        startTime = time.time()

        # Compute smoothed Mandelbrot
        result = mandelbrotCython.mandelbrot_dz(C, max_iter=max_iter)

        # Normalize and plot
        norm = result / np.max(result)
        norm = norm ** 0.8  # gamma correction
        norm /= 2.
        norm *= utils.DATA_NORM
        
        corr = (utils.DATA_NORM-1)/float( self.parent.maxIterM - 1)
        escapeCount = np.copy( norm)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr
        if self.parent.debugSpeed == "True": 
            self.parent.logWidget.append( "M: %5.3f s, Cython, Dz, min %g, max%g " % 
                                   (( time.time() - startTime), 
                                    escapeCount.min(), escapeCount.max()))
        self.parent.dataMandelbrotSet = escapeCount
        self.MBSUpdated.emit( self.parent.dataMandelbrotSet)

        return 


    def calcMandelbrotSetDzCythonTiled( self):

        width = self.parent.widthM
        xmin = self.parent.cxM - self.parent.deltaM/2.
        xmax = self.parent.cxM + self.parent.deltaM/2.
        ymin = self.parent.cyM - self.parent.deltaM/2.
        ymax = self.parent.cyM + self.parent.deltaM/2.

        if self.colorPars.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4

        log_horizon = np.log2(np.log(horizon))

        mandelbrotTiled.TileWorkerDz.NCOL = NCOL
        mandelbrotTiled.TileWorkerDz.NROW = NROW
        mandelbrotTiled.TileWorkerDz.width = width
        mandelbrotTiled.TileWorkerDz.finalImage = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorkerDz.xmin = xmin
        mandelbrotTiled.TileWorkerDz.xmax = xmax
        mandelbrotTiled.TileWorkerDz.ymin = ymin
        mandelbrotTiled.TileWorkerDz.ymax = ymax
        mandelbrotTiled.TileWorkerDz.max_iter = self.parent.maxIterM
        mandelbrotTiled.TileWorkerDz.horizon = horizon
        mandelbrotTiled.TileWorkerDz.finished_count = 0
        mandelbrotTiled.TileWorkerDz.total_tiles = NROW*NCOL
        mandelbrotTiled.TileWorkerDz.lock = threading.Lock()
        
        startTime = time.time()
        for row in range( NROW): 
            for col in range( NCOL): 
                temp = mandelbrotTiled.TileWorkerDz( col, row)
                temp.finished.connect( temp.collect)
                temp.run()

        while mandelbrotTiled.TileWorkerDz.finished_count < NROW*NCOL:
            self.parent.app.processEvents()

        result = mandelbrotTiled.TileWorkerDz.finalImage

        # Normalize and plot
        norm = result / np.max( result)
        norm = norm ** 0.8  # gamma correction
        norm /= 2.
        norm *= utils.DATA_NORM  
        
        corr = (utils.DATA_NORM-1)/float( self.parent.maxIterM - 1)
        escapeCount = np.copy( norm)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr
        if self.parent.debugSpeed == "True": 
            self.parent.logWidget.append( "%5.3f s, Cython, Dz, tiled, min %g, max%g " % 
                                   (( time.time() - startTime), 
                                    escapeCount.min(), escapeCount.max()))
        self.parent.dataMandelbrotSet = escapeCount
        self.MBSUpdated.emit( self.parent.dataMandelbrotSet)
        
        return
    
    def calcMandelbrotSetDZ( self):
        """
        derivative based distance estimation
        """
        # Image dimensions and bounds
        # Image dimensions and bounds
        width = self.parent.widthM
        xmin = self.parent.cxM - self.parent.deltaM/2.
        xmax = self.parent.cxM + self.parent.deltaM/2.
        ymin = self.parent.cyM - self.parent.deltaM/2.
        ymax = self.parent.cyM + self.parent.deltaM/2.

        max_iter = self.parent.maxIterM

        # Create complex grid
        x = np.linspace(xmin, xmax, width)
        y = np.linspace(ymin, ymax, width)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y

        # Initialize z and derivative dz
        Z = np.zeros_like(C, dtype=np.complex128)
        dZ = np.ones_like(C, dtype=np.complex128)
        
        # Track escape status and smooth iteration
        escaped = np.zeros(C.shape, dtype=bool)
        smooth_iter = np.zeros(C.shape, dtype=np.float64)
        distance = np.zeros(C.shape, dtype=np.float64)

        self.parent.progressLbl.show()
        self.parent.progressLbl.setText( "Progress: 0/%4d M" % (self.parent.maxIterM))
        self.parent.progressLbl.setStyleSheet("background-color:lightblue")

        for i in range(max_iter):
            Z = Z**2 + C
            dZ = 2 * Z * dZ + 1
            absZ = np.abs(Z)

            # Identify newly escaped points
            newly_escaped = (absZ > 4.0) & (~escaped)
            escaped |= newly_escaped

            # Compute smooth iteration count for newly escaped
            nu = i + 1 - np.log(np.log(absZ + 1e-8)) / np.log(2)
            smooth_iter[newly_escaped] = nu[newly_escaped]

            # Compute distance estimate for newly escaped
            zn = Z[newly_escaped]
            dz = dZ[newly_escaped]
            distance[newly_escaped] = np.abs(zn) * np.log(np.abs(zn)) / np.abs(dz)
            if (i % 100 == 0):
                self.parent.progressLbl.setText( "Progress: %d/%4d M" % (i, self.parent.maxIterM))

        # Combine smooth iteration and distance
        combined = np.zeros_like(C, dtype=np.float64)
        combined[escaped] = np.log1p(smooth_iter[escaped] + np.log1p(distance[escaped]))

        # Normalize and apply gamma correction
        norm = combined / np.max(combined)
        gamma = 0.8
        norm = norm ** gamma

        # Set interior points to black
        norm[~escaped] = 0.0

        norm *= utils.DATA_NORM
        
        self.parent.dataMandelbrotSet = norm
        self.MBSUpdated.emit( self.parent.dataMandelbrotSet)
        self.parent.progressLbl.setText( "Progress: %4d/%4d M" % ( i, self.parent.maxIterM))
        self.parent.progressLbl.setStyleSheet("background-color:%s" % self.parent.backgroundColor)
        self.parent.progressLbl.hide()

        return

    # CUDA kernel
            

    def calcMandelbrotSetNumba( self):

        if self.colorPars.smooth != "None": 
            self.parent.logWidget.append( "calcNumba: smooth must be None'")
            return 
            
        # Parameters
        width = self.parent.widthM
        xmin = self.parent.cxM - self.parent.deltaM/2.
        xmax = self.parent.cxM + self.parent.deltaM/2.
        ymin = self.parent.cyM - self.parent.deltaM/2.
        ymax = self.parent.cyM + self.parent.deltaM/2.

        max_iter = self.parent.maxIterM

        startTime = time.time()
        
        # Allocate output arrays
        image_gpu = np.zeros(( width, width), dtype=np.uint32)
        """
        for Mandelbrot set: 
          - one thread per pixel
          - threads per block: (16, 16) is a common sweet spot
          - blockspergrid_x, ~_y: how many blocks are
            needed to cover the whole image
            +  (a + b - 1)/b
              = Even if the image size is not divisible by 16,
                you still launch enough blocks.
              = Extra threads simply exit early inside the kernel.
            + blockspergrid = (63, 63)
          - 1 Mio threads do not run simultaneously
            + they are scheduled in warps (32 threads) and blocks
              (e.g. 256 theads)
              and they are executed in waves
            + warps are the physical execution unit
            + You launch 1,000,000 threads.
            + The GPU queues them.
            + It runs as many as it can at once (depending on SM count,
              occupancy, registers, etc.).
            + When one warp stalls (e.g., waiting on memory), another warp runs.
          - SIMT - single instruction multiple threads, SIMT
          - all 32 threads within one warp
            + execute the same instruction
            + at the same time
            + on different data
          - each warp executes in lockstep (SIMT)
        """
        threadsperblock = (16, 16)
        """
        block: 16 x 16 threads
        Warp 0: threads (0 - 31)
        Warp 1: threads (32 - 63)
        Warp 2: threads (64 - 95)
        ...
        Warp 7: threads (224 - 255)
        """
        blockspergrid_x = (width + threadsperblock[0] - 1) // threadsperblock[0]
        blockspergrid_y = (width + threadsperblock[1] - 1) // threadsperblock[1]
        blockspergrid = (blockspergrid_x, blockspergrid_y) # (63, 63) 
        """
        blocks define cooperation between threads
          + share data via shared memory
          + synchronize threads with __syncthreads()
            (no synchronize across blocks)
          + cooperate on partial results using shared memory
        blocks are the unit of scheduling on SMs (streaming multiprocessors)
        blocks define resource allocation
          - each block get a chunk of shared memory
          - ... a budget of registers
          -  ... a set of warps
        """
        d_image = cuda.to_device(image_gpu)
        mandelbrot_kernel[blockspergrid, threadsperblock]( xmin, xmax,
                                                           ymin, ymax,
                                                           d_image, max_iter)
        """
        obj[ key] is the same as obj.__getitem__( Key)
        Cuda overrides __getitem__
        """
        escapeCount = d_image.copy_to_host()

        corr = (utils.DATA_NORM-1)/float( self.parent.maxIterM - 1)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr
        if self.parent.debugSpeed == "True" and not self.parent.isAnimating: 
            self.parent.logWidget.append( "M: %5.3f s, numba, min %g, max %g " % 
                                   (( time.time() - startTime), 
                                    escapeCount.min(), escapeCount.max()))

        self.parent.dataMandelbrotSet = escapeCount
        self.MBSUpdated.emit( self.parent.dataMandelbrotSet)
        return 

    def inCardioid( self, x, y):
        xm = x - 0.25
        q = xm * xm + y * y
        return q * (q + xm) < 0.25 * y * y

    def inBulb( self, x, y):
        xp = x + 1.0
        return xp * xp + y * y < 0.0625  # 1/16
        
    def calcMandelbrotSetScalar( self):
        if self.colorPars.smooth != "None":
            self.parent.logWidget.append( "calcScalar: smooth must be None")
            return
        
        if self.parent.shaded == "True":
            self.parent.logWidget.append( "calcScalar: shaded must be False")
            return

        startTime = time.time()
        self.parent.progressLbl.show()
        self.parent.progressLbl.setText( "Progress: 0/%4d M" % (self.parent.widthM))
        self.parent.progressLbl.setStyleSheet("background-color:lightblue")
        self.parent.app.processEvents()

        width = self.parent.widthM
        
        # Create coordinate grid
        x = np.linspace( self.parent.cxM - self.parent.deltaM/2.,
                         self.parent.cxM + self.parent.deltaM/2.,
                         width)
        y = np.linspace( self.parent.cyM - self.parent.deltaM/2.,
                         self.parent.cyM + self.parent.deltaM/2., 
                         width)
        self.parent.dataMandelbrotSet = np.zeros(( width, width), dtype=np.int32)

        self.parent.scalarRandom = "False"
        coords = [(i, j) for j in range(width) for i in range(width)]
        if self.parent.scalarRandom == "True":
            np.random.shuffle(coords)

        # Mandelbrot iteration (scalar operations on a 2D field)
        stop = False

        loopCount = 0
        for i, j in coords: 
            loopCount += 1
            if loopCount % (20*width) == 0:
                self.parent.progressLbl.setText( "Progress: %d/%4d " % (j, width))
                self.parent.app.processEvents()
                if (loopCount % (20*width) == 0):
                    self.MBSUpdated.emit( self.parent.dataMandelbrotSet)
                    self.parent.app.processEvents()
            cx = x[i]
            cy = y[j]
            if self.parent.cardioidBulb == "True":
                if self.inCardioid( cx, cy) or self.inBulb( cx, cy):
                    self.parent.dataMandelbrotSet[ j, i] = self.parent.maxIterM
                    continue
            zx = 0.0
            zy = 0.0
            count = 0

            while zx*zx + zy*zy <= 4.0 and count < self.parent.maxIterM:
                zx_new = zx*zx - zy*zy + cx
                zy = 2.0*zx*zy + cy
                zx = zx_new
                count += 1
                    
            if self.parent.stopRequested:
                stop = True
                break

            self.parent.dataMandelbrotSet[j, i] = count

            if stop:
                self.parent.logWidget.append( "calcScalar: stop detected, break") 
                break


        corr = (utils.DATA_NORM-1)/float( self.parent.maxIterM - 1)
        self.parent.dataMandelbrotSet = self.parent.dataMandelbrotSet.astype(np.float64)
        self.parent.dataMandelbrotSet *= corr
                
        if self.parent.debugSpeed == "True": 
            self.parent.logWidget.append( "M: %5.3f s, Scalar, CardioidBulb %s" % 
                                   (( time.time() - startTime), repr( self.parent.cardioidBulb))) 
        self.parent.progressLbl.setText( "Progress: %4d/%4d M" % ( i, width))
        self.parent.progressLbl.setStyleSheet("background-color:%s" % self.parent.backgroundColor)
        self.parent.progressLbl.hide()

        self.MBSUpdated.emit( self.parent.dataMandelbrotSet)
        
        return 
# ===

    def calcJuliaSet( self, display = True):
        # 
        if self.parent.juliaMode == 'Off':
            return 

        self.isFilteredJ = False
        
        if self.parent.cython == "True":
            return self.calcJuliaSetCython()

        argout = True

        self.progressLbl.show()
        self.progressLbl.setText( "Progress: 0/%4d J" % ( self.maxIterJ))
        self.progressLbl.setStyleSheet("background-color:lightblue")

        if self.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        log_horizon = np.log2(np.log(horizon))

        c = complex( self.cxM, self.cyM)
        x = np.linspace( self.cxJ - self.deltaJ/2.,
                         self.cxJ + self.deltaJ/2.,
                         self.widthJ).reshape((1, self.widthJ))
        y = np.linspace( self.cyJ - self.deltaJ/2.,
                         self.cyJ + self.deltaJ/2.,
                         self.widthJ).reshape(( self.widthJ, 1))
        #
        # z: a 2D field containing the start values of the iterations
        #
        z = x + 1j * y
        #
        # c: a 2D field containing the center of the Mandelbrot set 
        #
        c = np.full(z.shape, c)
        
        escapeCount = np.zeros(z.shape)
        notdone = np.full(c.shape, True, dtype=bool)

        startTime = time.time()
        for it in range( self.maxIterJ):
            if self.numpyOnly or self.deltaM < 1e-11: 
                notdone = np.less( z.real*z.real + z.imag*z.imag, float( horizon))
            else: 
                notdone = ne.evaluate('z.real*z.real + z.imag*z.imag < %g' % float( horizon))
            #notdone = ne.evaluate('z.real*z.real + z.imag*z.imag < %g' % float( horizon))
            escapeCount[notdone] = it
            if self.numpyOnly or self.deltaM < 1e-11: 
                z[notdone] = z[notdone]**2 + c[notdone]
            else: 
                z = ne.evaluate('where(notdone,z**2+c,z)')
            #z = ne.evaluate('where(notdone,z**2+c,z)')
            if self.stopRequested:
                argout = False
                return 
            if display: 
                self.dataJuliaSet = escapeCount
                if it % 100 == 0:
                    self.showJuliaSet()
            self.app.processEvents()

        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= utils.DATA_NORM/float( self.maxIterJ) 

        if self.smooth == "DistEst": 
            temp = np.log( abs(z))
            temp[ temp <= 0.] = LOG_HELPER
            escapeCount = np.nan_to_num( escapeCount + 1 - np.log2( temp) + log_horizon)
            
        self.dataJuliaSet = escapeCount
        self.JuliaSetUpdated.emit( self.parent.dataJuliaSet)
        
        self.showJuliaSet()

        if self.debugSpeed == "True": 
            if not self.isAnimating: 
                self.logWidget.append( "J: %5.3f s, Python, NumpyOnly %s  " % 
                                       ((time.time() - startTime), repr( self.numpyOnly)))
        self.progressLbl.setText( "Progress: %4d/%4d J" % ( it, self.maxIterJ))
        self.progressLbl.setStyleSheet("background-color:%s" % self.backgroundColor)
        self.progressLbl.hide()
        return argout
    
    def calcJuliaSetCython( self, display = True):

        if self.parent.tiled == "True":
            return self.calcJuliaSetCythonTiled()
        
        # Define the complex plane grid
        re_min = self.cxJ - self.deltaJ/2.
        re_max = self.cxJ + self.deltaJ/2.
        im_min = self.cyJ - self.deltaJ/2.
        im_max = self.cyJ + self.deltaJ/2.

        real = np.linspace(re_min, re_max, self.widthJ)
        imag = np.linspace(im_min, im_max, self.widthJ)
        real_grid, imag_grid = np.meshgrid(real, imag)

        if self.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        log_horizon = np.log2(np.log(horizon))

        startTime = time.time()
        (output, zAbs) = mandelbrotCython.compute_julia( real_grid, imag_grid, 
                                                         self.cxM, self.cyM, 
                                                         self.maxIterJ, horizon)

        if self.debugSpeed == "True": 
            if not self.isAnimating: 
                self.logWidget.append( "J: %5.3f s, Cython" % (time.time() - startTime))

        output = output.astype(np.float64)
        output *= utils.DATA_NORM/float( self.maxIterJ) 

        if self.smooth == "DistEst": 
            temp = np.log( zAbs)
            temp[ temp <= 0.] = LOG_HELPER
            output = np.nan_to_num( output + 1 - np.log2( temp) + log_horizon) 

        self.dataJuliaSet = output
        self.JuliaSetUpdated.emit( self.parent.dataJuliaSet)

        return 

    def calcJuliaSetCythonTiled( self):
        import threading

        width = self.parent.widthM
        xmin = self.parent.cxM - self.parent.deltaM/2.
        xmax = self.parent.cxM + self.parent.deltaM/2.
        ymin = self.parent.cyM - self.parent.deltaM/2.
        ymax = self.parent.cyM + self.parent.deltaM/2.

        if self.colorPars.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        log_horizon = np.log2(np.log(horizon))

        mandelbrotTiled.TileWorkerJulia.NCOL = NCOL
        mandelbrotTiled.TileWorkerJulia.NROW = NROW
        mandelbrotTiled.TileWorkerJulia.width = width
        mandelbrotTiled.TileWorkerJulia.cxM = self.parent.cxM
        mandelbrotTiled.TileWorkerJulia.cyM = self.parent.cyM
        mandelbrotTiled.TileWorkerJulia.cxJ = self.parent.cxJ
        mandelbrotTiled.TileWorkerJulia.cyJ = self.parent.cyJ
        mandelbrotTiled.TileWorkerJulia.deltaJ = self.parent.deltaJ
        mandelbrotTiled.TileWorkerJulia.finalImage = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorkerJulia.finalZAbs = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorkerJulia.xmin = xmin
        mandelbrotTiled.TileWorkerJulia.xmax = xmax
        mandelbrotTiled.TileWorkerJulia.ymin = ymin
        mandelbrotTiled.TileWorkerJulia.ymax = ymax
        mandelbrotTiled.TileWorkerJulia.maxIterJ = self.parent.maxIterJ
        mandelbrotTiled.TileWorkerJulia.horizon = horizon
        mandelbrotTiled.TileWorkerJulia.finished_count = 0
        mandelbrotTiled.TileWorkerJulia.total_tiles = NROW*NCOL
        mandelbrotTiled.TileWorkerJulia.lock = threading.Lock()
        
        startTime = time.time()
        workers = []
        #self.parent.logWidget.append( "Starting Julia workers")

        for row in range( NROW): 
            for col in range( NCOL): 
                worker = mandelbrotTiled.TileWorkerJulia( col, row)
                workers.append( worker)
                worker.start()

        while mandelbrotTiled.TileWorkerJulia.finished_count < NROW*NCOL:
            self.parent.app.processEvents()

        escapeCount = mandelbrotTiled.TileWorkerJulia.finalImage
        zAbs = mandelbrotTiled.TileWorkerJulia.finalZAbs
        #
        # nongil cython code has no sqrt()
        #
        #zAbs = np.sqrt( zAbs) 
        
        corr = utils.DATA_NORM/float( self.parent.maxIterM)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr

        if self.colorPars.smooth == "DistEst":
            zAbs[ zAbs <= 0.] = LOG_HELPER
            temp = np.log( zAbs)
            temp[ temp <= 0.] = LOG_HELPER
            output = escapeCount
            corr = np.nan_to_num( escapeCount + 
                                  1 - np.log2( temp)*corr + log_horizon)
            self.parent.dataJuliaSet = np.where(output != 0, corr, output)
        else:
            self.parent.dataJuliaSet = escapeCount
        
        if self.parent.debugSpeed == "True": 
            if not self.parent.isAnimating: 
                self.parent.logWidget.append( "J: %5.3f s, Cython, tiled" % 
                                       (( time.time() - startTime)))

        self.JuliaSetUpdated.emit( self.parent.dataJuliaSet)
                
        return
    
