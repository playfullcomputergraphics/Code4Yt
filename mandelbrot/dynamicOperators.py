#!/usr/bin/env python3
"""
Class hierarchies:

  dynamicOperators.operatorWidget
    - PGViewer.Viewer
    - MPLViewer.Viewer
    - colorWidget.colorWidget

  mandelbrot.MBSMainWindow
    - PGViewer.Viewer
    - MPLViewer.Viewer
    - dynamicOperators.operatorWidget
    - colorWidget.colorWidget

"""
import os, sys, time, math, random, json, hashlib
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from scipy.ndimage import gaussian_filter
sys.path.append( "./cython") 
import PGViewer
import MPLViewer
import Shells
import colorWidget
from PIL import PngImagePlugin
import mandelbrotPlaces
from PIL import Image

try: 
    import dynamicOperatorsCython
    cythonOK = True
except:
    print(" failed to import dynamicOperatorsCython") 
    cythonOK = False

import numpy as np
sys.path.append( "../mandelbrot") 
import mandelbrot
import utils

DU_DEFAULT = 0.16
SLIDER_WIDTH = 400
FEED_MIN = 0.0
FEED_MAX = 0.1
KILL_MIN = 0.0
KILL_MAX = 0.1
DU_MIN = 0.0
DU_MAX = 0.4
DV_MIN = 0.0
DV_MAX = 0.3
SCALE = 1000

METADATA_MEMBERS = [
    'du', 'dv', 'iterationsMax', 'iterations','scaleDuDv', 'ratioDuDv', 
    'feedRate', 'killRate', 'sigma', 'alpha', 'dt', 'widthDynOp', 
    'uInit', 'vInit', 'normLoop', 'forever', 'operatorName', 'presetName', 
    ]
#
# beware of typos, check whether a member is in the list of known members

#
DynOp_Attrs = METADATA_MEMBERS + \
    [ 'parent', 'menuBar', 'fileMenu', 'clearAction',
      'exitAction', 'menuBarRight', 'helpMenu', 'overviewAction', 'gridLayout',
      'reactionLbl', 'feedRatePushButton', 'feedRateLbl', 'killRateLbl',
      'killRatePushButton', 'feedRateLineEdit', 'killRateLineEdit', 
      'sigmaSlider', 'sigmaSliderLbl', 'viewerFk', 
      'alphaSlider', 'alphaSliderLbl', 'sliderBusy', 'iterationsMaxSlider', 
      'iterationsMaxSliderLbl', 'UVempty', 'resetUVPb', 'iterations', 
      'normLoopCb', 'logWidget', 'updateGUIAction', 
      'statusBar', 'uInitCombo', 'vInitCombo', 'operatorCombo',
      'presetRDCombo', 'presetSSCombo', 'scaleSpaceLbl', 
      'wOutputCombo', "dtCombo", "dt", "wOutput", "U_in", "V_in",
      'forever', 'foreverCb', 'iteratedLbl', 'wCentral', 'useMPL', 
      'stopRequested', 'dataMandelbrotSet', 'app', 'debugColoring',
      'deltaLbl', 'mode', 'viewerMain', 'colorWidget', 'allColorsMenu', 'flagsMenu',
      'showDiffAction', 'colorsMenu', 'showDiff', 'backgroundColor', 
      'worker', 'thread', 'name', 'runStopPb',
      'lastImage', 'duLbl', 'dvLbl', 'duLineEdit', 'repeatPtr', 
      'dvLineEdit', 'duPushButton', 'dvPushButton', 'scaleDuDvCombo',
      'ratioDuDvCombo', 'placesWidget', 'widthDynOpCombo', 'screen',
      'sizeDynOpCombo', 'sizeDynOp', 'figSizeLarge', 'figSizeBig',
      'figSizeMedium', 'figSizeSmall', 'figSize', 'dataPtr',
      'switchPb', 'modeOperation', 'colorPars', 'lastReadLbl',
      'redisplayAction', 'clearScreenAction', 'geometryAction',
      'vLayout', 'icon', 'colorContainer', 'colorLayout',
      'lastFileRead', 'version', 'winDebugColoring', 'viewerDebugColoring',
      'debugColoringAction', 'operatorFunction', 
     ]

OPERATOR_VALUES = [ 'AntiDiffusionPython', 'GrayScott', 'GrayScottPython',
                    'AntiDiffusionV1', 'AntiDiffusionV2', 
                    'Shock', 'ShockOsherRudin'] 

U_INIT_VALUES = [ "Ones", "MBS", "Squares3"]
V_INIT_VALUES = [ "Ones", "MicroSeed", "MicroSeed3",
                  "LineSeed", "Square1", "Squares3",  
                  "Squares10", "Squares20", 'Squares50', 'Squares70', "Squares100", 
                  'Circle1', 'Circles3', 'Circles5','Circles15','Circles25',
                  'Circles50', 'Circles70']

W_OUTPUT_VALUES = [ "V_out", "U_out"]

