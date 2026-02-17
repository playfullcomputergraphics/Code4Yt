#!/usr/bin/env python3
# 1.2.2026
import os, sys, time, math, random, json, hashlib
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import matplotlib 
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.backend_bases import MouseButton
sys.path.append( "./cython") 
try: 
    import mandelbrotCython
    cythonOK = True
except: 
    cythonOK = False

try: 
    from numba import cuda
    numbaOK = True
except:
    numbaOK = False

import mandelbrotTiled
import mandelbrotPlaces
import threading

import numpy as np
import numexpr as ne
import utils
from PIL import Image
from PIL import PngImagePlugin
#
# NROW/NCOL used for tiling
# compare not-tiled/tiled
# 2: 0.53 / 0.17
# 4: 0.53 / 0.091
# 5: 0.53 / 0.085
#
NROW = 5
NCOL = 5

DPI = 100
DATA_NORM = 1024
TEXT_OFFSET = 0.03
CMAP_MAX = 1024 # appears also in mandelbrotPlaces.py
MODULO_VALUES = [ -1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
#POWER_VALUES = [ 2, 3, 4, 5, 6, 7, 8, 9, 10]
SPIRAL_VALUES = [ 0, -1, 1, 2, 3, 4]
NORMPAR_VALUES = [ 0.25, 0.05, 0.1, 0.15, 0.2, 
                   0.25, 0.3, 0.35, 0.4, 0.45, 
                   0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40, 50]
COLORROTATE_VALUES = [ 1, 5, 4, 3, 2, 1, -1, -2, -3, -4, -5]
NCOLORCYCLIC_VALUES = [ 128, 256]
ROTATEWAITTIME_VALUES = [ 0.1, 0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.2, 0.3]
NORM_VALUES = [ 'PowerNorm', 'LogNorm',
                'LinNorm', 'AsinhNorm', 
                'HistNorm', 'TwoSlopeNorm', 'StretchNorm', 
                ]
SCAN_POINT_VALUES = [ 200, 50, 100, 200, 300, 500, 1000]
ZOOM_VALUES = [ 4, 1., 1.2, 1.5, 2, 3, 4, 8, 16,]
WIDTH_VALUES = [ 1000, 10, 50, 100, 256, 400, 500, 600, 700, 800, 900, 1000, 1200]
WIDTH_BIG = WIDTH_VALUES[0]
WIDTH_SMALL = int( WIDTH_VALUES[0]/2.)
AZDEG_VALUES = [ 180, 30, 60, 90, 120, 180, 240, 300, 330, 360] 
ALTDEG_VALUES = [ 10, 1, 5, 20, 30, 40, 50, 60, 70, 80, 90]
ANIMATIONCOLOR_VALUES = [ 'Yes', 'No']
ANIMATIONFACTOR_VALUES = [ 0.97, 0.99, 0.98, 0.97, 0.96, 0.95]
BLEND_MODE_VALUES = [ 'overlay', 'hsv', 'soft'] 
VERT_EXAG_VALUES = [ 1., 1.5, 2., 3., 4., 5., 10., 20, 50., 100, 200, 300, 500]

MAX_ITER_VALUES = [ 512, 16, 32, 64, 128, 256, 384, 512, 768,
                    1024, 1536, 2048, 4096, 8192, 16384, 32768]
INTERPOLATION_VALUES = [ 'none', 'bicubic', 'nearest', 'bilinear',  'spline16',
           'spline36', 'hanning', 'hamming', 'hermite', 'kaiser', 'quadric',
           'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos']
SMOOTH_VALUES = [ 'None', 'DistEst', 'DZ']
JULIA_MODE_VALUES = [ 'Off', 'Tiny', 'Small', 'Medium', 'Big', 'Large', 'Huge'] 
MANDELBROT_MODE_VALUES = [ 'Tiny', 'Small', 'Medium', 'Big', 'Large', 'Huge'] 

LOG_HELPER = 0.001
    
METADATA_MEMBERS = [
    'cxM', 'cyM', 'deltaM', 'colorMapName', 'widthM', 'widthJ', 'flagReversed', 'flagCyclic',  
    'maxIterM', 'maxIterJ', 'norm', 'normPar', 'vmin', 'vmax', 'clip', 'smooth', 
    'modulo', 'power', 'rotateColorMapIndex', 'shaded', 'vert_exag', 
    'interpolation', 'blendMode', 'azDeg', 'altDeg', 'band', 'rotateWaitTime', 
    'colorRotateValue', 'scanCircle', 'showData']

#
# beware of typos, check whether a member is in the list of known members
#
MBS_Attrs = METADATA_MEMBERS + \
    [ 'app', 'figSizeBig', 'figSizeMedium', 'figSizeSmall', 'figSizeLarge', 'figSizeHuge', 
      'figSizeTiny', 'screen', 'screenWidthIn', 'screenHeightIn', 
      'figJ', 'imJ', 'geomJ', 'geomM', 'flagsAction', 'geometryAction',   
      'figSizeM', 'figSizeJ', 'axJ', 'dpi', 'modeOperation', 'animationFactorCombo', 
      'maxIterMCombo', 'maxIterJCombo', 'animationFactor', 
      'figM', 'figJuliaSet', 'busy', 'itOffset', 'isRotating', 
      'dataMandelbrotSet', 'dataJuliaSet', 'stopRequested',
      'figDebugSpiral', 'figDebugColoring', 'lastFileRead', 
      'widthCombo', 'cmapRotateSlider', 'cmapRotateSliderLbl', 'moduloCombo',
      'zoomCombo', 'maxIterMCombo', 'maxIterJCombo', 'normParCombo',  
      'colorMap', 'modFactor', 'scanCircle', 'reversedCb', 'cyclicCb',    
      'scanPoints', 'zoom', 'cxM', 'cyM', 'deltaM', 'cxJ', 'cyJ', 'deltaJ',
      'progress', 'imM', 'imageJuliaSet','menuBar', 'fileMenu',
      'pngMAction','pngJAction', 'clearAction','exitAction', 
      'menuBarRight', 'helpMenu', 'gridLayout', 'spiral', 'rotateColorsPb', 
      'interpolationModeCombo', 'scanCircleCb', 'logWidget', 
      'shadedCb', 'vert_exagModeCombo', 'clipCb', 'figSizeC', 'cbar', 
      'blendModeCombo', 'azDegCombo', 'altDegCombo', 'scanPointsCombo',
      'progressLbl', 'progressLblBg', 'colorRotateCombo',
      'statusBar', 'mgrM', 'mandelbrotKeyclick', 'scanMarker', 
      'textTitleM', 'mgrJ', 'juliaKeyclick', 'textTitleJ',
      'placesWidget', 'cxOld', 'cyOld', 'deltaOld', 'nColorCyclic', 'nColorCyclicCombo', 
      'animateAtConstantWidth', 'animateAtConstantWidthAction',  
      'figM3D', 'animatePb', 'debugSpiral', 'debugColoring',  
      'shaderAction', 'scansAction', 'placesAction', 'overviewAction', 'coloringAction',
      'smoothModeCombo', 'cython', 'highPrec', 'highPrecAction', 'smoothAction', 'miscAction', 
      'figSize3D', 'flagM3D', 'surface', 'fig3D','fig3D', 'clipCb', 'smoothModeCombo', 
      'surface', 'm3DCb', 'resetMarker', 'fontSize', 'numba', 'numbaAction',
      'dataMandelbrotSet3D', 'colorsMenu', 'allColorsMenu', 'cmapLbl',
      'deltaLbl', 'mandelbrotMode', 'mandelbrotModeCombo', 'rotateWaitTimeCombo', 
      'juliaMode', 'juliaModeCombo', 'isAnimating', 'spiralCombo', 
      'bandCb', 'dataLbl', 'normCombo', 'normFunc', 'scanPath', 'scanTexts',
      'repeatAction', 'ax3D', 'axDebugSpiral', 'axDebugColoring',  
      'axM', 'axJulia', 'iterPath', 'flagIterPath', 'iterPathCb', 'colorRotateExecPb', 
      'vmaxSlider', 'vmaxSliderLbl', 'vminSlider', 'vminSliderLbl', 'tiled',
      'flagsMenu', 'cythonAction', 'tiledAction', 'debugSpiralAction', 
      'debugColoringAction', 'debugSpeed', 'debugSpeedAction', 'numpyAction', 'numpy', 
      'centerHsh', 'centerMenu', 'resetMarkerAction', 'scalarAction', 'scalar', 
      'lastReadLbl', 'rmColor', 'rmColorAction', 'animateMaxIterAction',
      'numpyOnlyAction', 'numpyOnly', 'cardioidBulbAction', 'cardioidBulb', 'prangeAction', 'prange', 
     ]

class mandelBrotSetWidget( QMainWindow):
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        print(f"Key pressed: {key} ({event.text()})")
    def __init__(self, app, fontSize, modeOperation, parent=None):
        super().__init__(parent)
        #QWidget.__init__(self, parent, Qt.WindowStaysOnTopHint)

        self.setWindowTitle("mandelbrot.py")
        self.app = app
        self.fontSize = fontSize
        self.modeOperation = modeOperation # e.g. 'demo'

        self.findFigSizes()
        #
        # matplotlib interactive mode
        #
        plt.ion()

        self.initMembers() 
        
        self.setDefaults()

        self.prepareMenuBar()
        self.prepareCentralPart()
        self.prepareStatusBar()
        #
        # setCurrentIndices() called also by setDefaults(),
        # however, it is skipped because the widgets need
        # to exist in advance
        #
        self.setCurrentIndices()
        
        self.prepareMFigure()

        self.calcMandelbrotSet()
        self.showMandelbrotSet()

        self.figM.set_size_inches( self.figSizeM[0], self.figSizeM[1], forward = True)
        self.geomM = self.mgrM.window.geometry()
        self.mgrM.window.setGeometry( 50, 50, self.geomM.width(), self.geomM.height())

        if self.modeOperation.lower() == 'demo': 
            screens = self.app.screens()
            if len( screens) < 2:
                print( "\n__init__(): demo mode only at DownPc, exiting\n") 
                sys.exit( 255) 
            #self.setFixedSize( 562, 664)
            self.setGeometry( screens[1].geometry().x() + 870,
                              screens[1].geometry().y() + 10, 586, 650)
            self.show() # placing show() before the next statement is important!
            self.mgrM.window.setGeometry( 3845, 530, self.geomM.width(), self.geomM.height())
            self.app.processEvents()
        self.show()
        #
        # make sure MBS_ATTR is not polluted
        # +++
        for name in MBS_Attrs:
            try:
                temp = getattr( self, name)
            except:
                #print( "__init__: %s is not in self" % name)
                pass

        return

    def findFigSizes( self): 

        #screen = QDesktopWidget().screenGeometry(-1)
        cm = 1/2.54  # centimeters in inches
        self.screen = self.app.primaryScreen()
        """
        - 96 DPI → Windows baseline, what Qt reports as “physical”.
        - 100 DPI → Matplotlib’s default assumption if you don’t override.
        - 120 DPI → Windows scaling at 125%, common on HiDPI monitors.
        """
        dpi_x = self.screen.physicalDotsPerInchX() # 96
        dpi_y = self.screen.physicalDotsPerInchY() # 96
        self.dpi = DPI
        self.screenWidthIn  = self.screen.size().width()/dpi_x # just for informational purpose
        self.screenHeightIn = self.screen.size().height()/dpi_y

        self.figSizeC = ( 15*cm, 18*cm)
        if self.modeOperation.lower() == 'demo': 
            self.figSizeC = ( 11*cm, 16*cm)

        width = WIDTH_VALUES[0] # 1000
        """
          note: use setGeometry only for positioning the figure
                self.mgrM.window.setGeometry( 50, 50, self.geomM.width(), self.geomM.height())
        """
        figSizeInch = width / self.dpi
        self.figSizeHuge = ( figSizeInch*1.7, figSizeInch*1.7)
        self.figSizeLarge = ( figSizeInch*1.2, figSizeInch*1.2)
        self.figSizeBig = ( figSizeInch*0.85, figSizeInch*0.85)
        self.figSizeMedium = ( figSizeInch*0.7, figSizeInch*0.7)
        self.figSizeSmall = ( figSizeInch*0.5, figSizeInch*0.5)
        self.figSizeTiny = ( figSizeInch*0.35, figSizeInch*0.35)
            
        self.figSizeM = self.figSizeBig
        self.figSizeJ = self.figSizeBig
        self.figSize3D = self.figSizeBig
        return 

    def initMembers( self): 

        self.maxIterMCombo = None
        self.maxIterJCombo = None
        self.normParCombo = None
        self.cmapLbl = None
        self.progress = 0

        self.imM = None
        self.imJ = None
        self.figM = None
        self.figDebugSpiral = None
        self.figDebugColoring = None
        self.figM3D = None
        self.figJ = None
        self.cmapRotateSlider = None
        self.figM3D = None
        self.logWidget = None
        self.vmaxSliderLbl = None
        self.vminSliderLbl = None
        self.busy = False
        self.band = "False" 
        self.itOffset = 0
        self.rotateColorMapIndex = 0
        self.dataMandelbrotSet = None
        self.dataJuliaSet = None
        self.textTitleJ = None
        self.stopRequested = False
        self.scanPath = []
        self.scanTexts = []
        self.scanMarker = None
        self.cxOld = None
        self.cyOld = None
        self.deltaOld = None
        self.placesWidget = None
        self.flagIterPath = "False"
        self.iterPath = None
        self.cbar = None
        self.juliaMode = None
        self.cythonAction = None
        self.numpyAction = None
        self.numpyOnlyAction = None  # no NumExpr
        self.cardioidBulbAction = None     # Enable Cardioid/Bulb detection
        self.prangeAction = None     # Enable prange()
        self.scalarAction = None
        self.debugSpeedAction = None
        self.lastFileRead = None
        self.centerHsh = {}
        self.resetMarker = None
        return 

    def __setattr__( self, name, value):
        """
        +++
        this function protects agains typos. members can only be set, 
        if they have been defined
        """
        #print( "mandelBrotSetWidget.__setattr__: name %s, value %s" % (name, value))
        if name in MBS_Attrs or \
           name.find( 'SelColor') == 0 or \
           name.find( 'AllColor') == 0: 
            super( mandelBrotSetWidget, self).__setattr__(name, value)
        else:
            #
            # the MBN_ files become members of self,
            # needed by 'center' feature
            #
            if name.find( 'MBN_') != 0 and \
               name != 'Center':
                print( " unknown attribute: '%s'," %  name)
            super( mandelBrotSetWidget, self).__setattr__(name, value)
            #raise ValueError( "mandelBrotSetWidget.__setattr__: unknown attribute %s" % ( name))
    #
    # === the menu bar
    #
    def prepareMenuBar( self):

        self.menuBar = QMenuBar()
        self.setMenuBar( self.menuBar)
        #
        # file
        #
        self.fileMenu = self.menuBar.addMenu('&File')
        #
        # png MS
        #
        self.pngMAction = QAction('Create .png from the Mandelbrot figure', self)        
        self.pngMAction.triggered.connect( self.cb_pngM)
        self.fileMenu.addAction( self.pngMAction)
        #
        # png JS
        #
        self.pngJAction = QAction('Create .png from the Julia figure', self)        
        self.pngJAction.triggered.connect( self.cb_pngJ)
        self.fileMenu.addAction( self.pngJAction)
        #
        # self.geometry()
        #
        self.geometryAction = QAction('Geometry() to log', self)        
        self.geometryAction.triggered.connect( self.cb_geometry)
        self.fileMenu.addAction( self.geometryAction)
        #
        # exec iterMaxAnimation
        #
        self.animateMaxIterAction = QAction("AnimateMaxIter")
        self.animateMaxIterAction.triggered.connect( self.cb_animateMaxIter)
        self.fileMenu.addAction( self.animateMaxIterAction)
        #
        # clear log widget
        #
        self.clearAction = QAction('Clear log widget', self)        
        self.clearAction.triggered.connect( self.cb_clear)
        self.fileMenu.addAction( self.clearAction)
        #
        # repeat
        #
        self.repeatAction = QAction('Repeat last calculation', self)        
        self.repeatAction.triggered.connect( self.cb_repeat)
        self.fileMenu.addAction( self.repeatAction)
        #
        # png test
        #
        #self.pngTestAction = QAction('Create test png file', self)        
        #self.pngTestAction.triggered.connect( self.cb_pngTest)
        #self.fileMenu.addAction( self.pngTestAction)
        #
        # exit
        #
        self.exitAction = QAction('Exit', self)        
        self.exitAction.triggered.connect( sys.exit)
        self.fileMenu.addAction( self.exitAction)
         #
        # Colors
        #
        """
        Why your temporary variable works
        Qt takes ownership of the QAction when you add it to a menu:
        self.colorsMenu.addAction(temp)

        At that moment:
        - The menu becomes the parent/owner of the action.
        - Qt’s parent–child memory management ensures the action stays alive.
        - Python’s temporary variable temp can safely go out of scope.
        - The action will remain functional until the menu is destroyed.
        So you do not need to store the action on self unless you want
        to reference it later for some reason (e.g., enabling/disabling
        it dynamically).
        """
        self.colorsMenu = self.menuBar.addMenu('Colors')
        for clr in utils.CMAPS:
            temp = QAction( clr, self)
            temp.triggered.connect( self.mkColorCb( clr))
            self.colorsMenu.addAction( temp)
        self.colorsMenu.addSeparator()
        for clr in utils.CMAPS_CYCLIC:
            temp = QAction( clr, self)
            temp.triggered.connect( self.mkColorCb( clr))
            self.colorsMenu.addAction( temp)
        #
        # AllColors
        #
        self.allColorsMenu = self.menuBar.addMenu('AllColors')
        for elm in list( utils.CMAPS_DCT.keys()):
            subMenu = self.allColorsMenu.addMenu( elm)
            for clr in utils.CMAPS_DCT[elm]:
                temp = QAction( clr, self)
                temp.triggered.connect( self.mkColorCb( clr))
                subMenu.addAction( temp)
        #
        # flags
        #
        self.flagsMenu = self.menuBar.addMenu('Flags')
        #
        # cython
        #
        if cythonOK:
            self.cythonAction = QAction('Cython/C', self, checkable = True)        
            self.cythonAction.triggered.connect( self.cb_cython)
            self.cythonAction.setStatusTip('Enable cython code')
            self.cythonAction.setChecked( self.cython == "True")
            self.flagsMenu.addAction( self.cythonAction)
        #
        # tiled
        #
        if cythonOK:
            self.tiledAction = QAction('Cython/C-tiled', self, checkable = True)
            self.tiledAction.triggered.connect( self.cb_tiled)
            self.tiledAction.setStatusTip('Multithreaded')
            self.tiledAction.setChecked( self.tiled == "True")
            self.flagsMenu.addAction( self.tiledAction)
        #
        # Numpy/Numexpr
        #
        self.numpyAction = QAction('Numpy/NumExpr', self, checkable = True)        
        self.numpyAction.triggered.connect( self.cb_numpy)
        self.numpyAction.setStatusTip('Enable numpy/numexpr code')
        self.numpyAction.setChecked( self.numpy == "True")
        self.flagsMenu.addAction( self.numpyAction)
        #
        # Numba
        #
        if numbaOK:
            self.numbaAction = QAction('Numba/Cuda', self, checkable = True)        
            self.numbaAction.triggered.connect( self.cb_numba)
            self.numbaAction.setStatusTip('Enable multithreading')
            self.numbaAction.setChecked( self.numba == "True")
            self.flagsMenu.addAction( self.numbaAction)
        #
        # scalar
        #
        self.scalarAction = QAction('Scalar', self, checkable = True)        
        self.scalarAction.triggered.connect( self.cb_scalar)
        self.scalarAction.setStatusTip('Enable scalar algorithm, very slow')
        self.scalarAction.setChecked( self.scalar == "True")
        self.flagsMenu.addAction( self.scalarAction)
        #
        self.flagsMenu.addSeparator()
        #
        # numpyOnly
        #
        self.numpyOnlyAction = QAction('NumpyOnly', self, checkable = True)        
        self.numpyOnlyAction.triggered.connect( self.cb_numpyOnly)
        self.numpyOnlyAction.setStatusTip('Pure Numpy no NumExpr')
        self.numpyOnlyAction.setChecked( self.numpyOnly == "True")
        self.flagsMenu.addAction( self.numpyOnlyAction)
        #
        # cardioidBulb
        #
        self.cardioidBulbAction = QAction('Cardioid/Bulb', self, checkable = True)        
        self.cardioidBulbAction.triggered.connect( self.cb_cardioidBulb)
        self.cardioidBulbAction.setStatusTip('Cardioid/Bulb speedup feature')
        self.cardioidBulbAction.setChecked( self.cardioidBulb == "True")
        self.flagsMenu.addAction( self.cardioidBulbAction)
        #
        # prange
        #
        self.prangeAction = QAction('prange()', self, checkable = True)        
        self.prangeAction.triggered.connect( self.cb_prange)
        self.prangeAction.setStatusTip('prange() parallel-range()')
        self.prangeAction.setChecked( self.prange == "True")
        self.flagsMenu.addAction( self.prangeAction)
        #
        self.flagsMenu.addSeparator()
        #
        # ResetMarker black/white
        #
        self.rmColorAction = QAction('RM is black', self, checkable = True)        
        self.rmColorAction.triggered.connect( self.cb_rmColor)
        self.rmColorAction.setStatusTip('Switch RM (resetMarker) between black and white')
        self.rmColorAction.setChecked( self.rmColor == "black")
        self.flagsMenu.addAction( self.rmColorAction)
        #
        # animateAtConstantWidth
        #
        self.animateAtConstantWidthAction = QAction('Animate uses constant width', self, checkable = True) 
        self.animateAtConstantWidthAction.triggered.connect( self.cb_animateAtConstantWidth)
        self.animateAtConstantWidthAction.setStatusTip( "Disable width adjustment during animate")
        self.animateAtConstantWidthAction.setChecked( self.animateAtConstantWidth == "True")
        self.flagsMenu.addAction( self.animateAtConstantWidthAction)
        #
        # debugSpiral
        #
        self.debugSpiralAction = QAction('DebugSpiral', self, checkable = True) 
        self.debugSpiralAction.triggered.connect( self.cb_debugSpiral)
        self.debugSpiralAction.setStatusTip( "Enable debugSpiral mode")
        self.debugSpiralAction.setChecked( self.debugSpiral == "True")
        self.flagsMenu.addAction( self.debugSpiralAction)
        #
        # debugColoring
        #
        self.debugColoringAction = QAction('DebugColoring', self, checkable = True) 
        self.debugColoringAction.triggered.connect( self.cb_debugColoring)
        self.debugColoringAction.setStatusTip( "Enable debugColoring mode")
        self.debugColoringAction.setChecked( self.debugColoring == "True")
        self.flagsMenu.addAction( self.debugColoringAction)
        #
        # debugSpeed
        #
        self.debugSpeedAction = QAction('DebugSpeed', self, checkable = True) 
        self.debugSpeedAction.triggered.connect( self.cb_debugSpeed)
        self.debugSpeedAction.setStatusTip( "Enable debugSpeed mode")
        self.debugSpeedAction.setChecked( self.debugSpeed == "True")
        self.flagsMenu.addAction( self.debugSpeedAction)
        #
        #
        # HighPrec
        #
        #self.highPrecAction = QAction('HIGHPREC', self, checkable = True)        
        #self.highPrecAction.triggered.connect( self.cb_highPrec)
        #self.highPrecAction.setStatusTip('Enable high precision')
        #self.highPrecAction.setChecked( self.highPrec == "True")
        #self.flagsMenu.addAction( self.highPrecAction)
        #
        # Center
        #
        self.centerMenu = self.menuBar.addMenu('Center')
        self.addCenterItem( name = 'Center', cx = -0.75, cy = 0)
        #
        # help
        #
        self.menuBarRight = QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarRight, Qt.TopRightCorner)
        self.helpMenu = self.menuBarRight.addMenu('Help')
        self.menuBar.setCornerWidget( self.menuBarRight, Qt.TopRightCorner)
        #
        # Overview
        #
        self.overviewAction = self.helpMenu.addAction(self.tr("Overview"))
        self.overviewAction.triggered.connect( self.cb_helpOverview)
        #
        # Coloring
        #
        self.coloringAction = self.helpMenu.addAction(self.tr("Coloring"))
        self.coloringAction.triggered.connect( self.cb_helpColoring)
        #
        # Smooth
        #
        self.smoothAction = self.helpMenu.addAction(self.tr("Smooth"))
        self.smoothAction.triggered.connect( self.cb_helpSmooth)
        #
        # Shader
        #
        self.shaderAction = self.helpMenu.addAction(self.tr("Shader"))
        self.shaderAction.triggered.connect( self.cb_helpShader)
        #
        # Scans
        #
        self.scansAction = self.helpMenu.addAction(self.tr("Julia Scans"))
        self.scansAction.triggered.connect( self.cb_helpJuliaScans)
        #
        # Places
        #
        self.placesAction = self.helpMenu.addAction(self.tr("Places"))
        self.placesAction.triggered.connect( self.cb_helpPlaces)
        #
        # ResetMarker
        #
        self.resetMarkerAction = self.helpMenu.addAction(self.tr("ResetMarker"))
        self.resetMarkerAction.triggered.connect( self.cb_helpResetMarker)
        #
        # Flags
        #
        self.flagsAction = self.helpMenu.addAction(self.tr("Flags"))
        self.flagsAction.triggered.connect( self.cb_helpFlags)
        #
        # Misc
        #
        self.miscAction = self.helpMenu.addAction(self.tr("Misc"))
        self.miscAction.triggered.connect( self.cb_helpMisc)

        return
    #
    # === the status bar
    #
    def prepareStatusBar( self): 
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)
        #
        # places 
        #
        places = QPushButton("&Places")
        places.setToolTip( "Handle places")
        places.clicked.connect( self.cb_places)       
        self.statusBar.addWidget( places)
        #
        # store
        #
        store = QPushButton("Store")
        store.setToolTip( "Store .png incl. metadata in ./places")
        store.clicked.connect( self.cb_store)       
        self.statusBar.addWidget( store)
        #
        # store named
        #
        storeNamed = QPushButton("StoreNamed")
        storeNamed.setToolTip( "Store .png incl. metadata in ./places/MBN_<input>.png\nMBN_ files cannot be deleted by mandelbrot.py")
        storeNamed.clicked.connect( self.cb_storeNamed)       
        self.statusBar.addWidget( storeNamed)
        #
        # stop
        #
        stop = QPushButton("&Stop")
        stop.setToolTip( "Stop the Julia scan and animations")
        stop.clicked.connect( self.cb_stop)       
        self.statusBar.addPermanentWidget( stop)
        #
        # reset
        #
        reset = QPushButton("&Reset")
        reset.clicked.connect( self.cb_reset)       
        reset.setToolTip( "Reset all variables, set the reset marker and restart")
        self.statusBar.addPermanentWidget( reset)
        #
        # quit
        #
        quit = QPushButton("&Quit")
        quit.clicked.connect( self.cb_close)       
        self.statusBar.addPermanentWidget( quit)
        return 
    #    
    # === the central part
    #    
    def prepareCentralPart( self):

        w = QWidget()
        #
        # start with a vertical layout
        #
        self.gridLayout = QGridLayout()
        w.setLayout( self.gridLayout)
        self.gridLayout.setColumnMinimumWidth( 0, 200)
        self.gridLayout.setColumnMinimumWidth( 1, 200)

        self.setCentralWidget( w)
        row = -1
        #
        # color maps
        #
        self.cmapLbl = QLabel( "CMAP: %s" % self.colorMapName)
        #self.cmapLbl.setFixedWidth( 180)
        self.cmapLbl.setToolTip( "Open 'Colors' or 'AllColors' to select color maps.")
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.cmapLbl)
        #
        # reversed
        #
        self.reversedCb = QCheckBox( "Reversed", self)
        self.reversedCb.setToolTip( "If enabled, the color map is reversed.")
        self.reversedCb.setChecked( self.flagReversed == "True")
        self.reversedCb.clicked.connect( self.cb_reversed)
        hLayout.addWidget( self.reversedCb)
        #
        # cyclic
        #
        self.cyclicCb = QCheckBox( "Cyclic", self)
        self.cyclicCb.setToolTip( "If enabled, the color map is made cyclic, like prism or flag.")
        self.cyclicCb.setChecked( self.flagCyclic == "True")
        self.cyclicCb.clicked.connect( self.cb_cyclic)
        hLayout.addWidget( self.cyclicCb)

        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # rotate color map by slider
        #
        self.cmapRotateSliderLbl = QLabel( "C-Index: %-4d" % 0)
        self.cmapRotateSliderLbl.setFixedWidth( 120)
        self.cmapRotateSliderLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hLayout.addWidget( self.cmapRotateSliderLbl)

        self.cmapRotateSlider = QSlider(Qt.Horizontal)
        self.cmapRotateSlider.setToolTip( "Rotate the color map")
        self.cmapRotateSlider.valueChanged.connect( self.cb_cmapRotateSlider)
        self.cmapRotateSlider.setMinimum( 0) 
        self.cmapRotateSlider.setMaximum( CMAP_MAX - 1)
        self.cmapRotateSlider.setFixedWidth( 450)
        hLayout.addWidget( self.cmapRotateSlider)

        hLayout.addStretch()
        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()
        #
        # rotate the color map continuously
        #
        hLayout.addWidget( QLabel( "Continuously rotate CMAP by"))
        #
        # rotate by steps
        #
        self.colorRotateCombo = QComboBox()
        self.colorRotateCombo.setToolTip( "Continuously rotate by n steps.")
        for elm in COLORROTATE_VALUES:
            self.colorRotateCombo.addItem( str( elm))
        self.colorRotateCombo.setCurrentIndex( 0)
        self.colorRotateCombo.activated.connect( self.cb_colorRotateCombo )
        hLayout.addWidget( self.colorRotateCombo)
        hLayout.addStretch()
        
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # wait time
        #
        hLayout.addWidget( QLabel( "WaitTime"))
        self.rotateWaitTimeCombo = QComboBox()
        self.rotateWaitTimeCombo.setToolTip( "Slows down the color rotation.")
        for elm in ROTATEWAITTIME_VALUES:
            self.rotateWaitTimeCombo.addItem( str( elm))
        self.rotateWaitTimeCombo.setCurrentIndex( 0)
        self.rotateWaitTimeCombo.activated.connect( self.cb_rotateWaitTimeCombo )
        hLayout.addWidget( self.rotateWaitTimeCombo)
        #
        # exec rotate
        #
        self.colorRotateExecPb = QPushButton("Exec")
        self.colorRotateExecPb.setToolTip( "Exec color animation")
        self.colorRotateExecPb.clicked.connect( self.cb_colorRotateExecPb)
        hLayout.addStretch()
        hLayout.addWidget( self.colorRotateExecPb)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # Animation
        # Spiral
        #
        self.spiralCombo = QComboBox()
        self.spiralCombo.setToolTip( "Spiral, specify turn number. '-1' selects linear appoach.")
        for elm in SPIRAL_VALUES:
            self.spiralCombo.addItem( str( elm))
        self.spiralCombo.setCurrentIndex( 0)
        self.spiralCombo.activated.connect( self.cb_spiralCombo )
        hLayout.addWidget( QLabel( 'Animation: Spiral'))
        hLayout.addWidget( self.spiralCombo)
        hLayout.addWidget( QLabel( 'Turns'))
        hLayout.addStretch()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # animationFactor
        #
        self.animationFactorCombo = QComboBox()
        self.animationFactorCombo.setToolTip( "Zoom-in factor for animations")
        for elm in ANIMATIONFACTOR_VALUES:
            self.animationFactorCombo.addItem( str( elm))
        self.animationFactorCombo.setCurrentIndex( 0)
        self.animationFactorCombo.activated.connect( self.cb_animationFactorCombo )
        hLayout.addWidget( QLabel( 'A-Factor'))
        hLayout.addWidget( self.animationFactorCombo)
        #
        # exec animation
        #
        self.animatePb = QPushButton("Exec")
        self.animatePb.setToolTip( "Execute animation")
        self.animatePb.clicked.connect( self.cb_animateZoom)
        hLayout.addStretch()
        hLayout.addWidget( self.animatePb)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        # Linie ins GridLayout einfügen (z. B. in Zeile 1, Spalte 0, über 2 Spalten)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # maxIterM
        #
        self.maxIterMCombo = QComboBox()
        self.maxIterMCombo.setToolTip( "Max. no. of iterations to test whether c is in the Mandelbrot set. \nMaxIter therefore defines the maximum escape count. \nData generated by different MaxIter are normalised to 1024.")
        for elm in MAX_ITER_VALUES:
            self.maxIterMCombo.addItem( str( elm))
        self.maxIterMCombo.setCurrentIndex( 0)
        self.maxIterMCombo.activated.connect( self.cb_maxIterMCombo )
        hLayout.addWidget( QLabel( 'MaxIterM'))
        hLayout.addWidget( self.maxIterMCombo)
        hLayout.addStretch()
        #
        # maxIterJ
        #
        self.maxIterJCombo = QComboBox()
        self.maxIterJCombo.setToolTip( "Max. no. of iterations to test whether c is in the Julia set. \nMaxIter therefore defines the maximum escape count. \nData generated by different MaxIter are normalised to 1024.")
        for elm in MAX_ITER_VALUES:
            self.maxIterJCombo.addItem( str( elm))
        self.maxIterJCombo.setCurrentIndex( 0)
        self.maxIterJCombo.activated.connect( self.cb_maxIterJCombo )
        hLayout.addWidget( QLabel( 'MaxIterJ'))
        hLayout.addWidget( self.maxIterJCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # width
        #
        self.widthCombo = QComboBox()
        self.widthCombo.setToolTip( 
            "Width of the image in either direction, \n'256' generates test data.")
        for elm in WIDTH_VALUES:
            self.widthCombo.addItem( str( elm))
        self.widthCombo.setCurrentIndex( 0)
        self.widthCombo.activated.connect( self.cb_widthCombo )
        hLayout.addWidget( QLabel( 'Width'))
        hLayout.addWidget( self.widthCombo)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        # Linie ins GridLayout einfügen (z. B. in Zeile 1, Spalte 0, über 2 Spalten)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # norm/normPar
        #
        self.normCombo = QComboBox()
        self.normCombo.setToolTip( "Normalization method, modifies the transformation [vmin, vmax] -> [0, 1]")
        for elm in NORM_VALUES:
            self.normCombo.addItem( str( elm))
        self.normCombo.setCurrentIndex( 0)
        self.normCombo.activated.connect( self.cb_normCombo )
        
        self.normParCombo = QComboBox()
        self.normParCombo.setToolTip( "Normalization parameter, meaning depends on method")
        for elm in NORMPAR_VALUES:
            self.normParCombo.addItem( str( elm))
        self.normParCombo.setCurrentIndex( 0)
        self.normParCombo.activated.connect( self.cb_normParCombo )
        #
        # clip
        #
        self.clipCb = QCheckBox( "Clip", self)
        self.clipCb.setToolTip( "If enabled, colors below/above vmin/vmax \nare clipped to the lowest/hights color.")
        self.clipCb.setChecked( self.clip == "True")
        self.clipCb.clicked.connect( self.cb_clip)

        hLayout.addWidget( self.normCombo)
        hLayout.addWidget( self.normParCombo)
        hLayout.addWidget( self.clipCb)
        hLayout.addStretch()

        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()
        #
        # modulo
        #
        self.moduloCombo = QComboBox()
        self.moduloCombo.setToolTip( "data = data % modulo")
        for elm in MODULO_VALUES:
            self.moduloCombo.addItem( str( elm))
        self.moduloCombo.setCurrentIndex( 0)
        self.moduloCombo.activated.connect( self.cb_moduloCombo )
        hLayout.addWidget( QLabel( 'Modulo'))
        hLayout.addWidget( self.moduloCombo)
        #
        # bands
        #
        self.bandCb = QCheckBox( "Bands", self)
        self.bandCb.setToolTip( "Sets every second entry of the color maps to black.")
        self.bandCb.clicked.connect( self.cb_band)
        hLayout.addStretch()
        hLayout.addWidget( self.bandCb)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col, 1, 1)
        #
        # vmin
        #
        self.vminSlider = QSlider(Qt.Horizontal)
        self.vminSlider.setToolTip("Coloring transforms the range [vmin, vmax] to [0, 1]")
        self.vminSlider.setMinimum(0)
        self.vminSlider.setMaximum(1024)
        self.vminSlider.setValue( int( self.vmin))
        self.vminSlider.setFixedWidth(450)

        self.vminSliderLbl = QLabel("vmin: %4d" % int( self.vmin))
        self.vminSliderLbl.setFixedWidth( 100)
        self.vminSliderLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.vminSliderLbl)
        hLayout.addStretch()
        hLayout.addWidget(self.vminSlider)
        row += 1
        col = 0
        self.gridLayout.addLayout(hLayout, row, col, 1, 2)
        #
        # vmax
        #
        self.vmaxSlider = QSlider(Qt.Horizontal)
        self.vmaxSlider.setToolTip("Coloring transforms the range [vmin, vmax] to [0, 1]")
        self.vmaxSlider.setMinimum(0)
        self.vmaxSlider.setMaximum(1024)
        self.vmaxSlider.setValue( int( self.vmax))
        self.vmaxSlider.setFixedWidth(450)

        self.vmaxSliderLbl = QLabel("vmax: %4d" % int( self.vmax))
        self.vmaxSliderLbl.setFixedWidth( 100)
        self.vmaxSliderLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.vminSlider.valueChanged.connect(self.cb_vminSlider)
        self.vmaxSlider.valueChanged.connect(self.cb_vmaxSlider)
        
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.vmaxSliderLbl)
        hLayout.addStretch()
        hLayout.addWidget(self.vmaxSlider)
        row += 1
        col = 0
        self.gridLayout.addLayout(hLayout, row, col, 1, 2)
        #
        # smooth mode
        #
        self.smoothModeCombo = QComboBox()
        self.smoothModeCombo.setToolTip( "Smoothing modifies the discrete values of the escapeCount field such \nthat there are smooth transitions. This way banding is avoided (more or less). \n\n  - DistEst - the data is smoothed depending on how far the z(n) escapes. \n  - DZ - the data is smoothed depending on the derivative dz(n)")
        for elm in SMOOTH_VALUES:
            self.smoothModeCombo.addItem( str( elm))
        self.smoothModeCombo.setCurrentIndex( 0)
        self.smoothModeCombo.activated.connect( self.cb_smoothModeCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Smooth'))
        hLayout.addWidget( self.smoothModeCombo)
        hLayout.addStretch()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # interpolation mode
        #
        self.interpolationModeCombo = QComboBox()
        self.interpolationModeCombo.setToolTip( "Interpolation algorithm")
        for elm in INTERPOLATION_VALUES:
            self.interpolationModeCombo.addItem( str( elm))
        self.interpolationModeCombo.setCurrentIndex( 0)
        self.interpolationModeCombo.activated.connect( self.cb_interpolationModeCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Interpolation'))
        hLayout.addWidget( self.interpolationModeCombo)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        # Linie ins GridLayout einfügen (z. B. in Zeile 1, Spalte 0, über 2 Spalten)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # shaded
        #
        self.shadedCb = QCheckBox( "Shader", self)
        self.shadedCb.setToolTip( "Enable shading")
        self.shadedCb.clicked.connect( self.cb_shaded)
        row += 1
        col = 0
        self.gridLayout.addWidget( self.shadedCb, row, col)
        #
        # vert_exag mode
        #
        self.vert_exagModeCombo = QComboBox()
        for elm in VERT_EXAG_VALUES:
            self.vert_exagModeCombo.addItem( str( elm))
        self.vert_exagModeCombo.setCurrentIndex( 0)
        self.vert_exagModeCombo.setToolTip( "Higher values generate more depth in the image.")
        self.vert_exagModeCombo.activated.connect( self.cb_vert_exagModeCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Vertical Exageration'))
        hLayout.addWidget( self.vert_exagModeCombo)
        hLayout.addStretch()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # blend mode
        #
        self.blendModeCombo = QComboBox()
        self.blendModeCombo.setToolTip( "n.n.")
        for elm in BLEND_MODE_VALUES:
            self.blendModeCombo.addItem( str( elm))
        self.blendModeCombo.setCurrentIndex( 0)
        self.blendModeCombo.activated.connect( self.cb_blendModeCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Blend Mode'))
        hLayout.addWidget( self.blendModeCombo)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # azDeg
        #
        self.azDegCombo = QComboBox()
        self.azDegCombo.setToolTip( "Set azimutal angle of the light")
        for elm in AZDEG_VALUES:
            self.azDegCombo.addItem( str( elm))
        self.azDegCombo.setCurrentIndex( 0)
        self.azDegCombo.activated.connect( self.cb_azDegCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'azDegree'))
        hLayout.addWidget( self.azDegCombo)
        hLayout.addStretch()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # altDeg
        #
        self.altDegCombo = QComboBox()
        self.altDegCombo.setToolTip( "Set polar angle of the light")
        for elm in ALTDEG_VALUES:
            self.altDegCombo.addItem( str( elm))
        self.altDegCombo.setCurrentIndex( 0)
        self.altDegCombo.activated.connect( self.cb_altDegCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'altDegree'))
        hLayout.addWidget( self.altDegCombo)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        
        # Horizontale Linie erzeugen
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
        # Linie ins GridLayout einfügen (z. B. in Zeile 1, Spalte 0, über 2 Spalten)
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # scanPoints
        #
        self.scanPointsCombo = QComboBox()
        self.scanPointsCombo.setToolTip( "A Julia set is created for each scan point. \nUse MB-right to define a polygon or 3 points for a circular scan.")
        for elm in SCAN_POINT_VALUES:
            self.scanPointsCombo.addItem( str( elm))
        self.scanPointsCombo.setCurrentIndex( 0)
        self.scanPointsCombo.activated.connect( self.cb_scanPointsCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Julia Scans: '))
        hLayout.addWidget( QLabel( 'No. of Points'))
        hLayout.addWidget( self.scanPointsCombo)
        hLayout.addStretch()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # scanCircle
        #
        self.scanCircleCb = QCheckBox( "Scan Circle", self)
        self.scanCircleCb.setToolTip( "Select circular or polygon scans.")
        self.scanCircleCb.clicked.connect( self.cb_scanCircle)
        hLayout.addWidget( self.scanCircleCb)
        hLayout.addStretch()
        #
        # Exec Scan
        #
        temp = QPushButton("Execute Scan")
        temp.setToolTip( "Execute Jula scan")
        temp.clicked.connect( self.cb_execScan)
        hLayout.addWidget( temp)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()

        # Horizontale Linie erzeugen
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
        # Linie ins GridLayout einfügen (z. B. in Zeile 1, Spalte 0, über 2 Spalten)
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        hLayout = QHBoxLayout()
        #
        # MandelbrotMode
        #
        self.mandelbrotModeCombo = QComboBox()
        self.mandelbrotModeCombo.setToolTip( "Size of the Mandelbrot figure.")
        for elm in MANDELBROT_MODE_VALUES:
            self.mandelbrotModeCombo.addItem( str( elm))
        self.mandelbrotModeCombo.setCurrentIndex( 3)
        self.mandelbrotModeCombo.activated.connect( self.cb_mandelbrotModeCombo )
        hLayout.addWidget( QLabel( 'Mandelbrot'))
        hLayout.addWidget( self.mandelbrotModeCombo)
        #
        # M3D
        #
        self.m3DCb = QCheckBox( "M3D", self)
        self.m3DCb.setToolTip( "Open 3D plot")
        self.m3DCb.clicked.connect( self.cb_3D)
        hLayout.addWidget( self.m3DCb)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # JuliaMode
        #
        self.juliaModeCombo = QComboBox()
        self.juliaModeCombo.setToolTip( "Size of the Julia figure")
        for elm in JULIA_MODE_VALUES:
            self.juliaModeCombo.addItem( str( elm))
        self.juliaModeCombo.setCurrentIndex( 0)
        self.juliaModeCombo.activated.connect( self.cb_juliaModeCombo )
        hLayout.addWidget( QLabel( 'Julia'))
        hLayout.addWidget( self.juliaModeCombo)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # progress
        #
        self.progressLbl = QLabel( "Progress")
        self.progressLblBg = self.progressLbl.palette().window().color().name()
        hLayout.addWidget( self.progressLbl)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        self.progressLbl.hide()

        # Horizontale Linie erzeugen
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        # Linie ins GridLayout einfügen (z. B. in Zeile 1, Spalte 0, über 2 Spalten)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # zoom
        #
        self.zoomCombo = QComboBox()
        self.zoomCombo.setToolTip( "Zoom-in: delta -> delta/zoom")
        for elm in ZOOM_VALUES:
            self.zoomCombo.addItem( str( elm))
        self.zoomCombo.setCurrentIndex( 0)
        self.zoomCombo.activated.connect( self.cb_zoomCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Zoom'))
        hLayout.addWidget( self.zoomCombo)
        #
        # zoomout
        #
        temp = QPushButton("ZoomOut")
        temp.setToolTip( "Zoom out")
        temp.clicked.connect( self.cb_zoomOut)
        hLayout.addWidget( temp)
        #
        # zoomhome
        #
        temp = QPushButton("ZoomHome")
        temp.setToolTip( "Zoom back to whole fractal, leaving the reset marker")
        temp.clicked.connect( self.cb_zoomHome)
        hLayout.addWidget( temp)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # goto lastRead
        #
        temp = QPushButton("LastRead")
        temp.setToolTip( "Repeat last read")
        temp.clicked.connect( self.cb_lastRead)
        hLayout.addWidget( temp)
        #
        # lastRead file name
        #
        self.lastReadLbl = QLabel("n.n.")
        #self.lastReadLbl.setFixedWidth( 100)
        hLayout.addWidget( self.lastReadLbl)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col, 1, 3)
        hLayout = QHBoxLayout()
        #
        # logWidget
        #
        self.logWidget = QTextEdit()
        #self.logWidget.setMinimumHeight( 80)
        self.logWidget.setFixedHeight( 100)
        self.logWidget.setReadOnly( 1)
        row += 1
        col = 0
        self.gridLayout.addWidget( self.logWidget, row, col, 1, 3)
        hLayout = QHBoxLayout()
        #
        # delta
        #
        self.deltaLbl = QLabel( "Delta")
        hLayout.addWidget( self.deltaLbl)
        hLayout.addStretch()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # x, y, data
        #
        #
        # ShowData
        #
        #self.showDataCb = QCheckBox( "Show Data", self)
        #self.showDataCb.setToolTip( "Run ShowData code")
        #self.showDataCb.setChecked( self.showData == "True") 
        #self.showDataCb.clicked.connect( self.cb_showData)
        #hLayout.addWidget( self.showDataCb)
        #self.dataLbl = QLabel( "Data")
        #hLayout.addWidget( self.dataLbl)
        #hLayout.addStretch()
        #
        # IterPath
        #
        self.iterPathCb = QCheckBox( "IterPath", self)
        self.iterPathCb.setToolTip( "Path of the iterated z values")
        self.iterPathCb.setChecked( self.iterPath == "True") 
        self.iterPathCb.clicked.connect( self.cb_iterPath)
        hLayout.addWidget( self.iterPathCb)
        hLayout.addStretch()
        #
        # setRM (resetMarker)
        #
        temp = QPushButton("SetRM")
        temp.setToolTip( "Set reset marker")
        temp.clicked.connect( self.cb_setRM)
        hLayout.addWidget( temp)
        #
        # clearRM (resetMarker)
        #
        temp = QPushButton("ClearRM")
        temp.setToolTip( "Clear reset marker")
        temp.clicked.connect( self.cb_clearRM)
        hLayout.addWidget( temp)

        col = 1
        self.gridLayout.addLayout( hLayout, row, col)

        if not cythonOK:
            self.logWidget.append( "The cython interface does not exist")
            self.logWidget.append( "Consider to create one to speed-up")

        return

    def on_key_press(self, event):
        print(f"Matplotlib key pressed: {event.key}")
    #
    # the callbacks for the close figure events: 
    #   if a figure is close by clicking on the 'x' in the
    #   right upper corner, the related checkbox or combobox
    #   has to be updated.
    #
    def cb_closeFigJ( self, event):
        self.juliaMode = 'Off'
        self.juliaModeCombo.setCurrentIndex( 0)
        return

    def cb_closeFigDebugSpiral( self, event):
        self.debugSpiral = "False"
        self.debugSpiralAction.setChecked( self.debugSpiral == "True")
        return

    def cb_closeFigDebugColoring( self, event):
        self.debugColoring = "False"
        self.debugColoringAction.setChecked( self.debugColoring == "True")
        return

    def cb_closeFigM3D( self, event):
        self.flagM3D = "False"
        self.m3DCb.setChecked( self.flagM3D == "True")
        return
    #
    # --- 
    #
    def prepareDebugSpiralFigure( self, axes = 1):
        """
        display some data
        also possible: 
          fig = plt.figure()
          ax1 = fig.add_subplot(131)  # Left
          ax2 = fig.add_subplot(132)  # Middle
          ax3 = fig.add_subplot(133)  # Right
        """
        if self.figDebugSpiral is None:
            self.figDebugSpiral, self.axDebugSpiral = plt.subplots( axes, 1)
            self.figDebugSpiral.subplots_adjust(hspace=0.5) 
            self.figDebugSpiral.canvas.mpl_connect("close_event",
                                                   self.cb_closeFigDebugSpiral)
        return

    def prepareMFigure( self):
        if self.figM is None:
            self.figM, (self.axM) = plt.subplots( figsize= self.figSizeM, dpi = self.dpi)
            self.mgrM = self.figM.canvas.manager
            self.geomM = self.mgrM.window.geometry()
            self.mgrM.window.setGeometry( 50, 50, self.geomM.width(), self.geomM.height())
            #self.axM.set_aspect('equal', adjustable='box')

            self.figM.canvas.manager.set_window_title( 'Mandelbrot Set (use MB-left to zoom-in, MB-middle to move)')
            self.figM.canvas.mpl_connect("key_press_event", self.on_key_press)

            self.mandelbrotKeyclick = \
                self.figM.canvas.mpl_connect( 'button_press_event', 
                                                              self.cb_onClickMandelbrot)
            self.mandelbrotKeyclick = \
                self.figM.canvas.mpl_connect( 'motion_notify_event', 
                                                              self.cb_onMotionMandelbrot)

            #
            # mark the position where 'reset' was called
            #
            self.resetMarker = plt.text( 0, 0, '', color='blue',
                                         horizontalalignment='center',
                                         fontsize = 18,
                                         weight = 'normal', 
                                         verticalalignment='center')
            self.textTitleM = \
                plt.gcf().text( 0.02, 0.99, 
                                r'$z_{n+1} = z_n^%d + c, z_0 = 0$' % self.power,
                                color = 'white', fontname = 'monospace', size = 12,
                                horizontalalignment='left', verticalalignment='top',
                                bbox=dict(fill=False, edgecolor='white', linewidth=1))
            
            self.deltaLbl.setText( "Delta: %.2e" % (self.deltaM))

            self.figM.subplots_adjust( top=1., bottom=0., 
                                       left=0.0, right=1.,  
                                       hspace=0., wspace=0.)

        return 

    def mkCenterCb( self, name):
        def f():
            #self.logWidget.append( "mkCenter: resetMarker to %s: (%g, %g)" % 
            #                       (name, self.centerHsh[ name][ 'cx'], self.centerHsh[ name][ 'cy']))
            self.resetMarker.set( x = self.centerHsh[ name][ 'cx'], 
                                  y = self.centerHsh[ name][ 'cy'], 
                                  text = r'+', 
                                  color=self.rmColor)
            self.lastFileRead = self.centerHsh[ name][ 'fName'] 
            temp = self.trimCenterName( self.lastFileRead)
            self.lastReadLbl.setText( temp)
            return
        return f

    def trimCenterName( self, name):
        if name.find( './places/') == 0:
            name = name[ 9:]
        if name.find( 'MBN_') == 0:
            name = name[ 4:]
        if name.find( 'MB_') == 0:
            name = name[ 3:]
        if name.find( '.png') > 0:
            name = name[:-4]
        return name
    
    def addCenterItem( self, name = None, cx = None, cy = None):
        #
        #
        #
        fName = name
        name = self.trimCenterName( name)
            
        if name in self.centerHsh.keys():
            #self.logWidget.append( "addCenterItem: %s exists already" % (name))
            return 
            
        temp = "%s" % name
        self.centerHsh[ name] = {}
        self.centerHsh[ name][ 'cx'] = cx
        self.centerHsh[ name][ 'cy'] = cy
        self.centerHsh[ name][ 'fName'] = fName
        setattr( self, temp, QAction( temp, self))
        getattr( self, temp).triggered.connect( self.mkCenterCb( name))
        self.centerMenu.addAction( getattr( self, temp))
        return 
    

    def setColor( self, colorMapName, rotateColorMapIndex, band):
        """
        yes, in general the paramters exist in self already. However,
        they are required as a reminder that they have to exist before
        this function is executed.
        """
        self.colorMapName = colorMapName
        self.band = band
        if self.cmapLbl is not None:
            self.cmapLbl.setText( "CMAP: %s" % self.colorMapName)

        colorMapName = self.colorMapName
        if self.flagReversed == "True":
            colorMapName += '_r'

        #
        # prism and flag are already cyclic
        #
        if self.flagCyclic == "True" and \
           colorMapName != 'flag' and \
           colorMapName != 'prism':
            self.colorMap = plt.get_cmap( colorMapName, self.nColorCyclic)
            rot_temp = self.colorMap( np.linspace( 0, 1, self.nColorCyclic))
            self.colorMap = matplotlib.colors.ListedColormap( np.tile( rot_temp, (16, 1)))
        else: 
            self.colorMap = plt.get_cmap( colorMapName, CMAP_MAX)
            #
            # we shift black to the end to paint pixels containing maxIter black
            # and thereby we create a ListedColormap
            #
            temp = self.colorMap( np.arange( CMAP_MAX))
            #
            # shift black to index (CMAP_MAX - 1)
            #
            rot_temp = np.roll( temp, shift=(CMAP_MAX - 1), axis=0)  
            self.colorMap = matplotlib.colors.ListedColormap( rot_temp)
        #
        # the rotate slider need a ListedColormap
        #
        if self.cmapRotateSlider is not None: 
            self.cmapRotateSlider.setValue( rotateColorMapIndex)

        self.rotateColorMapFunc( rotateColorMapIndex)
        
        if self.band == "True": 
            colorsArr = self.colorMap(np.linspace(0, 1, CMAP_MAX))
            for i in range( len( colorsArr)): 
                if i % 2 == 0: 
                    colorsArr[i] = [0.123, 0.123, 0.123, 1]
            self.colorMap = colors.ListedColormap(colorsArr)
        return
    
    def mkColorCb( self, i):
        def f():
            self.colorMapName = i
            self.rotateColorMapIndex = 0
            self.setColor( self.colorMapName,
                           self.rotateColorMapIndex,
                           self.band)
            self.showMandelbrotSet()
            self.showJuliaSet()
            return 
        return f

    def findCurrentIndex( self, x, X):
        '''
        return the position as index of x in X
        used to setup combo boxes
        '''
        if str( x).lower() == 'linnormr':
            x = 'LinNorm'
            self.flagReversed = "True"
        
        for i in range( len( X)): 
            if x == X[ i]:
                return i
        print( "findCurrentIndex: failed for %s in %s" % (repr( x), repr( X)))
        return None

    def setCurrentIndices( self):
        
        if self.maxIterMCombo is None:
            return 

        self.reversedCb.setChecked( self.flagReversed == "True")

        self.cyclicCb.setChecked( self.flagCyclic == "True")
        
        self.cmapLbl.setText( "CMAP: %s" % self.colorMapName)
        
        #self.nColorCyclicCombo.setCurrentIndex( 
        #    self.findCurrentIndex( self.nColorCyclic, NCOLORCYCLIC_VALUES))

        self.widthCombo.setCurrentIndex( 
            self.findCurrentIndex( self.widthM, WIDTH_VALUES))
        
        self.colorRotateCombo.setCurrentIndex( 
            self.findCurrentIndex( self.colorRotateValue, COLORROTATE_VALUES))

        self.cmapRotateSlider.setValue( self.rotateColorMapIndex)
        
        self.moduloCombo.setCurrentIndex( 
            self.findCurrentIndex( self.modulo, MODULO_VALUES))
        self.zoomCombo.setCurrentIndex( 
            self.findCurrentIndex( self.zoom, ZOOM_VALUES))

        self.maxIterMCombo.setCurrentIndex( 
            self.findCurrentIndex( self.maxIterM, MAX_ITER_VALUES))
        self.maxIterJCombo.setCurrentIndex( 
            self.findCurrentIndex( self.maxIterJ, MAX_ITER_VALUES))
        
        self.bandCb.setChecked( self.band == "True")

        self.spiralCombo.setCurrentIndex( 
            self.findCurrentIndex( self.spiral, SPIRAL_VALUES))

        self.smoothModeCombo.setCurrentIndex( 
            self.findCurrentIndex( self.smooth, SMOOTH_VALUES))

        self.shadedCb.setChecked( self.shaded == "True")
            
        try: 
            self.vert_exagModeCombo.setCurrentIndex( 
                self.findCurrentIndex( self.vert_exag, VERT_EXAG_VALUES))
        except: 
            self.vert_exagModeCombo.setCurrentIndex( 0)

        self.interpolationModeCombo.setCurrentIndex( 
            self.findCurrentIndex( self.interpolation, INTERPOLATION_VALUES))
        self.blendModeCombo.setCurrentIndex( 
            self.findCurrentIndex( self.blendMode, BLEND_MODE_VALUES))

        self.normParCombo.setCurrentIndex( 
            self.findCurrentIndex( self.normPar, NORMPAR_VALUES))

        self.normCombo.setCurrentIndex( 
            self.findCurrentIndex( self.norm, NORM_VALUES))

        if self.norm in ['PowerNorm', 'AsinhNorm', 'TwoSlopeNorm', 
                         'StretchNorm', 'HistNorm']:
            self.normParCombo.setEnabled( True )
        else:
            self.normParCombo.setEnabled( False)

        if self.norm in [ 'LinNorm', 'AsinhNorm', 'TwoSlopeNorm', 
                          'PowerNorm', 'LogNorm', 'StretchNorm',]:
            self.vminSlider.setEnabled( True)
            self.vmaxSlider.setEnabled( True)
        else:
            self.vminSlider.setEnabled( False)
            self.vmaxSlider.setEnabled( False)

        self.vminSlider.setValue( int( self.vmin))
        self.vmaxSlider.setValue( int( self.vmax))

        self.clipCb.setChecked( self.clip == "True")

        try: 
            self.azDegCombo.setCurrentIndex( 
                self.findCurrentIndex( self.azDeg, AZDEG_VALUES))
        except:
            self.azDegCombo.setCurrentIndex( 0) 
            
        self.altDegCombo.setCurrentIndex( 
            self.findCurrentIndex( self.altDeg, ALTDEG_VALUES))

        self.scanPointsCombo.setCurrentIndex( 
            self.findCurrentIndex( self.scanPoints, SCAN_POINT_VALUES))
        self.scanCircleCb.setChecked( self.scanCircle == 'True')

        self.mandelbrotModeCombo.setCurrentIndex( 
            self.findCurrentIndex( self.mandelbrotMode, MANDELBROT_MODE_VALUES))

        self.juliaModeCombo.setCurrentIndex( 
            self.findCurrentIndex( self.juliaMode, JULIA_MODE_VALUES))

        self.animationFactorCombo.setCurrentIndex( 
            self.findCurrentIndex( self.animationFactor, ANIMATIONFACTOR_VALUES))

        self.animateAtConstantWidthAction.setChecked( self.animateAtConstantWidth == "True")

        self.debugSpiralAction.setChecked( self.debugSpiral == "True")

        self.debugColoringAction.setChecked( self.debugColoring == "True")

        self.debugSpeedAction.setChecked( self.debugSpeed == "True")
        
        #self.showDataCb.setChecked( self.showData == "True")
        
        return
    
    def createImageMFile( self, ext, fileName = None):
        # 
        plt.figure( self.figM.number) 

        if not os.path.exists( './places'):
            os.mkdir( './places') 

        if fileName is None: 
            key = "%g%g%g%d%s%g%s" % \
                ( getattr( self, 'cxM'), getattr( self, 'cyM'), getattr( self, 'deltaM'), 
                  getattr( self, 'maxIterJ'), getattr( self, 'shaded'), 
                  getattr( self, 'normPar'), getattr( self, 'colorMapName'))
            temp = hashlib.md5(key.encode()).hexdigest()[:8]  # e.g., 'a3f9c1d2'
            fName = "./places/MB_%s.%s" % ( temp, ext)
        else:
            fName = "./places/MBN_%s.%s" % ( fileName, ext)

        if os.path.exists( fName): 
            if os.path.exists( './vrsn'): 
                os.system( "./vrsn -s %s" % fName)
            else:
                self.logWidget.append( "%s exists, please rename." % fName)
                self.logWidget.append( "  or copy 'vrsn' to your PWD")
                return 

        plt.savefig(fName)

        temp = self.trimCenterName( fName)
        self.lastReadLbl.setText( temp)
        
        im = Image.open(fName)
        meta = PngImagePlugin.PngInfo()
        print( "Writing %s" % fName)
        
        for elm in METADATA_MEMBERS:
            meta.add_text( elm, str( getattr( self, elm)))
            print( " %14s : %s" % ( elm, str( getattr( self, elm))))
        print( "Writing done")

        im.save(fName, "png", pnginfo=meta)

        self.logWidget.append( "created %s" % fName)

        if self.placesWidget is not None:
            self.placesWidget.prepareCentralPart()
        #self.imM = None
        #self.showMandelbrotSet()
        return
    
    def createImageJFile( self, ext):
        # 
        plt.figure( self.figJ.number) 

        if not os.path.exists( './places'):
            os.mkdir( './places') 

        key = "%g%g%g%d%s%g%s" % \
            ( getattr( self, 'cxM'), getattr( self, 'cyM'), getattr( self, 'deltaM'), 
              getattr( self, 'maxIterJ'), getattr( self, 'shaded'), 
              getattr( self, 'normPar'), getattr( self, 'colorMapName'))
        temp = hashlib.md5(key.encode()).hexdigest()[:8]  # e.g., 'a3f9c1d2'
        fName = "./places/Julia_%s.%s" % ( temp, ext)

        if os.path.exists( fName): 
            if os.path.exists( './vrsn'): 
                os.system( "./vrsn -s %s" % fName)
            else:
                self.logWidget.append( "%s exists, please rename." % fName)
                self.logWidget.append( "  or copy 'vrsn' to your PWD")
                return 

        plt.savefig(fName)

        im = Image.open(fName)
        meta = PngImagePlugin.PngInfo()
        print( "Writing %s" % fName)
        
        for elm in METADATA_MEMBERS:
            meta.add_text( elm, str( getattr( self, elm)))
            print( " %14s : %s" % ( elm, str( getattr( self, elm))))
        print( "Writing done")

        im.save(fName, "png", pnginfo=meta)

        self.logWidget.append( "created %s" % fName)

        if self.placesWidget is not None:
            self.placesWidget.prepareCentralPart()

        return

    #
    #  === callbacks
    #

    def cb_pngM( self, fileName = None):
        self.createImageMFile( 'png', fileName = fileName)
        return
    
    def cb_pngJ( self):
        self.createImageJFile( 'png')
        return
    
    def cb_pngTest( self):
        plt.close()
        plt.figure(figsize=(3, 3))
        plt.plot(range(7), [3, 1, 4, 1, 5, 9, 2], 'r-o')
        if not os.path.exists( './images'):
            os.mkdir( './images') 
        fName = "./images/test.png"
        if os.path.exists( fName): 
            if os.path.exists( './vrsn'): 
                os.system( "./vrsn -s %s" % fName)
            else:
                self.logWidget.append( "%s exists, please rename." % fName)
                self.logWidget.append( "  or copy 'vrsn' to your PWD")
                return 
        plt.savefig(fName)
        self.logWidget.append( "created %s" % fName)
        plt.close()

        return

    def cb_places( self): 
        # 
        self.placesWidget = mandelbrotPlaces.places( self.app, parent = self)
        self.placesWidget.show()
        return 

    def cb_store( self): 
        # 
        self.cb_pngM()
        return 

    def cb_storeNamed( self): 
        #
        dlg = utils.InputDialog( "Enter file name")
        if dlg.exec_() == QDialog.Accepted:
            value = dlg.get_value()
            if value is None or len( value.strip()) == 0:
                self.logWidget.append( "storeNamed: no input, return")
                return 
        self.cb_pngM( fileName = value)
        return 

    def rotateColorMapFunc( self, shiftIndex):
        #
        # rotate only the first 1023 colors, leaving black, the last one, in place
        #
        rotatable = self.colorMap.colors[:-1]
        fixed = self.colorMap.colors[-1:]
        rotated = np.roll( rotatable, shift = shiftIndex, axis = 0)
        rotated_colors = np.vstack( (rotated, fixed))
        self.colorMap = matplotlib.colors.ListedColormap( rotated_colors)
        return
    
    def cb_cmapRotateSlider( self, colorIndex):
        """
        called from:
          - callback to slider movements
          - from mandelbrotPlaces
          - implicitly from self.cmapRotateSlider.setValue()
        """
        if self.busy:
            return

        self.busy = True
        shiftIndex = colorIndex - self.rotateColorMapIndex
        self.rotateColorMapIndex = colorIndex
        self.cmapRotateSliderLbl.setText( "C-Index: %-4d" % colorIndex)
        self.rotateColorMapFunc( shiftIndex)
        self.showMandelbrotSet()
        self.showJuliaSet()
        self.app.processEvents()
        self.busy = False
        return

    def cb_clear( self):
        self.logWidget.clear()
        return

    def cb_repeat( self):
        self.calcMandelbrotSet()
        self.calcJuliaSet()
        self.showMandelbrotSet()
        self.showJuliaSet()
        return

    def cb_geometry( self):

        self.logWidget.append( "Width %d px, Height %d px" %
                               ( self.screen.size().width(), self.screen.size().height()))
        self.logWidget.append( "Width %g in, Height %g in" %
                               ( self.screenWidthIn, self.screenHeightIn))
        self.logWidget.append( "figSizeMInch %s, dpi %d" %
                               ( repr( self.figSizeM), self.dpi))

        self.logWidget.append( "self.geometry(): %s" % repr( self.geometry()))
        self.logWidget.append( "figM %s " % self.mgrM.window.geometry())
        if self.debugColoring == "True":
            self.logWidget.append( "cb_geometry: figDebugColoring %s " %
                                   self.figDebugColoring.canvas.manager.window.geometry())
        if self.placesWidget is not None: 
            self.logWidget.append( "self.places.geometry(): %s" % repr( self.placesWidget.geometry()))
        return
    
    def rotateColorsContinuously( self):
        self.isRotating = True
        self.colorRotateExecPb.setStyleSheet("background-color:lightblue")
        colorIndexOld = self.rotateColorMapIndex
        self.logWidget.append( "rotate: started rotating at %d" % 
                               ( colorIndexOld))
        self.app.processEvents()
        self.calcMandelbrotSet( display = False)

        while True:
            time.sleep( self.rotateWaitTime)
            #
            # avoid that color rotation blocks
            #
            self.app.processEvents()
            colorIndex = self.rotateColorMapIndex + self.colorRotateValue
            if colorIndex >= CMAP_MAX:
                colorIndex = 0
            if colorIndex < 0:
                colorIndex = CMAP_MAX - 1
            self.cmapRotateSlider.setValue( colorIndex)
            if self.stopRequested:
                self.stopRequested = False
                self.colorRotateExecPb.setStyleSheet("background-color:%s" % self.progressLblBg)
                self.logWidget.append( "rotate: stopped at %d" % self.rotateColorMapIndex) 
                break

        self.isRotating = False
        self.showMandelbrotSet()
                
        return 

    def cb_colorRotateExecPb( self):
        if self.isRotating: 
            self.stopRequested = True
            self.logWidget.append( "rotateColorGoPb: stop requested")
            return

        self.rotateColorsContinuously()
        return
    
    def cb_colorRotateCombo( self, i):

        self.colorRotateValue = COLORROTATE_VALUES[ i]
        return 

    def cb_rotateWaitTimeCombo( self, i):

        self.rotateWaitTime = float( ROTATEWAITTIME_VALUES[ i])
        
        return

    def cb_animateZoom( self):
        #
            
        if self.deltaM > 2.9:
            temp = QMessageBox()
            temp.question(self,'', 
                          "animate: zoom-in first, then animate'", 
                          temp.Ok )
            return
        vminEnd = self.vmin
        vmaxDiff = 1024. - self.vmax
        vminStart = 0
        vmaxStart = 1024
        self.vmin = vminStart
        self.vmax = vmaxStart
        self.vminSlider.setValue( int( self.vmin))
        self.vmaxSlider.setValue( int( self.vmax))

        deltaStart = 3.
        deltaEnd = self.deltaM
        cxEnd = self.cxM
        cyEnd = self.cyM
        cxStart = -0.75
        cyStart = 0.
        self.cxM = cxStart
        self.cyM = cyStart
        self.deltaM = deltaStart
        self.cxM = cxEnd
        self.cyM = cyEnd
        self.isAnimating = True
        self.animatePb.setStyleSheet("background-color:lightblue")
        
        startTime = time.time()
        
        frames = int( math.log( deltaEnd/deltaStart)/math.log( self.animationFactor))
        radiusStart = 0.1
        radiusEnd = deltaEnd/5.
        t = np.linspace(0, 1, frames)
        tReverse = np.linspace(1, 0, frames)
        #
        # delta *= 0.05 gives an exponential decay, 
        # here is the functional expression
        #
        delta = deltaStart * np.exp( np.log( deltaEnd/deltaStart) * t)
        
        if self.spiral > 0: 
            theta = 2 * np.pi * self.spiral * t
            radius = radiusStart * np.exp( np.log(radiusEnd / radiusStart) * t)
            cx = cxEnd + radius * np.cos(theta) - radius[-1] * np.cos( theta[-1])
            cy = cyEnd + radius * np.sin(theta) - radius[-1] * np.sin( theta[-1])
        elif self.spiral == -1: 
            #
            # we move towards the target point coming from the center
            #
            if cxStart > cxEnd: 
                cx = cxEnd + delta*tReverse/3.
            else: 
                cx = cxEnd - delta*tReverse/3.
            if cyStart > cyEnd:
                cy = cyEnd + delta*tReverse/3.
            else: 
                cy = cyEnd - delta*tReverse/3.
        else:
            cx = np.ones( frames) * cxEnd
            cy = np.ones( frames) * cyEnd

        if self.debugSpiral == "True": 
            self.prepareDebugSpiralFigure( axes = 1)
            self.axDebugSpiral.clear()
            self.axDebugSpiral.scatter( cx, cy, color = 'blue', marker = 'o')
            self.axDebugSpiral.set_title( "cy vs. cx")
            self.axDebugSpiral.grid( True)
        else:
            if self.figDebugSpiral is not None: 
                plt.close( self.figDebugSpiral)
                self.figDebugSpiral = None

        #
        # take half of the width during animation to speed-up - 
        # unless the user does not permit it.
        #
        widthMOld = self.widthM
        if self.animateAtConstantWidth == "False": 
            newWidth = int( self.widthM * 0.5)
            if newWidth in WIDTH_VALUES: 
                self.widthM = newWidth
                self.setCurrentIndices()
            else: 
                self.logWidget.append( "cb_animateZoom: cannot use 50% of width, not in VALUES")

        colorIndexOld = self.rotateColorMapIndex
        for i in range( len( cx)):
            self.cxM = cx[i]
            self.cyM = cy[i]
            self.deltaM = delta[i]
            temp = (deltaStart - self.deltaM) / (deltaStart - deltaEnd)
            self.vmin = vminStart + temp * (vminEnd - vminStart)
            self.vmax = 1024. - vmaxDiff*temp
            self.vminSlider.setValue( int( self.vmin))
            self.vmaxSlider.setValue( int( self.vmax))
            self.calcMandelbrotSet( display = False)
            self.showMandelbrotSet()
            if self.stopRequested:
                self.stopRequested = False
                self.logWidget.append( "animate: stopped") 
                break
        self.widthM = widthMOld
        self.setCurrentIndices()
        self.logWidget.append( "animate: DONE, %g" % 
                               (( time.time() - startTime)))
        self.animatePb.setStyleSheet("background-color:%s" % self.progressLblBg)
        self.vmin = vminEnd
        self.vmax = (1024. - vmaxDiff)
        self.vminSlider.setValue( int( self.vmin))
        self.vmaxSlider.setValue( int( self.vmax))
        self.cxM = cxEnd
        self.cyM = cyEnd
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.app.processEvents()
        self.isAnimating = False
        return

    def cb_animateMaxIter( self):
        #
        self.isAnimating = True
        maxIterLow = self.maxIterM/8.
        maxIterHigh = self.maxIterM
        
        arrUp = np.linspace( 0, 1, 50, dtype=np.float64)
        temp = maxIterHigh - maxIterLow
        arrUp = arrUp*temp + float( maxIterLow) 

        arrDown = np.linspace( 0, -1, 50, dtype=np.float64)
        arrDown = arrDown*temp + float( maxIterHigh) 

        for elm in arrDown: 
            self.maxIterM = elm
            print( "Down %g" % elm) 
            self.calcMandelbrotSet()
            self.showMandelbrotSet()
        for elm in arrUp: 
            self.maxIterM = elm
            print( "Up %g" % elm) 
            self.calcMandelbrotSet()
            self.showMandelbrotSet()
            
        self.maxIterM = maxIterHigh
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
            
        self.isAnimating = False
        self.app.processEvents()
        return

    def cb_zoomOut( self):
        self.deltaM *= self.zoom
        if self.deltaM > 3.:
            self.cb_reset()
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return

    def cb_zoomHome( self): 
        #self.setResetMarker()
        self.cxM = -0.75
        self.cyM = 0.
        self.deltaM = 3.
        self.cxJ = 0.
        self.cyJ = 0.
        self.deltaJ = 3.
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return

    def readFile( self, fName):
        image = Image.open(fName)
        hsh = image.info
        image.close()
        self.lastFileRead = fName
        temp = self.trimCenterName( fName)
        self.lastReadLbl.setText( temp)
        self.logWidget.append( "Reading %s" % ( fName))
        print( "Reading %s" % ( fName))
        for elm in hsh:
            print( "  %-14s : %s" % ( elm, hsh[ elm]))
        print( "Reading Done")

        self.cxM = float( hsh[ 'cxM'])
        self.cyM = float( hsh[ 'cyM'])
        self.deltaM = float( hsh[ 'deltaM'])

        self.colorMapName = hsh[ 'colorMapName']
        try: 
            self.rotateColorMapIndex = int( hsh[ 'rotateColorMapIndex'])
        except: 
            try: 
                self.rotateColorMapIndex = int( hsh[ 'rotateColorMap'])
            except:
                self.rotateColorMapIndex = 0
                    
        self.flagReversed = "False"
        try: 
            self.flagReversed = hsh[ 'flagReversed']
        except:
            pass

        self.norm = hsh[ 'norm']
        if self.norm == "LinNormR":
            self.norm = "LinNorm"
            self.flagReversed = "True"
                
        self.normPar = float( hsh[ 'normPar'])
            
        self.band = "False"
        try: 
            self.band = hsh[ 'band']
        except:
            pass
            
        self.flagCyclic = "False"
        try: 
            self.flagCyclic = hsh[ 'flagCyclic']
        except:
            pass

        self.setColor( self.colorMapName,
                              self.rotateColorMapIndex,
                              self.band)
            
        self.widthM = int( hsh[ 'widthM'])
        self.widthJ = int( hsh[ 'widthJ'])
        self.modulo = int( hsh[ 'modulo'])
        self.smooth = hsh[ 'smooth']
        self.maxIterM = int( hsh[ 'maxIterM'])
        self.maxIterJ = int( hsh[ 'maxIterJ'])
        self.power = int( hsh[ 'power'])

        self.clip = "False"
        try: 
            self.clip = hsh[ 'clip']
        except:
            pass
        self.vmin = 0
        try: 
            self.vmin = float( hsh[ 'vmin'])
        except:
            pass
        self.vmax = 1024
        try: 
            self.vmax = float( hsh[ 'vmax'])
        except:
            pass
        self.shaded = hsh[ 'shaded']
        self.scanCircle = hsh[ 'scanCircle']
        self.vert_exag = 1.
        try: 
            self.vert_exag = float( hsh[ 'vert_exag'])
        except:
            pass
        self.interpolation = hsh[ 'interpolation']
        self.blendMode = hsh[ 'blendMode']
        self.azDeg = int( hsh[ 'azDeg'])
        self.altDeg = int( hsh[ 'altDeg'])

        self.addCenterItem( name = fName, cx = self.cxM, cy = self.cyM)
        
        self.setCurrentIndices()        

        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return 
        
    def cb_lastRead( self):
        if self.lastFileRead is None:
            self.logWidget.append( "No file read so far")
            return
        self.readFile( self.lastFileRead)
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return
        
    def cb_setRM( self):
        self.resetMarker.set( x = self.cxM, 
                              y = self.cyM, 
                              text = r'+', 
                              color=self.rmColor) 
        self.showMandelbrotSet()
        self.showJuliaSet()
        return
        
    def cb_clearRM( self):
        self.resetMarker.set( text = r'') 
        self.showMandelbrotSet()
        self.showJuliaSet()
        return
    
    def cb_close( self):
        plt.close( self.figM)
        self.figM = None
        plt.close( self.figJ)
        self.figJ = None
        plt.close( self.figM3D)
        self.figM3D = None
        self.close()
        sys.exit( 255) 
        return

    def cb_shaded( self, i):
        if i:
            self.shaded = 'True'
        else:
            self.shaded = 'False'
        self.showMandelbrotSet()
        self.showJuliaSet()
        return

    def cb_band( self, i):
        if i:
            self.band = "True" 
        else:
            self.band = "False"
        self.setColor( self.colorMapName,
                       self.rotateColorMapIndex,
                       self.band)
        self.showMandelbrotSet()
        self.showJuliaSet()
        return 

    def cb_spiralCombo( self, i):
        self.spiral = SPIRAL_VALUES[i]
        return 

    def cb_clip( self, i):
        if i:
            self.clip = "True" 
        else:
            self.clip = "False"
        self.showMandelbrotSet()
        self.showJuliaSet()
        return 

    def cb_reversed( self, i):
        if i:
            self.flagReversed = "True" 
        else:
            self.flagReversed = "False"
        self.setColor( self.colorMapName,
                       self.rotateColorMapIndex,
                       self.band)
        self.showMandelbrotSet()
        self.showJuliaSet()
        return 

    def cb_cyclic( self, i):
        if i:
            self.flagCyclic = "True" 
        else:
            self.flagCyclic = "False"
        self.setColor( self.colorMapName,
                       self.rotateColorMapIndex,
                       self.band)
        self.showMandelbrotSet()
        self.showJuliaSet()
        return 

    def cb_nColorCyclicCombo( self, i):
        self.nColorCyclic = int( NCOLORCYCLIC_VALUES[i])
        self.setColor( self.colorMapName,
                       self.rotateColorMapIndex,
                       self.band)
        self.showMandelbrotSet()
        self.showJuliaSet()
        return 

    def cb_cython( self, i):
        if i:
            self.cython = "True" 
            self.numba = "False" 
            if numbaOK: 
                self.numbaAction.setChecked( self.numba == "True") 
            self.scalar = "False" 
            self.scalarAction.setChecked( self.scalar == "True") 
            self.numpy = "False"
            self.numpyAction.setChecked( self.numpy == "True") 
        else:
            self.cython = "False"
            self.tiled = "False"
            self.tiledAction.setChecked( self.tiled == "True") 
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return 

    def cb_tiled( self, i):
        if i:
            self.tiled = "True"
            self.cython = "True"
            self.cythonAction.setChecked( self.cython == "True")
            if numbaOK: 
                self.numbaAction.setChecked( self.numba == "True") 
            self.scalar = "False" 
            self.scalarAction.setChecked( self.scalar == "True") 
            self.numpy = "False"
            self.numpyAction.setChecked( self.numpy == "True") 
        else:
            self.tiled = "False"
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return 

    def cb_numpy( self, i):
        if i:
            self.numpy = "True"
            self.cython = "False" 
            self.cythonAction.setChecked( self.cython == "True") 
            self.tiled = "False"
            self.tiledAction.setChecked( self.tiled == "True") 
            self.scalar = "False" 
            self.scalarAction.setChecked( self.scalar == "True") 
            self.numba = "False" 
            if numbaOK: 
                self.numbaAction.setChecked( self.numba == "True") 
        else:
            self.cython = "False"
            self.tiled = "False"
            self.tiledAction.setChecked( self.tiled == "True") 
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return 

    def cb_numba( self, i):
        if i:
            self.numba = "True" 
            self.cython = "False"
            self.tiled = "False"
            if cythonOK:
                self.cythonAction.setChecked( self.cython == "True")
                self.tiledAction.setChecked( self.cython == "True")
        else:
            self.numba = "False"
            self.cython = "True"
            self.tiled = "True"
            if cythonOK:
                self.cythonAction.setChecked( self.cython == "True") 
                self.tiledAction.setChecked( self.tiled == "True") 
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return 

    def cb_scalar( self, i):
        if i:
            self.numba = "False" 
            if numbaOK:
                self.numbaAction.setChecked( self.numba == "True")
            self.scalar = "True" 
            self.numpy = "False"
            if cythonOK:
                self.cython = "False"
                self.tiled = "False"
                self.cythonAction.setChecked( self.cython == "True")
                self.tiledAction.setChecked( self.cython == "True")
            else: 
                self.numpy = "True"
            self.numpyAction.setChecked( self.numpy == "True") 
        else:
            self.scalar = "False" 
            self.numba = "False"
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        return 

    def cb_numpyOnly( self, i):
        if i:
            self.numpyOnly = "True" 
        else:
            self.numpyOnly = "False" 
        return 

    def cb_cardioidBulb( self, i):
        if i:
            self.cardioidBulb = "True" 
        else:
            self.cardioidBulb = "False" 
        return 

    def cb_prange( self, i):
        if i:
            self.prange = "True" 
        else:
            self.prange = "False" 
        return 

    def cb_highPrec( self, i):
        if i:
            self.highPrec = "True" 
        else:
            self.highPrec = "False"
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return 

    def cb_animateAtConstantWidth( self, i):
        if i:
            self.animateAtConstantWidth = "True" 
        else:
            self.animateAtConstantWidth = "False" 
        return 

    def cb_debugSpiral( self, i):
        if i:
            self.debugSpiral = "True" 
        else:
            self.debugSpiral = "False"
            if self.figDebugSpiral is not None:
                plt.close( self.figDebugSpiral)
                self.figDebugSpiral = None

        return 

    def cb_debugColoring( self, i):
        if i:
            self.debugColoring = "True" 
            self.calcMandelbrotSet()
            self.showMandelbrotSet()
        else:
            self.debugColoring = "False"
            if self.figDebugColoring is not None:
                plt.close( self.figDebugColoring)
                self.figDebugColoring = None
                self.cbar = None

        return 

    def cb_debugSpeed( self, i):
        if i:
            self.debugSpeed = "True" 
        else:
            self.debugSpeed = "False"

        return 

    def cb_rmColor( self, i):
        if i:
            self.rmColor = 'black'
        else:
            self.rmColor = 'white'
        self.resetMarker.set( color=self.rmColor) 
        self.showMandelbrotSet()
        self.showJuliaSet()
        return 

    def cb_showData( self, i):
        if i:
            self.showData = "True" 
        else:
            self.showData = "False"
        return 
        
    def cb_smoothModeCombo( self, i):
        self.smooth = SMOOTH_VALUES[i]
            
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return
        
    def cb_scanCircle( self, i):
        if i:
            self.scanCircle = "True"
        else:
            self.scanCircle = "False"
        return

    def clearScanPars( self):
        if self.scanMarker is not None: 
            self.scanMarker.remove()
            self.scanMarker = None
            
        if self.cxOld is not None: 
            self.cxM = self.cxOld
            self.cyM = self.cyOld
            self.deltaM = self.deltaOld
        self.scanPath = []
        for t in self.scanTexts: 
            t.remove()
        self.scanTexts = []
        return 
    
    def cb_execScan( self):
        
        if len( self.scanPath) < 2:
            temp = QMessageBox()
            ret = temp.question(self,'', 
                                "execScan: use MB-Right to select scan points'", temp.Ok )
            return
        
        if self.juliaMode == 'Off':
            temp = QMessageBox()
            ret = temp.question(self,'', "Julia mode is 'Off'", temp.Ok )
            return 
        #
        # need  this because JuliaMode might have been enabled  
        # after the scan points have been defined
        #
        plt.figure( self.figM.number) 

        self.isAnimating = True
        
        self.cxOld = self.cxM
        self.cyOld = self.cyM
        self.deltaOld = self.deltaM
        startTime = time.time()
        if self.scanCircle == "False": 
            self.logWidget.append( "Starting scan")
            scanPointsSeg = int( self.scanPoints/(len( self.scanPath)-1))
            self.scanMarker = plt.text( 0, 0, '', color='cyan',
                                   fontsize = 16, 
                                   horizontalalignment='center', verticalalignment='center')
            for iPt in range( len( self.scanPath))[1:]:
                if self.stopRequested:  
                    break
                startPoint = self.scanPath[iPt-1]
                endPoint = self.scanPath[iPt]
                for i in range( scanPointsSeg):
                    self.cxM = startPoint[0] + (endPoint[0] - startPoint[0])/scanPointsSeg*i
                    self.cyM = startPoint[1] + (endPoint[1] - startPoint[1])/scanPointsSeg*i
                    self.scanMarker.set( x = self.cxM, y = self.cyM, text = r'+', color='cyan') 
                    if self.calcJuliaSet( display = False) is False:
                        break
                    self.showJuliaSet()
                    self.deltaM = 0.1
                    self.app.processEvents()
                    if self.stopRequested:  
                        break
            self.stopRequested = False
        else:
            if len( self.scanPath) != 3:
                temp = QMessageBox()
                ret = temp.question(self,'', "execScan: circular scans need 3 points'", temp.Ok )
                self.isAnimating = False
                return
            (c), r = self.circle_from_points()
            deltaPhi = 2.*math.pi/self.scanPoints
            self.logWidget.append( "Starting scan") 
            self.scanMarker = plt.text( 0, 0, '', color='cyan',
                                   fontsize = 16, 
                                   horizontalalignment='center',
                                   verticalalignment='center')
            for i in range( int( self.scanPoints)):
                self.cxM = c[0] + r*math.cos( deltaPhi*i)
                self.cyM = c[1] + r*math.sin( deltaPhi*i)
                self.scanMarker.set( x = self.cxM, y = self.cyM,
                                text = r'+', color='cyan') 
                if self.calcJuliaSet( display = False) is False:
                    break
                self.showJuliaSet()
                self.app.processEvents()
                if self.stopRequested:
                    self.stopRequested = False
                    break

        self.isAnimating = False

        self.logWidget.append( "Scan done, %g s" % (time.time() - startTime))

        self.clearScanPars()

        self.calcJuliaSet()
        self.showJuliaSet()
        return

    def cb_juliaModeCombo( self, i):
        
        self.juliaMode = JULIA_MODE_VALUES[ i]

        if self.juliaMode == 'Off':
            if self.figJ is not None: 
                plt.close( self.figJ)
                self.figJ = None
                self.imJ.remove()
                self.imJ = None
                return

        if self.juliaMode == 'Huge': 
            self.figSizeJ = self.figSizeHuge
        elif self.juliaMode == 'Large': 
            self.figSizeJ = self.figSizeLarge
        elif self.juliaMode == 'Big': 
            self.figSizeJ = self.figSizeBig
        elif self.juliaMode == 'Medium': 
            self.figSizeJ = self.figSizeMedium
        elif self.juliaMode == 'Small': 
            self.figSizeJ = self.figSizeSmall
        else: 
            self.figSizeJ = self.figSizeTiny

        if self.figJ is None:
            self.figJ, self.axJ = plt.subplots( figsize= self.figSizeJ, dpi = self.dpi,  
                                                           facecolor = 'white')
            self.mgrJ = self.figJ.canvas.manager
            #self.axJ.set_aspect('equal', adjustable='box')
            self.figJ.canvas.manager.set_window_title( 'Julia Set')
            self.figJ.canvas.mpl_connect("close_event",
                                         self.cb_closeFigJ)

            self.mgrJ = plt.get_current_fig_manager()
            self.figJ.subplots_adjust( top=1., bottom=0., 
                                              left=0.0, right=1.,  
                                              hspace=0., wspace=0.)
            self.juliaKeyclick = \
                self.figJ.canvas.mpl_connect( 'button_press_event',
                                                     self.cb_onClickJulia)
            
            self.textTitleJ = \
                plt.gcf().text( 0.02, 0.99,
                                r'$z_{n+1} = z_n^%d + c, z_0 = c$' % self.power,
                                color = 'white', fontname = 'monospace', size = 12,
                                horizontalalignment='left', verticalalignment='top',
                                bbox=dict(fill=False, edgecolor='white', linewidth=1))
            self.calcJuliaSet()
            self.showJuliaSet()

        self.geomJ = self.mgrJ.window.geometry()
        if self.modeOperation.lower() == 'demo': 
            self.figJ.canvas.manager.window.setGeometry( 5332, 535,
                                                         self.geomJ.width(), self.geomJ.height())
        else: 
            self.mgrJ.window.setGeometry( 1100, 1100, self.geomJ.width(), self.geomJ.height())
        self.figJ.set_size_inches( self.figSizeJ[0], self.figSizeJ[1], forward = True)
        return 

    def cb_mandelbrotModeCombo( self, i):
        self.mandelbrotMode = MANDELBROT_MODE_VALUES[i]
        if self.mandelbrotMode == 'Tiny': 
            self.figSizeM = self.figSizeTiny
        elif self.mandelbrotMode == 'Small': 
            self.figSizeM = self.figSizeSmall
        elif self.mandelbrotMode == 'Medium': 
            self.figSizeM = self.figSizeMedium
        elif self.mandelbrotMode == 'Big': 
            self.figSizeM = self.figSizeBig
        elif self.mandelbrotMode == 'Large': 
            self.figSizeM = self.figSizeLarge
        else: 
            self.figSizeM = self.figSizeHuge

        self.figM.set_size_inches( self.figSizeM[0], self.figSizeM[1], forward = True)
        self.geomM = self.mgrM.window.geometry()
        self.mgrM.window.setGeometry( 50, 50, self.geomM.width(), self.geomM.height())

        self.showMandelbrotSet()

        return 

    def cb_3D( self, i):
        if i:
            self.flagM3D = "True"
            if self.figM3D is None: 
                self.figM3D = \
                    self.figM3D = plt.figure( 3,
                                             figsize= self.figSize3D, facecolor="black", dpi=self.dpi)
                self.figM3D.canvas.manager.set_window_title( 'Mandelbrot Set 3D')
                self.figM3D.canvas.mpl_connect("close_event",
                                              self.cb_closeFigM3D)
                
                self.ax3D = self.figM3D.add_subplot(111, projection='3d')
                self.figM3D.subplots_adjust( top=1., bottom=0., 
                                            left=0.0, right=1., hspace=0.,wspace=0.)
                self.showMandelbrotSet3D()
        else: 
            self.flagM3D = "False"
            plt.close( self.figM3D)
            self.figM3D = None

        return 

    def cb_stop( self):
        self.stopRequested = True
        return

    def setDefaults( self):

        self.rmColor = 'white'
        if self.resetMarker is not None: 
            self.resetMarker.set( color=self.rmColor) 
            self.rmColorAction.setChecked( self.rmColor == "black")
        
        self.debugSpeed = "True"
        if self.debugSpeedAction is not None: 
            self.debugSpeedAction.setChecked( self.debugSpeed == "True")
        self.cardioidBulb = "True" 
        if self.cardioidBulbAction is not None: 
            self.cardioidBulbAction.setChecked( self.cardioidBulb == "True")
        self.prange = "True" 
        if self.prangeAction is not None: 
            self.prangeAction.setChecked( self.prange == "True")

        self.rmColor = 'white'
        self.flagReversed = "False"
        self.flagCyclic = "False"
        self.nColorCyclic = NCOLORCYCLIC_VALUES[0]
        self.isRotating = False
        self.rotateWaitTime = ROTATEWAITTIME_VALUES[0]
        self.colorRotateValue = COLORROTATE_VALUES[0]
        self.azDeg = AZDEG_VALUES[0]
        self.animationFactor = ANIMATIONFACTOR_VALUES[0]
        self.altDeg = ALTDEG_VALUES[0]
        self.blendMode = BLEND_MODE_VALUES[0]
        self.colorMapName = 'hot'
        self.rotateColorMapIndex = 0
        self.band = "False"
        self.setColor( self.colorMapName,
                       self.rotateColorMapIndex,
                       self.band)
        self.spiral = SPIRAL_VALUES[0]
        if cythonOK: 
            self.cython = "True"
            self.tiled = "True"
            if self.cythonAction is not None: 
                self.cythonAction.setChecked( self.cython == "True")
                self.tiledAction.setChecked( self.cython == "True")
            self.numpy = "False" 
            if self.numpyAction is not None: 
                self.numpyAction.setChecked( self.numpy == "True")
        else:
            self.numpy = "True" 
            self.cython = "False"
            self.tiled = "False"

        self.numba = "False"

        self.numpyOnly = "False" 
        if self.numpyOnlyAction is not None: 
            self.numpyOnlyAction.setChecked( self.numpyOnly == "True")


        self.scalar = "False" 
        if self.scalarAction is not None: 
            self.scalarAction.setChecked( self.scalar == "True")

        self.highPrec = "False"

        self.flagM3D = "False"
        self.surface = None
        self.smooth = SMOOTH_VALUES[ 0]
        self.interpolation = INTERPOLATION_VALUES[0]
        self.maxIterM = MAX_ITER_VALUES[0]
        self.maxIterJ = MAX_ITER_VALUES[0]
        if self.maxIterMCombo is not None: 
            self.maxIterMCombo.setCurrentIndex( 0) 
        if self.maxIterJCombo is not None: 
            self.maxIterJCombo.setCurrentIndex( 0) 
        self.modulo = MODULO_VALUES[0]
        self.modFactor= 2
        self.power = 2
        self.norm = NORM_VALUES[0]        
        self.normPar = NORMPAR_VALUES[0]
        if self.normParCombo is not None:
            self.normParCombo.setEnabled( True)
        self.vmin = 0
        self.vmax = DATA_NORM

        self.animateAtConstantWidth = "False"
        self.clip = "True" # 
        self.scanCircle = "False"
        self.scanPoints = SCAN_POINT_VALUES[0]
        self.shaded = 'False'
        self.vert_exag = VERT_EXAG_VALUES[0]
        self.widthM = WIDTH_VALUES[0]
        self.widthJ = WIDTH_VALUES[0]
        self.zoom = ZOOM_VALUES[0]
        self.mandelbrotMode = MANDELBROT_MODE_VALUES[ 3]
        if self.juliaMode == None: 
            self.juliaMode = JULIA_MODE_VALUES[ 0]
        self.clearScanPars()
            
        self.debugSpiral = "False"
        if self.figDebugSpiral is not None: 
            plt.close( self.figDebugSpiral)
            self.figDebugSpiral = None
        self.debugColoring = "False"
        if self.figDebugColoring is not None: 
            plt.close( self.figDebugColoring)
            self.figDebugColoring = None
            self.cbar = None
        if self.cbar is not None:
            self.cbar.remove()
            self.cbar = None

        self.cxM = -0.75
        self.cyM = 0.
        self.deltaM = 3.
        self.cxJ = 0.
        self.cyJ = 0.
        self.deltaJ = 3.

        self.showData = "False"
        self.isAnimating = False

        self.setCurrentIndices()
        return 

    def setResetMarker( self):
        #
        # do not set the reset marker, if we look at the whole plot
        #
        if self.deltaM < 2: 
            self.resetMarker.set( x = self.cxM, 
                                  y = self.cyM, 
                                  text = r'+', 
                                  color=self.rmColor) 
        else: 
            self.resetMarker.set( x = self.cxM, 
                                  y = self.cyM, 
                                  text = r'', 
                                  color=self.rmColor)
        return 

    def cb_reset( self):

        self.setResetMarker()
        self.setDefaults()
        self.setCurrentIndices()
        
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return 

    def cb_maxIterMCombo( self, i):
        self.maxIterM = int( MAX_ITER_VALUES[i])
        self.calcMandelbrotSet( display=False)
        self.showMandelbrotSet()
        return

    def cb_maxIterJCombo( self, i):
        self.maxIterJ = int( MAX_ITER_VALUES[i])
        self.calcJuliaSet()
        self.showJuliaSet()
        return

    def cb_vert_exagModeCombo( self, i):
        self.vert_exag = float( VERT_EXAG_VALUES[i]) 
        self.showMandelbrotSet()
        return

    def cb_blendModeCombo( self, i):
        self.blendMode = BLEND_MODE_VALUES[i]
        self.showMandelbrotSet()
        return

    def cb_interpolationModeCombo( self, i):
        self.interpolation = INTERPOLATION_VALUES[i]
        self.showMandelbrotSet()
        return

    def cb_azDegCombo( self, i):
        self.azDeg = int( AZDEG_VALUES[i])
        self.showMandelbrotSet()
        self.showJuliaSet()
        return

    def cb_altDegCombo( self, i):
        self.altDeg = int( ALTDEG_VALUES[i])
        self.showMandelbrotSet()
        self.showJuliaSet()
        return

    def cb_animationFactorCombo( self, i):
        self.animationFactor = ANIMATIONFACTOR_VALUES[i]
        return
    
    def cb_moduloCombo( self, i):
        self.modulo = int( MODULO_VALUES[i])
        self.showMandelbrotSet()
        self.showJuliaSet()
        return

    def cb_normParCombo( self, i):
        self.normPar = float( NORMPAR_VALUES[i])

        self.showMandelbrotSet()
        self.showJuliaSet()
        return

    def cb_vminSlider( self, i):
        if i >= self.vmax:
            if self.logWidget is not None: 
                self.logWidget.append( "vmin >= vmax, resetting vmin")
            else: 
                print( "vmin >= vmax, resetting vmin")
            self.vminSlider.setValue( 0)
            return
        if self.vminSliderLbl is not None:
            self.vminSliderLbl.setText( "vmin: %4d" % i)
        self.vmin = float(i)

        self.showMandelbrotSet()
        return

    def cb_vmaxSlider( self, i):
        if i <= self.vmin:
            if self.logWidget is not None: 
                self.logWidget.append( "vmax >= vmax, resetting vmax")
            else:
                print( "vmax >= vmax, resetting vmax")
            self.vmaxSlider.setValue( DATA_NORM)
            return
        if self.vmaxSliderLbl is not None:
            self.vmaxSliderLbl.setText( "vmax: %4d" % i)
        self.vmax = float(i)
        self.showMandelbrotSet()
        return

    def cb_normCombo( self, i):
        self.norm = NORM_VALUES[i]
        self.vmin = 0
        self.vmax = DATA_NORM
        if self.norm in [ 'LinNormRRRR']: 
            if self.cbar is not None:
                self.cbar.remove() # this also destroys the axes, has to be re-created
                self.axDebugColoring[3] = self.figDebugColoring.add_axes([0.125, 0.11, 0.775, 0.167])
                self.cbar = None
                self.logWidget.append( "cb_normCombo: color bar does not like LinNormR") 
        
        if self.widthM == 256:
            self.vmax = CMAP_MAX - 1
        self.setCurrentIndices()
        self.showMandelbrotSet()
        self.showJuliaSet()
        return

    def cb_scanPointsCombo( self, i):
        self.scanPoints = float( SCAN_POINT_VALUES[i])
        return

    def cb_zoomCombo( self, i):
        self.zoom = float( ZOOM_VALUES[i])
        return

    def cb_widthCombo( self, i):
        self.widthM = int( WIDTH_VALUES[i])
        self.widthJ = int( WIDTH_VALUES[i])
        self.calcMandelbrotSet()
        self.showMandelbrotSet()
        self.calcJuliaSet()
        self.showJuliaSet()
        return

    import math

    def circle_from_points( self):
        # Unpack points
        x1, y1 = self.scanPath[0]
        x2, y2 = self.scanPath[1]
        x3, y3 = self.scanPath[2]

        # Calculate the determinants
        A = x1 * (y2 - y3) - y1 * (x2 - x3) + x2 * y3 - x3 * y2
        B = (x1**2 + y1**2) * (y3 - y2) + (x2**2 + y2**2) * (y1 - y3) + (x3**2 + y3**2) * (y2 - y1)
        C = (x1**2 + y1**2) * (x2 - x3) + (x2**2 + y2**2) * (x3 - x1) + (x3**2 + y3**2) * (x1 - x2)
        D = (x1**2 + y1**2) * (x3 * y2 - x2 * y3) + \
            (x2**2 + y2**2) * (x1 * y3 - x3 * y1) + \
            (x3**2 + y3**2) * (x2 * y1 - x1 * y2)

        # Center of the circle
        xc = -B / (2 * A)
        yc = -C / (2 * A)
        
        # Radius of the circle
        r = math.sqrt((B**2 + C**2 - 4 * A * D) / (4 * A**2))
        
        return (xc, yc), r

    def getData( self, x, y):
        xMin = self.cxM - self.deltaM/2.
        yMin = self.cyM - self.deltaM/2.

        xPixel = int( (x - xMin)/self.deltaM*float(self.widthM))
        yPixel = int( (y - yMin)/self.deltaM*float( self.widthM))

        if xPixel > (self.widthM - 1):
            xPixel = self.widthM - 1
        if yPixel > (self.widthM - 1):
            yPixel = self.widthM - 1
        try: 
            temp = self.dataMandelbrotSet[ yPixel][ xPixel]
        except Exception as e:
            temp = -1
            print( "getData %s" % repr( e))
        return temp

    def cb_iterPath( self, i):
        if i:
            if self.deltaM < 3.:
                temp = QMessageBox()
                ret = temp.question(self,'', 
                                    "iterPath: only for the whole plot", temp.Ok )
                self.flagIterPath = "False" 
                self.iterPathCb.setChecked( self.iterPath == "True") 
                return 
                
            self.flagIterPath = "True" 
        else:
            self.flagIterPath = "False" 
            if self.iterPath is not None:
                self.iterPath.remove()
                self.iterPath = None
                #self.axM.set_xlim([-2, 1])
                #self.axM.set_ylim([-1.5, 1.5])
                #self.axM.axis('off')
                #self.axM.figure.canvas.draw_idle()
                return 
                
        return 

    def handleIterPath( self, event):
        
        plt.figure( self.figM.number)
        if self.iterPath is not None:
            self.iterPath.remove()
            self.iterPath = None
        #
        # Z**2 = (x**2 - y**2) + i*x*y
        #
        #x = [event.xdata]
        #y = [event.ydata]
        x = [0.]
        y = [0.]
        for n in range( 100):
            x.append( x[n-1]**2 - y[n-1]**2 + event.xdata)
            y.append( 2.*x[n-1]*y[n-1] + event.ydata)
            if (x[-1]**2 + y[-1]**2) > 20:
                #x = x[:-1]
                #y = y[:-1]
                break
        #if len( x) > 2:
        #    temp = math.sqrt( (x[-1] - x[-2])**2 + (y[-1] - y[-2])**2)
        #    self.logWidget.append( "convergence %g " % temp)
        self.iterPath, = self.axM.plot( x, y, linewidth = 0.75, color = 'white')
        self.axM.set_xlim([ self.cxM - self.deltaM/2., self.cxM + self.deltaM/2.])
        self.axM.set_ylim([ self.cyM - self.deltaM/2., self.cyM + self.deltaM/2.])
        return
    
    def cb_onMotionMandelbrot( self, event):

        if event is None: 
            return
        if event.inaxes is None:
            return

        if self.flagIterPath == "True": 
            self.handleIterPath( event)
            return 
        
        if self.showData != "True":
            return
        
        if self.dataMandelbrotSet is None:
            return
        
        try: 
            temp = self.getData( event.xdata, event.ydata)
        except Exception as e: 
            print( "cb_motion %s" % repr( e))

        self.dataLbl.setText( "x: %g, y: %g data: %g" % (event.xdata, event.ydata, temp))

        return 

    def cb_onClickMandelbrot( self, event):
        #
        # MB-Left: Zoom-in
        #
        if event.button is MouseButton.LEFT:
            if self.flagIterPath == "True": 
                self.handleIterPath( event)
                return 
            self.cxM = event.xdata
            self.cyM = event.ydata
            self.deltaM = self.deltaM/self.zoom
            self.calcMandelbrotSet()
            self.showMandelbrotSet()
            self.calcJuliaSet()
            self.showJuliaSet()

        #
        # MB-Right: define scan path
        #
        if event.button is MouseButton.RIGHT: 
            self.scanTexts.append( plt.text( event.xdata, event.ydata, r'*', color='cyan',
                                             fontsize = 20, 
                                             horizontalalignment='center', 
                                             verticalalignment='center'))
            self.scanPath.append( (event.xdata, event.ydata))
            self.logWidget.append( "New scan point %d %g %g " % 
                                   (len( self.scanPath), event.xdata, event.ydata))
            return 
        #
        # MB-Middle: shift center
        #
        elif event.button is MouseButton.MIDDLE:
            self.cxM = event.xdata
            self.cyM = event.ydata
            self.calcMandelbrotSet()
            self.showMandelbrotSet()
            self.calcJuliaSet()
            self.showJuliaSet()
        
        return

    def cb_onClickJulia( self, event):
        if event.button is MouseButton.LEFT:
            self.cxJ = event.xdata
            self.cyJ = event.ydata
            self.deltaJ = self.deltaJ/self.zoom
            self.logWidget.append( "onClickJ: cx %g cy %g" % (self.cxJ, self.cyJ))
            self.calcMandelbrotSet()
            self.showMandelbrotSet()
            self.calcJuliaSet()
            self.showJuliaSet()
        
        return

    def keyPressEvent(self, event):
        ind = self.cmapRotateSlider.value()

        if event.key() == Qt.Key_Left:
            ind -= 1
            if ind < 0:
                ind = 0
        elif event.key() == Qt.Key_Right:
            ind += 1
            if ind > (CMAP_MAX - 1):
                ind = CMAP_MAX - 1
        self.cmapRotateSlider.setValue(ind)
            
        return 
    #
    # === callbacks END
    #
    def calcMandelbrotSet( self, display = True):
        """
        +++ calculates self.dataMandelbrotSet
        """
        if self.widthM == 256:
            self.vmax = CMAP_MAX - 1
            self.setCurrentIndices()
            self.dataMandelbrotSet = np.tile(np.arange(256), (256, 1))
            return 
            
        if self.smooth == "DZ": 
            if self.cython == "True":
                return self.calcMandelbrotSetDzCython()
            else: 
                return self.calcMandelbrotSetDZ()

        if self.cython == "True": 
            return self.calcMandelbrotSetCython()

        if self.numba == "True": 
            return self.calcMandelbrotSetNumba()

        if self.scalar == "True": 
            return self.calcMandelbrotSetScalar()

        if self.numpy == "False":
            if cythonOK: 
                self.cython = "True"
                self.cythonAction.setChecked( self.cython == "True")
                return self.calcMandelbrotSetCython()
            self.logWidget.append( "calcMandelbrotSet: select a method")
            return 

        if display: 
            self.progressLbl.show()
            self.progressLbl.setText( "Progress: 0/%4d M" % (self.maxIterM))

        if self.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        log_horizon = np.log2(np.log(horizon))
            
        x = np.linspace( self.cxM - self.deltaM/2.,
                          self.cxM + self.deltaM/2.,
                          self.widthM, dtype=np.float64)
        y = np.linspace( self.cyM - self.deltaM/2.,
                          self.cyM + self.deltaM/2.,
                          self.widthM, dtype=np.float64)
        
        c = x + y[:,None]*1j
        self.progressLbl.setStyleSheet("background-color:lightblue")
        self.app.processEvents()

        z = np.zeros(c.shape, np.complex128)

        escapeCount = np.zeros(c.shape) 
        
        startTime = time.time()
        for it in range( self.maxIterM):
            #
            # notdone is a 2D array with True/False values
            #
            if self.numpyOnly or self.deltaM < 1e-11: 
                notdone = np.less( z.real*z.real + z.imag*z.imag, float( horizon))
            else: 
                notdone = ne.evaluate('z.real*z.real + z.imag*z.imag < %g' % float( horizon))
            #
            # escapeCount is set to it at the positions where notdone is true
            #
            escapeCount[notdone] = it
            if self.numpyOnly or self.deltaM < 1e-11: 
                z[notdone] = z[notdone]**2 + c[notdone]
            else: 
                z = ne.evaluate('where(notdone,z**2+c,z)')
            if (it % 100) == 0 and display:
                self.progressLbl.setText( "Progress: %4d/%4d M" % ( it, self.maxIterM))
                self.app.processEvents()
                self.dataMandelbrotSet = np.copy( escapeCount)
                self.dataMandelbrotSet3D = np.copy( escapeCount)
                #self.dataMandelbrotSet[ self.dataMandelbrotSet == it] = 0
                self.showMandelbrotSet()
                
            if self.stopRequested:
                break

        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= DATA_NORM/float( self.maxIterM) 

        self.dataMandelbrotSet3D = np.copy( escapeCount)
        #
        # smoothing algorithm from 
        # https://linas.org/art-gallery/escape/smooth.html
        #
        if self.smooth == "DistEst": 
            temp = np.log( abs(z))
            temp[ temp <= 0.] = LOG_HELPER
            escapeCount = np.nan_to_num( escapeCount + 1 - np.log2( temp) + log_horizon)
        
        if escapeCount.shape[0] == 10: 
            print( "calcMandelbrotSet: escapeCount %s" % repr( escapeCount))

        self.dataMandelbrotSet = escapeCount
        
        self.showMandelbrotSet()

        if self.debugSpeed == "True": 
            self.logWidget.append( "M: %5.3f s, Numpy/Numexpr, NumpyOnly %s" % 
                                   (( time.time() - startTime), repr( self.numpyOnly)))

        if display: 
            self.progressLbl.setText( "Progress: %4d/%4d M" % ( it, self.maxIterM))
            self.progressLbl.setStyleSheet("background-color:%s" % self.progressLblBg)
            self.progressLbl.hide()

        return 

    def calcMandelbrotSetCython( self):
        # +++

        if self.tiled == "True": 
            self.calcMandelbrotSetCythonTiled()
            return
        
        startTime = time.time()
        if self.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        log_horizon = np.log2(np.log(horizon))
        
        if self.highPrec == "True":
            self.logWidget.append( "Starting highPrec run, slow. ")
            self.app.processEvents()

            (escapeCount, zAbs) = mandelbrotCython.compute_mandelbrot_hp( 
                self.widthM, self.widthM, 
                self.cxM - self.deltaM/2., 
                self.cxM + self.deltaM/2., 
                self.cyM - self.deltaM/2., 
                self.cyM + self.deltaM/2., 
                self.maxIterM, horizon, 20, int( self.cardioidBulb == "True"))
        elif self.prange == "True":  
            (escapeCount, zAbs) = mandelbrotCython.compute_mandelbrot_parallel( 
                self.widthM, self.widthM, 
                self.cxM - self.deltaM/2., 
                self.cxM + self.deltaM/2., 
                self.cyM - self.deltaM/2., 
                self.cyM + self.deltaM/2., 
                self.maxIterM, horizon, int( self.cardioidBulb == "True"))
        else:
            (escapeCount, zAbs) = mandelbrotCython.compute_mandelbrot( 
                self.widthM, self.widthM, 
                self.cxM - self.deltaM/2., 
                self.cxM + self.deltaM/2., 
                self.cyM - self.deltaM/2., 
                self.cyM + self.deltaM/2., 
                self.maxIterM, horizon, int( self.cardioidBulb == "True"))

        corr = DATA_NORM/float( self.maxIterM)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr
        self.dataMandelbrotSet3D = np.copy( escapeCount)        

        if self.debugSpeed == "True": 
            self.logWidget.append( "M: %5.3f s, Cython, not tiled, CardioidBulb %s, prange() %s" % 
                                   (( time.time()-startTime), repr( self.cardioidBulb), repr( self.prange)))

        if self.smooth == "DistEst":
            zAbs[ zAbs <= 0.] = LOG_HELPER
            temp = np.log( zAbs)
            temp[ temp <= 0.] = LOG_HELPER
            output = escapeCount
            corr = np.nan_to_num( escapeCount + 
                                  1 - np.log2( temp)*corr + log_horizon)
            self.dataMandelbrotSet = np.where(output != 0, corr, output)
        else:
            self.dataMandelbrotSet = escapeCount

        return 

    def calcMandelbrotSetCythonTiled( self):
        # +++

        if self.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        width = self.widthM
        
        mandelbrotTiled.TileWorker.NCOL = NCOL
        mandelbrotTiled.TileWorker.NROW = NROW
        mandelbrotTiled.TileWorker.width = width
        mandelbrotTiled.TileWorker.finalImage = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorker.finalZAbs = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorker.xmin = self.cxM - self.deltaM/2.
        mandelbrotTiled.TileWorker.xmax = self.cxM + self.deltaM/2.
        mandelbrotTiled.TileWorker.ymin = self.cyM - self.deltaM/2.
        mandelbrotTiled.TileWorker.ymax = self.cyM + self.deltaM/2.
        mandelbrotTiled.TileWorker.max_iter = self.maxIterM
        mandelbrotTiled.TileWorker.horizon = horizon
        mandelbrotTiled.TileWorker.cardioidBulb = self.cardioidBulb
        mandelbrotTiled.TileWorker.prange = self.prange
        mandelbrotTiled.TileWorker.highPrec = self.highPrec
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
        if self.highPrec == "True": 
            self.logWidget.append( "Starting highPrec run, slow ")
            self.app.processEvents()

        for row in range( NROW): 
            for col in range( NCOL): 
                worker = mandelbrotTiled.TileWorker( col, row)
                workers.append( worker)
                worker.start()

        while mandelbrotTiled.TileWorker.finished_count < NROW*NCOL:
            self.app.processEvents()

        escapeCount = mandelbrotTiled.TileWorker.finalImage
        zAbs = mandelbrotTiled.TileWorker.finalZAbs
        #
        # nongil cython code has no sqrt()
        #
        #zAbs = np.sqrt( zAbs) 
        
        corr = DATA_NORM/float( self.maxIterM)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr
        self.dataMandelbrotSet3D = np.copy( escapeCount)        

        if self.smooth == "DistEst":
            zAbs[ zAbs <= 0.] = LOG_HELPER
            temp = np.log( zAbs)
            temp[ temp <= 0.] = LOG_HELPER
            output = escapeCount
            log_horizon = np.log2(np.log(horizon))
            corr = np.nan_to_num( escapeCount + 
                                  1 - np.log2( temp)*corr + log_horizon)
            self.dataMandelbrotSet = np.where(output != 0, corr, output)
        else:
            self.dataMandelbrotSet = escapeCount
        
        if self.debugSpeed == "True": 
            if not self.isAnimating: 
                self.logWidget.append( "M: %5.3f s, Cython, tiled, CardioidBulb %s, prange() %s" % 
                                       (( time.time() - startTime), repr( self.cardioidBulb), repr( self.prange))) 

        
        return

    def calcMandelbrotSetDzCython( self):

        if self.tiled == "True": 
            self.calcMandelbrotSetDzCythonTiled()
            return
        
        width = self.widthM
        xmin = self.cxM - self.deltaM/2.
        xmax = self.cxM + self.deltaM/2.
        ymin = self.cyM - self.deltaM/2.
        ymax = self.cyM + self.deltaM/2.

        max_iter = self.maxIterM

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
        norm *= DATA_NORM
        
        corr = DATA_NORM/float( self.maxIterM)
        escapeCount = np.copy( norm)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr
        if self.debugSpeed == "True": 
            self.logWidget.append( "M: %5.3f s, Cython, Dz, min %g, max%g " % 
                                   (( time.time() - startTime), 
                                    escapeCount.min(), escapeCount.max()))
        self.dataMandelbrotSet3D = np.copy( escapeCount)        
        self.dataMandelbrotSet = escapeCount

        return 


    def calcMandelbrotSetDzCythonTiled( self):
        # +++

        width = self.widthM
        xmin = self.cxM - self.deltaM/2.
        xmax = self.cxM + self.deltaM/2.
        ymin = self.cyM - self.deltaM/2.
        ymax = self.cyM + self.deltaM/2.

        if self.smooth == "DistEst": 
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
        mandelbrotTiled.TileWorkerDz.max_iter = self.maxIterM
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
            self.app.processEvents()

        result = mandelbrotTiled.TileWorkerDz.finalImage

        # Normalize and plot
        norm = result / np.max( result)
        norm = norm ** 0.8  # gamma correction
        norm /= 2.
        norm *= DATA_NORM  
        
        corr = DATA_NORM/float( self.maxIterM)
        escapeCount = np.copy( norm)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr
        if self.debugSpeed == "True": 
            self.logWidget.append( "%5.3f s, Cython, Dz, tiled, min %g, max%g " % 
                                   (( time.time() - startTime), 
                                    escapeCount.min(), escapeCount.max()))
        self.dataMandelbrotSet3D = np.copy( escapeCount)        
        self.dataMandelbrotSet = escapeCount
        
        return
    
    def calcMandelbrotSetDZ( self):
        """
        derivative based distance estimation
        """
        # Image dimensions and bounds
        # Image dimensions and bounds
        width = self.widthM
        xmin = self.cxM - self.deltaM/2.
        xmax = self.cxM + self.deltaM/2.
        ymin = self.cyM - self.deltaM/2.
        ymax = self.cyM + self.deltaM/2.

        max_iter = self.maxIterM

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

        self.progressLbl.show()
        self.progressLbl.setText( "Progress: 0/%4d M" % (self.maxIterM))
        self.progressLbl.setStyleSheet("background-color:lightblue")

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
                self.progressLbl.setText( "Progress: %d/%4d M" % (i, self.maxIterM))

        # Combine smooth iteration and distance
        combined = np.zeros_like(C, dtype=np.float64)
        combined[escaped] = np.log1p(smooth_iter[escaped] + np.log1p(distance[escaped]))

        # Normalize and apply gamma correction
        norm = combined / np.max(combined)
        gamma = 0.8
        norm = norm ** gamma

        # Set interior points to black
        norm[~escaped] = 0.0

        norm *= DATA_NORM
        
        self.dataMandelbrotSet = norm
        self.showMandelbrotSet()
        self.progressLbl.setText( "Progress: %4d/%4d M" % ( i, self.maxIterM))
        self.progressLbl.setStyleSheet("background-color:%s" % self.progressLblBg)
        self.progressLbl.hide()

        return

    # CUDA kernel
            

    def calcMandelbrotSetNumba( self):
        # +++

        if self.smooth != "None": 
            self.logWidget.append( "calcNumba: smooth must be None'")
            return 
            
        # Parameters
        width = self.widthM
        xmin = self.cxM - self.deltaM/2.
        xmax = self.cxM + self.deltaM/2.
        ymin = self.cyM - self.deltaM/2.
        ymax = self.cyM + self.deltaM/2.

        max_iter = self.maxIterM

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

        corr = DATA_NORM/float( self.maxIterM)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr
        self.dataMandelbrotSet3D = np.copy( escapeCount)        
        if self.debugSpeed == "True" and not self.isAnimating: 
            self.logWidget.append( "M: %5.3f s, numba, min %g, max %g " % 
                                   (( time.time() - startTime), 
                                    escapeCount.min(), escapeCount.max()))

        self.dataMandelbrotSet = escapeCount
        return 

    def inCardioid( self, x, y):
        xm = x - 0.25
        q = xm * xm + y * y
        return q * (q + xm) < 0.25 * y * y

    def inBulb( self, x, y):
        xp = x + 1.0
        return xp * xp + y * y < 0.0625  # 1/16
        
    def calcMandelbrotSetScalar( self):
        # +++
        if self.smooth != "None":
            self.logWidget.append( "calcScalar: smooth must be None")
            return
        
        if self.shaded == "True":
            self.logWidget.append( "calcScalar: shaded must be False")
            return
            
        startTime = time.time()
        self.progressLbl.show()
        self.progressLbl.setText( "Progress: 0/%4d M" % (self.widthM))
        self.progressLbl.setStyleSheet("background-color:lightblue")
        self.app.processEvents()

        width = self.widthM
        
        # Create coordinate grid
        x = np.linspace( self.cxM - self.deltaM/2.,
                         self.cxM + self.deltaM/2.,
                         width)
        y = np.linspace( self.cyM - self.deltaM/2.,
                         self.cyM + self.deltaM/2., 
                         width)
        self.dataMandelbrotSet = np.zeros(( width, width), dtype=np.int32)

        self.scalarRandom = "False"
        coords = [(i, j) for j in range(width) for i in range(width)]
        if self.scalarRandom == "True":
            np.random.shuffle(coords)

        # Mandelbrot iteration (scalar operations on a 2D field)
        stop = False

        loopCount = 0
        for i, j in coords: 
            loopCount += 1
            if loopCount % (20*width) == 0:
                self.progressLbl.setText( "Progress: %d/%4d " % (j, width))
                self.app.processEvents()
                if (loopCount % (20*width) == 0):
                    self.showMandelbrotSet()
                    self.app.processEvents()
            cx = x[i]
            cy = y[j]
            if self.cardioidBulb == "True":
                if self.inCardioid( cx, cy) or self.inBulb( cx, cy):
                    self.dataMandelbrotSet[ j, i] = self.maxIterM
                    continue
            zx = 0.0
            zy = 0.0
            count = 0

            while zx*zx + zy*zy <= 4.0 and count < self.maxIterM:
                zx_new = zx*zx - zy*zy + cx
                zy = 2.0*zx*zy + cy
                zx = zx_new
                count += 1
                    
            if self.stopRequested:
                stop = True
                break

            self.dataMandelbrotSet[j, i] = count

            if stop:
                self.logWidget.append( "calcScalar: stop detected, break") 
                break


        corr = DATA_NORM/float( self.maxIterM)
        self.dataMandelbrotSet = self.dataMandelbrotSet.astype(np.float64)
        self.dataMandelbrotSet *= corr
                
        if self.debugSpeed == "True": 
            self.logWidget.append( "M: %5.3f s, Scalar, CardioidBulb %s" % 
                                   (( time.time() - startTime), repr( self.cardioidBulb))) 
        self.progressLbl.setText( "Progress: %4d/%4d M" % ( i, width))
        self.progressLbl.setStyleSheet("background-color:%s" % self.progressLblBg)
        self.progressLbl.hide()
        self.showMandelbrotSet()
        
        return 

    def showMandelbrotSet( self):
        """
        displays self.dataMandelbrotSet

        About clipping, Copilot: 
        When you're using matplotlib.colors.Normalize(vmin=100, vmax=700, clip=False) 
        to normalize your Mandelbrot set data (ranging from 0 to 1023), here's how the 
        behavior differs depending on the clip parameter:

        With clip=True
        - Normalization range: Values are clipped to stay within [0,1].
        - Effect:
          - Values < 100 are mapped to 0.
          - Values > 700 are mapped to 1.
          - This causes saturation at both ends: many pixels may appear 
            fully dark or fully bright depending on the colormap.
          - The extremes (0 and 1) are overrepresented, which can distort the visual contrast.

        With clip=False
        - Normalization range: Values are not clipped, so they can fall outside [0,1].
        - Effect:
          - Values < 100 are mapped to negative values (e.g., 0 → -0.1).
          - Values > 700 are mapped to values > 1 (e.g., 1023 → ~1.5).
          - These out-of-range values are passed to the colormap, which may:
            - Wrap around (some colormaps like hsv or twilight are cyclic).
            - Clamp to edge colors (most colormaps like viridis, plasma,
              gray will map <0 to the lowest color and >1 to the highest).
          - This gives you more accurate contrast in the valid range,
            but outliers may distort the color mapping if not handled carefully.
        
        Display Implications
                        clip=True                    clip=False
        values < vmin   Mapped to 0, lowest value    Mapped below 0 but still shown as lowest value
        values > vmax   Mapped to 1, highest value   Mapped above 1, but still shown as highest value
        intermediate    Mapped linearly between      Same linear mapping
          values          0 and 1
        out-of-range    Clipped to [0,1]             Preserved as < 0, > 1
          values
        colormap        Saturation at ends           May cause color distortion if 
          behavior                                    color map wraps or interpolate
                                                      outside [0,1]
        use case        Safer for bounded vis.       Useful for diag or highlighting outliers

        """   
        if self.figM is None:
            return
        
        plt.figure( self.figM.number)

        M = np.copy( self.dataMandelbrotSet)

        if self.modulo != -1: 
            M = M % self.modulo

        extentArr = [self.cxM - self.deltaM/2.,
                     self.cxM + self.deltaM/2.,
                     self.cyM - self.deltaM/2.,
                     self.cyM + self.deltaM/2.]            

        normFunc = self.getNormFunc( M)
        if self.shaded == 'True': 
            light = colors.LightSource( azdeg=self.azDeg, altdeg=self.altDeg)
            M = light.shade( M, 
                             cmap=self.colorMap,
                             norm = normFunc,
                             vert_exag=self.vert_exag,
                             blend_mode=self.blendMode)
            normTemp = None
            cmapTemp = None
        else:
            normTemp = normFunc
            cmapTemp = self.colorMap
            
        if self.imM is None:
            self.axM.set_xlim([ self.cxM - self.deltaM/2., self.cxM + self.deltaM/2.])
            self.axM.set_ylim([ self.cyM - self.deltaM/2., self.cyM + self.deltaM/2.])

            self.imM = self.axM.imshow( M, origin = 'lower',
                                        cmap = cmapTemp,
                                        norm = normTemp,
                                        extent = extentArr,
                                        aspect='auto', # removes white borders left and right 
                                        interpolation = self.interpolation)
        else:
            if self.shaded != 'True':
                self.imM.set_norm( normFunc)
            self.imM.set_data(M)
                
            self.imM.set_extent( extentArr)
            self.imM.set_interpolation(self.interpolation)
            #
            # the shader has already dealt with the color map
            #
            if self.shaded != 'True':
                self.imM.set_cmap(self.colorMap)

            self.createDebugColoringOutput( M)

            self.axM.set_xlim([ self.cxM - self.deltaM/2., self.cxM + self.deltaM/2.])
            self.axM.set_ylim([ self.cyM - self.deltaM/2., self.cyM + self.deltaM/2.])

            #self.imM.autoscale()
            self.imM.changed()   # force redraw

        self.textTitleM.set( text = r'$z_{n+1} = z_n^%d + c, z_0 = 0$' % self.power)

        self.deltaLbl.setText( "Delta: %.2e" % (self.deltaM))

        self.showMandelbrotSet3D()
        #
        # sonst funktrioniert animation mit numba nicht
        #
        self.app.processEvents()
        
        return

    def showMandelbrotSet3D( self):
        """
        displays self.dataMandelbrotSet
        """

        if self.flagM3D == "False":
            return

        plt.figure( self.figM3D.number) 

        M = self.dataMandelbrotSet3D
        light = colors.LightSource(azdeg=self.azDeg, altdeg=self.altDeg)
        #
        # shading increases the shape of M (900, 900) -> (900, 900, 4)
        # surface does not like it
        #
        if False and self.shaded == 'True': 
            if self.modulo != -1: 
                temp = self.dataMandelbrotSet3D % self.modulo
            else: 
                temp = self.dataMandelbrotSet3D

            normFunc = self.getNormFunc( temp)
            M = light.shade( temp, 
                             cmap=self.colorMap, 
                             vert_exag=self.vert_exag,
                             norm=normFun,
                             blend_mode=self.blendMode)
        else:
            if self.modulo != -1: 
                M = M % self.modulo

        x = np.linspace( -2.5, 15, self.widthM)
        y = np.linspace( -2, 2, self.widthM)
        X, Y = np.meshgrid(x, y)
        if self.surface is not None:
            self.surface.remove()
            
        normFunc = self.getNormFunc( M)
        self.surface =  self.ax3D.plot_surface(X, Y, M, 
                                               rcount = int( self.widthM/4),
                                               norm=normFunc,
                                               cmap=self.colorMap, edgecolor='none')
        self.surface.autoscale()

        #plt.show()
        self.app.processEvents()
        return
    
    def calcJuliaSet( self, display = True):
        # 
        if self.juliaMode == 'Off':
            return 

        if self.cython == "True":
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
        escapeCount *= DATA_NORM/float( self.maxIterJ) 

        if self.smooth == "DistEst": 
            temp = np.log( abs(z))
            temp[ temp <= 0.] = LOG_HELPER
            escapeCount = np.nan_to_num( escapeCount + 1 - np.log2( temp) + log_horizon)
            
        self.dataJuliaSet = escapeCount
        
        self.showJuliaSet()

        if self.debugSpeed == "True": 
            if not self.isAnimating: 
                self.logWidget.append( "J: %5.3f s, Python, NumpyOnly %s  " % 
                                       ((time.time() - startTime), repr( self.numpyOnly)))
        self.progressLbl.setText( "Progress: %4d/%4d J" % ( it, self.maxIterJ))
        self.progressLbl.setStyleSheet("background-color:%s" % self.progressLblBg)
        self.progressLbl.hide()
        return argout
    
    def calcJuliaSetCython( self, display = True):

        if self.tiled == "True":
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
        output *= DATA_NORM/float( self.maxIterJ) 

        if self.smooth == "DistEst": 
            temp = np.log( zAbs)
            temp[ temp <= 0.] = LOG_HELPER
            output = np.nan_to_num( output + 1 - np.log2( temp) + log_horizon) 

        self.dataJuliaSet = output
        self.showJuliaSet()

        return 

    def calcJuliaSetCythonTiled( self):
        import threading

        width = self.widthM
        xmin = self.cxM - self.deltaM/2.
        xmax = self.cxM + self.deltaM/2.
        ymin = self.cyM - self.deltaM/2.
        ymax = self.cyM + self.deltaM/2.

        if self.smooth == "DistEst": 
            horizon = 2**40
        else: 
            horizon = 4
        log_horizon = np.log2(np.log(horizon))

        mandelbrotTiled.TileWorkerJulia.NCOL = NCOL
        mandelbrotTiled.TileWorkerJulia.NROW = NROW
        mandelbrotTiled.TileWorkerJulia.width = width
        mandelbrotTiled.TileWorkerJulia.cxM = self.cxM
        mandelbrotTiled.TileWorkerJulia.cyM = self.cyM
        mandelbrotTiled.TileWorkerJulia.cxJ = self.cxJ
        mandelbrotTiled.TileWorkerJulia.cyJ = self.cyJ
        mandelbrotTiled.TileWorkerJulia.deltaJ = self.deltaJ
        mandelbrotTiled.TileWorkerJulia.finalImage = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorkerJulia.finalZAbs = np.zeros(( width, width), dtype=np.float64)
        mandelbrotTiled.TileWorkerJulia.xmin = xmin
        mandelbrotTiled.TileWorkerJulia.xmax = xmax
        mandelbrotTiled.TileWorkerJulia.ymin = ymin
        mandelbrotTiled.TileWorkerJulia.ymax = ymax
        mandelbrotTiled.TileWorkerJulia.maxIterJ = self.maxIterJ
        mandelbrotTiled.TileWorkerJulia.horizon = horizon
        mandelbrotTiled.TileWorkerJulia.finished_count = 0
        mandelbrotTiled.TileWorkerJulia.total_tiles = NROW*NCOL
        mandelbrotTiled.TileWorkerJulia.lock = threading.Lock()
        
        startTime = time.time()
        workers = []
        #self.logWidget.append( "Starting Julia workers")

        for row in range( NROW): 
            for col in range( NCOL): 
                worker = mandelbrotTiled.TileWorkerJulia( col, row)
                workers.append( worker)
                worker.start()

        while mandelbrotTiled.TileWorkerJulia.finished_count < NROW*NCOL:
            self.app.processEvents()

        escapeCount = mandelbrotTiled.TileWorkerJulia.finalImage
        zAbs = mandelbrotTiled.TileWorkerJulia.finalZAbs
        #
        # nongil cython code has no sqrt()
        #
        #zAbs = np.sqrt( zAbs) 
        
        corr = DATA_NORM/float( self.maxIterM)
        escapeCount = escapeCount.astype(np.float64)
        escapeCount *= corr

        if self.smooth == "DistEst":
            zAbs[ zAbs <= 0.] = LOG_HELPER
            temp = np.log( zAbs)
            temp[ temp <= 0.] = LOG_HELPER
            output = escapeCount
            corr = np.nan_to_num( escapeCount + 
                                  1 - np.log2( temp)*corr + log_horizon)
            self.dataJuliaSet = np.where(output != 0, corr, output)
        else:
            self.dataJuliaSet = escapeCount
        
        if self.debugSpeed == "True": 
            if not self.isAnimating: 
                self.logWidget.append( "J: %5.3f s, Cython, tiled" % 
                                       (( time.time() - startTime)))
        
        return
    
    def showJuliaSet( self):
        """
        displayes self.dataJuliaSet
        """
        if self.figJ is None:
            return

        if self.dataJuliaSet is None:
            #print( "showJuliaSet, early return") 
            return 

        if self.juliaMode == 'Off':
            return 

        plt.figure( self.figJ.number) 

        M = np.copy( self.dataJuliaSet)
        if self.modulo != -1: 
            M = M % self.modulo

        extentArr = [ self.cxJ - self.deltaJ/2., 
                      self.cxJ + self.deltaJ/2,
                      self.cyJ - self.deltaJ/2,
                      self.cyJ + self.deltaJ/2]

        normFunc = self.getNormFunc( M)
        if normFunc is None:
            print( "return 4")
            return

        if self.shaded == 'True': 
            light = colors.LightSource(azdeg=self.azDeg, altdeg=self.altDeg)
            M = light.shade( M, 
                             cmap=self.colorMap, 
                             vert_exag=self.vert_exag,
                             norm=normFunc, 
                             blend_mode=self.blendMode)
            normTemp = None
            cmapTemp = None
        else:
            normTemp = normFunc
            cmapTemp = self.colorMap

        if self.imJ is None: 
            self.imJ =\
                plt.imshow( M,
                            cmap = cmapTemp,
                            norm = normTemp, 
                            extent = extentArr,
                            aspect='auto', # removes white borders left and right 
                            origin = 'lower',
                            interpolation = self.interpolation)
        else: 
            if self.shaded != 'True':
                self.imJ.set_norm( normFunc)
            self.imJ.set_data(M)
                
            self.imJ.set_extent( extentArr)
            self.imJ.set_interpolation(self.interpolation)
            #
            # the shader has already dealt with the color map
            #
            if self.shaded != 'True':
                self.imJ.set_cmap(self.colorMap)

            self.createDebugColoringOutput( M)

            self.axJ.set_xlim([ self.cxJ - self.deltaJ/2., self.cxJ + self.deltaJ/2.])
            self.axJ.set_ylim([ self.cyJ - self.deltaJ/2., self.cyJ + self.deltaJ/2.])

            self.imJ.changed()   # force redraw
            #self.imJ.autoscale() 

        self.textTitleJ.set( text = r'$z_{n+1} = z_n^%d + c, z_0 = c$' % self.power)
        #self.imJ.autoscale()
        self.app.processEvents()
        return 

    def cb_helpOverview(self):
        QMessageBox.about(self, self.tr("Help Basics"), self.tr(
"<h3> The Mandelbrot Set</h3>"
" This application is about exploring the Mandelbrot set (M) and the \
area that is adjacent to it. Descriptions about the Mandelbrot set \
can be found at many places. Here we give only a very brief overview \
allowing us to define the variables used in the graphical user interface. \
            <br><br>\
M is in the complex plane. It is generated by iterating \
z(n+1)=z(n)**2 + c, z(0) = 0. With z and c being complex numbers. n runs from 0 to \
iterMax. The question is for which \
numbers c the sequence z(n) stays within a radius of 2 and for which \
numbers z(n) tends towards infinity. The stable numbers c are members of M. They \
are usually colored black. The color of the non-stable numbers \
depends on how fast z(n) crosses the r=2 boundary. \
The n at which the z(n) actually crosses the boundary is called \
escape count. The image displayed in the \
figure 'Mandelbrot Set' shows the escape counts. \
            <br><br>\
The Julia set appearing in the second figure is also generated by the \
above mentioned formula, except that z(0) is set to c.\
"  
"<ul>"
"<li> MB-left - Zoom into the set</li>"
"<li> MB-middle - Move center, no zoom</li>"
"<li> MB-right - Define start and end points for scans.</li>"
"</ul>" 
                ))

    def cb_helpColoring( self):
        dialog = QDialog()
        dialog.setWindowTitle("Help")
        dialog.setFixedSize( 600, 700)  # Set desired width and height
        layout = QVBoxLayout()
        
        label = QLabel("<h3> Coloring</h3>"
"<ul>"
"<li> CMap - The color map used for the display of the data. Can be selected from 'Colors' and 'AllColors'</li>"
"<li> Reversed - Reverse the color map</li>"
"<li> Cyclic CMAP - Make other color maps cyclic, like prism or flag. CMAPs that give good cyclic CMAPS can be found in Colors below the separator.</li>"
"<li> C-Index - Rotate the color map by a slider</li>"
"<li> Rotate CMAP - Continuously rotate the color map by n steps, use WaitTime to slow down the loop.</li>"
"<li> Animation - Approach a target point in a spiral. No. of turns may be selected. IF -1, we have a linear approach. The A-Factor specifies the approach speed.</li>"
"<li> MaxIterM/J - The maximum no. of iterations used to test whether a complex number c is a member of M. After zooming into the images several times, MaxIterM usually needs to be increased</li>"
"<li> Width - Number of pixels in either direction. If set to 256, a test image is created.</li>"
"<li> NormMethod - Data are normalised from [0,1023] to [0,1]. Different functions can be selected.</li>"
"<ul>"
"<li> PowerNorm - Linearly map the data, [vmin, vmax], to [0, 1], then apply a power-law normalization. NormPar is the exponent.</li>"
"<li> LogNorm - Map the data, [vmin, vmax], to [0, 1] using a log scale.</li>"
"<li> AsinhNorm - Map the data, [vmin, vmax], to [0, 1] using a inverse hyperbolic sine scale. NormPar is the linear width.</li>"
"<li> LinNorm - Linearly map the data, [vmin, vmax], to [0, 1].</li>"
"<li> HistNorm - vmin, vmax = np.percentile(M, [normPar, 100. - normPar]) </li>"
"<li> StretchNorm - Applying some streching </li>"
"</ul>"
"<li> NormPar - Parameter for the normalisation functions.</li>"
"<li> Clip - If checked, colors below vmin/vmax are clipped to the lowest/highest color.</li>"
"<li> Modulo - Modulo is applied to the data before they are normalised.</li>"
"<li> Bands - Every second color is set to black.</li>"
"<li> vmin, vmax - defines the data range to be mapped to [0, 1], clipping (Flags) can be enabled or disabled.</li>"
"</ul>")

        label.setWordWrap(True)
        layout.addWidget(label)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)
        dialog.exec_()
    
    def cb_helpSmooth(self):
        QMessageBox.about(self, self.tr("Help Smooth"), self.tr(
            "<h3> Smooth</h3>"
            "<ul>"
            "<li> None - no smoothing</li>"
            "<li> DistEst - the data is smoothed depending on how far the z(n) escapes</li>"
            "<li> DZ - the data, the escape count field, is smoothed depending on the derivative dZ</li>"
            "<li> Interpolation - different algorithms can be used to interpolate the data</li>"
            "</ul>"
                ))
        
    
    def cb_helpShader(self):
        QMessageBox.about(self, self.tr("Help Shader"), self.tr(
            "<h3> The Shader</h3>"
            "<ul>"
            "<li> Vertical exageration, blend mode: input for the shader</li>"
            "<li> azDegree, altDegree: angles defining the light direction</li>"
            "</ul>"
                ))
        
    def cb_helpJuliaScans(self):
        QMessageBox.about(self, self.tr("Help Julia Scans"), self.tr(
            "<h3> Julia Scans</h3>"
            "During Julia scans a point is moved through the complex plane and the corresponding Julia set is displayed. The waypoints of the scan are selected by MB-right. Circular scans are defined by 3 points."
            "<ul>"
            "<li> ScanPoints - The number of scan points along all waypoints.</li>"
            "<li> ScanCircle - The scan is executed in a circular path.</li>"
            "</ul>"
                ))
    def cb_helpMisc(self):
        QMessageBox.about(self, self.tr("Help Smooth"), self.tr(
            "<h3> Misc</h3>"
            "<ul>"
            "<li> Mandelbrot mode: selector for the figure size.</li>"
            "<li> M3D: open 3D plot figure</li>"
            "<li> Julia Mode: selector for the figure size</li>"
            "<li> Zoom - zoom factor</li>"
            "<li> ZoomOut - undo last zoom</li>"
            "<li> ZoomHome - Reset center coordinated and delta</li>"
            "<li> LastRead - Re-read the last file</li>"
            "<li> ClearRM - Clear reset marker</li>"
            "<li> IterPath: Display the iterated sequence of z(n)</li>"
            "<li> Delta: Width of the current image </li>"
            "<li> ShowData: If enabled, shows, x, y, data </li>"
            "</ul>"
                ))
        
        
    def cb_helpResetMarker(self):
        QMessageBox.about(self, self.tr("Help ResetMarker"), self.tr(
            "<h3> The ResetMarker </h3>"
            "<ul>"
            "<li> The ResetMarker is a '+' sign printed at a certain position of the image displayed in the Mandelbrot Set figure. </li>"
            "<li> The position can be the center of the region of interest which was visible when 'Reset' was clicked. Hence the name.</li>"
            "<li> The position can also by selected an action widget below 'Center'. These are the centers of the .png files read. </li>"
            "<li> The reset marker remains visible until 'ClearRM' is clicked. </li>"
            "</ul>" 
                ))
        
    def cb_helpPlaces(self):
        QMessageBox.about(self, self.tr("Help Places"), self.tr(
            "<h3> The Places </h3>"
            "<ul>"
            "<li> Places - Launch the Places widget to load parameters of interesting places that have been stored before. </li>"
            "<li> Store - Store an interesting place, i.e. store a .png in the ./places directory. The .png files contains metadata allowing mandelbrot.py to continue operation at the place. The file names are MB_'hashCode'.png. Files of this kind can me deleted by MB-Right</li>"
            "<li> StoreNamed - Store an interesting place in a named file. Very much like 'Store' except that the user is prompted for the central part of the file name: MBN_'userInput'.png. MBN_ files cannot be deleted by mandelbrot.py </li>"
            "</ul>" 
                ))
        
    def cb_helpFlags(self):
        QMessageBox.about(self, self.tr("Help Place"), self.tr(
            "<h3> Flags </h3>"
            "<ul>"
            "<li> Cython/C - The calculation is done in Cython/C </li>"
            "<li> Cython/C-tiled - The calculation is done multi-threaded with each thread taking care of a tile, a part of the escape count field. </li>"
            "<li> Animate uses constant width - animated zooms are accelerated by reducing the width by a factor of 2. At the endpoint the width is resetted. If this flag is checked, the width is not changed. </li>"
            "<li> DebugSpiral - If checked, debug information for spiral animated zooms is displayed. </li>"
            "<li> DebugColoring - If checked, debug information for coloring is displayed. A histogramm of the escape count field, the normalization function, the normalized data and a color bar. </li>"
            "<li> DebugSpeed - If checked, the elapsed time for the computations is written to the log widget </li>"

            "</ul>" 
                ))

#

    def getNormFunc( self, M):

        if self.vmax <= self.vmin:
            temp = QMessageBox()
            ret = temp.question(self,'',
                                "getNormFunc: vmax %g <= vmin %g " % (self.vmin, self.vmax), 
                                temp.Ok )
            return None
        #
        # [vmin, vmax] -> [0, 255]
        #
        if self.norm == 'LinNorm':
            normFunc = utils.LinNorm( vmin=self.vmin, vmax=self.vmax, 
                                      clip = ( self.clip == "True"))
        elif self.norm == 'TwoSlopeNorm':
            normFunc = colors.TwoSlopeNorm( self.normPar, vmin=self.vmin, vmax=self.vmax)

        elif self.norm == 'AsinhNorm':
            normFunc = colors.AsinhNorm( linear_width = self.normPar, 
                                         vmin=self.vmin, vmax=self.vmax, 
                                      clip = ( self.clip == "True"))

        elif self.norm == "PowerNorm":
            normFunc = colors.PowerNorm( gamma = self.normPar,
                                         vmin=self.vmin, vmax=self.vmax, 
                                         clip = ( self.clip == "True"))
        elif self.norm == "LogNorm":
            temp = self.vmin
            if temp <= 0.:
                temp = 0.1
            normFunc = colors.LogNorm( vmin=temp, vmax=self.vmax,
                                       clip = ( self.clip == "True"))
        elif self.norm == "HistNorm":
            vmin, vmax = np.percentile(M, [self.normPar, 100. - self.normPar])
            normFunc = utils.LinNorm( vmin=vmin, vmax=vmax,
                                       clip = ( self.clip == "True"))
        elif self.norm == "StretchNorm":
            self.logWidget.append( "StretchNorm: min, %g, max %g" %
                                   ( M.min(), M.max()))
            temp = (M - np.mean(M)) * self.normPar
            temp = temp - temp.min()
            self.logWidget.append( "StretchNorm: vmin %g, vmax %g, min, %g, max %g" %
                                   ( self.vmin, self.vmax, temp.min(), temp.max()))
            M = np.clip( temp, self.vmin, self.vmax, out = M)
            normFunc = utils.LinNorm( vmin=self.vmin, vmax=self.vmax,
                                       clip = ( self.clip == "True"))
        else:
            print( "getNormFunc: Failed to identify norm, %s, exit" % self.norm)
            sys.exit( 255)
        return normFunc
    
    def createDebugColoringOutput( self, M):

        if self.debugColoring == "False":
            if self.figDebugColoring is not None:
                plt.close( self.figDebugColoring)
                self.figDebugColoring = None
                self.cbar = None
            return 

        if self.figDebugColoring is None:
            self.figDebugColoring, self.axDebugColoring = \
                plt.subplots(4, 1, figsize= self.figSizeC)
            #for i, ax in enumerate( self.axDebugColoring):
            #    print(f"Axes {i}:", ax.get_position().bounds)
            self.figDebugColoring.subplots_adjust(hspace=0.5) 
            self.figDebugColoring.canvas.mpl_connect("close_event",
                                                     self.cb_closeFigDebugColoring)
            self.figDebugColoring.canvas.manager.set_window_title( 'Debug coloring')
            if self.modeOperation.lower() == 'demo': 
                self.figDebugColoring.canvas.manager.window.setGeometry( 5332, 535, 433, 668)

        plt.figure( self.figDebugColoring.number)
        
        self.axDebugColoring[0].clear()
        flat_data = M.ravel()
        self.axDebugColoring[0].hist( flat_data, bins = 256, log = True) 
        self.axDebugColoring[0].set_title( "Escape Counts")

        normFunc = self.getNormFunc( M)
        x = np.linspace(0, DATA_NORM, DATA_NORM)
        y = normFunc( x)
        self.axDebugColoring[1].clear()
        self.axDebugColoring[1].plot( x, y)
        self.axDebugColoring[1].set_title( "%s, normPar %g, vmin %g, vmax %g" % 
                                          (self.norm, self.normPar, self.vmin, self.vmax))
        
        self.axDebugColoring[2].clear()
        M1 = normFunc( M)
        flat_data = M1.ravel()
        self.axDebugColoring[2].hist( flat_data, bins = 256, log = True) 
        self.axDebugColoring[2].set_title( "Normalized Data (no shader)")
        
        if self.cbar is not None:
            self.cbar.remove() # this also destroys the axes, has to be re-created
            self.axDebugColoring[3] = self.figDebugColoring.add_axes([0.125, 0.11, 0.775, 0.167])
            self.cbar = None

        self.cbar = self.figDebugColoring.colorbar( self.imM,
                                                    orientation = 'horizontal', 
                                                    cax = self.axDebugColoring[3]) 
        self.cbar.ax.set_title("Colorbar")
            
        plt.figure( self.figM.number)

        return

if numbaOK: 

    @cuda.jit
    def in_cardioid( x, y):
        xm = x - 0.25
        q = xm * xm + y * y
        return q * (q + xm) < 0.25 * y * y

    @cuda.jit
    def in_bulb(x, y):
        xp = x + 1.0
        return xp * xp + y * y < 0.0625  # 1/16

    # decorator: compile python function into a GPU kernel
    @cuda.jit
    def mandelbrot_kernel( xmin, xmax, ymin, ymax, image, max_iter):
        height, width = image.shape
        x, y = cuda.grid(2)
        """
        It expands to:
        x=threadIdx.x + blockIdx.x * blockDim.x
        y=threadIdx.y + blockIdx.y * blockDim.y
        So each thread gets a unique (x, y) pair.
        """
        if x < width and y < height:
            real = xmin + x * (xmax - xmin) / width
            imag = ymin + y * (ymax - ymin) / height
            #
            if in_cardioid( real, imag) or in_bulb( real, imag):
                image[ y, x] = max_iter
            else: 
                c = complex(real, imag)
                z = 0j
                count = 0
                while abs(z) <= 2 and count < max_iter:
                    z = z*z + c
                    count += 1
                image[y, x] = count
        return

def parseCLI():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="Arractors",
        epilog='''\
  attractors.py [--fs size]

    ''')

    parser.add_argument( '--fs',
                         dest="fontSize", action="store", default=12, help='font size, def.: 12')
    parser.add_argument( '--mode',
                         dest="mode", action="store", default="None", help='enable e.g. demo mode')
    args = parser.parse_args()

    return args
        
def main():

    args = parseCLI()
        
    app = QApplication(sys.argv)
    #
    # the fontSize tells the rest of the program what the user wants.
    #
    app.setStyleSheet("*{font-size: %dpt;}" % int( args.fontSize))

    w = mandelBrotSetWidget( app, int( args.fontSize), args.mode)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
