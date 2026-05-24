#!/usr/bin/env python3

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys, time, math, os, json
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5.QtCore import QEvent
import FractalEngine
from PIL import Image
from PIL import PngImagePlugin
import utils
import PGViewer
import Shells
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
import mandelbrotPlaces
import dynamicOperators
import colorWidget

SPIRAL_VALUES = [ 1, -1, 0, 1, 2, 3, 4]
ANIMATIONFACTOR_VALUES = [ 0.98, 0.99, 0.98, 0.97, 0.96, 0.95]
MAX_ITER_VALUES = [ 512, 16, 32, 64, 128, 256, 384, 512, 768,
                    1024, 1536, 2048, 4096, 8192, 16384, 32768]

SCAN_POINT_VALUES = [ 200, 20, 100, 200, 500, 1000, 2000, 5000]
JULIA_MODE_VALUES = [ 'Off', 'Small', 'Medium', 'Big', 'Large'] 
ZOOM_VALUES = [ 4, 1., 1.2, 1.5, 2, 3, 4, 8, 16,]

METADATA_MEMBERS = [
    'cxM', 'cyM', 'deltaM', 'widthM', 'widthJ', 'execDynOp', 
    'maxIterM', 'maxIterJ', 'scanCircle', 
    ]
#
# beware of typos, check whether a member is in the list of known members
#
MBS_Attrs = METADATA_MEMBERS + \
    [ 'app', 'figSizeBig', 'figSizeMedium', 'figSizeSmall', 'figSizeLarge',
      'name', 'screen', 'screenWidthIn', 'screenHeightIn', 
      'geomM', 'geometryAction', 'version', 'DynOpPb', 
      'figSizeM', 'figSizeJ', 'dpi', 'modeOperation', 'animationFactorCombo', 
      'maxIterMCombo', 'maxIterJCombo', 'animationFactor', 
      'busy', 'isRotating', 'updateGUIAction', 'redisplayAction', 
      'dataMandelbrotSet', 'dataJuliaSet', 'stopRequested', 'lastFileRead', 
      'zoomCombo', 'maxIterMCombo', 'maxIterJCombo', 'scanCircle', 'lastImage', 
      'scanPoints', 'zoom', 'cxM', 'cyM', 'deltaM', 'cxJ', 'cyJ', 'deltaJ',
      'menuBar', 'fileMenu', 'vLayout', 'colorContainer', 
      'pngMAction','pngJAction', 'clearAction','exitAction', 
      'menuBarRight', 'helpMenu', 'gridLayout', 'spiral', 
      'scanCircleCb', 'logWidget', 'widthMCombo', 'widthJCombo', 
      'figSizeC', 'viewerSpiral', 'colorWidget', 
      'scanPointsCombo', 'normParCombo', 'colorLayout', 'icon', 
      'progressLbl', 'progressLblBg', 'execDynOpCb', 
      'statusBar', 'scanMarker', 'placesWidget', 'cxOld', 'cyOld', 'deltaOld', 
      'animateAtConstantWidth', 'animateAtConstantWidthAction',  
      'animatePb', 'debugSpiral', 'debugColoring',  
      'overviewAction', 'cython', 'figSize3D', 
      'fontSize', 'numba', 'numbaAction', 'colorsMenu', 'allColorsMenu', 
      'deltaLbl', 'mandelbrotMode', 'mandelbrotModeCombo', 
      'juliaMode', 'juliaModeCombo', 'isAnimating', 'spiralCombo', 
      'scanPath', 'scanTexts', 'repeatAction', 'viewerDebugColoring', 
      'iterPath', 'flagIterPath', 'iterPathCb', 'tiled',
      'flagsMenu', 'cythonAction', 'tiledAction', 'debugSpiralAction', 
      'debugColoringAction', 'debugSpeed', 'debugSpeedAction', 'numpyAction', 'numpy', 
      'centerHsh', 'centerMenu', 'scalarAction', 'scalar', 
      'lastReadLbl', 'rmColor', 'rmColorAction', 
      'isFilteredM', 'operatorWidget',
      'backgroundColor', 'engine', 'viewerMain', 'viewerJS', 'winDebugColoring',
      'operatorWidget', 'useMPL', 'colorPars', 'wCentral', 'switchPb', 
     ]


