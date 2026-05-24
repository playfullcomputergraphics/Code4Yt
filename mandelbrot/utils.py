#!/bin/env python3

from matplotlib.colors import Normalize
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import math, random
import numpy as np
from PIL import Image
from PIL import PngImagePlugin
import os, hashlib, time
import mandelbrot, dynamicOperators
import inspect
import MPLViewer, PGViewer

CMAP_MAX = 1024 
#CMAP_MAX = 4096
DATA_NORM = 1024 
DPI = 100

#
# write .png files only from MPL
#
PNG_VERSION = "MPL_1.0.0"

NCOLORCYCLIC_VALUES = [ 128, 256]

CMAP_MAX = 1024 

ANIMATIONFACTOR_VALUES = [ 0.97, 0.99, 0.98, 0.97, 0.96, 0.95]

PRESET_RD_VALUES = {
    "Alpha 1 (F100k470, Loops, spots, chaotic)":
    { "params": { "F": 0.010, "k": 0.047, "IterationsMax": 10000, "dt": 0.1}}, 
    "Alpha 2 (F140k540, Spots, fluctuating, pulsating)":
    { "params": { "F": 0.014, "k": 0.054, "IterationsMax": 10000, "dt": 0.2}}, 
    "Beta 1 (F140k390, Chaos, boiling)":
    { "params": { "F": 0.014, "k": 0.039, "IterationsMax": 20000, "dt": 0.1}},
    "Beta 2 (F260k510, Chaos, boiling)":
    { "params": { "F": 0.026, "k": 0.051, "IterationsMax": 10000, "dt": 0.2}},
    "Beta 3 (F390k580, Chaos to Turing negatons)":
    { "params": { "F": 0.039, "k": 0.058, "IterationsMax": 10000, "dt": 0.2}},
    "Beta 4 (F353k566, Chaos with negatons)":
    { "params": { "F": 0.0353, "k": 0.0566, "IterationsMax": 10000, "dt": 0.2}},
    "Delta (F420k590, Turing patterns)":
    { "params": { "F": 0.042, "k": 0.059, "IterationsMax": 5000, "dt": 0.1}},
    "Epsilon (F220k590, Spots, fluctuating)":
    { "params": { "F": 0.022, "k": 0.059, "IterationsMax": 10000, "dt": 0.5}},
    "Eta (F340k618, Spots and worms)":
    { "params": { "F": 0.034, "k": 0.0618, "IterationsMax": 10000, "dt": 0.5}},
    "Gamma (F260k550, Mazes with some chaos)":
    { "params": { "F": 0.026, "k": 0.055, "IterationsMax": 10000, "dt": 0.5}},
    "Iota (F460k594, Negatons)":
    { "params": { "F": 0.046, "k": 0.0594, "IterationsMax": 10000, "dt": 0.5}},
    "Kappa 1 (F500k630, Mazes)":
    { "params": { "F": 0.050, "k": 0.063, "IterationsMax": 10000, "dt": 1.0}},
    "Kappa 2 (F820k590, Precritical bubbles)":
    { "params": { "F": 0.082, "k": 0.059, "IterationsMax": 20000, "dt": 1.0}},
    "Kappa 3 (F290k570, Mazes)":
    { "params": { "F": 0.029, "k": 0.057, "IterationsMax": 10000, "dt": 1.0}},
    "Kappa 4 (F820k600, Worms and loops)":
    { "params": { "F": 0.082, "k": 0.06, "IterationsMax": 20000, "dt": 1.0}},
    "Kappa 5 (F460k630, Worms join into maze)":
    { "params": { "F": 0.046, "k": 0.063, "IterationsMax": 10000, "dt": 1.0}},
    "Lambda (F300k630, Self-replicating pots)":
    { "params": { "F": 0.03, "k": 0.063, "IterationsMax": 10000, "dt": 0.5}},
    "Mu 1 (F460k650, Spots, Worms from Spots)":
    { "params": { "F": 0.046, "k": 0.065, "IterationsMax": 10000, "dt": 1.0}},
    "Mu 2 (F580k650, Spots turn into worms, all spots)":
    { "params": { "F": 0.058, "k": 0.065, "IterationsMax": 10000, "dt": 1.0}},
    "Nu (F740k640, Stable solitons)":
    { "params": { "F": 0.074, "k": 0.064, "IterationsMax": 10000, "dt": 1.0}},
    "Pi 1 (F620k610, Stripes, spots, negative)     ":
    { "params": { "F": 0.062, "k": 0.061, "IterationsMax": 10000, "dt": 1.0}},
    "Pi 2 (F620k609, U-Skate)":
    { "params": { "F": 0.062, "k": 0.0609, "IterationsMax": 15000, "dt": 0.5}},
    "Rho 1 (F900k590, Crosses, spots)":
    { "params": { "F": 0.090, "k": 0.059, "IterationsMax": 10000, "dt": 0.5}},
    "Rho 2 (F1020k550, Bubbles, soap)":
    { "params": { "F": 0.102, "k": 0.055, "IterationsMax": 10000, "dt": 1.0}},
    "Rho 3 (F980k570, Bubbles)":
    { "params": { "F": 0.098, "k": 0.057, "IterationsMax": 10000, "dt": 1.0}},
    "Sigma 1 (F900k570, Bubbles, breaking connections)":
    { "params": { "F": 0.090, "k": 0.057, "IterationsMax": 10000, "dt": 1.0}},
    "Sigma 2 (F980k555, Negative Bubbles)":
    { "params": { "F": 0.098, "k": 0.0555, "IterationsMax": 10000, "dt": 1.0}},
    "Solitons (F540k670)":
    { "params": { "F": 0.054, "k": 0.067, "IterationsMax": 10000, "dt": 0.5}},
    "Theta 1 (F300k565, Super-resonant mazes)":
    { "params": { "F": 0.030, "k": 0.0565, "IterationsMax": 10000, "dt": 0.5}},
    "Theta 2 (F370k600, Fingerprints)":
    { "params": { "F": 0.037, "k": 0.06, "IterationsMax": 10000, "dt": 0.5}},
    "Xi (F140k470, Waves, fluctuating)":
    { "params": { "F": 0.014, "k": 0.047, "IterationsMax": 10000, "dt": 0.5}},
    "Zeta 1 (F260k590, Spots, fluctuating)":
    { "params": { "F": 0.026, "k": 0.059, "IterationsMax": 10000, "dt": 0.5}},
    "Zeta 2 (F250k600, Pulsating solitons)":
    { "params": { "F": 0.025, "k": 0.06, "IterationsMax": 10000, "dt": 0.5}},
    "A la carte":
    { "params": { "F": 0., "k": 0.0, "IterationsMax": 0, "dt": 0.}},
}

