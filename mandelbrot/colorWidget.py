#!/usr/bin/env python3

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import PGViewer
import utils
import time

METADATA_MEMBERS = [
    ]
#
# beware of typos, check whether a member is in the list of known members
#
COLORWIDGET_Attrs = METADATA_MEMBERS + \
    [ 'app', 'busy', 'cmapLbl', 'smoothModeCombo',
      'interpolationModeCombo', 'cmapRotateSliderLbl',
      'cmapRotateSlider', 'colorRotateExecPb', 'normCombo',
      'normParCombo', 'vminSlider', 'vminSliderLbl',
      'vmaxSlider', 'vmaxSliderLbl', 'shadedCb', 
      'azDegCombo', 'altDegCombo', 'vert_exagCombo', 'blendModeCombo', 
      'reversedCb', 'cyclicCb', 'colorRotateCombo', 'rotateWaitTimeCombo',
      'parent', 'name', 'isRotating', 'blackFixedCb',
      'colorPars', 'blendMode_values', 'vert_exag_values', 
      'interpolation_values', 
     ]

class colorWidget( QWidget):

    setColor = pyqtSignal()
    redisplay = pyqtSignal()
    calcMBS = pyqtSignal()
    logWidget = pyqtSignal( str)
    
    def __init__(self, app = None, parent=None, colorPars = None):
        super().__init__()

        self.name = "colorWidget"
        self.app = app
        self.parent = parent
        self.colorPars = colorPars

        #print("colorWidget.__init__(): self.parent.name %s" % self.parent.name)

        self.initMembers()
        self.prepareWidget()
        self.toPG()