DT_VALUES = [ 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

class operatorWidget( QMainWindow):

    #invokeOpFunc = pyqtSignal()
    frameReady = pyqtSignal(np.ndarray)
    setDebugColoring = pyqtSignal( bool)

    testSignal = pyqtSignal()
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        print(f"Key pressed: {key} ({event.text()})")
        
    def __init__(self, app, parent=None, vInit = None, mode = None,
                 colorPars = None, 
                 modeOperation = None, useMPL = True):
        super().__init__(parent)
        #QWidget.__init__(self, parent, Qt.WindowStaysOnTopHint)

        if useMPL: 
            self.setWindowTitle("Dynamic Operator (MPL)")
        else: 
            self.setWindowTitle("Dynamic Operator (PG)")
        self.name = "DynOp"
        self.app = app
        self.parent = parent
        self.vInit = vInit
        #print( "%s.init: vInit %s" % ( self.name, self.vInit))
        self.colorPars = colorPars
        self.modeOperation = modeOperation # e.g. 'demo'
        self.useMPL = useMPL

        self.debugColoring = "False"
        self.deltaLbl = None
        
        self.viewerMain = None
        if mode is not None:
            self.mode = mode
        else:
            if self.parent is not None: 
                self.mode = "From%s" % self.parent.name

        self.backgroundColor = self.palette().color( self.backgroundRole()).name()
            
        self.initMembers() 
        
        self.setDefaults()

        if self.colorPars is None:
            self.colorPars = utils.ColorPars( parent = self)
            
        if self.mode == 'standalone':
            #print( "operatorWidget.__init__(): standalone")

            self.viewerMain = Shells.ViewerShell( parent = self,
                                                  app = self.app, 
                                                  title = "DynOp", 
                                                  colorPars = self.colorPars)
            self.viewerDebugColoring = Shells.ViewerShell( parent = self,
                                                           app = self.app,
                                                           title = "Coloring",
                                                           colorPars = self.colorPars)
            self.setDebugColoring.connect( self.viewerMain.setDebugColoring)
            self.screen = self.app.primaryScreen()
            temp = int( self.screen.size().height()*0.85)
            self.figSizeLarge = ( temp, temp)
            self.figSizeBig = ( int( temp*0.8), int( temp*0.8))
            self.figSizeMedium = ( int( temp*0.6), int( temp*0.6))
            self.figSizeSmall = ( int( temp*0.4), int( temp*0.4))
            self.figSize = self.figSizeLarge
            #self.viewerMain.resize( self.figSize[0], self.figSize[1])
            self.viewerMain.setGeometry( 50, 50, self.figSize[0], self.figSize[1])
            self.viewerMain.setWindowFlags(Qt.Window)
            self.viewerMain.show()
            self.colorWidget = colorWidget.colorWidget( self.app, self,
                                                        colorPars = self.colorPars)
            self.colorWidget.setColor.connect( self.viewerMain.setColor)
            #self.colorWidget.calcMBS.connect( self.engine.calcMandelbrotSet)
            self.colorWidget.redisplay.connect( self.redisplay)
            self.viewerMain.coloringOutput.connect( self.viewerDebugColoring.mpl.createDebugColoringOutput)
            
            self.dataPtr = self
            self.repeatPtr = None
        else: 
            self.dataPtr = self.parent
            V_INIT_VALUES.append( 'MBS') 
            self.repeatPtr = self.parent.cb_repeat
            self.colorWidget = self.parent.colorWidget
            self.viewerMain = self.parent.viewerMain
            self.figSizeLarge = None
            self.figSizeBig = None
            self.figSizeMedium = None
            self.figSizeSmall = None
            self.figSize = None

            
        if self.mode == 'standalone':
            self.setGeometry( 1000, 50, self.width(), self.height())
        else:
            self.setGeometry( 1100, 150, self.width(), self.height())
            
        self.viewerFk = utils.JpgViewer( fileName = 'FkMapMRob.jpg')
        self.viewerFk.setWindowTitle( "FeedRate/KillRate")
        self.viewerFk.setWindowFlags(Qt.Window)
        self.viewerFk.incrFeedRate.connect( self.cb_incrFeedRate) 
        self.viewerFk.decrFeedRate.connect( self.cb_decrFeedRate) 
        self.viewerFk.incrKillRate.connect( self.cb_incrKillRate) 
        self.viewerFk.decrKillRate.connect( self.cb_decrKillRate) 
        self.viewerFk.labelFk.clicked.connect( self.cb_FkEvent)
        self.viewerFk.hide()

        self.placesWidget = None
        if True or self.mode == 'standalone':
            self.placesWidget = mandelbrotPlaces.places( self.app,
                                                         parent = self,
                                                         prefix = "DynOp",
                                                         viewerFk = self.viewerFk)
        
        #if self.mode == 'standalone':
        #    self.viewerFk.label.clicked.connect( self.cb_FkEvent)

        self.prepareMenuBar()
        self.prepareCentralWidget()
        self.prepareStatusBar()
        #
        # +++
        #
        if self.mode == 'standalone':
            self.frameReady.connect( self.displayDynOp)
            self.colorWidget.setColor.connect(self.viewerMain.setColor)
            self.colorWidget.redisplay.connect( self.redisplay)
            self.colorWidget.logWidget.connect( self.logWidget.append)
        else: 
            #print( "operatorWidget.__init__(): self.parent.name %s" % self.parent.name) 
            self.frameReady.connect( self.parent.displayDynOp) 
            self.makeOperatorFunction()

        self.loadPreset( self.presetName)
        #
        # updateGUI() called also by setDefaults(),
        # however, it is skipped because the widgets need
        # to exist in advance
        #
        self.updateGUI()

        self.enableWidgets()
        
        if self.mode == 'standalone': 
            utils.readPng( "./places/DynOpNP_F425k63221.png",
                           MBSObj  = None,
                           DynOpObj = self,
                           ColorWidgetObj = self.colorWidget,
                           ColorParsObj = self.colorPars)
        #
        # make sure MBS_ATTR is not polluted
        # +++
        """
        for name in DynOp_Attrs:
            try:
                temp = getattr( self, name)
            except:
                print( "%s.__init__: %s is not in self" % ( self.name, name))
                pass
        """
        return

        
    def initMembers( self): 

        self.operatorFunction = None 
        self.winDebugColoring = None
        self.thread = None
        self.lastReadLbl = None
        self.iterationsMaxSliderLbl = None

        self.allColorsMenu = None
        self.colorsMenu = None
        self.worker = None
        self.scaleDuDvCombo = None
        self.ratioDuDvCombo = None
        
        self.sizeDynOpCombo = None
        self.sizeDynOp = utils.SIZE_VALUES[0]
        self.feedRateLbl = None
        self.killRateLbl = None
        self.duLbl = None
        self.dvLbl = None
        self.widthDynOpCombo = None
        
        self.scaleDuDv = utils.SCALEDUDV_VALUES[0]
        self.ratioDuDv = utils.RATIODUDV_VALUES[0]
        
        self.lastImage = None
        self.widthDynOp = utils.WIDTH_VALUES[0]
        self.dataMandelbrotSet = np.zeros(( self.widthDynOp, self.widthDynOp))
        self.UVempty = True
        
        self.showDiff = "False" 
        self.stopRequested = False

        self.foreverCb = None
        self.U_in = None
        self.V_in = None
        self.sliderBusy = False
        self.feedRate = 0.04
        self.killRate = 0.055
        self.du = DU_DEFAULT
        self.dv = DU_DEFAULT/2.
        self.dt = 0.2
        self.sigma = 1.0
        self.alpha = 0.5
        self.iterationsMax = 0
        self.uInit = 'Ones'
        if self.vInit is None: 
            self.vInit = 'Squares100'
        self.wOutput = 'V_out'
        self.widthDynOp = utils.WIDTH_VALUES[0]
        self.normLoop = "True"
        self.forever = "False"
        self.operatorName = 'GrayScott'
        #self.operatorName = 'AntiDiffusionV1'
        self.iterationsMaxSlider = None
        self.feedRateLbl = None
        self.killRateLbl = None
        self.sigmaSlider = None
        self.alphaSlider = None
        self.uInitCombo = None
        self.vInitCombo = None
        self.wOutputCombo = None
        self.presetName = "Delta (F420k590, Turing patterns)"
        self.operatorCombo = None
        self.presetRDCombo = None
        self.presetSSCombo = None
        self.dtCombo = None

        return 

    def updateGUI( self):

        if self.iterationsMaxSliderLbl is not None:
            self.iterationsMaxSliderLbl.setText( "IterationsMax: %d" % self.iterationsMax)
        if self.iterationsMaxSlider is not None:
            self.iterationsMaxSlider.setValue( self.iterationsMax)
        
        if self.sizeDynOpCombo is not None: 
            self.sizeDynOpCombo.setCurrentIndex(
                utils.findCurrentIndex( self.sizeDynOp, utils.SIZE_VALUES))
        
        if self.foreverCb is not None:
            self.foreverCb.setChecked( self.forever == "True")
        
        if self.operatorCombo is not None: 
            self.operatorCombo.setCurrentIndex( 
                utils.findCurrentIndex( self.operatorName, OPERATOR_VALUES))

        if self.feedRateLbl is not None: 
            self.feedRateLbl.setText( "F: %6.4f" % self.feedRate)
        if self.killRateLbl is not None: 
            self.killRateLbl.setText( "k: %6.4f" % self.killRate)
        if self.duLbl is not None: 
            self.duLbl.setText( "Du: %6.4f" % self.du)
        if self.dvLbl is not None: 
            self.dvLbl.setText( "Dv: %6.4f" % self.dv)
        if self.scaleDuDvCombo is not None:
            self.scaleDuDvCombo.setCurrentIndex(
            utils.findCurrentIndex( self.scaleDuDv, utils.SCALEDUDV_VALUES))
        try: 
            if self.ratioDuDvCombo is not None:
                self.ratioDuDvCombo.setCurrentIndex(
                    utils.findCurrentIndex( self.ratioDuDv, utils.RATIODUDV_VALUES))
        except:
            self.ratioDuDv = 2.
            if self.ratioDuDvCombo is not None:
                self.ratioDuDvCombo.setCurrentIndex(
                    utils.findCurrentIndex( self.ratioDuDv, utils.RATIODUDV_VALUES))
        
        if self.sigmaSlider is not None: 
            self.sigmaSlider.setValue( int( self.sigma*10))
        if self.alphaSlider is not None: 
            self.alphaSlider.setValue( int( self.alpha*10))
            
        if self.uInitCombo is not None: 
            self.uInitCombo.setCurrentIndex(
                utils.findCurrentIndex( self.uInit, U_INIT_VALUES))
        if self.vInitCombo is not None: 
            self.vInitCombo.setCurrentIndex(
            utils.findCurrentIndex( self.vInit, V_INIT_VALUES))
            
        if self.wOutputCombo is not None: 
            self.wOutputCombo.setCurrentIndex(
                utils.findCurrentIndex( self.wOutput, W_OUTPUT_VALUES))
            
        if self.widthDynOpCombo is not None: 
            self.widthDynOpCombo.setCurrentIndex(
                utils.findCurrentIndex( self.widthDynOp, utils.WIDTH_VALUES))
            
        if self.presetRDCombo is not None:
            if self.presetName in sorted(utils.PRESET_RD_VALUES.keys()): 
                temp = utils.findCurrentIndex( self.presetName, sorted(utils.PRESET_RD_VALUES.keys()))
                self.presetRDCombo.setCurrentIndex( temp)
        if self.presetSSCombo is not None: 
            if self.presetName in sorted(utils.PRESET_SS_VALUES.keys()): 
                temp = utils.findCurrentIndex( self.presetName, sorted(utils.PRESET_SS_VALUES.keys()))
                self.presetSSCombo.setCurrentIndex( temp)
                
        if self.dtCombo is not None: 
            self.dtCombo.setCurrentIndex(
                utils.findCurrentIndex( self.dt, DT_VALUES))
        
        return

    def __setattr__( self, name, value):
        """
        +++
        this function protects agains typos. members can only be set, 
        if they have been defined
        """
        #print( "operatorWidget.__setattr__: name %s, value %s" % (name, value))
        if name in DynOp_Attrs or \
           name.find( 'SelColor') == 0 or \
           name.find( 'AllColor') == 0: 
            super( operatorWidget, self).__setattr__(name, value)
        else:
            #
            # the MBN_ files become members of self,
            # needed by 'center' feature
            #
            if name.find( 'MBN_') != 0 and \
               name != 'Center':
                print( " unknown attribute (Operator): '%s'," %  name)
            super( operatorWidget, self).__setattr__(name, value)
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
        # redisplay
        #
        self.redisplayAction = QAction('Redisplay', self)        
        self.redisplayAction.triggered.connect( self.redisplay)
        self.fileMenu.addAction( self.redisplayAction)
        #
        # clearScreen
        #
        self.clearScreenAction = QAction('Clear screen', self)        
        self.clearScreenAction.triggered.connect( self.cb_clearScreen)
        self.fileMenu.addAction( self.clearScreenAction)
        #
        # self.geometry()
        #
        self.geometryAction = QAction('Geometry() to log', self)        
        self.geometryAction.triggered.connect( self.cb_geometry)
        self.fileMenu.addAction( self.geometryAction)
        #
        # updateGUI
        #
        self.updateGUIAction = QAction('UpdateGUI', self)        
        self.updateGUIAction.triggered.connect( self.updateGUI)
        self.fileMenu.addAction( self.updateGUIAction)
        #
        # clear log widget
        #
        self.clearAction = QAction('Clear log widget', self)        
        self.clearAction.triggered.connect( self.cb_clear)
        self.fileMenu.addAction( self.clearAction)
        #
        # exit
        #
        self.exitAction = QAction('Exit', self)        
        self.exitAction.triggered.connect( sys.exit)
        self.fileMenu.addAction( self.exitAction)

        if self.mode == 'standalone':
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
        self.showDiffAction = QAction('ShowDiff', self, checkable = True)        
        self.showDiffAction.triggered.connect( self.cb_showDiff)
        self.showDiffAction.setStatusTip('Enable/disable diffusion parameters')
        self.showDiffAction.setChecked( self.showDiff == "True")
        self.flagsMenu.addAction( self.showDiffAction)
        #
        # debugColoring
        #
        self.debugColoringAction = QAction('DebugColoring', self, checkable = True) 
        self.debugColoringAction.triggered.connect( self.cb_debugColoring)
        self.debugColoringAction.setStatusTip( "Enable debugColoring mode")
        self.debugColoringAction.setChecked( self.debugColoring == "True")
        self.flagsMenu.addAction( self.debugColoringAction)
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
    # === the status bar
    #
    def prepareStatusBar( self): 
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)
        if True or self.mode == 'standalone':
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
            store.setToolTip( "Store .png incl. metadata in ./places/DynOp*")
            store.clicked.connect( self.cb_store)       
            self.statusBar.addWidget( store)
            #
            # store named
            #
            storeNamed = QPushButton("StoreNamed")
            storeNamed.setToolTip( "Store .png incl. metadata in ./places/DynOpN_<input>.png")
            storeNamed.clicked.connect( self.cb_storeNamed)       
            self.statusBar.addWidget( storeNamed)
        #
        # openPar
        #
        openPar = QPushButton("F/k-Map")
        openPar.setToolTip( "Open a feedRate/killRate map.\nProvided by Robert Munafo, https://www.mrob.com/pub/comp/xmorphia, \nlicence:  Creative Commons Attribution-NonCommercial 4.0 International License")
        openPar.clicked.connect( self.cb_FkMap)       
        self.statusBar.addWidget( openPar)
        #
        # Switch
        #
        
        if self.mode == 'standalone':
            if self.useMPL: 
                self.switchPb = QPushButton("PG")
            else: 
                self.switchPb = QPushButton("MPL")
            self.switchPb.setToolTip( "Switch between PG/MPL")
            self.switchPb.pressed.connect( self.cb_switch)       
            self.statusBar.addPermanentWidget( self.switchPb)
        #
        # run
        #
        self.runStopPb = QPushButton("Run")
        self.runStopPb.setToolTip( "Toggle run/stop, shortcut Alt+r")
        self.runStopPb.pressed.connect( self.cb_runStop)       
        self.statusBar.addPermanentWidget( self.runStopPb)
        #self.runStopPb.setShortcut( "Alt+r") requires text to contain 'r'
        #
        # this shortcut is independent of the texts 'Run' or 'Stop'
        #
        shortcut = QShortcut(QKeySequence("Alt+r"), self)
        shortcut.activated.connect(self.cb_runStop)
        #
        # reset
        #
        self.resetUVPb = QPushButton("Reset")
        self.resetUVPb.setToolTip( "Reset U/V fields, shortcut Alt+c")
        self.resetUVPb.pressed.connect( self.cb_resetUV)       
        self.statusBar.addPermanentWidget( self.resetUVPb)
        shortcut = QShortcut(QKeySequence("Alt+c"), self)
        shortcut.activated.connect(self.cb_resetUV)
        #
        # deleteOperator
        #
        #temp = QPushButton("RmOp")
        #temp.clicked.connect( self.cb_deleteOperator)       
        #self.statusBar.addPermanentWidget( temp)
        #
        # makeOperator
        #
        #temp = QPushButton("MakeOp")
        #temp.clicked.connect( self.cb_makeOperatorFunction)       
        #self.statusBar.addPermanentWidget( temp)
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
    def prepareCentralWidget( self):

        self.wCentral = QWidget()
        self.setCentralWidget( self.wCentral)
        self.vLayout = QVBoxLayout()
        self.wCentral.setLayout( self.vLayout)
        
        if self.mode == 'standalone': 
            #
            # the color widget goes into a container
            #
            self.colorContainer = QWidget()
            self.colorLayout = QVBoxLayout(self.colorContainer)
            self.colorLayout.setContentsMargins(0, 0, 0, 0)
            self.colorLayout.addWidget( self.colorWidget)
            self.vLayout.addWidget(self.colorContainer)
        
        wGrid = QWidget()
        self.vLayout.addWidget( wGrid)
        
        #
        # start with a vertical layout
        #
        self.gridLayout = QGridLayout()
        wGrid.setLayout( self.gridLayout)
        #self.gridLayout.setColumnMinimumWidth( 0, 200)
        #self.gridLayout.setColumnMinimumWidth( 1, 200)

        row = -1
        hLayout = QHBoxLayout()
        # 
        # Operator
        #
        self.operatorCombo = QComboBox()
        self.operatorCombo.setToolTip( "Chose the operator type")
        for elm in OPERATOR_VALUES:
            self.operatorCombo.addItem(elm)
        self.operatorCombo.setCurrentIndex(
            utils.findCurrentIndex( self.operatorName, OPERATOR_VALUES))
        self.operatorCombo.activated.connect( self.cb_operatorCombo )
        hLayout.addWidget( QLabel( 'Operator'))
        hLayout.addWidget( self.operatorCombo)
        hLayout.addStretch()
        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()

        #
        # U Initialization
        #
        #self.uInitCombo = QComboBox()
        #self.uInitCombo.setToolTip( "What is U")
        #for elm in U_INIT_VALUES:
        #    self.uInitCombo.addItem( str( elm))
        #self.uInitCombo.setCurrentIndex( 0)
        #self.uInitCombo.activated.connect( self.cb_uInitCombo )
        #hLayout.addWidget( QLabel( 'uInit'))
        #hLayout.addWidget( self.uInitCombo)
        #
        # V Initialization
        #
        self.vInitCombo = QComboBox()
        self.vInitCombo.setToolTip( "What is V")
        for elm in V_INIT_VALUES:
            self.vInitCombo.addItem( str( elm))
        self.vInitCombo.setCurrentIndex(
            utils.findCurrentIndex( self.vInit, V_INIT_VALUES))
        self.vInitCombo.activated.connect( self.cb_vInitCombo )
        hLayout.addWidget( QLabel( 'vInit'))
        hLayout.addWidget( self.vInitCombo)
        #
        # W output
        #
        #self.wOutputCombo = QComboBox()
        #self.wOutputCombo.setToolTip( "What is W")
        #for elm in W_OUTPUT_VALUES:
        #    self.wOutputCombo.addItem( str( elm))
        #self.wOutputCombo.setCurrentIndex(
        #    utils.findCurrentIndex( self.wOutput, W_OUTPUT_VALUES))
        #self.wOutputCombo.activated.connect( self.cb_wOutputCombo )
        #hLayout.addWidget( QLabel( 'wOutput'))
        #hLayout.addWidget( self.wOutputCombo)
        #
        # widthDynOp
        #
        self.widthDynOpCombo = QComboBox()
        self.widthDynOpCombo.setToolTip( "The with of the image")
        for elm in utils.WIDTH_VALUES:
            self.widthDynOpCombo.addItem( str( elm))
        self.widthDynOpCombo.setCurrentIndex(
            utils.findCurrentIndex( self.widthDynOp, utils.WIDTH_VALUES))
        self.widthDynOpCombo.activated.connect( self.cb_widthDynOpCombo )
        hLayout.addWidget( QLabel( 'Width'))
        hLayout.addWidget( self.widthDynOpCombo)
        #
        # sizeWindow
        #
        if self.mode == 'standalone':
            self.sizeDynOpCombo = QComboBox()
            self.sizeDynOpCombo.setToolTip( "The with of the image")
            for elm in utils.SIZE_VALUES:
                self.sizeDynOpCombo.addItem( str( elm))
            self.sizeDynOpCombo.setCurrentIndex(
                utils.findCurrentIndex( self.sizeDynOp, utils.SIZE_VALUES))
            self.sizeDynOpCombo.activated.connect( self.cb_sizeDynOpCombo )
            hLayout.addWidget( QLabel( 'Size'))
            hLayout.addWidget( self.sizeDynOpCombo)
        hLayout.addStretch()
        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()
        #
        # iterationsMax
        #
        self.iterationsMaxSliderLbl = QLabel( "IterationsMax: %d" % self.iterationsMax)
        self.iterationsMaxSliderLbl.setFixedWidth( 250)
        self.iterationsMaxSliderLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hLayout.addWidget( self.iterationsMaxSliderLbl)
        hLayout.addStretch()

        self.iterationsMaxSlider = utils.ArrowAwareSlider(Qt.Horizontal)
        self.iterationsMaxSlider.setToolTip( "Change the number of iterationsMax")
        self.iterationsMaxSlider.setValue( 10)
        
        self.iterationsMaxSlider.arrowPressed.connect( self.cb_iterSliderArrow)
        self.iterationsMaxSlider.valueChanged.connect( self.cb_iterSlider)
        self.iterationsMaxSlider.sliderReleased.connect( self.cb_iterSliderReleased)
        self.iterationsMaxSlider.setMinimum( 0) 
        self.iterationsMaxSlider.setMaximum( 500)
        self.iterationsMaxSlider.setFixedWidth( SLIDER_WIDTH)
        hLayout.addWidget( self.iterationsMaxSlider)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()
        #
        # forever
        #
        self.foreverCb = QCheckBox( "Forever", self)
        self.foreverCb.setToolTip( "Run forever")
        self.foreverCb.setChecked( self.forever == "True")
        self.foreverCb.clicked.connect( self.cb_forever)
        hLayout.addWidget( self.foreverCb)

        #
        # iterated
        #
        self.iteratedLbl = QLabel( "Iterated:") 
        self.iteratedLbl.setFixedWidth( 350)
        #self.iteratedLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hLayout.addWidget( self.iteratedLbl)
        hLayout.addStretch()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # Reaction-Diffusion
        #
        self.reactionLbl = QLabel( "Reaction-Diffusion")
        self.reactionLbl.setToolTip( "n.n.")
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.reactionLbl)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # Feed rate
        #
        self.feedRateLbl = QLabel( "F: %6.4f" % self.feedRate)
        self.feedRateLbl.setFixedWidth( 100) 
        self.feedRateLineEdit = QLineEdit()
        self.feedRateLineEdit.setFixedWidth( 100) 
        self.feedRatePushButton = QPushButton( "Apply")
        self.feedRatePushButton.setToolTip( "Feed rate")
        self.feedRatePushButton.clicked.connect( self.cb_feedRatePushButton)       
        hLayout.addWidget( self.feedRateLbl)
        hLayout.addWidget( self.feedRateLineEdit)
        hLayout.addWidget( self.feedRatePushButton)
        hLayout.addStretch()
        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # Kill rate
        #
        self.killRateLbl = QLabel( "k: %6.4f" % self.killRate)
        self.killRateLbl.setFixedWidth( 100) 
        self.killRateLineEdit = QLineEdit()
        self.killRateLineEdit.setFixedWidth( 100) 
        self.killRatePushButton = QPushButton( "Apply")
        self.killRatePushButton.setToolTip( "Kill rate")
        self.killRatePushButton.clicked.connect( self.cb_killRatePushButton)       
        hLayout.addWidget( self.killRateLbl)
        hLayout.addWidget( self.killRateLineEdit)
        hLayout.addWidget( self.killRatePushButton)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # Du, Diffusion of U
        #
        self.duLbl = QLabel( "Du: %g" % self.du)
        self.duLbl.setFixedWidth( 100) 
        self.duLineEdit = QLineEdit()
        self.duLineEdit.setFixedWidth( 100) 
        self.duPushButton = QPushButton( "Apply")
        self.duPushButton.clicked.connect( self.cb_duPushButton)       
        hLayout.addWidget( self.duLbl)
        hLayout.addWidget( self.duLineEdit)
        hLayout.addWidget( self.duPushButton)
        hLayout.addStretch()
        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # Dv, Diffusion of V
        #
        self.dvLbl = QLabel( "Dv: %g" % self.dv)
        self.dvLbl.setFixedWidth( 100) 
        self.dvLineEdit = QLineEdit()
        self.dvLineEdit.setFixedWidth( 100) 
        self.dvPushButton = QPushButton( "Apply")
        self.dvPushButton.clicked.connect( self.cb_dvPushButton)       
        hLayout.addWidget( self.dvLbl)
        hLayout.addWidget( self.dvLineEdit)
        hLayout.addWidget( self.dvPushButton)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # scale Du/Dv
        #
        self.scaleDuDvCombo = QComboBox()
        self.scaleDuDvCombo.setToolTip( "Common scale for Du and Dv.\nBigger/smaller scales make patterns bigger/smaller")
        for elm in utils.SCALEDUDV_VALUES:
            self.scaleDuDvCombo.addItem(str(elm))
        self.scaleDuDvCombo.setCurrentIndex( 0)
        self.scaleDuDvCombo.activated.connect( self.cb_scaleDuDvCombo )
        temp = QLabel( 'DuDvScale:')
        temp.setFixedWidth( 100) 
        hLayout.addWidget( temp)
        hLayout.addWidget( self.scaleDuDvCombo)
        hLayout.addStretch()
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # ratio Du/Dv
        #
        self.ratioDuDvCombo = QComboBox()
        self.ratioDuDvCombo.setToolTip( "Ratio Du/Dv, change pattern type,\n 4 - more stripes, 1.33 - more chaos")
        for elm in utils.RATIODUDV_VALUES:
            self.ratioDuDvCombo.addItem(str(elm))
        self.ratioDuDvCombo.setCurrentIndex( 0)
        self.ratioDuDvCombo.activated.connect( self.cb_ratioDuDvCombo )
        temp = QLabel( 'DuDvRatio:')
        temp.setFixedWidth( 100) 
        hLayout.addWidget( temp)
        hLayout.addWidget( self.ratioDuDvCombo)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()

        #
        # PresetsRD reaction - diffusion
        #
        self.presetRDCombo = QComboBox()
        self.presetRDCombo.setToolTip( "Preset for reaction-diffusion")
        for elm in sorted(utils.PRESET_RD_VALUES.keys()):
            self.presetRDCombo.addItem(elm)
        self.presetRDCombo.setCurrentIndex( 0)
        self.presetRDCombo.activated.connect( self.cb_presetRDCombo )
        hLayout.addWidget( QLabel( 'PresetRD'))
        hLayout.addWidget( self.presetRDCombo)
        #
        # dt
        #
        self.dtCombo = QComboBox()
        self.dtCombo.setToolTip( "Time interval")
        for elm in DT_VALUES:
            self.dtCombo.addItem( str(elm))
        self.dtCombo.setCurrentIndex(
            utils.findCurrentIndex( self.dt, DT_VALUES))
        self.dtCombo.activated.connect( self.cb_dtCombo )
        hLayout.addWidget( QLabel( 'dt'))
        hLayout.addWidget( self.dtCombo)
        hLayout.addStretch() 
        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()
        
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)

        #
        # Scale-Space
        #
        self.scaleSpaceLbl = QLabel( "Scale-Space")
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.scaleSpaceLbl)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        
        #
        # sigma
        #
        self.sigmaSliderLbl = QLabel( "Sigma: %g" % self.sigma)
        self.sigmaSliderLbl.setFixedWidth( 150)
        self.sigmaSliderLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hLayout.addWidget( self.sigmaSliderLbl)

        self.sigmaSlider = utils.ArrowAwareSlider(Qt.Horizontal)
        self.sigmaSlider.setToolTip( "Controls how wide the blur kernel is")
        self.sigmaSlider.setValue( int( self.sigma*10))
        self.sigmaSlider.valueChanged.connect( self.cb_sigmaSlider)
        self.sigmaSlider.arrowPressed.connect( self.cb_sigmaSliderArrow)
        self.sigmaSlider.sliderReleased.connect( self.cb_sigmaSliderReleased)
        self.sigmaSlider.setMinimum( 0) 
        self.sigmaSlider.setMaximum( SCALE)
        self.sigmaSlider.setFixedWidth( SLIDER_WIDTH)
        hLayout.addWidget( self.sigmaSlider)

        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()
        #
        # alpha
        #
        self.alphaSliderLbl = QLabel( "Alpha: %g" % self.alpha)
        self.alphaSliderLbl.setFixedWidth( 150)
        self.alphaSliderLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hLayout.addWidget( self.alphaSliderLbl)

        self.alphaSlider = utils.ArrowAwareSlider(Qt.Horizontal)
        self.alphaSlider.setToolTip( "Controls how strong the high frequency component is added back\nalpha == 1 classic unsharp mask, \nalpha > 1 aggressive sharpening\nalpha < 1 gentle sharpening")
        self.alphaSlider.setValue( int( self.alpha*10))
        self.alphaSlider.arrowPressed.connect( self.cb_alphaSliderArrow)
        self.alphaSlider.valueChanged.connect( self.cb_alphaSlider)
        self.alphaSlider.sliderReleased.connect( self.cb_alphaSliderReleased)
        self.alphaSlider.setMinimum( 0) 
        self.alphaSlider.setMaximum( SCALE)
        self.alphaSlider.setFixedWidth( SLIDER_WIDTH)
        hLayout.addWidget( self.alphaSlider)

        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()

        #
        # PresetsSS scale - space
        #
        self.presetSSCombo = QComboBox()
        self.presetSSCombo.setToolTip( "presets for scale-space operators")
        for elm in sorted(utils.PRESET_SS_VALUES.keys()):
            self.presetSSCombo.addItem(elm)
        self.presetSSCombo.setCurrentIndex( 0)
        self.presetSSCombo.activated.connect( self.cb_presetSSCombo )
        hLayout.addWidget( QLabel( 'PresetSS'))
        hLayout.addWidget( self.presetSSCombo)
        hLayout.addStretch() 
        row += 1 
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # normLoop
        #
        self.normLoopCb = QCheckBox( "NormLoop", self)
        self.normLoopCb.setToolTip( "If 'True', the normalization is executed with the loop")
        self.normLoopCb.setChecked( self.normLoop == "True")
        self.normLoopCb.clicked.connect( self.cb_normLoop)
        hLayout.addWidget( self.normLoopCb)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
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
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
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
        self.gridLayout.addWidget( self.logWidget, row, col, 1, 2)
        hLayout = QHBoxLayout()

        # rebuild icon
        self._createIcon()

        # force correct placement immediately
        self._positionIcon()

        return

    def _createIcon(self):
        self.icon = QLabel(self.wCentral)
        pm = QPixmap("./DynOpIcon.png").scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
    
    def resizeEvent(self, event):
        super().resizeEvent(event)

        # position relative to central widget
        cw = self.wCentral
        x = cw.width() - self.icon.width() - 20
        y = 5
        self.icon.move(x, y)    

    def on_key_press(self, event):
        print(f"Matplotlib key pressed: {event.key}")

    @pyqtSlot( np.ndarray)
    def displayDynOp( self, img) :
        #print( "%s.displayDynOp, %s" % (self.name, repr( self.viewerMain.updateImage)))
        self.lastImage = img.copy()
        self.viewerMain.updateImage( img)
        return 
        
    @pyqtSlot()
    def redisplay( self):
        #print( "%s.redisplay" % self.name)
        if self.lastImage is not None: 
            self.viewerMain.updateImage( self.lastImage)
        return 

    #
    #  === callbacks
    #


    @pyqtSlot()
    def cb_lastRead( self):
        if self.lastFileRead is None:
            self.logWidget.append( "No file read so far")
            return
        utils.readPng( self.lastFileRead,
                       MBSObj = None, 
                       DynOpObj = self,
                       ColorWidgetObj = self.colorWidget,
                       ColorParsObj = self.colorPars)
        return
    
    @pyqtSlot()
    def cb_clearScreen( self):
        if self.useMPL:
            self.viewerMain.ax.clear()
            self.viewerMain.canvas.draw()
        else:
            self.viewerMain.img.clear()
            
        return 
    @pyqtSlot()
    def cb_geometry( self):

        self.logWidget.append( "Width %d px, Height %d px" %
                               ( self.screen.size().width(), self.screen.size().height()))
        self.logWidget.append( "self.geometry(): %s" % repr( self.geometry()))
        self.logWidget.append( "ViewerMain %s " % self.viewerMain.geometry())

        return

    @pyqtSlot( float, float)
    def cb_FkEvent( self, x, y):
        print( "%s.cb_FkEvent: feedRate %g killRate %g" %
               ( self.name, self.feedRate, self.killRate))
        self.feedRate = y
        self.killRate = x
        self.presetName = "A la carte"
        self.updateGUI()
        self.forever = "True"
        self.foreverCb.setChecked( self.forever == "True")
        self.makeOperatorFunction()
        self.cb_resetUV()
        self.cb_runStop()
        # print( "%s.cb_FkEvent x %g y %g" % (self.name, x, y))
        return

    @pyqtSlot()
    def cb_incrFeedRate( self):
        self.feedRate += 0.0001
        self.viewerFk.labelFk.paintFk( self.feedRate, self.killRate) 
        self.updateGUI()
        self.makeOperatorFunction()
        self.cb_resetUV()
        self.cb_runStop()
        return
    
    @pyqtSlot()
    def cb_decrFeedRate( self):
        self.feedRate -= 0.0001
        self.viewerFk.labelFk.paintFk( self.feedRate, self.killRate) 
        self.updateGUI()
        self.makeOperatorFunction()
        self.cb_resetUV()
        self.cb_runStop()
        return

    @pyqtSlot()
    def cb_incrKillRate( self):
        self.killRate += 0.0001
        self.viewerFk.labelFk.paintFk( self.feedRate, self.killRate) 
        self.updateGUI()
        self.makeOperatorFunction()
        self.cb_resetUV()
        self.cb_runStop()
        return
    
    @pyqtSlot()
    def cb_decrKillRate( self):
        self.killRate -= 0.0001
        self.viewerFk.labelFk.paintFk( self.feedRate, self.killRate) 
        self.updateGUI()
        self.makeOperatorFunction()
        self.cb_resetUV()
        self.cb_runStop()
        return
    
    def cb_places( self):
        self.placesWidget.show()
        return

    def cb_feedRatePushButton( self): 
        self.feedRate = float( self.feedRateLineEdit.text()) 
        self.feedRateLbl.setText( "F: %6.4f" % self.feedRate)
        self.feedRateLineEdit.clear()
        self.viewerFk.label.paintFk( self.feedRate, self.killRate) 
        self.updateGUI()
        return 

    def cb_killRatePushButton( self): 
        self.killRate = float( self.killRateLineEdit.text()) 
        self.killRateLbl.setText( "k: %6.4f" % self.killRate)
        self.killRateLineEdit.clear()
        self.viewerFk.label.paintFk( self.feedRate, self.killRate) 
        self.updateGUI()
        return 

    def cb_duPushButton( self): 
        self.du = float( self.duLineEdit.text()) 
        self.duLbl.setText( "  Du: %6.4f" % self.du)
        self.duLineEdit.clear()
        self.updateGUI()
        return 

    def cb_dvPushButton( self): 
        self.dv = float( self.dvLineEdit.text()) 
        self.dvLbl.setText( "  Du: %6.4f" % self.dv)
        self.dvLineEdit.clear()
        self.updateGUI()
        return 

    def cb_iterSlider( self, i):
        self.iterationsMax = i
        self.forever = "False"
        self.foreverCb.setChecked( self.forever == "True")
        self.iterationsMaxSliderLbl.setText( "IterationsMax: %d" % self.iterationsMax)
        return
    def cb_iterSliderArrow( self, i):
        if self.sliderBusy:
            return 
        self.sliderBusy = True
        self.iterationsMax = i
        self.forever = "False"
        self.foreverCb.setChecked( self.forever == "True")
        #self.iterationsMaxSliderLbl.setText( "IterationsMax: %d" % self.iterationsMax)
        #self.makeOperatorFunction()
        #if self.repeatPtr is not None:
        #    self.repeatPtr()
        #self.sliderBusy = False
        return
    def cb_iterSliderReleased( self):
        if self.sliderBusy:
            return 
        #self.sliderBusy = True
        #self.makeOperatorFunction()
        #if self.repeatPtr is not None:
        #    self.repeatPtr()
        #self.sliderBusy = False
        return
    
    def cb_showDiff( self, i):
        pass
        return

    def mkColorCb( self, i):
        def f():
            self.colorPars.colorMapName = i
            print( "%s.mkColorCb: %s id %d" % 
                   ( self.name, self.colorPars.colorMapName, id( self.colorPars.colorMapName)))
            self.colorPars.rotateColorMapIndex = 0
            if self.colorWidget.cmapLbl is not None:
                self.colorWidget.cmapLbl.setText( "CMAP: %s" % self.colorPars.colorMapName)
            self.viewerMain.setColor()
            self.viewerMain.updateImage( self.dataPtr.dataMandelbrotSet)

            return 
        return f

    def enableWidgets( self):

        #print( "%s.enableWidgets operator %s " % ( self.name, self.operatorName))
        
        if self.operatorName == 'GrayScott':
            self.dtCombo.setEnabled( True)
            self.presetRDCombo.setEnabled( True)
            self.presetSSCombo.setEnabled( False)
            self.feedRateLineEdit.setEnabled( True)
            self.feedRatePushButton.setEnabled( True)
            self.killRateLineEdit.setEnabled( True)
            self.killRatePushButton.setEnabled( True)
            self.duLineEdit.setEnabled( True)
            self.duPushButton.setEnabled( True)
            self.dvLineEdit.setEnabled( True)
            self.dvPushButton.setEnabled( True)
            self.scaleDuDvCombo.setEnabled( True) 
            self.ratioDuDvCombo.setEnabled( True) 
            self.vInitCombo.setEnabled( True)
            #self.uInitCombo.setEnabled( True)
            #self.wOutputCombo.setEnabled( True)
            self.forever = "False"
            self.foreverCb.setChecked( self.forever == "True")
            self.foreverCb.setEnabled( True)
            self.sigmaSlider.setEnabled( False)
            self.alphaSlider.setEnabled( False)
            self.normLoopCb.setEnabled( False)
        elif self.operatorName == 'GrayScottPython':
            self.dtCombo.setEnabled( True)
            self.presetRDCombo.setEnabled( True)
            self.presetSSCombo.setEnabled( False)
            self.feedRateLineEdit.setEnabled( True)
            self.feedRatePushButton.setEnabled( True)
            self.killRateLineEdit.setEnabled( True)
            self.killRatePushButton.setEnabled( True)
            self.duLineEdit.setEnabled( True)
            self.duPushButton.setEnabled( True)
            self.dvLineEdit.setEnabled( True)
            self.dvPushButton.setEnabled( True)
            self.scaleDuDvCombo.setEnabled( True) 
            self.ratioDuDvCombo.setEnabled( True) 
            self.vInitCombo.setEnabled( True)
            #self.uInitCombo.setEnabled( True)
            #self.wOutputCombo.setEnabled( True)
            self.forever = "False"
            self.foreverCb.setChecked( self.forever == "True")
            self.foreverCb.setEnabled( True)
            self.sigmaSlider.setEnabled( True)
            self.alphaSlider.setEnabled( False)
            self.normLoopCb.setEnabled( False)
        else:
            self.dtCombo.setEnabled( False)
            self.presetRDCombo.setEnabled( False)
            self.presetSSCombo.setEnabled( True)
            self.feedRateLineEdit.setEnabled( False)
            self.feedRatePushButton.setEnabled( False)
            self.killRateLineEdit.setEnabled( False)
            self.killRatePushButton.setEnabled( False)
            self.duLineEdit.setEnabled( False)
            self.duPushButton.setEnabled( False)
            self.dvLineEdit.setEnabled( False)
            self.dvPushButton.setEnabled( False)
            self.scaleDuDvCombo.setEnabled( False) 
            self.ratioDuDvCombo.setEnabled( False) 
            self.vInitCombo.setEnabled( True)
            #self.uInitCombo.setEnabled( False)
            #self.wOutputCombo.setEnabled( False)
            self.forever = "False"
            self.foreverCb.setChecked( self.forever == "True")
            self.foreverCb.setEnabled( True)
            self.sigmaSlider.setEnabled( True)
            self.alphaSlider.setEnabled( True)
            self.normLoopCb.setEnabled( True)
        return 

    def cb_operatorCombo( self, i): 
        self.operatorName = OPERATOR_VALUES[i]
        self.enableWidgets()
        self.makeOperatorFunction()
        return 

    def cb_scaleDuDvCombo( self, i):
        self.scaleDuDv = utils.SCALEDUDV_VALUES[i]
        self.du = DU_DEFAULT
        self.du *= self.scaleDuDv
        self.dv = self.du/self.ratioDuDv
        self.duLbl.setText( "  Du: %g" % self.du)
        self.dvLbl.setText( "  Dv: %g" % self.dv)
        self.makeOperatorFunction()
        return
    
    def cb_ratioDuDvCombo( self, i):
        self.ratioDuDv = utils.RATIODUDV_VALUES[i]
        self.du = 0.16
        self.dv = 0.08
        self.du *= self.scaleDuDv
        self.dv = self.du/self.ratioDuDv
        self.duLbl.setText( "  Du: %g" % self.du)
        self.dvLbl.setText( "  Dv: %g" % self.dv)
        self.makeOperatorFunction()
        return
    
    def cb_sigmaSlider( self, i):
        # 0 10
        self.sigma = float(i)/10.
        self.sigmaSliderLbl.setText( "Sigma: %g" % self.sigma)
        return
    def cb_sigmaSliderReleased( self):
        self.makeOperatorFunction()
        #self.parent.filterMandelbrotSet()
        #self.parent.showMandelbrotSet()
        return
    def cb_sigmaSliderArrow( self, i):
        if self.arrowSliderBusy:
            return 
        self.sigma = float(i)/10.
        self.sigmaSliderLbl.setText( "Sigma: %g" % self.sigma)
        self.arrowSliderBusy = True
        self.makeOperatorFunction()
        #self.parent.filterMandelbrotSet()
        #self.parent.showMandelbrotSet()
        self.arrowSliderBusy = False
        return

    def cb_alphaSlider( self, i):
        # 0 10
        self.alpha = float(i)/10.
        self.alphaSliderLbl.setText( "Alpha: %g" % self.alpha)
        return
    def cb_alphaSliderArrow( self, i):
        if self.arrowSliderBusy:
            return 
        self.alpha = float(i)/10.
        self.alphaSliderLbl.setText( "Sigma: %g" % self.alpha)
        self.arrowSliderBusy = True
        self.makeOperatorFunction()
        #self.parent.filterMandelbrotSet()
        #self.parent.showMandelbrotSet()
        self.arrowSliderBusy = False
        return
    def cb_alphaSliderReleased( self):
        self.makeOperatorFunction()
        #self.parent.filterMandelbrotSet()
        #self.parent.showMandelbrotSet()
        return

    def cb_normLoop( self, i):
        if i:
            self.normLoop = "True"
        else:
            self.normLoop = "False"
        self.makeOperatorFunction()
        #self.parent.filterMandelbrotSet()
        #self.parent.showMandelbrotSet()
        return

    def cb_forever( self, i):
        if i:
            self.forever = "True"
        else:
            self.forever = "False"
        return

    def cb_uInitCombo( self, i):
        self.uInit = U_INIT_VALUES[i]
        return

    def cb_vInitCombo( self, i):
        self.vInit = V_INIT_VALUES[ i]
        if self.mode != 'standalone':
            data = self.dataPtr.dataMandelbrotSet.copy()
        else:
            data = np.ones( ( self.widthDynOp, self.widthDynOp))

        self.U_in, self.V_in = self.prepareUandV( data, self.uInit, self.vInit)

        V_in = np.clip( self.V_in * 1023, 0, 1023).astype(np.float32)
        self.dataPtr.dataMandelbrotSet = V_in.copy()
        self.frameReady.emit( self.dataPtr.dataMandelbrotSet)

        return

    def cb_wOutputCombo( self, i):
        self.wOutput = W_OUTPUT_VALUES[ i]
        return

    def cb_widthDynOpCombo( self, i):
        self.widthDynOp = utils.WIDTH_VALUES[ i]
        self.makeOperatorFunction()
        self.cb_resetUV()
        return

    def cb_sizeDynOpCombo( self, i):
        self.sizeDynOp = utils.SIZE_VALUES[i]
        if self.sizeDynOp == 'Small': 
            self.figSize = self.figSizeSmall
        elif self.sizeDynOp == 'Medium': 
            self.figSize = self.figSizeMedium
        elif self.sizeDynOp == 'Big': 
            self.figSize = self.figSizeBig
        else:
            self.figSize = self.figSizeLarge

        self.viewerMain.resize( int( self.figSize[0]), int( self.figSize[1]))
        
        return
    
    def cb_clear( self):
        self.logWidget.clear()
        return

    def cb_close( self):

        if self.mode == 'standalone':
            #print( "%s.cb_close: calling self.viewerMain.close()" % self.name)
            if self.mode == 'standalone':
                self.viewerDebugColoring.close()
            self.viewerMain.close()
            self.viewerFk.close()
            self.close()
            if self.placesWidget is not None: 
                self.placesWidget.close()
        else: 
            self.hide()

        return

    def setDefaults( self):
        self.widthDynOp = utils.WIDTH_VALUES[0]
        self.debugColoring = "False"
        self.updateGUI()
        return 

    @pyqtSlot( bool)
    def cb_debugColoring( self, i):
        if not self.useMPL:
            utils.message( None, "%s.cb_debugColoring: only with MPL" % ( self.name))
            return 
        if i:
            self.setDebugColoring.emit( True)
            self.debugColoring = "True" 
            self.viewerDebugColoring.showMPL()
            self.viewerDebugColoring.show()
        else:
            self.setDebugColoring.emit( False)
            self.debugColoring = "False"
            self.viewerDebugColoring.hide()

        return 
    
    def cb_reset( self):
        self.setDefaults()
        self.updateGUI()
        return

    def loadPreset(self, name):
        #print( "%s.loadPreset %s" % ( self.name, name))
        self.logWidget.append( "%s.loadPreset %s" % ( self.name, name))
        if name == 'A la carte':
            self.logWidget.append( "%s.loadPreset-1 %s" % ( self.name, name))
            self.logWidget.append( "Loading 'A la carte' F %g, k %g, iterationsMax %d, dt %g" %
                                   (self.feedRate, self.killRate, self.iterationsMax, self.dt))
            return
        
        if name in utils.PRESET_RD_VALUES:
            self.loadPresetRD( name)
        elif name in utils.PRESET_SS_VALUES:
            self.loadPresetSS( name)
        else:
            temp = QMessageBox()
            temp.question(self,'', 
                          "%s.loadPreset: not found %s" % ( self.name, name ), 
                          temp.Ok )
            return
        #
        # disable 'forever; because the preset contains iterationsMax
        #
        self.forever = "False"
        self.foreverCb.setChecked( self.forever == "True")

        #self.makeOperatorFunction()
        #self.parent.showMandelbrotSet()

        return

    def loadPresetSS(self, name):
        p = utils.PRESET_SS_VALUES[name]
        self.logWidget.append( "Loading-SS %s %s" % (name, repr( p)))

        self.sigma = p["Sigma"]
        self.sigmaSlider.setValue( int( self.sigma*10.))
        self.alpha = p["Alpha"]
        self.alphaSlider.setValue( int( self.alpha*10.))
        self.normLoop = p["NormLoop"]
        self.normLoopCb.setChecked( self.normLoop == "True")
        self.iterationsMax = p["IterationsMax"]
        self.iterationsMaxSliderLbl.setText( "IterationsMax: %d" % self.iterationsMax)
        self.iterations = 0
        self.iteratedLbl.setText( "Iterated: %d" %  (self.iterations))

        self.updateGUI()
        
        return
    
    def loadPresetRD(self, name):
        p = utils.PRESET_RD_VALUES[name][ 'params']
        self.logWidget.append( "Loading-RD %s %s" % (name, repr( p)))
        self.feedRate = p["F"]
        self.killRate = p["k"]
        self.viewerFk.labelFk.paintFk( self.feedRate, self.killRate) 
        self.du = 0.16 # p["Du"]
        self.scaleDuDv = self.du/DU_DEFAULT
        self.ratioDuDv = self.du/self.dv
        self.dv = 0.08 # p["Dv"]
        temp = self.dv*SCALE/DV_MAX
        
        self.dt = p["dt"]
        self.dtCombo.setCurrentIndex(
            utils.findCurrentIndex( self.dt, DT_VALUES))
        
        self.iterationsMax = p["IterationsMax"]
        self.iterationsMaxSliderLbl.setText( "IterationsMax: %d" % self.iterationsMax)

        self.iterations = 0
        self.iteratedLbl.setText( "Iterated: %d" %  (self.iterations))

        self.updateGUI()
        
        return

    def cb_presetRDCombo(self, i):
        name = sorted(utils.PRESET_RD_VALUES.keys())[i]
        if name == "A la carte":
            temp = QMessageBox()
            temp.question(self,'', 
                          "loadPresetRD: Click into the F/k-map to select 'A la carte'", 
                          temp.Ok )
            return 
        self.presetName = sorted(utils.PRESET_RD_VALUES.keys())[i]
        
        self.loadPresetRD( self.presetName)
        self.makeOperatorFunction()

        return

    def cb_dtCombo(self, i):
        self.dt = float( DT_VALUES[i])
        self.makeOperatorFunction()
        return
    
    def cb_presetSSCombo(self, i):
        self.presetName = sorted(utils.PRESET_SS_VALUES.keys())[i]
        self.loadPreset( self.presetName) 
        self.makeOperatorFunction()
        return

    def cb_deleteOperator(self):
        self.operatorFunction = None
        if self.repeatPtr is not None:
            self.repeatPtr()
        return 

    def catchFrameReady( self, data):
        if data.shape[0] == 10: 
            print( "operator.catchFrameReady: data %s" % repr( data))
        
        if self.mode == 'standalone':
            self.displayDynOp( data)
        else:
            self.parent.displayDynOp( data)
        return


    def catchLogMessage( self, msg):
        self.logWidget.append( msg)
        #print( "%s.catchLogMsg: %s" % ( self.name, msg))
        return
    
    def catchIterationInfo( self, nIter, elapsed, diff):
        self.iteratedLbl.setText( "Iterated: %d, fps: %5.0f, diff: %.2g" %
                                  (nIter, elapsed, diff))

        return 
    
    def invokeTestFunction( self):
        while True:
            time.sleep( 1)
            print( "testFunction busy")
            self.worker.frameReady.emit( self.dataPtr.dataMandelbrotSet)
            if self.stopRequested:
                print( "worker found stopRequested")
                self.parent.stopRequested = False
                break
        return

    def cb_resetUV( self):

        if self.mode != 'standalone':
            if self.repeatPtr is not None:
                temp = self.dataPtr.execDynOp
                self.dataPtr.execDynOp = "False"
                self.repeatPtr()
                self.dataPtr.execDynOp = temp
            data = self.dataPtr.dataMandelbrotSet.copy()
        else:
            data = np.ones( ( self.widthDynOp, self.widthDynOp))
            
        self.U_in, self.V_in = self.prepareUandV( data, self.uInit, self.vInit)

        self.iterations = 0
        self.catchIterationInfo( self.iterations, 0., 0.)
        
        if self.wOutput == "U_in":
            self.dataPtr.dataMandelbrotSet = self.U_in.copy()
        else:
            self.dataPtr.dataMandelbrotSet = self.V_in.copy()
            
        self.dataPtr.dataMandelbrotSet = \
            np.clip( self.dataPtr.dataMandelbrotSet * 1023, 0, 1023).astype(np.float32)
        self.frameReady.emit( self.dataPtr.dataMandelbrotSet)
        self.UVempty = True
        return
    
    def cb_runStop(self):
        """
        if running stops the operator, otherwise starts the operator
        """
        #print( "%s.cb_runStop: begin" % self.name)

        #
        # if we pressed "Run" in the DynOp widget, we enable "execDynOp" in MBS 
        # this way the png file will be filled with DynOp parameters
        #
        if self.mode != 'standalone':
            self.dataPtr.execDynOp = "True"
            self.dataPtr.execDynOpCb.setChecked( self.dataPtr.execDynOp == "True")
        
        if (self.thread is not None) and self.thread.isRunning():
            print( "%s.cb_runStop: is running, calling stopOp" % self.name) 
            self.stopOp()
            return 

        #print( "%s.cb_runStop: is not running, calling startOp" % self.name) 
        self.startOp()
        return 

    def stopOp( self): 
        #print( "%s.stopOp: begin" % self.name) 
        if (self.thread is not None) and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
            if self.mode != 'standalone':
                self.parent.DynOpPb.setStyleSheet("background-color:%s" % self.backgroundColor)
            self.runStopPb.setStyleSheet("background-color:%s" % self.backgroundColor)
            self.iteratedLbl.setStyleSheet("background-color:%s" % self.backgroundColor)
            self.runStopPb.setText( "Run")

            if self.iterations > self.iterationsMax:
                self.iterationsMax = self.iterations
            self.updateGUI()

        return

    def startOp( self):

        #print( "%s.startOp" % self.name) 
        self.makeOperatorFunction()
        self.worker = DynamicOperatorWorker( self, self.operatorFunction)
        self.thread = QThread()
        self.worker.moveToThread( self.thread)
        self.worker.finished.connect( self.thread.quit)
        self.thread.started.connect( self.worker.step)
        self.thread.start()
        if self.mode != 'standalone':
            self.parent.DynOpPb.setStyleSheet("background-color:lightblue")
        self.iteratedLbl.setStyleSheet("background-color:lightblue")
        self.runStopPb.setStyleSheet("background-color:lightblue")
        self.runStopPb.setText( "Stop") 

        return

    def catchFinished( self):
        #print( "%s.catchFinished: " % self.name)
        self.iteratedLbl.setStyleSheet("background-color:%s" % self.backgroundColor)
        self.runStopPb.setStyleSheet("background-color:%s" % self.backgroundColor)
        if self.mode != "standalone": 
            self.parent.DynOpPb.setStyleSheet("background-color:%s" % self.backgroundColor)
        self.runStopPb.setText( "Run")
        
        return

    
    def cb_runOp( self):
        """
        called from engine.calcMandelbrotSetCythonTiled
        """
        self.cb_resetUV()
        self.updateGUI()
        self.makeOperatorFunction()
        self.worker = DynamicOperatorWorker( self, self.operatorFunction)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.step)
        self.worker.finished.connect( self.thread.quit)
        self.thread.start()
        
        if self.mode != 'standalone':
            self.parent.DynOpPb.setStyleSheet("background-color:lightblue")
        self.runStopPb.setStyleSheet("background-color:lightblue")
        self.iteratedLbl.setStyleSheet("background-color:lightblue")
        self.runStopPb.setText( "Stop") 

        # there is also isFinished()
        while self.thread.isRunning():
            self.app.processEvents()
            time.sleep( 0.1)
            
        return

    def cb_switch( self):

        if self.useMPL:
            self.useMPL = False
            self.colorWidget.toPG()
            self.switchPb.setText( "MPL")
            self.viewerMain.showPG()
        else:
            self.useMPL = True
            self.colorWidget.toMPL()
            self.switchPb.setText( "PG")
            self.viewerMain.showMPL()

        self.viewerMain.setGeometry( 50, 50, self.figSize[0], self.figSize[1])
        self.viewerMain.setWindowFlags(Qt.Window)
        self.viewerMain.show()

        self.frameReady.emit( self.dataPtr.dataMandelbrotSet)
        
        return
    
    def cb_makeOperatorFunction(self):
        self.makeOperatorFunction()
        #self.parent.showMandelbrotSet()
        return

    def makeOperatorFunction(self):
        
        #print("%s.makeOperatorFunction %s" % (self.name, self.operatorName))
        
        if self.operatorName == "GrayScott":
            if self.mode != 'standalone':
                data = self.dataPtr.dataMandelbrotSet.copy()
            else:
                data = np.ones( ( self.widthDynOp, self.widthDynOp))
            F = self.feedRate
            k = self.killRate
            Du = self.du
            Dv = self.dv
            dt = self.dt
            uInit = self.uInit
            vInit = self.vInit
            nIter = 1
            if self.UVempty:
                self.iterations = 0
                self.U_in, self.V_in = self.prepareUandV( data, uInit, vInit)
                #print( "%s.makeOpFunc data %s V_in %s" %
                #       ( self.name, repr( data.shape), repr( self.V_in.shape)))
            else: 
                pass
            def operatorFunction( U_in, V_in, nIter):
                return self.grayScottWrapper( U_in, V_in, F, k, Du, Dv,
                                              dt, nIter)
            self.operatorFunction = operatorFunction
            
        elif self.operatorName == "GrayScottPython": 
            if self.mode != 'standalone':
                data = self.dataPtr.dataMandelbrotSet.copy()
            else:
                data = np.ones(( self.widthDynOp, self.widthDynOp))
            F = self.feedRate
            k = self.killRate
            sigma = self.sigma
            Du = self.du
            Dv = self.dv
            normLoop = self.normLoop
            nIter = 1
            uInit = self.uInit
            vInit = self.vInit
            if self.UVempty:
                self.iterations = 0
                self.U_in, self.V_in = self.prepareUandV( data, uInit, vInit)
            def operatorFunction( U_in, V_in, nIter):
                return self.grayScottPython( U_in, V_in, sigma, F, k, Du, Dv, 
                                              normLoop, nIter)
            self.operatorFunction = operatorFunction
            
        elif self.operatorName == "AntiDiffusionV1": 
            if self.mode != 'standalone':
                data = self.dataPtr.dataMandelbrotSet.copy()
            else:
                data = np.ones(( self.widthDynOp, self.widthDynOp))
            sigma = self.sigma
            alpha = self.alpha
            normLoop = self.normLoop
            nIter = 1
            uInit = self.uInit
            vInit = self.vInit
            if self.UVempty:
                self.iterations = 0
                self.U_in, self.V_in = self.prepareUandV( data, uInit, vInit)
            def operatorFunction( U_in, V_in, nIter):
                temp = self.antiDiffusionV1Wrapper( U_in, V_in,
                                                    sigma, alpha, nIter,
                                                    int( normLoop == "True"))
                return temp
            self.operatorFunction = operatorFunction

        elif self.operatorName == "AntiDiffusionV2": 
            if self.mode != 'standalone':
                data = self.dataPtr.dataMandelbrotSet.copy()
            else:
                data = np.ones(( self.widthDynOp, self.widthDynOp))
            sigma = self.sigma
            alpha = self.alpha
            normLoop = self.normLoop
            nIter = 1
            uInit = self.uInit
            vInit = self.vInit
            if self.UVempty:
                self.iterations = 0
                self.U_in, self.V_in = self.prepareUandV( data, uInit, vInit)
            def operatorFunction( U_in, V_in, nIter):
                temp = self.antiDiffusionV2Wrapper( U_in, V_in,
                                                    sigma, alpha, nIter,
                                                    int( normLoop == "True"))
                return temp
            self.operatorFunction = operatorFunction
            
        elif self.operatorName == "AntiDiffusionPython": 
            if self.mode != 'standalone':
                data = self.dataPtr.dataMandelbrotSet.copy()
            else:
                data = np.ones(( self.widthDynOp, self.widthDynOp))
            sigma = self.sigma
            alpha = self.alpha
            normLoop = self.normLoop
            nIter = 1
            uInit = self.uInit
            vInit = self.vInit
            if self.UVempty:
                self.iterations = 0
                self.U_in, self.V_in = self.prepareUandV( data, uInit, vInit)
                #self.U_in = np.clip( self.U_in * 1023, 0, 1023).astype(np.float32)
                #self.V_in = np.clip( self.V_in * 1023, 0, 1023).astype(np.float32)
                
            def operatorFunction( U_in, V_in, nIter):
                return self.antiDiffusionPython( U_in, V_in,
                                                 sigma, alpha, nIter,
                                                 int( normLoop == "True"))
            self.operatorFunction = operatorFunction
            
        elif self.operatorName == "Shock": 
            if self.mode != 'standalone':
                data = self.dataPtr.dataMandelbrotSet.copy()
            else:
                data = np.ones(( self.widthDynOp, self.widthDynOp))
            sigma = self.sigma
            alpha = self.alpha
            normLoop = self.normLoop
            nIter = 1
            uInit = self.uInit
            vInit = self.vInit
            if self.UVempty:
                self.iterations = 0
                self.U_in, self.V_in = self.prepareUandV( data, uInit, vInit)
            def operatorFunction( U_in, V_in, nIter):
                return self.shock( U_in, V_in, sigma, alpha, nIter, normLoop)
            self.operatorFunction = operatorFunction
            
        elif self.operatorName == "ShockOsherRudin": 
            if self.mode != 'standalone':
                data = self.dataPtr.dataMandelbrotSet.copy()
            else:
                data = np.ones(( self.widthDynOp, self.widthDynOp))
            sigma = self.sigma
            alpha = self.alpha
            normLoop = self.normLoop
            nIter = 1
            uInit = self.uInit
            vInit = self.vInit
            if self.UVempty:
                self.iterations = 0
                self.U_in, self.V_in = self.prepareUandV( data, uInit, vInit)
            def operatorFunction( U_in, V_in, nIter):
                return self.shockOsherRudin( U_in, V_in, sigma, alpha, nIter, normLoop)
            self.operatorFunction = operatorFunction
        return 


    
    def grayScottWrapper( self, U_in, V_in, F, k, Du, Dv, dt, nIter): 
        """ 
        data can be MBS
        """
        #print( "OpFunc: GrayScott U_in %s Y_in %s F: %g k: %g du: %g dv: %g nIter: %d dt: %g" %
        #       (  repr( U_in.shape), repr( V_in.shape), F, k, Du, Dv, nIter, dt))

        if U_in is None or V_in is None:
            print( "GrayScottWrapper: U_in or V_in are None, exit")
            sys.exit( 255)
        
            
        U_in, V_in = dynamicOperatorsCython.grayScott( U_in, V_in,
                                                       Du, Dv, F, k, nIter, self.dt)
        return U_in, V_in

    def grayScottPython( self, U_in, V_in, sigma, F, k, Du, Dv,
                         normLoop, nIter):

        self.worker.logMessage.emit( "OpFunc: GrayScottPython, sigma %g F: %g k: %g du: %g dv: %g it: %d" %
               ( sigma, F, k, Du, Dv, nIter))

        for i in range( nIter):
            
            U_blur = gaussian_filter( U_in, sigma=sigma)
            V_blur = gaussian_filter( V_in, sigma=sigma)

            UVV = U_in * V_in * V_in

            U_in = U_in + Du * (U_blur - U_in) - UVV + F * (1 - U_in)
            V_in = V_in + Dv * (V_blur - V_in) + UVV - (F + k) * V_in

            if normLoop == "True":
                U_in = np.clip(U_in, 0, 1)
                V_in = np.clip(V_in, 0, 1)

        return U_in, V_in
    
    def antiDiffusionV1Wrapper( self, U_in, V_in, sigma, alpha, iterations, normLoop):
        data = V_in.copy().astype(np.float64)
        data = 1023.*(data - data.min()) / (data.max() - data.min())

        temp  = dynamicOperatorsCython.antiDiffusionV1( data.astype( np.float64),
                                                        sigma, alpha, iterations,
                                                        int( normLoop == "True"))
        temp = 1023.*(temp - temp.min()) / (temp.max() - temp.min())
        # Convert back to uint8 only at the end
        self.V_in = temp.copy()
        #temp = np.clip( temp * 1023, 0, 1023).astype(np.float32)
        return temp, temp

    def antiDiffusionV2Wrapper( self, U_in, V_in, sigma, alpha, iterations, normLoop):
        data = V_in.copy().astype(np.float64)
        data = 1023.*(data - data.min()) / (data.max() - data.min())
        
        temp  = dynamicOperatorsCython.antiDiffusionV2( data.astype( np.float64),
                                                        sigma, alpha, iterations,
                                                        int( normLoop == "True"))
        # Convert back to uint8 only at the end
        #self.V_in = temp.copy()
        return temp.astype(np.uint8), temp.astype(np.uint8)
    
    def antiDiffusionPython(self, U_in, V_in, sigma, alpha, nIter, normLoop):
        data = V_in.copy().astype(np.float64)
        data = 1023.*(data - data.min()) / (data.max() - data.min())

        for i in range( nIter):

            blurred = gaussian_filter(data, sigma=(sigma, sigma))

            # Sharpening in float64
            data = data + alpha * (data - blurred)

            # Normalize inside loop if requested
            if normLoop == 1:
                dmin = data.min()
                dmax = data.max()
                data = (data - dmin) / (dmax - dmin) * 255.0

        # Final normalization if normLoop == 0
        if normLoop == 0:
            dmin = data.min()
            dmax = data.max()
            data = (data - dmin) / (dmax - dmin) * 255.0

        # Convert back to uint8 only at the end
        #self.V_in = data.copy()
        #return data.astype(np.uint8), data.astype(np.uint8)
        return data.astype( np.float32), data.astype( np.float32)

    def shock( self, U_in, V_in, sigma, alpha, nIter, normLoop):

        data = V_in.copy().astype(np.float64)
        data = 1023.*(data - data.min()) / (data.max() - data.min())

        #data = V_in
        for i in range( nIter):
            # Smooth version of the image
            blurred = gaussian_filter(data, sigma=sigma)

            # Laplacian approximation (second derivative)
            lap = blurred - data

            # Gradient magnitude approximation (first derivative)
            grad = np.abs(data - blurred)

            # Shock update step
            data = data - alpha * np.sign(lap) * grad

            # Optional: nonlinear normalization inside loop
            if normLoop == "True":
                BS_norm = (data - data.min()) / (data.max() - data.min())
                data = (BS_norm * 255).astype(np.uint8)

        if self.normLoop == "False": 
            BS_norm = (data - data.min()) / (data.max() - data.min())
            data = (BS_norm * 255).astype(np.uint8)

        return data, data

        
    def shockOsherRudin( self, U_in, V_in, sigma, alpha, nIter, normLoop):

        data = V_in.copy().astype(np.float64)
        data = 1023.*(data - data.min()) / (data.max() - data.min())

        for i in range( nIter):
            # Smooth version of the image
            blurred = gaussian_filter(data, sigma=sigma)

            # First derivative (gradient magnitude)
            grad = np.abs(data - blurred)

            # Second derivative (Laplacian sign)
            lap = blurred - data
            s = np.sign(lap)

            # Osher–Rudin shock update
            data = data - alpha * s * grad

            # Optional: normalize inside loop for nonlinear behavior
            if normLoop == "True":
                BS_norm = (data - data.min()) / (data.max() - data.min())
                data = (BS_norm * 255).astype(np.uint8)

        if self.normLoop == "False": 
            BS_norm = (data - data.min()) / (data.max() - data.min())
            data = (BS_norm * 255).astype(np.uint8)
                
        return data, data
    
    def prepareUandV( self, base, uInit, vInit):

        w = base.shape[0]

        # Initialfelder
        
        if uInit == "Ones":
            U_in = np.ones( base.shape, dtype=np.float32)
        elif uInit == "MBS":
            U_in = base.copy()
        elif uInit == "Squares3":
            U_in = np.zeros( base.shape, dtype=np.float32)
            U_in = utils.squares( U_in, 3)

        if vInit == "Ones":
            V_in = np.ones( base.shape, dtype=np.float32)
        elif vInit == "MBS":
            V_in = base.copy().astype(np.float32)
            V_in = V_in/1023.
            #V_in = (V_in - V_in.min()) / (V_in.max() - V_in.min()) 
        elif vInit == "Circle1":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.circles( V_in, 1)
        elif vInit == "Circles3":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.circles( V_in, 3)
        elif vInit == "Circles5":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.circles( V_in, 5)
        elif vInit == "Circles15":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.circles( V_in, 15)
        elif vInit == "Circles25":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.circles( V_in, 25)
        elif vInit == "Circles50":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.circles( V_in, 50)
        elif vInit == "Circles70":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.circles( V_in, 70)
        elif vInit == "Squares3":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.squares( V_in, 3)
        elif vInit == "Square1":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.squares( V_in, 1)
        elif vInit == "Squares3":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.squares( V_in, 3)
        elif vInit == "Squares10":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.squares( V_in, 10)
        elif vInit == "Squares20":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.squares( V_in, 20)
        elif vInit == "Squares50":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.squares( V_in, 50)
        elif vInit == "Squares70":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.squares( V_in, 70)
        elif vInit == "Squares100":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in = utils.squares( V_in, 100)
        elif vInit == "LineSeed":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in[int(w/2):int(w/2 + 5),int( w/2):int(w/2+50)] = 0.5
        elif vInit == "MicroSeed":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in[int(w/2):int(w/2 + 2),int( w/2):int(w/2 + 2)] = 0.5
        elif vInit == "MicroSeed3":
            V_in = np.zeros( base.shape, dtype=np.float32)
            V_in[int(w/2):int(w/2 + 5),int( w/2):int(w/2 + 5)] = 0.5
            V_in[int(w/2 + 7):int(w/2 + 12),int( w/2 + 7):int(w/2 + 12)] = 0.5
            V_in[int(w/2 + 7):int(w/2 + 12),int( w/2 -12):int(w/2 - 2)] = 0.5

        if V_in.shape[0] == 10: 
            print( "prepareUandV: U %s" % repr( U_in))
            print( "prepareUandV: V %s" % repr( V_in))
            
        return U_in, V_in

    #
    # === callbacks END
    #
    def cb_store( self): 
        #
        utils.writePng( midFix = None,
                        prefix = "DynOp", 
                        DynOpObj = self,
                        MBSObj = self.parent, 
                        ColorParsObj = self.colorPars)

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
                        prefix = "DynOpN", 
                        DynOpObj = self,
                        MBSObj = self.parent, 
                        ColorParsObj = self.colorPars)
        return 
        
    def extractParameters( self, hsh):

        print( "")
        print( "Reading DynamicOperator parameters")
        try: 
            del hsh[ 'operatorFunction']
        except:
            pass
        #
        # read PGDynamicOperators parameters
        #
        self.operatorName = 'GrayScott'
        try: 
            self.operatorName = hsh[ 'operatorName']
            del hsh[ 'operatorName']
        except:
            pass
        print( "  operatorName: %s " % self.operatorName)
        
        self.widthDynOp = 500
        try: 
            self.widthDynOp = int( hsh[ 'widthDynOp'])
            del hsh[ 'widthDynOp']
        except:
            pass
        print( "  widthDynOp: %d " % self.widthDynOp)
        
        self.iterations = 10000
        try: 
            self.iterations = int( hsh[ 'iterations'])
            del hsh[ 'iterations']
        except:
            pass
        print( "  iterations: %d " % self.iterations)

        self.iterationsMax = 10000
        try: 
            self.iterationsMax = int( hsh[ 'iterationsMax'])
            del hsh[ 'iterationsMax']
        except:
            pass
        print( "  iterationsMax: %d " % self.iterationsMax)
        
        self.feedRate = 0.032
        try:
            self.feedRate = float( hsh[ 'feedRate'])
            del hsh[ 'feedRate']
        except:
            pass
        print( "  feedRate: %g " % self.feedRate)
        
        self.killRate = 0.0576
        try:
            self.killRate = float( hsh[ 'killRate'])
            del hsh[ 'killRate']
        except:
            pass
        print( "  killRate: %g " % self.killRate)
        
        self.du = 0.16
        try:
            self.du = float( hsh[ 'du'])
            del hsh[ 'du']
        except:
            pass
        print( "  du: %g " % self.du)
        
        self.dv = 0.08
        try:
            self.dv = float( hsh[ 'dv'])
            del hsh[ 'dv']
        except:
            pass
        print( "  dv: %g " % self.dv)

        self.scaleDuDv = 1
        try:
            self.scaleDuDv = float( hsh[ 'scaleDuDv'])
            del hsh[ 'scaleDuDv']
        except:
            pass
        print( "  scaleDuDv: %g " % self.scaleDuDv)
        
        self.ratioDuDv = 2
        try:
            self.ratioDuDv = float( hsh[ 'ratioDuDv'])
            del hsh[ 'ratioDuDv']
        except:
            pass
        print( "  ratioDuDv: %g " % self.ratioDuDv)
        
        self.dt = 0.5
        try:
            self.dt = float( hsh[ 'dt'])
            del hsh[ 'dt']
        except:
            pass
        print( "  dt: %g " % self.dt)

        self.sigma = 1
        try:
            self.sigma = float( hsh[ 'sigma'])
            del hsh[ 'sigma']
        except:
            pass
        print( "  sigma: %g " % self.sigma)

        self.alpha = 0.5
        try:
            self.alpha = float( hsh[ 'alpha'])
            del hsh[ 'alpha']
        except:
            pass
        print( "  alpha: %g " % self.alpha)
        
        self.forever = "False"
        try:
            self.forever = hsh[ 'forever']
            del hsh[ 'forever']
        except:
            pass
        #
        # reading a png we don't want to start a run-forever
        #
        self.forever = "False"
        print( "  forever: %s (enforced)" % self.forever)
        
        self.presetName = 'Delta (Turing patterns)'
        try: 
            self.presetName = hsh[ 'presetName']
            del hsh[ 'presetName']
        except:
            pass
        print( "  presetName: %s" % self.presetName)

        self.uInit = 'Ones'
        try:
            self.uInit = hsh[ 'uInit']
            del hsh[ 'uInit']
        except:
            pass
        print( "  uInit: %s" % self.uInit)
        
        self.vInit = 'Squares50'
        try:
            self.vInit = hsh[ 'vInit']
            del hsh[ 'vInit']
        except:
            pass
        print( "  vInit: %s" % self.vInit)
        
        self.normLoop = "True"
        try:
            self.normLoop = hsh[ 'normLoop']
            del hsh[ 'normLoop']
        except:
            pass
        print( "  normLoop: %s" % self.normLoop)
        
        return
    
    def cb_FkMap( self):
        self.viewerFk.show()
        return 

    def cb_helpOverview(self):
        QMessageBox.about(self, self.tr("Help Basics"), self.tr(
"<h3> The Operator Widget</h3>"
" n.n.            <br><br>"  
"<ul>"
"<li> MB-left - Zoom into the set</li>"
"<li> MB-middle - Move center, no zoom</li>"
"<li> MB-right - Define start and end points for scans.</li>"
"</ul>" 
                ))