PRESET_SS_VALUES = {
    'Shock': { 'Sigma': 1.2, 'Alpha': 1.0, 'IterationsMax': 6, 'NormLoop': 'False'},
    'ShockOsherRudin': { 'Sigma': 1.2, 'Alpha': 1.0, 'IterationsMax': 6, 'NormLoop': 'True'} ,
    'SoftSharpen': { 'Sigma': 1.0, 'Alpha': 0.6, 'IterationsMax': 2, 'NormLoop': 'True'},
    'EdgedMetal': { 'Sigma': 2.0, 'Alpha': 1.0, 'IterationsMax': 2, 'NormLoop': 'True'},
    'HighContrastSharpen': { 'Sigma': 2.5, 'Alpha': 1.3, 'IterationsMax': 4, 'NormLoop': 'True'},
    'TuringStripes': { 'Sigma': 3.0, 'Alpha': 1.6, 'IterationsMax': 6, 'NormLoop': 'True'},
    'LabyrinthPattern': { 'Sigma': 4.0, 'Alpha': 1.8, 'IterationsMax': 10, 'NormLoop': 'True'},
    'WaveFromtRipples': { 'Sigma': 5.0, 'Alpha': 2.0, 'IterationsMax': 12, 'NormLoop': 'True'},
    'ChaoticReactionDiff': { 'Sigma': 40., 'Alpha': 20., 'IterationsMax': 20, 'NormLoop': 'True'},
    'ExplosiveInstability': { 'Sigma': 7.5, 'Alpha': 3.5, 'IterationsMax': 20, 'NormLoop': 'True'},
}

SIZE_VALUES = [ 'Big', 'Small', 'Medium', 'Big', 'Large'] 

WIDTH_VALUES = [ 500, 10, 50, 100, 200, 250, 256, 300, 400, 500, 600,
                 700, 800, 900, 1000, 1200]

SCALEDUDV_VALUES = [ 1., 0.1, 0.2, 0.3, 0.5, 0.7, 1., 1.1, 1.2, 1.3, 1.5, 2., 3., 4, 5]
RATIODUDV_VALUES = [ 2., 0.5, 1., 1.3, 1.5, 2., 2.5, 3., 4.]

COLORROTATE_VALUES = [ 1, 5, 4, 3, 2, 1, -1, -2, -3, -4, -5]
ROTATEWAITTIME_VALUES = [ 0.1, 0.001, 0.005, 0.01, 0.02, 0.03, 0.05,
                          0.06, 0.07, 0.08, 0.09, 0.1, 0.2, 0.3]
HEIGHT_EXP_VALUES = [ 0.7, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5,
                      0.6, 0.7, 0.8, 0.9, 1., 1.5, 2.0]