#        self.show()

        #
        # make sure MBS_ATTR is not polluted
        # +++
        #for name in COLORWIDGET_Attrs:
        #    try:
        #        temp = getattr( self, name)
        #    except:
        #        print( "%s.__init__: %s is not in self" % ( self.name, name))
        #        pass
        
        return 

    def __setattr__( self, name, value):
        """
        +++
        this function protects agains typos. members can only be set, 
        if they have been defined
        """
        #print( "mandelbrotSetWidget.__setattr__: name %s, value %s" % (name, value))
        if name in COLORWIDGET_Attrs or \
           name.find( 'SelColor') == 0 or \
           name.find( 'AllColor') == 0: 
            super( colorWidget, self).__setattr__(name, value)
        else:
            print( " unknown attribute (colorWidget): '%s'," %  name)
            super( colorWidget, self).__setattr__(name, value)

    def initMembers( self):
        self.smoothModeCombo = None
        self.isRotating = False
        self.busy = False
        return
    #
    # color widget
    #
    def prepareWidget( self):

        gridLayout = QGridLayout()
        self.setLayout( gridLayout)

        row = -1
        #
        # color maps
        #
        self.cmapLbl = QLabel( "CMAP: %s" % self.colorPars.colorMapName)
        #self.cmapLbl.setFixedWidth( 180)
        self.cmapLbl.setToolTip( "Open 'Colors' or 'AllColors' to select color maps.")
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.cmapLbl)
        #
        # reversed
        #
        self.reversedCb = QCheckBox( "Reversed", self)
        self.reversedCb.setToolTip( "If enabled, the color map is reversed.")
        self.reversedCb.setChecked( self.colorPars.flagReversed == "True")
        self.reversedCb.clicked.connect( self.cb_reversed)
        hLayout.addWidget( self.reversedCb)
        #
        # cyclic
        #
        self.cyclicCb = QCheckBox( "Cyclic", self)
        self.cyclicCb.setToolTip( "If enabled, the color map is made cyclic, like prism or flag.")
        self.cyclicCb.setChecked( self.colorPars.flagCyclic == "True")
        self.cyclicCb.clicked.connect( self.cb_cyclic)
        hLayout.addWidget( self.cyclicCb)

        #
        # smooth mode
        #
        if self.parent.name == "MBSMainWindow":
            self.smoothModeCombo = QComboBox()
            self.smoothModeCombo.setToolTip( "Smoothing modifies the discrete values of the escapeCount field such \nthat there are smooth transitions. This way banding is avoided (more or less). \n\n  - DistEst - the data is smoothed depending on how far the z(n) escapes. \n  - DZ - the data is smoothed depending on the derivative dz(n)")
            for elm in utils.SMOOTH_VALUES:
                self.smoothModeCombo.addItem( str( elm))
            self.smoothModeCombo.setCurrentIndex( 0)
            self.smoothModeCombo.activated.connect( self.cb_smoothModeCombo )
            hLayout.addWidget( QLabel( 'Smooth'))
            hLayout.addWidget( self.smoothModeCombo)
        #
        # interpolation mode
        #
        self.interpolationModeCombo = QComboBox()
        self.interpolationModeCombo.setToolTip( "Interpolation algorithm")
        for elm in utils.PG_INTERPOLATION_VALUES:
            self.interpolationModeCombo.addItem( str( elm))
        self.colorPars.interpolation = utils.PG_INTERPOLATION_VALUES[0]

        self.interpolationModeCombo.setCurrentIndex( 0)
        self.interpolationModeCombo.activated.connect( self.cb_interpolationModeCombo )
        hLayout.addWidget( QLabel( 'Interpol.'))
        hLayout.addWidget( self.interpolationModeCombo)
        hLayout.addStretch()
        
        row += 1
        col = 0
        gridLayout.addLayout( hLayout, row, col, 1, 2)
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
        self.cmapRotateSlider.setMaximum( utils.CMAP_MAX - 1)
        self.cmapRotateSlider.setFixedWidth( 450)
        hLayout.addWidget( self.cmapRotateSlider)
        #
        # blackFixed
        #
        if self.parent.name == "MBSMainWindow":
            self.blackFixedCb = QCheckBox( "BlackFixed", self)
            self.blackFixedCb.setToolTip( "Color black is fixed ath the end of the colorMap and is not rotated")
            self.blackFixedCb.setChecked( self.colorPars.blackFixed == "True")
            self.blackFixedCb.clicked.connect( self.cb_blackFixed)
            hLayout.addWidget( self.blackFixedCb)
        hLayout.addStretch()
        row += 1 
        col = 0
        gridLayout.addLayout( hLayout, row, col, 1, 2)
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
        for elm in utils.COLORROTATE_VALUES:
            self.colorRotateCombo.addItem( str( elm))
        self.colorRotateCombo.setCurrentIndex( 0)
        self.colorRotateCombo.activated.connect( self.cb_colorRotateCombo )
        hLayout.addWidget( self.colorRotateCombo)
        hLayout.addStretch()
        
        row += 1
        col = 0
        gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # wait time
        #
        hLayout.addWidget( QLabel( "WaitTime"))
        self.rotateWaitTimeCombo = QComboBox()
        self.rotateWaitTimeCombo.setToolTip( "Slows down the color rotation.")
        for elm in utils.ROTATEWAITTIME_VALUES:
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
        gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        # Linie ins GridLayout einfügen (z. B. in Zeile 1, Spalte 0, über 2 Spalten)
        row += 1
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # norm/normPar
        #
        self.normCombo = QComboBox()
        self.normCombo.setToolTip( "Normalization method, modifies the transformation [vmin, vmax] -> [0, 1]")
        for elm in utils.NORM_VALUES:
            self.normCombo.addItem( str( elm))
        self.normCombo.setCurrentIndex( 0)
        self.normCombo.activated.connect( self.cb_normCombo )
        
        self.normParCombo = QComboBox()
        self.normParCombo.setToolTip( "Normalization parameter, meaning depends on method")
        for elm in utils.NORMPAR_VALUES:
            self.normParCombo.addItem( str( elm))
        self.normParCombo.setCurrentIndex( 0)
        self.normParCombo.activated.connect( self.cb_normParCombo )

        hLayout.addWidget( self.normCombo)
        hLayout.addWidget( self.normParCombo)
        hLayout.addStretch()

        row += 1
        col = 0
        gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()
        #
        # vmin
        #
        self.vminSlider = QSlider(Qt.Horizontal)
        self.vminSlider.setToolTip("Coloring transforms the range [vmin, vmax] to [0, 1]")
        self.vminSlider.setMinimum(0)
        self.vminSlider.setMaximum(1024)
        self.vminSlider.setValue( int( self.colorPars.vmin))
        self.vminSlider.setFixedWidth(450)

        self.vminSliderLbl = QLabel("vmin: %4d" % int( self.colorPars.vmin))
        self.vminSliderLbl.setFixedWidth( 100)
        self.vminSliderLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.vminSliderLbl)
        hLayout.addStretch()
        hLayout.addWidget(self.vminSlider)
        row += 1
        col = 0
        gridLayout.addLayout(hLayout, row, col, 1, 2)
        #
        # vmax
        #
        self.vmaxSlider = QSlider(Qt.Horizontal)
        self.vmaxSlider.setToolTip("Coloring transforms the range [vmin, vmax] to [0, 1]")
        self.vmaxSlider.setMinimum(0)
        self.vmaxSlider.setMaximum(1024)
        self.vmaxSlider.setValue( int( self.colorPars.vmax))
        self.vmaxSlider.setFixedWidth(450)

        self.vmaxSliderLbl = QLabel("vmax: %4d" % int( self.colorPars.vmax))
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
        gridLayout.addLayout(hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()
        #
        # horizontal line
        #
        row += 1
        gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # shaded
        #
        self.shadedCb = QCheckBox( "Shader", self)
        self.shadedCb.setChecked( self.colorPars.shaded == "True")
        self.shadedCb.setToolTip( "Enable shading")
        self.shadedCb.clicked.connect( self.cb_shaded)
        row += 1
        col = 0
        gridLayout.addWidget( self.shadedCb, row, col)
        hLayout = QHBoxLayout()
        #
        # vert_exag
        #
        self.vert_exagCombo = QComboBox()
            
        for elm in utils.PG_VERT_EXAG_VALUES:
            self.vert_exagCombo.addItem( str( elm))

        self.vert_exagCombo.setCurrentIndex( 0)
        self.vert_exagCombo.setToolTip( "Controls relief steepness")
        self.vert_exagCombo.activated.connect( self.cb_vert_exagCombo )
        hLayout.addWidget( QLabel( 'Vert_Exag'))
        hLayout.addWidget( self.vert_exagCombo)
        #
        # blendMode
        #
        self.blendModeCombo = QComboBox()
        self.blendModeCombo.setToolTip( "Modulates the light intensity")
        for elm in utils.PG_BLEND_MODE_VALUES:
            self.blendModeCombo.addItem( str( elm))
        self.blendModeCombo.setCurrentIndex( 0)
        self.blendModeCombo.activated.connect( self.cb_blendModeCombo )
        hLayout.addWidget( QLabel( 'Blend'))
        hLayout.addWidget( self.blendModeCombo)
        hLayout.addStretch()
        row += 1
        col = 0
        gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # azDeg
        #
        self.azDegCombo = QComboBox()
        self.azDegCombo.setToolTip( "Set azimutal angle of the light")
        for elm in utils.AZDEG_VALUES:
            self.azDegCombo.addItem( str( elm))
        self.azDegCombo.setCurrentIndex( 0)
        self.azDegCombo.activated.connect( self.cb_azDegCombo )
        hLayout.addWidget( QLabel( 'azDegree'))
        hLayout.addWidget( self.azDegCombo)
        #
        # altDeg
        #
        self.altDegCombo = QComboBox()
        self.altDegCombo.setToolTip( "Set polar angle of the light")
        for elm in utils.ALTDEG_VALUES:
            self.altDegCombo.addItem( str( elm))
        self.altDegCombo.setCurrentIndex( 0)
        self.altDegCombo.activated.connect( self.cb_altDegCombo )
        hLayout.addWidget( QLabel( 'altDegree'))
        hLayout.addWidget( self.altDegCombo)
        hLayout.addStretch()
        col = 1
        gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # horizontal line
        #
        row += 1
        gridLayout.addWidget(line, row, 0, 1, 2)
        return 

    
    @pyqtSlot( bool)
    def cb_cyclic( self, i):
        if i:
            temp = "True"
        else: 
            temp = "False"
        self.colorPars.flagCyclic = temp
        self.setColor.emit()
        self.redisplay.emit()
            
        return 

    @pyqtSlot( bool)
    def cb_blackFixed( self, i):
        if i:
            temp = "True"
        else: 
            temp = "False"
        self.colorPars.blackFixed = temp
        self.setColor.emit()
        self.redisplay.emit()
        return

    @pyqtSlot( int)
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
        self.cmapRotateSliderLbl.setText( "C-Index: %-4d" % colorIndex)
        self.colorPars.rotateColorMapIndex = colorIndex
        self.colorPars.colorPhase = float( colorIndex)/utils.CMAP_MAX
        self.setColor.emit()
        self.redisplay.emit()

        self.busy = False
        return

    @pyqtSlot( int)
    def cb_colorRotateCombo( self, i):
        self.colorPars.colorRotateValue = utils.COLORROTATE_VALUES[ i]
        self.redisplay.emit()
        return

    @pyqtSlot( int)
    def cb_rotateWaitTimeCombo( self, i):
        self.colorPars.rotateWaitTime = float( utils.ROTATEWAITTIME_VALUES[ i])
        self.redisplay.emit()
        return

    @pyqtSlot()
    def rotateColorsContinuously( self):
        self.isRotating = True
        self.colorRotateExecPb.setStyleSheet("background-color:lightblue")
        colorIndexOld = self.colorPars.rotateColorMapIndex
        self.logWidget.emit( "rotate: started rotating at %d" % 
                               ( colorIndexOld))
        self.app.processEvents()
        self.parent.engine.calcMandelbrotSet( display = False)

        while True:
            time.sleep( self.colorPars.rotateWaitTime)
            #
            # avoid that color rotation blocks
            #
            self.app.processEvents()
            colorIndex = self.colorPars.rotateColorMapIndex + self.colorPars.colorRotateValue
            if colorIndex >= utils.CMAP_MAX:
                colorIndex = 0
            if colorIndex < 0:
                colorIndex = utils.CMAP_MAX - 1
            self.cmapRotateSlider.setValue( colorIndex)
            if self.parent.stopRequested:
                self.parent.stopRequested = False
                self.colorRotateExecPb.setStyleSheet("background-color:%s" %
                                                     self.parent.backgroundColor)
                self.logWidget.emit( "rotate: stopped at %d" %
                                     self.colorPars.rotateColorMapIndex) 
                break

        self.isRotating = False
        self.redisplay.emit()
                
        return 
    
    @pyqtSlot()
    def cb_colorRotateExecPb( self):
        if self.isRotating: 
            self.parent.stopRequested = True
            self.parent.logWidget.append( "rotateColorGoPb: stop requested")
            return

        self.rotateColorsContinuously()
        return
    
    @pyqtSlot( bool)
    def cb_reversed( self, i):
        if i:
            temp = "True" 
        else:
            temp = "False"
        self.colorPars.flagReversed = temp
        self.setColor.emit()
        self.redisplay.emit()
            
        return 

    @pyqtSlot( int)
    def cb_normCombo( self, i):

        self.colorPars.norm = utils.NORM_VALUES[ i]
        if self.colorPars.norm == "LogNorm":
            self.normParCombo.clear()
            for elm in utils.NORMPAR_VALUES_LOG:
                self.normParCombo.addItem( str( elm))
            self.colorPars.normPar = 100
            self.normParCombo.setEnabled( True)
        elif self.colorPars.norm == "InvLogNorm":
            self.normParCombo.clear()
            for elm in utils.NORMPAR_VALUES_LOG:
                self.normParCombo.addItem( str( elm))
            self.colorPars.normPar = 100
            self.normParCombo.setEnabled( True)
        elif self.colorPars.norm == "PowerNorm":
            self.normParCombo.clear()
            for elm in utils.NORMPAR_VALUES:
                self.normParCombo.addItem( str( elm))
            self.colorPars.normPar = utils.NORMPAR_VALUES[0]
            self.normParCombo.setEnabled( True)
        else:
            self.normParCombo.setEnabled( False)

        self.setColor.emit()
        self.redisplay.emit()

        return

    @pyqtSlot( int)
    def cb_normParCombo( self, i):
        if self.colorPars.norm == "PowerNorm": 
            self.colorPars.normPar = float( utils.NORMPAR_VALUES[i])
        elif self.colorPars.norm == "LogNorm": 
            self.colorPars.normPar = float( utils.NORMPAR_VALUES_LOG[i])
        elif self.colorPars.norm == "InvLogNorm": 
            self.colorPars.normPar = float( utils.NORMPAR_VALUES_LOG[i])
            
        self.setColor.emit()
        self.redisplay.emit()
        
        return

    def cb_vminSlider( self, i):

        if i >= self.colorPars.vmax:
            self.logWidget.emit( "vmin >= vmax, resetting vmin")
            self.vminSlider.setValue( 0)
            return
        if self.vminSliderLbl is not None:
            self.vminSliderLbl.setText( "vmin: %4d" % i)
        self.colorPars.vmin = float(i)
        self.redisplay.emit()
        return

    def cb_vmaxSlider( self, i):
        if i <= self.colorPars.vmin:
            self.logWidget.emit( "vmax >= vmax, resetting vmax")
            self.vmaxSlider.setValue( utils.DATA_NORM)
            return
        if self.vmaxSliderLbl is not None:
            self.vmaxSliderLbl.setText( "vmax: %4d" % i)
        self.colorPars.vmax = float(i)
        self.redisplay.emit()
        return

    def cb_smoothModeCombo( self, i):

        print( "%s.smoothModeCombo" % self.name) 
        if self.parent.name != "MBSMainWindow":
            temp = QMessageBox()
            ret = temp.question(self,'', "Smooth only for MBS", temp.Ok )
            return 
            
        self.colorPars.smooth = utils.SMOOTH_VALUES[i]
        self.calcMBS.emit()
        return

    def cb_interpolationModeCombo( self, i):
        self.colorPars.interpolation = self.interpolation_values[i]
        self.redisplay.emit()
        return

    def cb_shaded( self, i):
        if i:
            self.colorPars.shaded = 'True'
        else:
            self.colorPars.shaded = 'False'
        self.redisplay.emit()
        return

    def cb_vert_exagCombo( self, i):
        self.colorPars.vert_exag = float( self.vert_exag_values[i])
        self.redisplay.emit()
        return

    def cb_blendModeCombo( self, i):
        self.colorPars.blendMode = self.blendMode_values[i]
        self.redisplay.emit()
        return

    def cb_azDegCombo( self, i):
        self.colorPars.azDeg = float( utils.AZDEG_VALUES[i])
        self.redisplay.emit()
        return

    def cb_altDegCombo( self, i):
        self.colorPars.altDeg = float( utils.ALTDEG_VALUES[i])
        self.redisplay.emit()

        return

    def updateGUI( self):
        
        if self.normParCombo is not None:
            self.normParCombo.setEnabled( True)
        self.reversedCb.setChecked( self.colorPars.flagReversed == "True")

        self.cyclicCb.setChecked( self.colorPars.flagCyclic == "True")

        self.colorRotateCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.colorPars.colorRotateValue, utils.COLORROTATE_VALUES))

        self.cmapRotateSlider.setValue( self.colorPars.rotateColorMapIndex)

        if self.smoothModeCombo is not None:
            self.smoothModeCombo.setCurrentIndex( 
                utils.findCurrentIndex( self.colorPars.smooth, utils.SMOOTH_VALUES))

        self.shadedCb.setChecked( self.colorPars.shaded == "True")

        if self.parent.name == "MBSMainWindow":
            self.blackFixedCb.setChecked( self.colorPars.blackFixed == "True")

        self.interpolationModeCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.colorPars.interpolation,
                                    self.interpolation_values))

        self.cmapLbl.setText( "CMAP: %s" % self.colorPars.colorMapName)
        
        self.vert_exagCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.colorPars.vert_exag, self.vert_exag_values))

        self.blendModeCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.colorPars.blendMode, self.blendMode_values))
        
        self.normCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.colorPars.norm, utils.NORM_VALUES))

        self.vminSlider.setEnabled( True)
        self.vmaxSlider.setEnabled( True)

        self.vminSlider.setValue( int( self.colorPars.vmin))

        self.vmaxSlider.setValue( int( self.colorPars.vmax))

        self.azDegCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.colorPars.azDeg, utils.AZDEG_VALUES))
            
        self.altDegCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.colorPars.altDeg, utils.ALTDEG_VALUES))

        if self.colorPars.norm == "PowerNorm": 
            self.normParCombo.setCurrentIndex( 
                utils.findCurrentIndex( self.colorPars.normPar, utils.NORMPAR_VALUES))
            self.normParCombo.setEnabled( True)
        elif self.colorPars.norm == "LogNorm": 
            self.normParCombo.setCurrentIndex( 
                utils.findCurrentIndex( self.colorPars.normPar, utils.NORMPAR_VALUES_LOG))
            self.normParCombo.setEnabled( True)
        elif self.colorPars.norm == "InvLogNorm": 
            self.normParCombo.setCurrentIndex( 
                utils.findCurrentIndex( self.colorPars.normPar, utils.NORMPAR_VALUES_LOG))
            self.normParCombo.setEnabled( True)
        else:
            self.normParCombo.setEnabled( False)

        self.app.processEvents()
        
        return 

    def toMPL( self): 
        #
        # blendMode
        #
        self.blendModeCombo.clear()
        self.blendMode_values = utils.BLEND_MODE_VALUES
        for elm in self.blendMode_values:
            self.blendModeCombo.addItem( str( elm))
        self.blendModeCombo.setCurrentIndex( 0)
        self.colorPars.blendMode = self.blendMode_values[0]
        #
        # vert_exag
        #
        self.vert_exagCombo.clear()
        self.vert_exag_values = utils.VERT_EXAG_VALUES
        for elm in self.vert_exag_values:
            self.vert_exagCombo.addItem( str( elm))
        self.vert_exagCombo.setCurrentIndex( 0)
        self.colorPars.vert_exag = self.vert_exag_values[0]
        #
        # interpolation
        #
        self.interpolationModeCombo.clear()
        self.interpolation_values = utils.INTERPOLATION_VALUES
        for elm in self.interpolation_values:
            self.interpolationModeCombo.addItem( str( elm))
        self.colorPars.interpolation = self.interpolation_values[0]

        return 

    def toPG( self): 
        #
        # blendMode
        #
        self.blendModeCombo.clear()
        self.blendMode_values = utils.PG_BLEND_MODE_VALUES
        for elm in self.blendMode_values:
            self.blendModeCombo.addItem( str( elm))
        self.blendModeCombo.setCurrentIndex( 0)
        self.colorPars.blendMode = self.blendMode_values[0]
        #
        # vert_exag
        #
        self.vert_exagCombo.clear()
        self.vert_exag_values = utils.PG_VERT_EXAG_VALUES
        for elm in self.vert_exag_values:
            self.vert_exagCombo.addItem( str( elm))
        self.vert_exagCombo.setCurrentIndex( 0)
        self.colorPars.vert_exag = self.vert_exag_values[0]
        #
        # interpolation
        #
        self.interpolationModeCombo.clear()
        self.interpolation_values = utils.PG_INTERPOLATION_VALUES
        for elm in self.interpolation_values:
            self.interpolationModeCombo.addItem( str( elm))
        self.colorPars.interpolation = self.interpolation_values[0]

        return 

