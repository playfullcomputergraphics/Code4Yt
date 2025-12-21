#!/bin/env python3

from matplotlib.colors import Normalize
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import math
import numpy as np

CMAPS = [ 'hot', 'viridis', 
          'gnuplot2', 'nipy_spectral', 'jet',
          'magma', 'inferno', 
         ]

CMAPS_CYCLIC = [ 'flag', 'prism', 'jet', 'turbo', 
                 'gist_rainbow', 'hsv', 'twilight', 'Paired', 
                 'Set1', 
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