AMBIENT_VALUES = [ 0.40, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35,
                   0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
GRAD_SCALE_VALUES = [ 2.0, 1., 1.5, 2.0, 2.5, 3., 3.5, 4., 10, 15, 20]
PG_VERT_EXAG_VALUES = [ 0.1, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5,
                        1, 1.5, 2, 3, 4, 5, 10, 50, 100]
VERT_EXAG_VALUES = [ 1, 1.5, 2, 3, 4, 5, 10, 20, 50, 100, 200, 300, 500]

PG_BLEND_MODE_VALUES = [ 'lum', 'overlay', 'rgb', 'soft', 'lum']
BLEND_MODE_VALUES = [ 'overlay', 'hsv', 'soft'] 

SHADE_GAIN_VALUES = [ 2.5, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7,
                      1.8, 1.9, 2., 2.5, 3., 3.5, 4., 4.5, 5.0, 5.5, 6.0]
STRENGTH_VALUES = [ 0.2, 0., 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1., 1.5] 
AZDEG_VALUES = [ 180, 30, 60, 90, 120, 180, 240, 300, 330, 360] 
ALTDEG_VALUES = [ 10, 1, 3, 5, 8, 20, 30, 40, 50, 60, 70, 80, 90]
ROTATEWAITTIME_VALUES = [ 0.1, 0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.06,
                          0.07, 0.08, 0.09, 0.1, 0.2, 0.3]
COLORROTATE_VALUES = [ 1, 5, 4, 3, 2, 1, -1, -2, -3, -4, -5]
SMOOTH_VALUES = [ 'None', 'DistEst', 'DZ']
PG_INTERPOLATION_VALUES = [ 'none', 'Gauss03', 'Gauss04', 'Gauss05', 'Gauss06', 
                         ]
INTERPOLATION_VALUES = [ 'none', 'bicubic', 'nearest', 'bilinear',  'spline16',
                         'spline36', 'hanning', 'hamming', 'hermite', 'kaiser', 'quadric',
                         'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos']
MODULO_VALUES = [ -1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

NORM_VALUES = [ 'PowerNorm', 'LogNorm', 'InvLogNorm', 'LinNorm', 
                ]
NORMPAR_VALUES = [ 0.25, 0.05, 0.1, 0.15, 0.2, 
                   0.25, 0.3, 0.35, 0.4, 0.45, 
                   0.5, 0.6, 0.7, 0.8, 0.9, 1, 2]
NORMPAR_VALUES_LOG = [ 10, 20, 50, 100, 200, 500, 1000]

CMAPS = [ 'hot', 'viridis', 
          'gnuplot2', 'nipy_spectral',
          'magma', 'inferno', 'bwr', 'Wistia', 
         ]

CMAPS_CYCLIC = [ 'flag', 'prism', 'jet', 'turbo', 
                 'gist_rainbow', 'hsv', 'twilight', 'Paired', 
                 'Pastel1', 'Set1', 'Set2', 'tab10',  
                ]
CMAPS_DCT = { 
    'Uniform': ['viridis', 'plasma', 'inferno', 'magma', 'cividis'],
    'Sequential': ['Greys',  'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                   'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                   'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn'], 
    'Sequential2': ['binary', 'gist_yarg', 'gist_gray', 'gray',
                    'bone', 'pink', 'spring', 'summer', 'autumn',
                    'winter', 'cool', 'Wistia', 'hot', 'afmhot',
                    'gist_heat', 'copper'], 
    'Diverging': ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                  'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm',
                  'bwr', 'seismic', 'vanimo'], 
    'Cyclic': ['twilight', 'twilight_shifted', 'hsv'], 
    'Qualitative': ['Pastel1', 'Pastel2', 'Paired', 'Accent',
                    'Dark2', 'Set1', 'Set2', 'Set3', 'tab10',
                    'tab20', 'tab20b', 'tab20c'],
    'Miscellaneous': ['flag', 'prism', 'ocean', 'gist_earth',
                      'terrain', 'gist_stern', 'gnuplot',
                      'gnuplot2', 'CMRmap', 'cubehelix', 'brg',
                      'gist_rainbow', 'rainbow', 'jet',
                      'turbo', 'nipy_spectral', 'gist_ncar'],}

BACKGROUND_CMAPS = [ 'white', 'black', 'lightyellow', 'lightcyan', 'azure',
                      'dimgrey', 'grey', 'lightgrey', 'whitesmoke']


def createPng( self, fName): 
    if fName.find( '.png') == -1:
        fName += '.png'
    plt.close()
    self.timer.stop()
    self.fig = None
    self.calledFromCreateImage = True
    self.prepareMain()
    self.timerEvent()
    self.calledFromCreateImage = False
    if not os.path.exists( './images'):
        os.mkdir( './images') 
    fName = "./images/%s.%s" % ( fNameIn, ext)
    if os.path.exists( fName): 
        if os.path.exists( './vrsn'): 
            os.system( "./vrsn -s %s" % fName)
        else:
            self.logWidget.append( "%s exists, please rename." % fName)
            self.logWidget.append( "  or copy 'vrsn' to your PWD")
            return 
        plt.savefig(fName)
        self.logWidget.append( "created %s" % fName)
        plt.close( self.fig)
        self.fig = None
        self.restart()
        return

def createGif( self, fName, nFrames = 20, interval = 50): 
    import matplotlib.animation as animation

    if fName.find( '.gif') == -1:
        fName += '.gif'
    self.timer.stop()
    plt.close()
    self.fig = None
    self.calledFromCreateImage = True
    #self.restart()
    self.logWidget.append( "Creating gif file, takes a few seconds") 
    self.app.processEvents()
    self.prepareMain()
    cm = 1/2.54  # centimeters in inches
    if  self.calledFromCreateImage:
        self.fig.set_size_inches( 22*cm, 22*cm)

    ani = animation.FuncAnimation(
        self.fig, self.updatePlot, nFrames, interval=interval, repeat = False)
    self.calledFromCreateImage = False
    if not os.path.exists( './images'):
        os.mkdir( './images')
    if os.path.exists( fName): 
        if os.path.exists( './vrsn'): 
            os.system( "./vrsn -s %s" % fName)
        else:
            self.logWidget.append( "%s exists, please rename." % fName)
            self.logWidget.append( "  or copy 'vrsn' to your PWD")
            return
            
    self.logWidget.append( "Calling the writer") 
    self.app.processEvents()
    writer = animation.PillowWriter( fps=20,
                                     metadata=dict(artist='Me'),
                                     bitrate=1800)
    ani.save( fName, writer=writer)
    self.logWidget.append( "created %s" % fName)
    plt.close( self.fig)
    self.fig = None
    self.restart()
    return 

def derivative( x, y):
    '''
    '''

    x = np.array( x)
    x = x - x[0]
    y = np.array( y)
    ty = np.array( y)

    npoint = len( x)

    for i in range( 1, npoint - 1):
      det = (x[i]*x[i+1]*x[i+1] - x[i+1]*x[i]*x[i] - 
             x[i-1]*x[i+1]*x[i+1] + x[i+1]*x[i-1]*x[i-1] + 
             x[i-1]*x[i]*x[i] - x[i]*x[i-1]*x[i-1])
      if det == 0.:
        raise ValueError( "calc.derivative: det == 0.")

      za1 = (y[i]*x[i+1]*x[i+1] - y[i+1]*x[i]*x[i] -
             y[i-1]*x[i+1]*x[i+1] + y[i+1]*x[i-1]*x[i-1] +
             y[i-1]*x[i]*x[i] - y[i]*x[i-1]*x[i-1])
      za2 = (x[i]*y[i+1] - x[i+1]*y[i] -
             x[i-1]*y[i+1] + x[i+1]*y[i-1] +
             x[i-1]*y[i] - x[i]*y[i-1])

      if i == 1:
          ty[0]   = (za1 + 2.0*za2*x[0])/det

      if i == (npoint - 2):
          ty[ npoint - 1] = (za1 + 2.0*za2*x[npoint -1])/det

      ty[i] = (za1 + 2.0*za2*x[i])/det
 
    return ty


class LinNorm(Normalize):
    def __init__(self, vmin=None, vmax=None, clip=False):
        super().__init__(vmin, vmax, clip)
        self.vmin1 = vmin
        self.vmax1 = vmax

    def __call__(self, value, clip=None):
        # Automatically scale if vmin/vmax are not set
        if self.vmin is None or self.vmax is None:
            self.autoscale(np.asarray(value))

        # Normalize to [0, 1]
        result = (np.asarray(value) - self.vmin1) / (self.vmax1 - self.vmin1)

        # Clip if requested
        if clip or self.clip:
            result = np.clip(result, 0, 1)

        return result

class LinNormR(Normalize):
    def __init__(self, vmin=None, vmax=None, clip=False):
        super().__init__(vmin, vmax, clip)
        self.vmin1 = vmin
        self.vmax1 = vmax

    def __call__(self, value, clip=None):
        # Automatically scale if vmin/vmax are not set
        if self.vmin is None or self.vmax is None:
            self.autoscale(np.asarray(value))

        # Normalize to [0, 1]
        result = (np.asarray(value) - self.vmin1) / (self.vmax1 - self.vmin1)

        # Clip if requested
        if clip or self.clip:
            result = np.clip(result, 0, 1)

        return (1. - result)

class InputDialog(QDialog):
    def __init__(self, prompt="Enter File Name:", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter File Name")

        layout = QVBoxLayout(self)

        self.label = QLabel(prompt)
        layout.addWidget(self.label)

        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.accept)
        layout.addWidget(self.apply_button)
        return 

    def get_value(self):
        return self.line_edit.text()

def findCurrentIndex( x, X):
    '''
    return the position as index of x in X
    used to setup combo boxes
    '''
    #if str( x).lower() == 'linnormr':
    #    x = 'LinNorm'
    #    self.flagReversed = "True"

    if len( X) == 0:
        print( "utils.findCurrentindex: x %s len(X) == 0" % x)
        return 
        
    for i in range( len( X)): 
        if x == X[ i]:
            return i
    print( "findCurrentIndex: failed for %s in %s" % (repr( x), repr( X)))
    return None

class ArrowAwareSlider(QSlider):
    arrowPressed = pyqtSignal(int)   # sendet neuen Wert nach Pfeiltaste

    def keyPressEvent(self, event):
        key = event.key()

        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            # Erst Standardverhalten ausführen (Slider bewegt sich)
            super().keyPressEvent(event)

            # Danach eigenen Callback triggern
            self.arrowPressed.emit(self.value())
        else:
            super().keyPressEvent(event)

def gauss( data, meanX, meanY, A, sigmaX, sigmaY):
    nPts = 20 
    wX = 4.*sigmaX
    wY = 4.*sigmaY
    dX = wX/nPts
    dY = wY/nPts
    x0 = meanX - nPts/2.
    y0 = meanY - nPts/2.
    for i in range( 20):
        x = x0 + i*dX
        for j in range( 20):
            y = y0 + j*dY
            data[ int(x0 + i)][ int( y0 + i)] = \
                A*math.exp( -x**2/(2.*sigmaX) - y**2/(2.*sigmaY))
    
    return data
import numpy as np

def gaussian_2d(A, meanX, meanY, sigmaX, sigmaY, shape=(1000, 1000)):
    """
    Create a 2D Gaussian on a grid of given shape.
    
    Parameters
    ----------
    A : float
        Amplitude of the Gaussian.
    meanX, meanY : float
        Center position of the Gaussian.
    sigmaX, sigmaY : float
        Standard deviations in x and y direction.
    shape : tuple
        Shape of the output array (default: 1000x1000).
    """
    ny, nx = shape
    y = np.arange(ny)
    x = np.arange(nx)
    X, Y = np.meshgrid(x, y)

    gauss = A * np.exp(
        -(((X - meanX)**2) / (2 * sigmaX**2)
          + ((Y - meanY)**2) / (2 * sigmaY**2))
    )
    return gauss.astype(np.float32, copy=False)


def rectangles( data, nrect):
    w = data.shape[0]
    for i in range( nrect):
        wr = random.random()*w/5.
        hr = random.random()*w/5.
        cx = w/3 + random.random()*w/2.
        cy = w/3 + random.random()*w/2.
        z = random.random()*0.8 + 0.1
        x1 = int(cx - wr/2)
        x2 = int(cx + wr/2)
        y1 = int(cy - hr/2)
        y2 = int(cy + hr/2)
        if x1 < 0:
            x1 = 0
        if x1 > (w-1):
            x1 = w - 1
        if x2 < 0:
            x2 = 0
        if x2 > (w-1):
            x2 = w - 1
        if y1 < 0:
            y1 = 0
        if y1 > (w-1):
            y1 = w - 1
        if y2 < 0:
            y2 = 0
        if y2 > (w-1):
            y2 = w - 1
        data[ x1: x2, y1:y2] = z
    return data

def squares( data, nsquare):
    s = data.shape[0]
    if nsquare == 1:
        w = s/20.
        cx = s/2.
        cy = s/2.
        z = 0.5
        x1 = int(cx - w/2)
        x2 = int(cx + w/2)
        y1 = int(cy - w/2)
        y2 = int(cy + w/2)
        data[ x1: x2, y1:y2] = z
        return data
        
    count = 0
    while count < nsquare:
        #w = s*random.random()/10.
        w = 10
        cx = w/2. + random.random()*(s-w)
        cy = w/2. + random.random()*(s-w)
        z = random.random()*0.8 + 0.2
        x1 = int(cx - w/2)
        x2 = int(cx + w/2)
        y1 = int(cy - w/2)
        y2 = int(cy + w/2)
        if np.any(data[x1:x2, y1:y2]):
            continue
        count += 1
        data[ x1: x2, y1:y2] = z

    return data

def circles( data, ncircle):
    s = data.shape[0]
    if ncircle == 1:
        add_circle( data, center = (s/2., s/2.), radius = s/20, value = 0.5)
        return data
        
    count = 0
    while count < ncircle:
        #w = s*random.random()/50.
        w = s/100.
        cx = s/20 + random.random()*s/1.2
        cy = s/20 + random.random()*s/1.2
        z = random.random()*0.8 + 0.2
        add_circle( data, center = (cx, cy), radius = w, value = z)
        count += 1
    return data

def add_circle(field, center, radius, value):
    """
    Draw a filled circle into a 2D field.

    Parameters
    ----------
    field : np.ndarray
        2D array to modify in-place.
    center : tuple (cx, cy)
        Circle center in array coordinates.
    radius : float
        Circle radius in grid units.
    value : float
        Value to assign inside the circle.
    """
    h, w = field.shape
    y, x = np.ogrid[:h, :w]
    cx, cy = center

    mask = (x - cx)**2 + (y - cy)**2 <= radius**2
    field[mask] = value
    return 

def message( self, msg): 
    temp = QMessageBox()
    temp.question(self,'', "%s" % msg, temp.Ok )
    return 

def trimCenterName( name):
    nameIn = name
    
    if name.find( './places/') == 0:
        name = name[ 9:]
        
    if name.find( 'MB_') == 0:
        name = name[ 3:]
    if name.find( 'MBN_') == 0:
        name = name[ 4:]
        
    if name.find( 'DynOp_') == 0:
        name = name[ 6:]
    if name.find( 'DynOpN_') == 0:
        name = name[ 7:]
        
    if name.find( '.png') > 0:
        name = name[:-4]
        
    #print( "utils.trimCenterName: %s -> %s" % (nameIn, name)) 
    return name

class ClickableThumbnail(QLabel):
    clickedMbLeft = pyqtSignal(str)  # Emit the image path
    clickedMbRight = pyqtSignal(str)  # Emit the image path
    clickedMbMiddle = pyqtSignal(str)  # Emit the image path

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.image_path = image_path

    def mousePressEvent(self, event):
        if hasattr( self.parent, 'resetMarker'):
            self.parent.resetMarker.set( text = r'') 
        if event.button() == 1:
            self.clickedMbLeft.emit(self.image_path)
        elif event.button() == 2:
            self.clickedMbRight.emit(self.image_path)
        elif event.button() == 4:
            self.clickedMbMiddle.emit(self.image_path)
        return
    
    def enterEvent(self, event):
        #print("Hover enter: %s, text %s" %
        #       (self.image_path, self.parent.path2Lbl[ self.image_path].text()))
        # call your callback here
        if self.parent.path2Lbl is not None:
            self.parent.path2Lbl[ self.image_path].setStyleSheet( "QLabel { color: yellow; font-family: Consolas, monospace;font-size: 10pt; }")
        event.accept()
        
    
    def leaveEvent(self, event):
        #print("Hover leave:", self.image_path)
        # call your callback here
        if self.parent.path2Lbl is not None:
            self.parent.path2Lbl[ self.image_path].setStyleSheet( "QLabel { color: blue; font-family: Consolas, monospace;font-size: 10pt; }")

        event.accept()

class JpgViewer(QWidget):
    incrFeedRate = pyqtSignal()
    decrFeedRate = pyqtSignal()
    incrKillRate = pyqtSignal()
    decrKillRate = pyqtSignal()
    
    def __init__(self, fileName = None, parent=None):
        super().__init__(parent)

        self.labelFk = ClickableLabel( self)
        self.name = "JpgViewer"
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.labelFk)
        self.setLayout( self.layout)

        image = Image.open( fileName)
        arr = np.array( image)
        arr = np.flipud( arr) 
        image.close()
        self.setData( arr)

        self.setWindowTitle("Jpg Viewer")
        #self.resize(w, h)
        self.labelFk.setMinimumSize(1, 1)
        self.labelFk.setScaledContents(True)
        #self.resize( 450, 450)

        self.arrFkPath = []
        
        self.prepareStatusBar()

        return

    def prepareStatusBar( self): 
        hLayout = QHBoxLayout()
        self.layout.addLayout( hLayout)
        
        left = QPushButton("Left") 
        left.setToolTip( "Decrease kill rate")
        left.clicked.connect( self.cb_leftPb)
        hLayout.addWidget( left)
        
        up = QPushButton("Up") 
        up.setToolTip( "Increase feed rate")
        up.clicked.connect( self.cb_upPb)
        hLayout.addWidget( up) 
        
        down = QPushButton("Down") 
        down.setToolTip( "Decrease feed rate")
        down.clicked.connect( self.cb_downPb)
        hLayout.addWidget(down)

        right = QPushButton("Right") 
        right.setToolTip( "Increase kill rate")
        right.clicked.connect( self.cb_rightPb)
        hLayout.addWidget( right)

        quit = QPushButton("&Quit") 
        quit.setToolTip( "Close the window")
        quit.clicked.connect( self.cb_quit)
        hLayout.addWidget( quit)

        return 

    def cb_leftPb( self):
        self.decrKillRate.emit()
        return 

    def cb_rightPb( self):
        self.incrKillRate.emit()
        return 

    def cb_upPb( self):
        print( "%s.cb_upPb. newFeedRate.emit" % self.name)
        self.incrFeedRate.emit()
        return 

    def cb_downPb( self):
        self.decrFeedRate.emit()
        return 

    def cb_quit( self):
        self.hide()
        return 
                                
    def closeEvent( self, event):
        self.hide()
        event.ignore()
        #print( "%s.close event: hide and ignore" % self.name)
        return

    def addFkPath( self, path, F, k):
        # +++
        temp = ClickableLabel( self)
        #temp.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        #temp.setFont(QFont('Arial', 10))
        temp.setStyleSheet( "QLabel { color: blue; font-family: Consolas, monospace;font-size: 10pt; }")
        temp.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        temp.setText( path)
        temp.adjustSize()
        
        y = (F - self.ymin)/(self.ymax - self.ymin)*self.height()
        x = (k - self.xmin)/(self.xmax - self.xmin)*self.width()
        y = self.height() - y
        
        temp.move(int(x + 12), int(y))
        temp.show()

        self.arrFkPath.append( temp)
        
        #print( "%s.addFkPath %s F %g k %g y %g x %g" % ( self.name, path, F, k, y, x))

        return temp
    
    def setData( self, img):
        img = img.T
        img = np.rot90(img, k=1, axes=(1, 2))
        # Convert (C, H, W) → (H, W, C)
        img = np.transpose(img, (1, 2, 0)).copy()
        h, w, c = img.shape
        # Select QImage format
        if c == 4:
            fmt = QImage.Format_RGBA8888
            bytes_per_line = 4 * w
        elif c == 3:
            fmt = QImage.Format_RGB888
            bytes_per_line = 3 * w
        else:
            raise ValueError("Only 3 or 4 channel images are supported")

        # Create QImage
        qimg = QImage(img.data, w, h, bytes_per_line, fmt)

        # Convert to QPixmap
        pixmap = QPixmap.fromImage(qimg)

        self.labelFk.setPixmap(pixmap)
        # +++
        self.w = int( w*0.8)
        self.h = int( h*0.8)

        self.resize( self.w, self.h)
        self.xmin = 0.0195
        self.xmax = 0.0745
        self.ymin = -0.0025
        self.ymax = 0.113
        return
    