class DynamicOperatorWorker(QObject):

    frameReady = pyqtSignal(np.ndarray)
    logMessage = pyqtSignal(str)
    iterationInfo = pyqtSignal(int, float, float)  
    finished = pyqtSignal()
    
    def __init__(self, parent, operator):
        super().__init__()
        self.parent = parent
        self.name = "DynOpWorker"
        self.frameReady.connect( self.parent.catchFrameReady)
        self.finished.connect( self.parent.catchFinished)
        self.iterationInfo.connect( self.parent.catchIterationInfo)
        self.logMessage.connect( self.parent.catchLogMessage)

        self.operator = operator
            
        self.prevV = self.parent.V_in.copy()
        self.startTimeTotal = time.time()
        return 

    @pyqtSlot()
    def start(self):
        QTimer.singleShot(0, self.step)

    @pyqtSlot()
    def step(self):

        #print( "%s.step, iterations %d iterationsMax %d " %
        #       ( self.name, self.parent.iterations, self.parent.iterationsMax))

        if self.parent.forever == "False": 
            if self.parent.iterations >= self.parent.iterationsMax:
                self.logMessage.emit( "OpFunc: nothing to be done iterations %s, return" %
                                      ( self.parent.iterations))
                self.finished.emit()
                return

        if self.parent.iterations < 10:
            nIter = 1
        elif self.parent.iterations < 50:
            nIter = 5
        elif self.parent.iterations < 100:
            nIter = 10
        elif self.parent.iterations < 200:
            nIter = 20
        else:
            nIter = 50
        startTime = time.time()

        self.parent.U_in, self.parent.V_in = \
            self.operator( self.parent.U_in, self.parent.V_in, nIter)
        
        if self.parent.wOutput == "V_out":
            if self.parent.V_in.max() < 1.5: 
                V_out = np.clip( self.parent.V_in * 1023, 0, 1023).astype(np.float32)
            else:
                V_out = self.parent.V_in.copy()
            self.parent.dataPtr.dataMandelbrotSet = V_out.copy()
        else:
            if self.parent.U_in.max() < 1.5: 
                U_out = np.clip( self.parent.U_in * 1023, 0, 1023).astype(np.float32)
            else:
                U_out = self.parent.U_in.copy()
            self.parent.dataPtr.dataMandelbrotSet = U_out.copy()

        self.parent.iterations += nIter

        self.frameReady.emit( self.parent.dataPtr.dataMandelbrotSet)

        self.parent.UVempty = False

        diff = np.abs(self.parent.V_in - self.prevV).mean()
        self.prevV = self.parent.V_in.copy()
        fps = float( nIter)/(time.time() - startTime)
        self.iterationInfo.emit( self.parent.iterations, fps, diff)
        
        if self.parent.forever == "False": 
            if self.parent.iterations >= self.parent.iterationsMax:
                if self.parent.useMPL:
                    temp = "(MPL)"
                else: 
                    temp = "(PG)"
                self.logMessage.emit( "%s.step: %s total time %g %s" %
                                      ( self.name,
                                        self.parent.operatorName,
                                        ( time.time() - self.startTimeTotal), temp))
                self.logMessage.emit( "%s.step: iterations %d iterationsMax %d" %
                                      ( self.name,
                                        self.parent.iterations,
                                        self.parent.iterationsMax))
                if self.parent.operatorName.find( "AntiDiffusion") == 0:
                    self.logMessage.emit( "%s.step: Sigma %g Alpha %g normLoop %s"  %
                                          ( self.name,
                                            self.parent.sigma,
                                            self.parent.alpha,
                                            repr( self.parent.normLoop)))
                elif self.parent.operatorName.find( "GrayScottPython") == 0:
                    self.logMessage.emit( "%s.step: F %g k %g sigma" %
                                          ( self.name,
                                            self.parent.feedRate,
                                            self.parent.killRate, 
                                            self.parent.sigma))
                elif self.parent.operatorName.find( "GrayScott") == 0:
                    self.logMessage.emit( "%s.step: F %g k %g" %
                                          ( self.name,
                                            self.parent.feedRate,
                                            self.parent.killRate))
                    
                #print( "%s.step, worker finished at iterations %d" %
                #       (self.name, self.parent.iterations))
                self.finished.emit()
                return

        QTimer.singleShot( 10, self.step)
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
    parser.add_argument( '-m',
                         dest="useMPL", action="store_true", help='Use MPL')
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

    w = operatorWidget( app, mode = 'standalone', modeOperation = args.mode, useMPL = args.useMPL)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
 