class MBSMainWindow( QMainWindow):
    setColor = pyqtSignal()
    setDebugColoring = pyqtSignal( bool)
    
    def __init__(self, app, fontSize = None, modeOperation = None, useMPL = True, parent=None):
        super().__init__()

        self.name = "MBSMainWindow"
        self.app = app
        self.useMPL = useMPL
        self.fontSize = fontSize
        self.modeOperation = modeOperation # e.g. 'demo'
        self.findFigSizes()

        #
        # colorPars is a singleton passed to all modules that refer to color
        #
        self.colorPars = utils.ColorPars( parent = self)

        self.engine = FractalEngine.FractalEngine( self, colorPars = self.colorPars)

        self.viewerMain = Shells.ViewerShell( parent = self,
                                              app = self.app, 
                                              title = "MBS", 
                                              colorPars = self.colorPars)
        self.viewerJS = Shells.ViewerShell( parent = self,
                                            app = self.app, 
                                            title = "Julia Set", 
                                            colorPars = self.colorPars)
        self.viewerDebugColoring = Shells.ViewerShell( parent = self,
                                                       app = self.app,
                                                       title = "Coloring",
                                                       colorPars = self.colorPars)
        self.setWindowTitle("Mandelbrot Set")

        self.viewerSpiral = PGViewer.SpiralDebugView( self)
        self.viewerSpiral.setWindowTitle( "Spiral Debug")
        self.viewerSpiral.resize( 400, 400)
        self.viewerSpiral.setWindowFlags(Qt.Window)

        #self.viewerMain.resize( self.figSizeM[0], self.figSizeM[1] )
        self.viewerMain.setGeometry( 50, 50, self.figSizeM[0], self.figSizeM[1])
        self.viewerMain.setWindowFlags(Qt.Window)
        self.viewerMain.show()

        self.viewerJS.resize( self.figSizeJ[0], self.figSizeJ[1] )
        self.viewerJS.setWindowFlags(Qt.Window)

        self.colorPars.setColor.connect( self.viewerMain.setColor)
        self.colorPars.setColor.connect( self.viewerJS.setColor)
        
        self.colorWidget = colorWidget.colorWidget( app = self.app, parent = self,
                                                    colorPars = self.colorPars)

        self.colorWidget.setColor.connect( self.viewerMain.setColor)
        self.colorWidget.setColor.connect( self.viewerJS.setColor)
        self.colorWidget.calcMBS.connect( self.engine.calcMandelbrotSet)
        self.colorWidget.redisplay.connect( self.redisplay)

        self.engine.MBSUpdated.connect( self.displayMBS)
        self.engine.JuliaSetUpdated.connect(self.viewerJS.updateImage)

        self.setDebugColoring.connect( self.viewerMain.setDebugColoring)
        
        self.viewerMain.clickedMB1.connect(self.cb_onViewerClickedMB1)
        self.viewerMain.clickedShiftMB1.connect(self.cb_onViewerClickedShiftMB1)
        self.viewerMain.clickedMB2.connect(self.cb_onViewerClickedMB2)
        self.viewerMain.clickedMB3.connect(self.cb_onViewerClickedMB3)
        self.viewerMain.deltaLbl.connect(self.cb_deltaLbl)
        self.viewerMain.coloringOutput.connect( self.viewerDebugColoring.mpl.createDebugColoringOutput)
        
        self.initMembers() 
        self.setDefaults()

        self.prepareMenuBar()
        self.prepareCentralWidget()
        self.prepareStatusBar()

        self.updateGUI()

        self.engine.calcMandelbrotSet()
        
        #self.viewerMain.setWorldRect() # for PG: MB1, MB2
        
        self.setColor.connect( self.viewerMain.setColor)
        
        self.setColor.emit()

        self.placesWidget = mandelbrotPlaces.places( self.app, parent = self, prefix = "MB")

        self.operatorWidget = dynamicOperators.operatorWidget(
            self.app, parent = self,
            colorPars = self.colorPars, 
            vInit = "MBS", useMPL = self.useMPL)
        
        if self.modeOperation.lower() == 'demo': 
            screens = self.app.screens()
            if len( screens) < 2:
                print( "\n__init__(): demo mode only at DownPc, exiting\n") 
                sys.exit( 255) 

            #self.setFixedSize( 562, 664)
            self.setGeometry( 4930, 566, 800, 670)
            self.viewerMain.setGeometry( 3845, 530,
                                         int( self.figSizeM[0]*0.6), int( self.figSizeM[1]*0.6))

            self.operatorWidget.setGeometry(5149, 923, 580, 630)
            self.app.processEvents()
        else: 
            self.setGeometry( 900, 50, self.width(), self.height())

        #
        # make sure MBS_ATTR is not polluted
        # +++
        for name in MBS_Attrs:
            try:
                temp = getattr( self, name)
            except:
                #print( "%s.__init__: %s is not in self" % ( self.name, name))
                pass

        self.show()
            
        return
    
    def __setattr__( self, name, value):
        """
        +++
        this function protects agains typos. members can only be set, 
        if they have been defined
        """
        #print( "mandelbrotSetWidget.__setattr__: name %s, value %s" % (name, value))
        if name in MBS_Attrs or \
           name.find( 'SelColor') == 0 or \
           name.find( 'AllColor') == 0: 
            super( MBSMainWindow, self).__setattr__(name, value)
        else:
            #
            # the MBN_ files become members of self,
            # needed by 'center' feature
            #
            if name.find( 'MBN_') != 0 and \
               name != 'Center':
                print( " unknown attribute (main): '%s'," %  name)
            super( MBSMainWindow, self).__setattr__(name, value)
            #raise ValueError( "MBSMainWindow.__setattr__: unknown attribute %s" % ( name))

    def displayMBS( self, img):
        #print( "%s.displayEscapeCount" % self.name)
        self.displayImage( img)
        return
    
    def displayDynOp( self, img):
        #print( "%s.displayDynOp" % self.name)
        self.displayImage( img)
        return
    
    def displayImage( self, img):
        #print( "%s.displayImage" % self.name)
        self.lastImage = img.copy()
        self.viewerMain.updateImage( img)
        self.app.processEvents()
        return 

    def redisplay( self):
        """
        redisplay last displayed image
        """
        #print( "%s.redisplay" % self.name)
        if self.lastImage is not None: 
            self.viewerMain.updateImage( self.lastImage)
        if self.juliaMode != "Off": 
            self.viewerJS.updateImage( self.dataJuliaSet)
    
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
        self.dpi = utils.DPI
        self.screenWidthIn  = self.screen.size().width()/dpi_x # just for informational purpose
        self.screenHeightIn = self.screen.size().height()/dpi_y

        #print( "findFigSizes: screen.width %d height %d dpi %d dpi_x %d dpi_y %d " %
        #       ( self.screen.size().width(), self.screen.size().height(), self.dpi, dpi_x, dpi_y))
        self.figSizeC = ( 15*cm, 18*cm)
        if self.modeOperation.lower() == 'demo': 
            self.figSizeC = ( 11*cm, 16*cm)

        # width = utils.WIDTH_VALUES[0] # 1000
        width = self.screen.size().height()*0.9 # because always want to have the same fig size
        self.figSizeLarge = ( width, width)
        self.figSizeBig = ( int( width*0.8), int( width*0.8))
        self.figSizeMedium = ( int( width*0.6), int( width*0.6))
        self.figSizeSmall = ( int( width*0.4), int( width*0.4))
            
        self.figSizeM = self.figSizeBig
        self.figSizeJ = self.figSizeBig
        self.figSize3D = self.figSizeBig
        return 
    
    def initMembers( self):

        self.scanMarker = None
        self.rmColorAction = None
        self.cxOld = None
        
        self.execDynOp = "False"        
        self.operatorWidget = None
        self.lastImage = None
        self.animateAtConstantWidth = "True"
        self.debugSpiral = "False"
        self.isRotating = False
        self.flagIterPath = "False" 
        self.dataJuliaSet = None
        self.centerHsh = {}
        #self.placesWidget = None
        self.scanTexts = []
        self.scanPath = []
        self.scalarAction = None
        self.winDebugColoring = None
        self.busy = False

        self.cythonAction = None
        self.numpyAction = None
        self.maxIterMCombo = None
        self.maxIterJCombo = None
        self.normParCombo = None
        
        self.cxM = -0.75
        self.cyM = 0.
        self.deltaM = 3.
        self.cxJ = 0.
        self.cyJ = 0.
        self.deltaJ = 3.
        self.backgroundColor = self.palette().color( self.backgroundRole()).name()
        
        return

    def setDefaults( self):
        
        self.scalar = "False" 
        if self.scalarAction is not None: 
            self.scalarAction.setChecked( self.scalar == "True")
        
        self.cxM = -0.75
        self.cyM = 0.
        self.deltaM = 3.
        self.cxJ = 0.
        self.cyJ = 0.
        self.deltaJ = 3.
        
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

        self.rmColor = 'w'
        self.viewerMain.setResetMarkerColor( self.rmColor) 
        if self.rmColorAction is not None: 
            self.rmColorAction.setChecked( self.rmColor == "k")

        self.debugColoring = "False"
        #if self.useMPL and self.viewerDebugColoring is not None:
        #    self.viewerDebugColoring.hide()
        
        self.debugSpeed = "False"

        self.stopRequested = False
        
        self.iterPath = None
        self.widthM = utils.WIDTH_VALUES[0]
        self.widthJ = utils.WIDTH_VALUES[0]
        self.zoom = ZOOM_VALUES[0]
        self.maxIterM = MAX_ITER_VALUES[0]
        self.maxIterJ = MAX_ITER_VALUES[0]
        if self.maxIterMCombo is not None: 
            self.maxIterMCombo.setCurrentIndex( 0) 
        if self.maxIterJCombo is not None: 
            self.maxIterJCombo.setCurrentIndex( 0) 
        self.spiral = SPIRAL_VALUES[0]
        self.scanPoints = SCAN_POINT_VALUES[0]
        self.scanCircle = "False"
        self.mandelbrotMode = utils.SIZE_VALUES[ 0]
        self.juliaMode = JULIA_MODE_VALUES[ 0]
        self.animationFactor = ANIMATIONFACTOR_VALUES[0]
        return

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
        # updateGUI
        #
        self.updateGUIAction = QAction('UpdateGUI', self)        
        self.updateGUIAction.triggered.connect( self.cb_updateGUI)
        self.fileMenu.addAction( self.updateGUIAction)
        #
        # redisplay
        #
        self.redisplayAction = QAction('Redisplay', self)        
        self.redisplayAction.triggered.connect( self.redisplay)
        self.fileMenu.addAction( self.redisplayAction)
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
        # exit
        #
        self.exitAction = QAction('Exit', self)        
        self.exitAction.triggered.connect( sys.exit)
        self.fileMenu.addAction( self.exitAction)
        #
        # Colors
        #
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
        # scalar
        #
        self.scalarAction = QAction('Scalar', self, checkable = True)        
        self.scalarAction.triggered.connect( self.cb_scalar)
        self.scalarAction.setStatusTip('Enable scalar algorithm, very slow')
        self.scalarAction.setChecked( self.scalar == "True")
        self.flagsMenu.addAction( self.scalarAction)
        #
        # ResetMarker black/white
        #
        self.rmColorAction = QAction('RM is black', self, checkable = True)        
        self.rmColorAction.triggered.connect( self.cb_rmColor)
        self.rmColorAction.setStatusTip('Switch RM (resetMarker) between black and white')
        self.rmColorAction.setChecked( self.rmColor == "black")
        self.flagsMenu.addAction( self.rmColorAction)
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

        return
    #    
    # === the central part
    #    
    def prepareCentralWidget( self):
        
        self.wCentral = QWidget()
        self.setCentralWidget( self.wCentral)
        self.vLayout = QVBoxLayout()
        self.wCentral.setLayout( self.vLayout)

        #
        # the color widget
        #
        self.colorContainer = QWidget()
        self.colorLayout = QVBoxLayout(self.colorContainer)
        self.colorLayout.setContentsMargins(0, 0, 0, 0)
        self.colorLayout.addWidget( self.colorWidget)
        
        self.vLayout.addWidget(self.colorContainer)
        
        wGrid = QWidget()
        self.vLayout.addWidget( wGrid)
        #
        # the central widget has a grid layout
        #
        self.gridLayout = QGridLayout()
        wGrid.setLayout( self.gridLayout)
        self.gridLayout.setColumnMinimumWidth( 0, 200)
        self.gridLayout.setColumnMinimumWidth( 1, 200)

        row = -1
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
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
        temp = QPushButton("Exec")
        temp.setToolTip( "Execute Jula scan")
        temp.clicked.connect( self.cb_execScan)
        hLayout.addWidget( temp)
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
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        hLayout = QHBoxLayout()
        #
        # MandelbrotMode
        #
        self.mandelbrotModeCombo = QComboBox()
        self.mandelbrotModeCombo.setToolTip( "Size of the Mandelbrot figure.")
        for elm in utils.SIZE_VALUES:
            self.mandelbrotModeCombo.addItem( str( elm))
        self.mandelbrotModeCombo.setCurrentIndex( 3)
        self.mandelbrotModeCombo.activated.connect( self.cb_mandelbrotModeCombo )
        hLayout.addWidget( QLabel( 'Mandelbrot'))
        hLayout.addWidget( self.mandelbrotModeCombo)
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
        self.progressLbl.hide()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
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
        # widthM
        #
        self.widthMCombo = QComboBox()
        self.widthMCombo.setToolTip( 
            "Width of the image in either direction, \n'256' generates test data.")
        for elm in utils.WIDTH_VALUES:
            self.widthMCombo.addItem( str( elm))
        self.widthMCombo.setCurrentIndex( 0)
        self.widthMCombo.activated.connect( self.cb_widthMCombo )
        hLayout.addWidget( QLabel( 'WidthM'))
        hLayout.addWidget( self.widthMCombo)
        #
        # widthJ
        #
        self.widthJCombo = QComboBox()
        self.widthJCombo.setToolTip( 
            "Width of the image in either direction, \n'256' generates test data.")
        for elm in utils.WIDTH_VALUES:
            self.widthJCombo.addItem( str( elm))
        self.widthJCombo.setCurrentIndex( 0)
        self.widthJCombo.activated.connect( self.cb_widthJCombo )
        hLayout.addWidget( QLabel( 'WidthJ'))
        hLayout.addWidget( self.widthJCombo)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # horizontal line
        #
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
        self.logWidget.append( "Use Shift-MB1 to inspect the image") 
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
        temp.clicked.connect( self.viewerMain.setResetMarker)
        hLayout.addWidget( temp)
        #
        # clearRM (resetMarker)
        #
        temp = QPushButton("ClearRM")
        temp.setToolTip( "Clear reset marker")
        temp.clicked.connect( self.viewerMain.clearResetMarker)
        hLayout.addWidget( temp)

        col = 1
        self.gridLayout.addLayout( hLayout, row, col)

        if not cythonOK:
            self.logWidget.append( "The cython interface does not exist")
            self.logWidget.append( "Consider to create one to speed-up")

        # rebuild icon
        self._createIcon()

        # force correct placement immediately
        self._positionIcon()

        return

    def _createIcon(self):
        self.icon = QLabel(self.wCentral)
        if not os.path.exists( "./MBSIcon.png"):
            print( "%s.createIcon: ./MBSIcon.png is missing" % self.name)
            return
        
        pm = QPixmap("./MBSIcon.png").scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon.setPixmap(pm)
        self.icon.setFixedSize(pm.size())
        self.icon.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _positionIcon(self):
        cw = self.wCentral
        x = cw.width() - self.icon.width() - 5
        y = 5
        self.icon.move(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._positionIcon()
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
        store.setToolTip( "Store .png incl. metadata in ./places/MB*")
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
        # ExecDynOp
        #
        self.execDynOpCb = QCheckBox("XOp")
        self.execDynOpCb.setToolTip( "Execute dynamic operator")
        self.execDynOpCb.clicked.connect( self.cb_execDynOp)       
        self.statusBar.addPermanentWidget( self.execDynOpCb)
        #
        # Operator
        #
        self.DynOpPb = QPushButton("DynOp")
        self.DynOpPb.setToolTip( "Open Dynamic Self.DynOpPb widget")
        self.DynOpPb.clicked.connect( self.cb_dynamicOperator)       
        self.statusBar.addPermanentWidget( self.DynOpPb)
        #
        # Switch
        #
        if self.useMPL: 
            self.switchPb = QPushButton("PG")
        else: 
            self.switchPb = QPushButton("MPL")
        self.switchPb.setToolTip( "Switch between PG/MPL")
        self.switchPb.pressed.connect( self.cb_switch)       
        self.statusBar.addPermanentWidget( self.switchPb)
        #
        # stop
        #
        stop = QPushButton("&Stop")
        stop.setToolTip( "Stop the Julia scans and animations")
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

    def addCenterItem( self, name = None, cx = None, cy = None):
        #
        #
        #
        fName = name
        name = utils.trimCenterName( name)
            
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

    def updateGUI( self):

        self.execDynOpCb.setChecked( self.execDynOp == "True")
        
        self.debugSpiralAction.setChecked( self.debugSpiral == "True")
        
        self.animationFactorCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.animationFactor, ANIMATIONFACTOR_VALUES))

        self.spiralCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.spiral, SPIRAL_VALUES))
        
        if self.maxIterMCombo is None:
            return 

        self.widthMCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.widthM, utils.WIDTH_VALUES))

        self.widthJCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.widthJ, utils.WIDTH_VALUES))

        self.zoomCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.zoom, ZOOM_VALUES))

        self.maxIterMCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.maxIterM, MAX_ITER_VALUES))
        self.maxIterJCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.maxIterJ, MAX_ITER_VALUES))

        self.scanPointsCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.scanPoints, SCAN_POINT_VALUES))
        self.scanCircleCb.setChecked( self.scanCircle == 'True')

        self.mandelbrotModeCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.mandelbrotMode, utils.SIZE_VALUES))

        self.juliaModeCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.juliaMode, JULIA_MODE_VALUES))

        self.debugColoringAction.setChecked( self.debugColoring == "True")

        self.debugSpeedAction.setChecked( self.debugSpeed == "True")
        
        #self.showDataCb.setChecked( self.showData == "True")
        
        return

    #    
    # === callbacks    
    #

    #def cb_coloringOutput( self, a, b):
    #    print( "%s.cb_coloringOutput: relaying output" % self.name)
    #    self.viewerDebugColoring.mpl.createDebugColoringOutput( a, b)
    #    return 

    def cb_deltaLbl( self, txt):
        self.deltaLbl.setText( txt)
        return 
    
    def cb_switch( self):
        
        if self.useMPL:
            #print( "%s.cb_switch: to PG" % self.name)
            self.useMPL = False
            self.colorWidget.toPG()
            self.switchPb.setText( "MPL")
            self.viewerMain.showPG()
            #self.viewerDebugColoring.showPG()
        else: 
            #print( "%s.cb_switch: to MPL" % self.name)
            self.useMPL = True
            self.colorWidget.toMPL()
            self.switchPb.setText( "PG")
            self.viewerMain.showMPL()

        self.colorWidget.updateGUI()
        
        self.operatorWidget.close()
        self.operatorWidget = dynamicOperators.operatorWidget(
            self.app, parent = self,
            colorPars = self.colorPars, 
            vInit = "MBS", useMPL = self.useMPL)

        if self.modeOperation.lower() == 'demo': 
            self.setGeometry( 4930, 566, 800, 670)
            self.viewerMain.setGeometry( 3845, 530,
                                         int( self.figSizeM[0]*0.6), int( self.figSizeM[1]*0.6))

            self.operatorWidget.setGeometry(5149, 923, 580, 630)
            self.app.processEvents()
        else: 
            self.setGeometry( 900, 50, self.width(), self.height())
        
        #self.redisplay()
        self.cb_repeat()
        self._positionIcon()
        return
    
    @pyqtSlot()
    def cb_repeat( self):
        self.engine.calcMandelbrotSet()
        self.engine.calcJuliaSet()
        return
    
    @pyqtSlot( float, float)
    def cb_onViewerClickedMB1( self, x, y):
        """
        MB1 zoom-in
        """
        #print( "%s.onViewerClickedMB1: x %g y %g " % ( self.name, x, y))
        self.cxM = x
        self.cyM = y
        self.deltaM = self.deltaM/self.zoom
        #self.viewerMain.setWorldRect() # for PG
        self.engine.calcMandelbrotSet()
        self.engine.calcJuliaSet()
        
        return

    @pyqtSlot( int, int, float, float, str)
    def cb_onViewerClickedShiftMB1( self, ix, iy, x, y, pixel):
        """
        Shift-MB1 coordinates, pixel 
        """
        self.logWidget.append( "(%d, %d) (%g, %g) %s" %
                               (ix, iy, x, y, repr( pixel)))
        
        return
    
    @pyqtSlot( float, float)
    def cb_onViewerClickedMB2( self, x, y):
        """
        MB2 - move ROI
        """
        print( "mandelbrot: MB2 x %g y %g " % ( x, y)) 
        self.cxM = x
        self.cyM = y
        self.deltaM = self.deltaM
        #self.viewerMain.setWorldRect() # for PG
        self.engine.calcMandelbrotSet()
        self.engine.calcJuliaSet()
        
        return

    @pyqtSlot( float, float)
    def cb_onViewerClickedMB3(self, x, y):

        # print( "main.clickedMB3: x %g, y %g" % (x, y))

        if not self.useMPL: 
            #print( "main.clickedMB3: View range: %s" % repr( self.viewerMain.viewBox.viewRange()))
        
            marker = pg.TextItem( "+", color='w', anchor=(0.5, 0.5))
            marker.setZValue(10)
            marker.setPos( x, y)
            # self.viewerMain.plot.getViewBox().addItem(marker)
            self.viewerMain.addMarker(marker)
            font = QFont()
            font.setPointSize(17)   # choose your size
            marker.setFont( font)
            
            self.scanTexts.append(marker)
            self.scanPath.append((x, y))
            self.logWidget.append( "New scan point %d %g %g " % 
                                   (len( self.scanPath), x, y))
        else:
            t = self.viewerMain.addText( x, y, r'+',
                                         color='cyan',
                                         fontsize = 20,
                                         horizontalalignment='center',
                                         verticalalignment='center')
            self.scanTexts.append( t)
            self.scanPath.append( ( x, y))
            self.logWidget.append( "New scan point %d %g %g (MPL)" % 
                                   (len( self.scanPath), x, y))
            
        return

    @pyqtSlot()
    def cb_execScan( self):
        
        if len( self.scanPath) < 2:
            temp = QMessageBox()
            ret = temp.question(self,'', 
                                "execScan: use MB-Right to select scan points'", temp.Ok )
            return
        
        if self.juliaMode == 'Off':
            self.cb_juliaModeCombo( 2)
            self.updateGUI()
            
            #temp = QMessageBox()
            #ret = temp.question(self,'', "Julia mode is 'Off'", temp.Ok )
            #return 

        self.isAnimating = True
        
        self.cxOld = self.cxM
        self.cyOld = self.cyM
        self.deltaOld = self.deltaM
        startTime = time.time()

        self.logWidget.append( "Starting scan")
        scanPointsSeg = int( self.scanPoints/(len( self.scanPath)-1))
        if not self.useMPL: 
            self.scanMarker = pg.TextItem( "*", color='w', anchor=(0.5, 0.5))
            self.scanMarker.setZValue(10)
            #self.viewerMain.viewBox.addItem( self.scanMarker, ignoreBounds=True)
            self.viewerMain.addMarker( self.scanMarker, ignoreBounds=True)
            font = QFont()
            font.setPointSize(17)   
            self.scanMarker.setFont( font)
        else:
            self.scanMarker = self.viewerMain.addText( 0., 0., r'',
                                         color='white',
                                         fontsize = 20, 
                                         horizontalalignment='center', 
                                         verticalalignment='center')

            self.viewerMain.mpl.canvas.draw()
            

        if self.scanCircle == "False":         
            for iPt in range( len( self.scanPath))[1:]:
                if self.stopRequested:  
                    break
                startPoint = self.scanPath[iPt-1]
                endPoint = self.scanPath[iPt]
                for i in range( scanPointsSeg):
                    self.cxM = startPoint[0] + (endPoint[0] - startPoint[0])/scanPointsSeg*i
                    self.cyM = startPoint[1] + (endPoint[1] - startPoint[1])/scanPointsSeg*i
                    if not self.useMPL:
                        self.scanMarker.setPos( self.cxM, self.cyM) 
                        self.scanMarker.setText( text = r'*', color='b')
                    else: 
                        self.scanMarker.set( text = '*', x = self.cxM, y = self.cyM,
                                             transform = self.viewerMain.mpl.ax.transData) 
                        self.viewerMain.mpl.canvas.draw()

                    if self.engine.calcJuliaSet( display = False) is False:
                        break
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
            for i in range( int( self.scanPoints)):
                self.cxM = c[0] + r*math.cos( deltaPhi*i)
                self.cyM = c[1] + r*math.sin( deltaPhi*i)
                if not self.useMPL:
                    self.scanMarker.setPos( self.cxM, self.cyM) 
                    self.scanMarker.setText( text = r'*', color='b')
                else: 
                    self.scanMarker.set( text = '*', x = self.cxM, y = self.cyM, 
                                         transform = self.viewerMain.mpl.ax.transData) 
                    self.viewerMain.mpl.canvas.draw()
                if self.engine.calcJuliaSet( display = False) is False:
                    break
                self.app.processEvents()
                if self.stopRequested:
                    self.stopRequested = False
                    break

        self.isAnimating = False

        self.logWidget.append( "Scan done, %g s" % (time.time() - startTime))

        self.clearScanPars()

        self.engine.calcJuliaSet()

        return

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
    
    def clearScanPars( self):
        if self.scanMarker is not None: 
            if not self.useMPL:
                self.viewerMain.removeItem( self.scanMarker)
                #self.viewerMain.plot.getViewBox().removeItem( self.scanMarker)
                self.scanMarker = None
            else:
                self.scanMarker.remove()
                self.viewerMain.mpl.canvas.draw_idle()
            
        if self.cxOld is not None: 
            self.cxM = self.cxOld
            self.cyM = self.cyOld
            self.deltaM = self.deltaOld
            self.cxOld = None
            
        self.scanPath = []
        for t in self.scanTexts: 
            if not self.useMPL: 
                self.viewerMain.removeItem( t)
                #self.viewerMain.plot.getViewBox().removeItem( t)
            else:
                t.remove()
                self.viewerMain.mpl.canvas.draw_idle()
        self.scanTexts = []
        return 

    @pyqtSlot()
    def cb_timeout(self):
        print( "PGMandelbrot: time-out") 
        return 

    def mkColorCb( self, i):
        def f():
            #print( "PGM: mkColor %s" % i)
            self.colorPars.colorMapName =  i
            self.colorPars.rotateColorMapIndex = 0
            if self.colorWidget.cmapLbl is not None:
                self.colorWidget.cmapLbl.setText( "CMAP: %s" % self.colorPars.colorMapName)
            self.viewerMain.setColor()
            self.viewerJS.setColor() 
            self.viewerMain.updateImage( self.dataMandelbrotSet)
            #self.viewerJS.updateImage( self.dataJuliaSet)

            return 
        return f

    from PyQt5.QtGui import QImage, QPainter

    def save_plotitem_as_pngV1( self, plt, filename, width=1200, height=900):
        
        exporter = pg.exporters.ImageExporter( plt)

        # set export parameters if needed
        exporter.parameters()['width'] = 1000   
        
        # save to file
        exporter.export('fileName.png')
        return
    
    def save_plotitem_as_pngV2( self, widget, filename, width=1200, height=900):
        qimg = QImage(width, height, QImage.Format_ARGB32)
        qimg.fill(0)  # black or transparent background
        
        painter = QPainter(qimg)
        qimg = widget.grab().toImage()
        painter.end()

        qimg.save(filename)
        return
    
    def save_plotitem_as_png( self, widget, filename, width=1200, height=900):
        qimg = widget.grab().toImage()
        qimg.save(filename)
        return
    
    def cb_pngM( self, midFix = None):
        utils.writePng( midFix,
                        prefix = "MB", 
                        MBSObj = self,
                        DynOpObj = self.operatorWidget,
                        ColorParsObj = self.colorPars) 
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
            temp = utils.trimCenterName( self.lastFileRead)
            self.lastReadLbl.setText( temp)
            return
        return f
    
    
    @pyqtSlot()
    def cb_pngJ( self):
        print( "PGMandelbrot: cb_pngJ")
        return

    @pyqtSlot()
    def cb_geometry( self):

        self.logWidget.append( "Screen size: %d x %d" %
                               ( self.screen.size().width(), self.screen.size().height()))
        #self.logWidget.append( "Width %g in, Height %g in" %
        #                       ( self.screenWidthIn, self.screenHeightIn))

        self.logWidget.append( "self.geometry(): %s" % repr( self.geometry()))
        self.logWidget.append( "MBS %s " % repr( self.viewerMain.geometry()))
        self.logWidget.append( "cb_geometry: viewerDebugColoring %s " %
                               repr( self.viewerDebugColoring.geometry()))
        if self.placesWidget is not None: 
            self.logWidget.append( "self.places.geometry(): %s" %
                                   repr( self.placesWidget.geometry()))
        if self.operatorWidget is not None: 
            self.logWidget.append( "self.operator.geometry(): %s" %
                                   repr( self.operatorWidget.geometry()))
        return

    @pyqtSlot()
    def cb_clear( self):
        self.logWidget.clear()
        return

    @pyqtSlot( bool)
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
        self.engine.calcMandelbrotSet()
        return 

    @pyqtSlot( bool)
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

        self.engine.calcMandelbrotSet()
        return 

    @pyqtSlot( bool)
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

        self.engine.calcMandelbrotSet()
        return 

    @pyqtSlot( bool)
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

        self.engine.calcMandelbrotSet()
        return 

    @pyqtSlot( bool)
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

        self.engine.calcMandelbrotSet()
        return 

    @pyqtSlot( bool)
    def cb_rmColor( self, i):
        if i:
            self.rmColor = 'k'
        else:
            self.rmColor = 'w'
        self.viewerMain.setResetMarkerColor( self.rmColor) 
        self.viewerMain.updateImage( self.dataMandelbrotSet)

        return

    @pyqtSlot( bool)
    def cb_debugSpiral( self, i):
        if i:
            self.debugSpiral = "True"
            self.viewerSpiral.show()
        else:
            self.debugSpiral = "False"
            self.viewerSpiral.hide()

        return 
    
    @pyqtSlot( bool)
    def cb_debugColoring( self, i):
        if not self.useMPL:
            return 
        if i:
            self.setDebugColoring.emit( True)
            self.debugColoring = "True" 
            self.viewerDebugColoring.showMPL()
            self.engine.calcMandelbrotSet()
            self.viewerDebugColoring.show()
        else:
            self.setDebugColoring.emit( False)
            self.debugColoring = "False"
            self.viewerDebugColoring.hide()

        return 

    @pyqtSlot( bool)
    def cb_debugSpeed( self, i):
        if i:
            self.debugSpeed = "True" 
        else:
            self.debugSpeed = "False"

        return

    @pyqtSlot()
    def cb_helpOverview( self):
        print( "PGMandelbrot: cb_helpOverView")
        return

    @pyqtSlot( int)
    def cb_spiralCombo( self, i):
        self.spiral = SPIRAL_VALUES[i]
        return

    @pyqtSlot( int)
    def cb_animationFactorCombo( self, i):
        self.animationFactor = ANIMATIONFACTOR_VALUES[i]
        return

    @pyqtSlot()
    def cb_animateZoom( self):
            
        if self.deltaM > 2.9:
            temp = QMessageBox()
            temp.question(self,'', 
                          "animate: zoom-in first, then animate'", 
                          temp.Ok )
            return
        vminEnd = self.colorPars.vmin

        vmaxDiff = 1024. - self.colorPars.vmax
        vminStart = 0
        vmaxStart = 1024
        self.colorPars.vmin = vminStart
        self.colorPars.vmax = vmaxStart
        self.colorWidget.vminSlider.setValue( int( self.colorPars.vmin))
        self.colorWidget.vmaxSlider.setValue( int( self.colorPars.vmax))

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
            self.viewerSpiral.updateScatter( cx, cy)
        else:
            #self.viewerSpiral.hide()
            pass

        #
        # take half of the width during animation to speed-up - 
        # unless the user does not permit it.
        #
        widthMOld = self.widthM
        if self.animateAtConstantWidth == "False": 
            newWidth = int( self.widthM * 0.5)
            if newWidth in utils.WIDTH_VALUES: 
                self.widthM = newWidth
                self.updateGUI()
            else: 
                self.logWidget.append( "cb_animateZoom: cannot use 50% of width, not in VALUES")

        colorIndexOld = self.colorPars.rotateColorMapIndex
        for i in range( len( cx)):
            self.cxM = cx[i]
            self.cyM = cy[i]
            self.deltaM = delta[i]
            temp = (deltaStart - self.deltaM) / (deltaStart - deltaEnd)
            self.colorPars.vmin = vminStart + temp * (vminEnd - vminStart)
            self.colorPars.vmax = 1024. - vmaxDiff*temp
            self.colorWidget.vminSlider.setValue( int( self.colorPars.vmin))
            self.colorWidget.vmaxSlider.setValue( int( self.colorPars.vmax))
            self.engine.calcMandelbrotSet( display = False)
            if self.stopRequested:
                self.stopRequested = False
                self.logWidget.append( "animate: stopped") 
                break
        self.widthM = widthMOld
        self.updateGUI()
        self.logWidget.append( "animate: DONE, %g" % 
                               (( time.time() - startTime)))
        self.animatePb.setStyleSheet("background-color:%s" % self.backgroundColor)
        self.colorPars.vmin = vminEnd
        self.colorPars.vmax = (1024. - vmaxDiff)
        self.colorWidget.vminSlider.setValue( int( self.colorPars.vmin))
        self.colorWidget.vmaxSlider.setValue( int( self.colorPars.vmax))
        self.cxM = cxEnd
        self.cyM = cyEnd
        self.engine.calcMandelbrotSet()
        self.app.processEvents()
        self.isAnimating = False
        return

    @pyqtSlot( int)
    def cb_maxIterMCombo( self, i):
        self.maxIterM = int( MAX_ITER_VALUES[i])
        self.engine.calcMandelbrotSet()
        return

    @pyqtSlot( int)
    def cb_maxIterJCombo( self, i):
        self.maxIterJ = int( MAX_ITER_VALUES[i])
        self.engine.calcJuliaSet()
        return

    @pyqtSlot( int)
    def cb_widthMCombo( self, i):
        self.widthM = int( utils.WIDTH_VALUES[i])
        self.engine.calcMandelbrotSet()
        return

    @pyqtSlot( int)
    def cb_widthJCombo( self, i):
        self.widthJ = int( utils.WIDTH_VALUES[i])
        self.engine.calcMandelbrotSet()
        return

    @pyqtSlot( int)
    def cb_scanPointsCombo( self, i):
        self.scanPoints = float( SCAN_POINT_VALUES[i])
        return
    
    @pyqtSlot( bool)
    def cb_scanCircle( self, i):
        if i:
            self.scanCircle = "True"
        else:
            self.scanCircle = "False"
        return
    
    @pyqtSlot( bool)
    def cb_execDynOp( self, i):
        if i:
            self.execDynOp = "True"
        else:
            self.execDynOp = "False"
        self.engine.calcMandelbrotSet()
        self.engine.calcJuliaSet()
        return

    @pyqtSlot( int)
    def cb_mandelbrotModeCombo( self, i):
        self.mandelbrotMode = utils.SIZE_VALUES[i]
        if self.mandelbrotMode == 'Small': 
            self.figSizeM = self.figSizeSmall
        elif self.mandelbrotMode == 'Medium': 
            self.figSizeM = self.figSizeMedium
        elif self.mandelbrotMode == 'Big': 
            self.figSizeM = self.figSizeBig
        else:
            self.figSizeM = self.figSizeLarge

        self.viewerMain.resize( int( self.figSizeM[0]), int( self.figSizeM[1]))
        
        return

    @pyqtSlot( int)
    def cb_juliaModeCombo( self, i):
        
        self.juliaMode = JULIA_MODE_VALUES[ i]

        if self.juliaMode == 'Off':
            self.viewerJS.hide()
            return

        self.viewerJS.show()
        
        if self.juliaMode == 'Large': 
            self.figSizeJ = self.figSizeLarge
        elif self.juliaMode == 'Big': 
            self.figSizeJ = self.figSizeBig
        elif self.juliaMode == 'Medium': 
            self.figSizeJ = self.figSizeMedium
        elif self.juliaMode == 'Small': 
            self.figSizeJ = self.figSizeSmall
        else: 
            self.figSizeJ = self.figSizeTiny

        self.viewerJS.resize( int( self.figSizeJ[0]), int( self.figSizeJ[1]))

        self.engine.calcJuliaSet()

        return

    @pyqtSlot( int)
    def cb_zoomCombo( self, i):
        self.zoom = float( ZOOM_VALUES[i])
        return

    @pyqtSlot()
    def cb_zoomOut( self):
        self.deltaM *= self.zoom
        if self.deltaM > 3.:
            self.cb_reset()
        self.engine.calcMandelbrotSet()
        return

    @pyqtSlot()
    def cb_zoomHome( self): 
        #self.setResetMarker()
        self.cxM = -0.75
        self.cyM = 0.
        self.deltaM = 3.
        self.cxJ = 0.
        self.cyJ = 0.
        self.deltaJ = 3.
        #self.viewerMain.setWorldRect() # for PG
        self.engine.calcMandelbrotSet()

        return

    @pyqtSlot( bool)
    def cb_iterPath( self, i):
        if i:
            if self.deltaM < 3.:
                temp = QMessageBox()
                ret = temp.question(self,'', 
                                    "iterPath: only for the whole plot", temp.Ok )
                self.flagIterPath = "False" 
                self.iterPathCb.setChecked( self.iterPath == "True") 
                return 
                
            self.viewerMain.connectOnMouseMoved( True) 
            self.flagIterPath = "True" 
        else:
            self.viewerMain.connectOnMouseMoved( False) 
            self.flagIterPath = "False" 

        return

    @pyqtSlot()
    def cb_places( self):
        #self.placesWidget = mandelbrotPlaces.places( self.app, parent = self)
        self.placesWidget.show()
        return

    @pyqtSlot()
    def cb_store( self): 
        utils.writePng( midFix = None,
                        prefix = "MB", 
                        MBSObj = self,
                        DynOpObj = self.operatorWidget,
                        ColorParsObj = self.colorPars) 
        return
        # 
        #self.cb_pngM()
        #return 

    @pyqtSlot()
    def cb_updateGUI( self): 
        # 
        self.updateGUI()
        self.colorWidget.updateGUI()
        return 

    @pyqtSlot()
    def cb_storeNamed( self): 
        #
        dlg = utils.InputDialog( "Enter file name")
        if dlg.exec_() == QDialog.Accepted:
            value = dlg.get_value()
            if value is None or len( value.strip()) == 0:
                self.logWidget.append( "storeNamed: no input, return")
                return
        else:
            return 
        utils.writePng( midFix = value,
                        prefix = "MBN", 
                        MBSObj = self,
                        DynOpObj = self.operatorWidget,
                        ColorParsObj = self.colorPars) 
        return
        #self.cb_pngM( fileName = value)
        #return 

    @pyqtSlot()
    def cb_dynamicOperator( self):

        if not self.operatorWidget.isVisible():
            self.operatorWidget.show()
            return
        
        self.logWidget.append( "The operator widget exists, please locate it.")
        self.logWidget.append( "raise_() does not work properly")
        return 

    @pyqtSlot()
    def cb_stop( self):
        self.stopRequested = True
        return

    @pyqtSlot()
    def cb_reset( self):

        self.clearScanPars()
        self.viewerMain.setResetMarker()
        self.setDefaults()
        self.colorPars.setDefaults()
        self.updateGUI()
        self.colorWidget.cb_normCombo( 0)
        self.colorWidget.updateGUI()
        self.engine.calcMandelbrotSet()
        self.engine.calcJuliaSet()

        return

    @pyqtSlot()
    def cb_clear( self):
        print( "PGMandelbrot: cb_clear")
        return

    @pyqtSlot()
    def cb_close( self):
        self.viewerMain.close()
        self.viewerJS.close()
        self.viewerDebugColoring.close()
        self.placesWidget.close()
        self.close()
        return

    @pyqtSlot()
    def cb_lastRead( self):
        if self.lastFileRead is None:
            self.logWidget.append( "No file read so far")
            return
                        
        utils.readPng( self.lastFileRead,
                       MBSObj = self, 
                       DynOpObj = self.operatorWidget,
                       ColorWidgetObj = self.colorWidget,
                       ColorParsObj = self.colorPars)

        self.engine.calcMandelbrotSet()
        self.engine.calcJuliaSet()
        return
    #
    # === end callbacks
    #

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
    parser.add_argument( '-m',
                         dest="useMPL", action="store_true", help='Use MPL')
    args = parser.parse_args()

    return args
        
def main():

    args = parseCLI()
        
    app = QApplication(sys.argv)
    #
    # the fontSize tells the rest of the program what the user wants.
    #
    app.setStyleSheet("*{font-size: %dpt;}" % int( args.fontSize))

    w = MBSMainWindow( app, fontSize = int( args.fontSize), modeOperation = args.mode, useMPL = args.useMPL)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