class ClickableLabel(QLabel):
    clicked = pyqtSignal( float, float)   # x, y in label coordinates
    moved = pyqtSignal( float, float)   # x, y in label coordinates

    def __init__( self, parent):

        super().__init__(parent)
        self.parent = parent
        self.name = "ClickableLabel"
        #self.setMouseTracking(True) enables move event
        self.cursor_pos = None

        self.initMembers()
        
        return

    def initMembers( self):
        self.painter = None
        self.FkMarker = None
        return
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.pos().x()
            xtemp = x/float( self.parent.w)*\
                (self.parent.xmax - self.parent.xmin) + self.parent.xmin
            y = event.pos().y()
            y = self.parent.h - y
            ytemp = y/float( self.parent.h)*\
                (self.parent.ymax - self.parent.ymin) + self.parent.ymin
            self.FkMarker = event.pos()
            self.update()
            
            self.clicked.emit( xtemp, ytemp)
        elif event.button() == Qt.RightButton:
            self.FkMarker = None
            self.update()

        return

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.FkMarker is not None:
            x = self.FkMarker.x()
            y = self.FkMarker.y()
            self.paintCross( x, y)
        return

    def paintCross( self, x, y):
        #print( "%s.paintCross: F %g, k %g" % ( self.name, x, y))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        painter.setPen(QPen(Qt.white, 2))
        size = 6
        painter.drawLine( int( x - size), int( y), int( x + size), int( y))
        painter.drawLine( int( x), int( y - size), int( x), int( y + size))
        
        return

    def paintFk( self, F, k):
        #print( "%s.paintFk: F %g, k %g" % ( self.name, F, k))
        y = int( (F - self.parent.ymin)/(self.parent.ymax - self.parent.ymin)*self.parent.h)
        x = int( (k - self.parent.xmin)/(self.parent.xmax - self.parent.xmin)*self.parent.w)
        y = self.parent.h - y
        self.FkMarker = QPoint(x, y)
        # Trigger repaint
        self.update()
        return

    def enterEvent(self, event):
        #print("Hover enter: text %s" % (self.text()))
        # call your callback here
        event.accept()
        return 
    
    def leaveEvent(self, event):
        #print("Hover leave: text %s" % (self.text()))
        # call your callback here
        event.accept()
        return 
    
COLORPARS_METADATA_MEMBERS = [
    "colorMapName", "vmin", "vmax", 
    "flagReversed", "colorPhase", "flagCyclic", "rotateColorMapIndex",
    "norm", "normPar", "shaded", "blackFixed", "nColorCyclic",
    "resetMarker", "rotateWaitTime", "colorRotateValue", "vert_exag",
    "blendMode", "smooth", "interpolation", "altDeg", "azDeg", "clip",
    "band", 
]

#
# beware of typos, check whether a member is in the list of known members
#
COLORPARS_ATTRS = COLORPARS_METADATA_MEMBERS + \
    [ 'app', 'busy', 'cmapLbl', 'smoothModeCombo', 'colorMap', 
      'interpolationModeCombo', 'cmapRotateSliderLbl',
      'cmapRotateSlider', 'colorRotateExecPb', 'normCombo',
      'normParCombo', 'vminSlider', 'vminSliderLbl',
      'vmaxSlider', 'vmaxSliderLbl', 'shadedCb', 
      'azDegCombo', 'altDegCombo', 'vert_exagCombo', 'blendModeCombo', 
      'reversedCb', 'cyclicCb', 'colorRotateCombo', 'rotateWaitTimeCombo',
      'parent', 'name', 'isRotating', 'blackFixedCb',
      'colorPars', 'isRotating', 'animationFactor', 'useMPL', 
     ]

class ColorPars( QWidget):

    setColor = pyqtSignal()
    
    def __init__( self, parent = None):

        super().__init__(parent)
        self.parent = parent
        self.name = "ColorPars"
        #print( "%s.__init__: called from %s" % ( self.name, self.parent.name))

        self.colorMapName = 'hot'
        self.vmin = 0
        self.vmax = 1023
        self.colorMapName = 'hot'
        self.flagReversed = "False"
        self.colorPhase = 0
        self.flagCyclic = "False"
        self.rotateColorMapIndex = 0
        self.norm = NORM_VALUES[0]        
        self.normPar = NORMPAR_VALUES[0]
        self.shaded = "False"
        self.blackFixed = "True"
        self.nColorCyclic = NCOLORCYCLIC_VALUES[0]
        
        self.resetMarker = None
    
        self.rotateWaitTime = ROTATEWAITTIME_VALUES[0]
        self.colorRotateValue = COLORROTATE_VALUES[0]
        if self.parent.useMPL:
            self.vert_exag = float( VERT_EXAG_VALUES[0])
            self.blendMode = BLEND_MODE_VALUES[0]
            self.interpolation = INTERPOLATION_VALUES[0]
        else:
            self.vert_exag = float( PG_VERT_EXAG_VALUES[0])
            self.blendMode = PG_BLEND_MODE_VALUES[0]
            self.interpolation = PG_INTERPOLATION_VALUES[0]
        self.smooth = SMOOTH_VALUES[ 0]
        
        self.altDeg = ALTDEG_VALUES[0]
        self.azDeg = AZDEG_VALUES[0]
        self.clip = "True"
        self.band = "False"

        return 

    def __setattr__( self, name, value):
        #print( "ColorPars.__setattr__: name %s, value %s" %
        #       (name, value))

        if name in COLORPARS_ATTRS:
            super( ColorPars, self).__setattr__(name, value)
        else:
            #
            # the MBN_ files become members of self,
            # needed by 'center' feature
            #
            if name.find( 'MBN_') != 0 and \
               name != 'Center':
                print( " unknown attribute (colorPars): '%s'," %  name)
            super( ColorPars, self).__setattr__(name, value)

    def extractParameters( self, hsh):

        print( "")
        print( "Reading ColorPars")
        
        self.colorMapName = hsh[ 'colorMapName']
        del hsh[ 'colorMapName']
        print( "  colorMapName: %s " % self.colorMapName)
        
        try: 
            self.colorPhase = float( hsh[ 'colorPhase'])
            del hsh[ 'colorPhase']
        except: 
            pass
        print( "  colorPhase: %g " % self.colorPhase)
                
        try: 
            self.rotateColorMapIndex = int( hsh[ 'rotateColorMapIndex'])
            del hsh[ 'rotateColorMapIndex']
        except: 
            self.rotateColorMapIndex = 0
        print( "  rotateColorMapIndex: %d " % self.rotateColorMapIndex)

        self.rotateWaitTime = ROTATEWAITTIME_VALUES[0]
        try:
            self.rotateWaitTime = float( hsh[ 'rotateWaitTime'])
            del hsh[ 'rotateWaitTime']
        except:
            pass
        print( "  rotateWaitTime: %g " % self.rotateWaitTime)
        
        self.colorRotateValue = COLORROTATE_VALUES[0]
        try:
            self.colorRotateValue = float( hsh[ 'colorRotateValue'])
            del hsh[ 'colorRotateValue']
        except:
            pass
        print( "  colorRotateValue: %g " % self.colorRotateValue)
        
        self.flagReversed = "False"
        try: 
            self.flagReversed = hsh[ 'flagReversed']
            del hsh[ 'flagReversed']
        except:
            pass
        print( "  flagReversed: %s " % self.flagReversed)
        
        self.norm = hsh[ 'norm']
        del hsh[ 'norm'] 
        print( "  norm: %s " % self.norm)
        if self.norm == "LinNormR":
            self.norm = "LinNorm"
            self.flagReversed = "True"
        self.normPar = float( hsh[ 'normPar'])
        del hsh[ 'normPar']
        print( "  normPar: %g " % self.normPar)
        
        self.flagCyclic = "False"
        try: 
            self.flagCyclic = hsh[ 'flagCyclic']
            del hsh[ 'flagCyclic'] 
        except:
            pass
        print( "  flagCyclic: %s " % self.flagCyclic)
        
        self.smooth = hsh[ 'smooth']
        del hsh[ 'smooth'] 
        print( "  smooth: %s " % self.smooth)
        
        self.vmin = 0
        try: 
            self.vmin = float( hsh[ 'vmin'])
            del hsh[ 'vmin'] 
        except:
            pass
        print( "  vmin: %g " % self.vmin)
        
        self.vmax = 1024
        try: 
            self.vmax = float( hsh[ 'vmax'])
            del hsh[ 'vmax'] 
        except:
            pass
        print( "  vmax: %g " % self.vmax)
        
        self.shaded = hsh[ 'shaded']
        del hsh[ 'shaded']
        print( "  shaded: %s " % self.shaded)
        
        self.blackFixed = "True"
        try: 
            self.blackFixed = hsh[ 'blackFixed']
            del hsh[ 'blackFixed'] 
        except:
            pass
        print( "  blackFixed: %s " % self.blackFixed)
        
        self.vert_exag = 1.
        try: 
            self.vert_exag = float( hsh[ 'vert_exag'])
            del hsh[ 'vert_exag'] 
        except:
            pass
        if not self.parent.useMPL: 
            if self.vert_exag not in PG_VERT_EXAG_VALUES:
                self.vert_exag = PG_VERT_EXAG_VALUES[0]
        else: 
            if self.vert_exag not in VERT_EXAG_VALUES:
                self.vert_exag = VERT_EXAG_VALUES[0]
        print( "  vert_exag: %g " % self.vert_exag)
            
        try: 
            self.interpolation = hsh[ 'interpolation']
            del hsh[ 'interpolation'] 
        except:
            pass
        if not self.parent.useMPL:
            if self.interpolation not in PG_INTERPOLATION_VALUES:
                self.interpolation = PG_INTERPOLATION_VALUES[0]
        else: 
            if self.interpolation not in INTERPOLATION_VALUES:
                self.interpolation = INTERPOLATION_VALUES[0]
        print( "  interpolation: %s " % self.interpolation)

        try: 
            self.blendMode = hsh[ 'blendMode']
            del hsh[ 'blendMode'] 
        except:
            pass

        if not self.parent.useMPL:
            if self.blendMode not in PG_BLEND_MODE_VALUES:
                self.blendMode = 'lum'
        else: 
            if self.blendMode not in BLEND_MODE_VALUES:
                self.blendMode = 'soft'
        print( "  blendMode: %s " % self.blendMode)

        self.azDeg = int( float( hsh[ 'azDeg']))
        del hsh[ 'azDeg'] 
        print( "  azDeg: %g " % self.azDeg)

        self.altDeg = int( float( hsh[ 'altDeg'])) # '90.0' gave trouble
        del hsh[ 'altDeg'] 
        print( "  altDeg: %g " % self.altDeg)

        return

    def setDefaults( self):

        self.norm = NORM_VALUES[0]        
        self.normPar = NORMPAR_VALUES[0]
        
        self.flagReversed = "False"
        self.flagCyclic = "False"
        self.nColorCyclic = NCOLORCYCLIC_VALUES[0]
        self.isRotating = False
        self.rotateWaitTime = ROTATEWAITTIME_VALUES[0]
        self.colorRotateValue = COLORROTATE_VALUES[0]
        self.azDeg = AZDEG_VALUES[0]
        self.animationFactor = ANIMATIONFACTOR_VALUES[0]
        self.altDeg = ALTDEG_VALUES[0]
        if self.parent.useMPL:
            self.vert_exag = float( VERT_EXAG_VALUES[0])
            self.blendMode = BLEND_MODE_VALUES[0]
            self.interpolation = INTERPOLATION_VALUES[0]
        else:
            self.vert_exag = float( PG_VERT_EXAG_VALUES[0])
            self.blendMode = PG_BLEND_MODE_VALUES[0]
            self.interpolation = PG_INTERPOLATION_VALUES[0]
        
        self.colorMapName = 'hot'
        self.rotateColorMapIndex = 0
        self.band = "False"
        self.setColor.emit()
        return

def formatThumbLabel( path):
        argout = path.split('/')[-1]
        argout = argout.split( '.')[-2]
        temp = argout.split( '_')
        #
        # take4 care of e.g. DynOp_09be0f19_00001.png
        #
        if len( temp) == 3:
            argout = temp[-2] + "..."
        else:
            argout = temp[-1]
        return argout
#
# fName: ./places/DynOp_46f17cef.png
#
def handleFeedAndKillRate( fName, viewerFk):
    image = Image.open(fName)
    hsh = image.info
    image.close()
    feedRate = float( hsh[ 'feedRate'])
    killRate = float( hsh[ 'killRate'])
    temp = formatThumbLabel( fName)
    lbl = viewerFk.addFkPath( temp, feedRate, killRate) 
    #print( "utils.handleFeedAndKillRate: fName %s F %g k %g" % ( temp, feedRate, killRate))
    return lbl

def readPng( fName,
             MBSObj = None,
             DynOpObj = None,
             ColorWidgetObj = None, 
             ColorParsObj = None):

    if (DynOpObj is not None) and \
       (DynOpObj.thread is not None) and \
       DynOpObj.thread.isRunning():
        message( None, "readPngMBS: operatorWorker is already running, return")
        return 
    #
    # find the calling function:
    #   if 'DynOp' is part of the file name it is DynOpObj
    #
    if fName.find( "DynOp") > 0:
        isMBS = False
        calledFromObj = DynOpObj
        if MBSObj is not None:
            message( None, "utils.readPng: fName %s but MSBObj is not None, return " %
                     ( fName))
            return 
    else:
        isMBS = True
        calledFromObj = MBSObj

    print( "utils.readPng: calledFromObj %s" % (calledFromObj.name))
    image = Image.open(fName)

    hsh = image.info
    image.close()
    calledFromObj.lastFileRead = fName
    temp = trimCenterName( fName)
    calledFromObj.lastReadLbl.setText( temp)
    calledFromObj.logWidget.append( "Reading %s" % ( fName))
    
    #print( "Reading %s" % ( fName))
    #for elm in hsh:
    #    print( "  %-14s : %s" % ( elm, hsh[ elm]))
    #print( "Reading Done")

    calledFromObj.version = "MPL_1.0.0"
    try: 
        calledFromObj.version = hsh[ 'Version']
    except:
        hsh[ 'Version'] = calledFromObj.version

    try: 
        temp = hsh[ 'useMPL'] == "True"
        del hsh[ 'useMPL']
        print( "%s.readPng: comparing %s and %s" %
               ( calledFromObj.name, temp, calledFromObj.useMPL))
        if temp != calledFromObj.useMPL:
            message( None, "readPng: File was created with useMPL == %s, \nwe are at useMPL == %s" %
                     ( repr( temp), repr( calledFromObj.useMPL)))
    except:
        pass


    if calledFromObj.name == "MBSMainWindow":
        print( "")
        print( "Reading Mandelbrot parameters") 
        MBSObj.cxM = float( hsh[ 'cxM'])
        print( "  cxM: %g " % MBSObj.cxM)
        del hsh[ 'cxM'] 
        MBSObj.cyM = float( hsh[ 'cyM'])
        print( "  cyM: %g " % MBSObj.cyM)
        del hsh[ 'cyM'] 
        MBSObj.deltaM = float( hsh[ 'deltaM'])
        print( "  deltaM: %g " % MBSObj.deltaM)
        del hsh[ 'deltaM'] 
        MBSObj.widthM = int( hsh[ 'widthM'])
        print( "  widthM: %g " % MBSObj.widthM)
        del hsh[ 'widthM'] 
        MBSObj.widthJ = int( hsh[ 'widthJ'])
        print( "  widthJ: %g " % MBSObj.widthJ)
        del hsh[ 'widthJ'] 
        MBSObj.maxIterM = int( hsh[ 'maxIterM'])
        print( "  maxIterM: %d " % MBSObj.maxIterM)
        del hsh[ 'maxIterM'] 
        MBSObj.maxIterJ = int( hsh[ 'maxIterJ'])
        print( "  maxIterJ: %d " % MBSObj.maxIterJ)
        del hsh[ 'maxIterJ'] 
        MBSObj.scanCircle = hsh[ 'scanCircle']
        print( "  scanCircle: %s " % MBSObj.scanCircle)
        del hsh[ 'scanCircle'] 
        MBSObj.addCenterItem( name = fName, cx = MBSObj.cxM, cy = MBSObj.cyM)

        MBSObj.execDynOp = "False"
        try:
            MBSObj.execDynOp = hsh[ 'execDynOp']
        except:
            pass
        print( "  execDynOp: %s " % MBSObj.execDynOp)
    #
    # extract ColorPars parameters
    #
    ColorParsObj.extractParameters( hsh)
    #
    # extract DynOp parameters
    #
    DynOpObj.extractParameters( hsh) 
    DynOpObj.viewerFk.labelFk.paintFk( DynOpObj.feedRate, DynOpObj.killRate) 
    #
    # set current indices
    #
    calledFromObj.updateGUI()
    ColorWidgetObj.updateGUI()
    calledFromObj.viewerMain.setColor()

    if (not isMBS) or (MBSObj.execDynOp == "True"): 
        #print( "readPngMBS: not isMBS or execDynOp == True") 
        DynOpObj.enableWidgets()
        #
        # iterationsMax may differ from the preset
        #
        if DynOpObj.iterations > DynOpObj.iterationsMax: 
            DynOpObj.iterationsMax = DynOpObj.iterations
        DynOpObj.iterations = 0
        calledFromObj.updateGUI()
        DynOpObj.updateGUI()
        DynOpObj.makeOperatorFunction()
        DynOpObj.cb_resetUV()
        DynOpObj.show()
        #
        # note that if isMBS and execDynOp: calcMandelbrotSet() calls runOp()
        #
        if not isMBS:  
            DynOpObj.startOp()
    
    if isMBS:
        calledFromObj.engine.calcMandelbrotSet()

    return 

def writePng( midFix = None,
              prefix = None, 
              MBSObj = None,
              DynOpObj = None,
              ColorParsObj = None): 
    """
    writePng() can be called from mandelbrot.py of dynamicOperators.py
    """

    if prefix == "MB":
        isMBS = True
        calledFromObj = MBSObj
    else:
        isMBS = False
        calledFromObj = DynOpObj
    # no there are nice PG plots
    #if not calledFromObj.useMPL:
    #    message( "%s.writePng: only for MPL" % (MBSObj.name))
    #    return

    print( "utils.writePng: calledFromObj %s" % ( calledFromObj.name))
    
    if prefix is None:
        prefix = "MB"
        
    ext = 'png'
            
    print( "%s.writePng: ext %s, midFix %s %s" %
           ( calledFromObj.name, ext, midFix, midFix is None))

    # 
    if not os.path.exists( './places'):
        os.mkdir( './places') 

    if prefix == "MB":
        key = "%g%g%g%d%s%g%s%d" % \
            ( getattr( MBSObj, 'cxM'),
              getattr( MBSObj, 'cyM'),
              getattr( MBSObj, 'deltaM'), 
              getattr( MBSObj, 'maxIterJ'),
              getattr( ColorParsObj, 'shaded'), 
              getattr( ColorParsObj, 'normPar'),
              getattr( ColorParsObj, 'colorMapName'),
              time.time())
    else: 
        key = "%s%g%g%s%s%g%s%d" % \
            ( getattr( DynOpObj, 'presetName'), 
              getattr( DynOpObj, 'feedRate'), 
              getattr( DynOpObj, 'killRate'), 
              getattr( DynOpObj, 'operatorName'),
              getattr( ColorParsObj, 'shaded'), 
              getattr( ColorParsObj, 'normPar'),
              getattr( ColorParsObj, 'colorMapName'),
              time.time()) 
        
    if midFix is None: 
        temp = hashlib.md5(key.encode()).hexdigest()[:8]  # e.g., 'a3f9c1d2'
        fName = "./places/%s_%s.%s" % ( prefix, temp, ext)
    else: 
        #
        # the mid part of the file name has been supplied, add
        # 2B of hash code to allow for several files
        #
        temp = hashlib.md5(key.encode()).hexdigest()[:2]  # e.g., 'a3f9c1d2'
        fName = "./places/%s_%s%s.%s" % ( prefix, midFix, temp, ext)

    if os.path.exists( fName): 
        if os.path.exists( './vrsn'): 
            os.system( "./vrsn -s %s" % fName)
        else:
            calledFromObj.logWidget.append( "%s exists, please rename." % fName)
            calledFromObj.logWidget.append( "  or copy 'vrsn' to your PWD")
            return

    if calledFromObj.viewerMain.current == 'mpl':
        print( "writePng: write from MPL") 
        calledFromObj.viewerMain.mpl.fig.savefig(fName)
    elif calledFromObj.viewerMain.current == 'pg':
        print( "writePng: write from PG") 
        qimg = calledFromObj.viewerMain.pg.view.grab().toImage()
        qimg.save( fName)
    else: 
        message( None, "writePng: unable to detect mpl/pg, return ")
        return
        
    temp = trimCenterName( fName)
    if calledFromObj.lastReadLbl is not None: 
        calledFromObj.lastReadLbl.setText( temp)
        
    im = Image.open(fName)
    meta = PngImagePlugin.PngInfo()
    print( "Writing %s" % fName)
    
    meta.add_text( 'Version', PNG_VERSION)
    print( " %14s : %s" % ( 'Version', PNG_VERSION))
    meta.add_text( 'Content', prefix)
    print( " %14s : %s" % ( 'Content', prefix))
    meta.add_text( 'useMPL', str( calledFromObj.useMPL))
    print( " %14s : %s" % ( 'useMPL', str(calledFromObj.useMPL)))

    if MBSObj is not None: 
        print( "Mandelbrot parameters")
        for elm in mandelbrot.METADATA_MEMBERS:
            meta.add_text( elm, str( getattr( MBSObj, elm)))
            print( "  %14s : %s" % ( elm, str( getattr( MBSObj, elm))))
        
    print( "ColorPars")
    for elm in COLORPARS_METADATA_MEMBERS:
        meta.add_text( elm, str( getattr( ColorParsObj, elm)))
        print( "  %14s : %s" % ( elm, str( getattr( ColorParsObj, elm))))

    if calledFromObj == DynOpObj or MBSObj.execDynOp == 'True': 
        print( "DynOp parameters")
        for elm in dynamicOperators.METADATA_MEMBERS:
            meta.add_text( elm, str( getattr( DynOpObj, elm)))
            print( "  %14s : %s" % ( elm, str( getattr( DynOpObj, elm))))

    print( "Writing done")

    im.save(fName, "png", pnginfo=meta)

    calledFromObj.logWidget.append( "created %s" % fName)

    if calledFromObj.placesWidget is not None:
        calledFromObj.placesWidget.prepareCentralWidget()

    return
