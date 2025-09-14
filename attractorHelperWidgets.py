#!/usr/bin/env python

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

RESOLUTION = 1000
INCREMENTS = [1, 2, 5, 10, 100]


class SliderWidget( QSlider):
    def __init__(self, parent, par):
        super().__init__()
        self.var  = parent.var
        self.setMinimumWidth( 300)
        self.setRange( 0, RESOLUTION)
        if par.upper() in parent.parent.cfgHsh[self.var]: 
            val = parent.posToSliderIndex( parent.parent.cfgHsh[self.var][ par.upper()], 
                                           parent.parent.cfgHsh[self.var][ "%sMIN" % par.upper()],
                                           parent.parent.cfgHsh[self.var][ "%sMAX" % par.upper()]) 
        elif par.upper() in parent.parent.cfgHsh: 
            val = parent.posToSliderIndex( parent.parent.cfgHsh[ par.upper()], 
                                           parent.parent.cfgHsh[ "%sMIN" % par.upper()],
                                           parent.parent.cfgHsh[ "%sMAX" % par.upper()])
        else:
            print( "attractorHelperWidget.SliderWidget: something is wrong with %s " % par.upper())
            
        self.setValue( int( val))
        self.setOrientation( 1) # 1 horizontal, 2 vertical
        return
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Left:
            self.setValue(self.value() - 1)
        elif event.key() == Qt.Key_Right:
            self.setValue(self.value() + 1)
        elif event.key() == Qt.Key_Up:
            self.setValue(self.value() + 1) # For vertical sliders
        elif event.key() == Qt.Key_Down:
            self.setValue(self.value() - 1) # For vertical sliders
        self.setFocus()
        self.activateWindow()
        return
    
class parWidget( QMainWindow):
    def __init__(self, app, parent=None):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle("%s Parameters" % parent.attractor)
        self.app = app
        self.parent = parent
        self.var  = self.parent.var
        self.nPar = self.parent.cfgHsh[ 'NPAR']
        self.parHsh = {}
        geoScreen = QDesktopWidget().screenGeometry(-1)
        self.geoWidth = geoScreen.size().width()
        self.geoHeight = geoScreen.size().height()

        font = QFont( 'Sans Serif')
        if self.geoWidth <= 1920:
            font.setPixelSize( 16)
        else:
            font.setPixelSize( 22)
        self.app.setFont( font)

        self.fig = None

        self.prepareMenuBar()
        self.prepareCentralPart()
        self.prepareStatusBar()

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
        self.exitAction = QAction('Exit', self)        
        self.exitAction.triggered.connect( self.cb_close)
        self.fileMenu.addAction( self.exitAction)
        #
        # help
        #
        self.menuBarRight = QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarRight, QtCore.Qt.TopRightCorner)
        self.helpMenu = self.menuBarRight.addMenu('Help')
        self.menuBar.setCornerWidget( self.menuBarRight, QtCore.Qt.TopRightCorner)
        return
    #    
    # === the central part
    #    
    def prepareCentralPart( self):

        w = QWidget()
        #
        # start with a vertical layout
        #
        self.layout = QGridLayout()
        w.setLayout( self.layout)
        self.setCentralWidget( w)
        row = -1
        for i in range( 1, self.nPar + 1):
            par = 'p%d' % i
            self.parHsh[ par] = {}
            self.parHsh[ par][ 'Increment'] = 1
            self.parHsh[ par][ 'SliderLabel'] = QLabel( "%s: %10.4f" % ( self.convert( i), getattr( self.parent, par)))
            self.parHsh[ par][ 'Slider'] = SliderWidget( self, par)
            self.parHsh[ par][ 'Slider'].setToolTip( "Slide through %s" % par.upper())
            self.parHsh[ par][ 'Slider'].sliderReleased.connect( self.makeCbSlider( par))
            self.parHsh[ par][ 'Slider'].sliderMoved.connect( self.makeCbSliderMoved( par))
            self.parHsh[ par][ 'PushButtonDown'] = QPushButton( '<')
            self.parHsh[ par][ 'PushButtonDown'].setMaximumWidth( 30)
            self.parHsh[ par][ 'PushButtonDown'].pressed.connect( self.makeCbPushButtonDown( par))
            self.parHsh[ par][ 'PushButtonUp'] = QPushButton( '>')
            self.parHsh[ par][ 'PushButtonUp'].setMaximumWidth( 30)
            self.parHsh[ par][ 'PushButtonUp'].pressed.connect( self.makeCbPushButtonUp( par))
            self.parHsh[ par][ 'IncrCombo'] = QComboBox()
            self.parHsh[ par][ 'IncrCombo'].setToolTip( "Change increment")
            for elm in INCREMENTS:
                self.parHsh[ par][ 'IncrCombo'].addItem( str( elm))
            self.parHsh[ par][ 'IncrCombo'].setCurrentIndex( 0)
            self.parHsh[ par][ 'IncrCombo'].activated.connect( self.makeCbIncrCombo( par))
            self.parHsh[ par][ 'LineEdit'] = QLineEdit()
            self.parHsh[ par][ 'LineEdit'].setMaximumWidth( 80)
            self.parHsh[ par][ 'LineEdit'].setAlignment(QtCore.Qt.AlignRight)
            self.parHsh[ par][ 'PushButtonApply'] = QPushButton( 'Apply')
            self.parHsh[ par][ 'PushButtonApply'].setMaximumWidth( 80)
            self.parHsh[ par][ 'PushButtonApply'].pressed.connect( self.makeCbPushButtonApply( par))
            row += 1
            col = 0
            self.layout.addWidget( self.parHsh[ par][ 'SliderLabel'], row, 0)
            col += 1
            self.layout.addWidget( self.parHsh[ par][ 'PushButtonDown'], row, col)
            col += 1
            self.layout.addWidget( self.parHsh[ par][ 'Slider'], row, col)
            col += 1
            self.layout.addWidget( self.parHsh[ par][ 'PushButtonUp'], row, col)
            col += 1
            self.layout.addWidget( self.parHsh[ par][ 'IncrCombo'], row, col)
            col += 1
            self.layout.addWidget( self.parHsh[ par][ 'LineEdit'], row, col)
            col += 1
            self.layout.addWidget( self.parHsh[ par][ 'PushButtonApply'], row, col)
        return 

    def convert( self, i):
        """
        convert 'P1' to 'a', 'P2' to 'b', etc.
        """
        CONVERT = { 'P1': 'a', "P2": 'b', "P3": 'c', "P4": 'd', "P5": 'e', "P6": 'f'}
        try: 
            argout = CONVERT[ "P%d" % i]
        except:
            argout = "abc"
        return argout
    
    def makeCbSlider( self, par):
        def f():
            setattr( self.parent, par,
                     self.sliderIndexToPos( self.parHsh[ par][ 'Slider'].value(), 
                                            self.parent.cfgHsh[self.var][ '%sMIN' % par.upper()], 
                                            self.parent.cfgHsh[self.var][ '%sMAX' % par.upper()]))
            self.parHsh[ par][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( par.upper(), getattr( self.parent, par)))
            self.parHsh[ par][ 'LineEdit'].setText( "%g" % ( getattr( self.parent, par)))
            self.parent.apply()
            return 
        return f

    def makeCbSliderMoved( self, par):
        def f():
            setattr( self.parent, par, 
                     self.sliderIndexToPos( self.parHsh[ par][ 'Slider'].value(), 
                                            self.parent.cfgHsh[self.var][ '%sMIN' % par.upper()], 
                                            self.parent.cfgHsh[self.var][ '%sMAX' % par.upper()]))
            self.parHsh[ par][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( par.upper(), getattr( self.parent, par)))
            return 
        return f
    
    def makeCbPushButtonDown( self, par):
        def f():
            self.parHsh[ par][ 'Slider'].setValue( self.parHsh[ par][ 'Slider'].value() - self.parHsh[ par][ 'Increment'])
            setattr( self.parent, par, 
                     self.sliderIndexToPos(
                         self.parHsh[ par][ 'Slider'].value(),
                         self.parent.cfgHsh[self.var][ '%sMIN' % par.upper()], 
                         self.parent.cfgHsh[self.var][ '%sMAX' % par.upper()]))
            self.parHsh[ par][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( par.upper(), getattr( self.parent, par)))
            self.parHsh[ par][ 'LineEdit'].setText( "%g" % ( getattr( self.parent, par)))
            self.parent.apply()
            
            return 
        return f

    def makeCbPushButtonUp( self, par):
        def f():
            self.parHsh[ par][ 'Slider'].setValue( self.parHsh[ par][ 'Slider'].value() + self.parHsh[ par][ 'Increment'])
            setattr( self.parent, par, 
                     self.sliderIndexToPos( self.parHsh[ par][ 'Slider'].value(), 
                                            self.parent.cfgHsh[self.var][ '%sMIN' % par.upper()], 
                                            self.parent.cfgHsh[self.var][ '%sMAX' % par.upper()]))
            self.parHsh[ par][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( par.upper(), getattr( self.parent, par)))
            self.parHsh[ par][ 'LineEdit'].setText( "%g" % ( getattr( self.parent, par)))
            self.parent.apply()
            
            return 
        return f

    def makeCbIncrCombo( self, par):
        def f( i):
            self.parHsh[ par][ 'Increment'] = int( INCREMENTS[i])
            return
        return f

    def makeCbPushButtonApply( self, par):
        def f():
            setattr( self.parent, par, float( self.parHsh[ par][ 'LineEdit'].text()))
            self.parHsh[ par][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( par.upper(),
                                                         float( self.parHsh[ par][ 'LineEdit'].text())))
            self.parHsh[ par][ 'Slider'].setValue(
                self.posToSliderIndex( getattr( self.parent, par), 
                                       self.parent.cfgHsh[self.var][ '%sMIN' % par.upper()], 
                                       self.parent.cfgHsh[self.var][ '%sMAX' % par.upper()]))
            self.parent.apply()
            
            return
        return f
    #
    # === the status bar
    #
    def prepareStatusBar( self): 
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)
        #
        # reset
        #
        reset = QPushButton("&Reset")
        reset.clicked.connect( self.cb_reset)       
        self.statusBar.addPermanentWidget( reset)
        #
        # quit
        #
        quit = QPushButton("&Quit")
        quit.clicked.connect( self.cb_close)       
        self.statusBar.addPermanentWidget( quit)
        return 
    #
    #  === callbacks
    #
    def cb_close( self):
        self.parent.oneShotOnOff = False
        self.parent.setCurrentIndices()
        self.parent.restart()
        self.close()
        return

    def posToSliderIndex( self, pos, min, max):
        """
        index/RESOLUTION = (pos - min)/ (max - min)
        index = (pos - min)/ (max - min)* RESOLUTION
        """
        return int( (pos - min)/ (max - min)*RESOLUTION)

    def sliderIndexToPos( self, index, min, max):
        """
        index/RESOLUTION = (pos - min)/ (max - min)
        index = (pos - min)/ (max - min)*RESOLUTION
        pos = index/RESOLUTION*(max - min) + min
        """
        return float( index)/ float(RESOLUTION)*(max - min) + min

    #
    # reset
    #
    def cb_reset( self):

        for i in range( 1, self.nPar + 1):
            par = 'p%d' % i
            parUpper = par.upper()
            
            setattr( self.parent, par, self.parent.cfgHsh[self.var][ parUpper])
            self.parHsh[ par][ 'Slider'].setValue( self.posToSliderIndex( getattr( self.parent, par), 
                                                       self.parent.cfgHsh[self.var][ '%sMIN' % parUpper], 
                                                       self.parent.cfgHsh[self.var][ '%sMAX' % parUpper]))
            self.parHsh[ par][ 'SliderLabel'].setText( "%s: %10.4f" % ( parUpper, getattr( self.parent, par)))
            self.parHsh[ par][ 'LineEdit'].setText( "%g" % getattr( self.parent, par))

        self.parent.apply()
        return
    
class startValuesWidget( QMainWindow):
    def __init__(self, app, parent=None):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle("%s Start Values" % parent.attractor)
        self.app = app
        self.parent = parent
        self.var  = self.parent.var
        self.strtHsh = {}
        geoScreen = QDesktopWidget().screenGeometry(-1)
        self.geoWidth = geoScreen.size().width()
        self.geoHeight = geoScreen.size().height()

        font = QFont( 'Sans Serif')
        if self.geoWidth <= 1920:
            font.setPixelSize( 16)
        else:
            font.setPixelSize( 22)
        self.app.setFont( font)

        self.fig = None

        self.prepareMenuBar()
        self.prepareCentralPart()
        self.prepareStatusBar()

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
        self.exitAction = QAction('Exit', self)        
        self.exitAction.triggered.connect( self.cb_close)
        self.fileMenu.addAction( self.exitAction)
        #
        # help
        #
        self.menuBarRight = QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarRight, QtCore.Qt.TopRightCorner)
        self.helpMenu = self.menuBarRight.addMenu('Help')
        self.menuBar.setCornerWidget( self.menuBarRight, QtCore.Qt.TopRightCorner)
        return
    #    
    # === the central part
    #    
    def prepareCentralPart( self):

        w = QWidget()
        #
        # start with a vertical layout
        #
        self.layout = QGridLayout()
        w.setLayout( self.layout)
        self.setCentralWidget( w)
        row = -1
        for strt in [ 'xStart', 'yStart', 'zStart']:
            self.strtHsh[ strt] = {}
            self.strtHsh[ strt][ 'Increment'] = 1
            self.strtHsh[ strt][ 'SliderLabel'] = QLabel( "%s: %10.4f" % ( strt, getattr( self.parent, strt)))
            self.strtHsh[ strt][ 'Slider'] = SliderWidget( self, strt)
            self.strtHsh[ strt][ 'Slider'].setToolTip( "Slide through %s" % strt)
            self.strtHsh[ strt][ 'Slider'].sliderReleased.connect( self.makeCbSlider( strt))
            self.strtHsh[ strt][ 'Slider'].sliderMoved.connect( self.makeCbSliderMoved( strt))
            self.strtHsh[ strt][ 'PushButtonDown'] = QPushButton( '<')
            self.strtHsh[ strt][ 'PushButtonDown'].setMaximumWidth( 30)
            self.strtHsh[ strt][ 'PushButtonDown'].pressed.connect( self.makeCbPushButtonDown( strt))
            self.strtHsh[ strt][ 'PushButtonUp'] = QPushButton( '>')
            self.strtHsh[ strt][ 'PushButtonUp'].setMaximumWidth( 30)
            self.strtHsh[ strt][ 'PushButtonUp'].pressed.connect( self.makeCbPushButtonUp( strt))
            self.strtHsh[ strt][ 'IncrCombo'] = QComboBox()
            self.strtHsh[ strt][ 'IncrCombo'].setToolTip( "Change increment")
            for elm in INCREMENTS:
                self.strtHsh[ strt][ 'IncrCombo'].addItem( str( elm))
            self.strtHsh[ strt][ 'IncrCombo'].setCurrentIndex( 0)
            self.strtHsh[ strt][ 'IncrCombo'].activated.connect( self.makeCbIncrCombo( strt))
            self.strtHsh[ strt][ 'LineEdit'] = QLineEdit()
            self.strtHsh[ strt][ 'LineEdit'].setMaximumWidth( 80)
            self.strtHsh[ strt][ 'LineEdit'].setAlignment(QtCore.Qt.AlignRight)
            self.strtHsh[ strt][ 'PushButtonApply'] = QPushButton( 'Apply')
            self.strtHsh[ strt][ 'PushButtonApply'].setMaximumWidth( 80)
            self.strtHsh[ strt][ 'PushButtonApply'].pressed.connect( self.makeCbPushButtonApply( strt))
            row += 1
            col = 0
            self.layout.addWidget( self.strtHsh[ strt][ 'SliderLabel'], row, 0)
            col += 1
            self.layout.addWidget( self.strtHsh[ strt][ 'PushButtonDown'], row, col)
            col += 1
            self.layout.addWidget( self.strtHsh[ strt][ 'Slider'], row, col)
            col += 1
            self.layout.addWidget( self.strtHsh[ strt][ 'PushButtonUp'], row, col)
            col += 1
            self.layout.addWidget( self.strtHsh[ strt][ 'IncrCombo'], row, col)
            col += 1
            self.layout.addWidget( self.strtHsh[ strt][ 'LineEdit'], row, col)
            col += 1
            self.layout.addWidget( self.strtHsh[ strt][ 'PushButtonApply'], row, col)
        return 

    def makeCbSlider( self, strt):
        def f():
            if '%sMIN' % strt.upper() in self.parent.cfgHsh[self.var]:
                setattr( self.parent, strt,
                         self.sliderIndexToPos( self.strtHsh[ strt][ 'Slider'].value(), 
                                                self.parent.cfgHsh[self.var][ '%sMIN' % strt.upper()], 
                                                self.parent.cfgHsh[self.var][ '%sMAX' % strt.upper()]))
            elif '%sMIN' % strt.upper() in self.parent.cfgHsh:
                setattr( self.parent, strt,
                         self.sliderIndexToPos( self.strtHsh[ strt][ 'Slider'].value(), 
                                                self.parent.cfgHsh[ '%sMIN' % strt.upper()], 
                                                self.parent.cfgHsh[ '%sMAX' % strt.upper()]))
            else:
                print( "attractorHelperWidget.makeCbSlider: something is wrong with %s " % strt.upper())
                
            self.strtHsh[ strt][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( strt.upper(), getattr( self.parent, strt)))
            self.strtHsh[ strt][ 'LineEdit'].setText( "%g" % ( getattr( self.parent, strt)))
            self.parent.apply()
            return 
        return f

    def makeCbSliderMoved( self, strt):
        def f():
            if '%sMIN' % strt.upper() in self.parent.cfgHsh[self.var]: 
                setattr( self.parent, strt, 
                         self.sliderIndexToPos(
                             self.strtHsh[ strt][ 'Slider'].value(),
                             self.parent.cfgHsh[self.var][ '%sMIN' % strt.upper()], 
                             self.parent.cfgHsh[self.var][ '%sMAX' % strt.upper()]))
            elif '%sMIN' % strt.upper() in self.parent.cfgHsh: 
                setattr( self.parent, strt, 
                         self.sliderIndexToPos(
                             self.strtHsh[ strt][ 'Slider'].value(),
                             self.parent.cfgHsh[ '%sMIN' % strt.upper()], 
                             self.parent.cfgHsh[ '%sMAX' % strt.upper()]))

            self.strtHsh[ strt][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( strt.upper(), getattr( self.parent, strt)))
            return 
        return f
    
    def makeCbPushButtonDown( self, strt):
        def f():
            self.strtHsh[ strt][ 'Slider'].setValue( self.strtHsh[ strt][ 'Slider'].value() - self.strtHsh[ strt][ 'Increment'])

            if '%sMIN' % strt.upper() in self.parent.cfgHsh[self.var]: 
                setattr( self.parent, strt, 
                         self.sliderIndexToPos(
                             self.strtHsh[ strt][ 'Slider'].value(),
                             self.parent.cfgHsh[self.var][ '%sMIN' % strt.upper()], 
                             self.parent.cfgHsh[self.var][ '%sMAX' % strt.upper()]))
            elif '%sMIN' % strt.upper() in self.parent.cfgHsh: 
                setattr( self.parent, strt, 
                         self.sliderIndexToPos(
                             self.strtHsh[ strt][ 'Slider'].value(),
                             self.parent.cfgHsh[ '%sMIN' % strt.upper()], 
                             self.parent.cfgHsh[ '%sMAX' % strt.upper()]))
            else:
                print( "attractorHelperWidget.makeCbPushDown: something is wrong with %s " % strt.upper())
                

            self.strtHsh[ strt][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( strt, getattr( self.parent, strt)))
            self.strtHsh[ strt][ 'LineEdit'].setText( "%g" % ( getattr( self.parent, strt)))
            self.parent.apply()
            
            return 
        return f

    def makeCbPushButtonUp( self, strt):
        def f():
            self.strtHsh[ strt][ 'Slider'].setValue( self.strtHsh[ strt][ 'Slider'].value() + self.strtHsh[ strt][ 'Increment'])
            if '%sMIN' % strt.upper() in self.parent.cfgHsh[self.var]: 
                setattr( self.parent, strt, 
                         self.sliderIndexToPos(
                             self.strtHsh[ strt][ 'Slider'].value(),
                             self.parent.cfgHsh[self.var][ '%sMIN' % strt.upper()], 
                             self.parent.cfgHsh[self.var][ '%sMAX' % strt.upper()]))
            elif '%sMIN' % strt.upper() in self.parent.cfgHsh: 
                setattr( self.parent, strt, 
                         self.sliderIndexToPos(
                             self.strtHsh[ strt][ 'Slider'].value(),
                             self.parent.cfgHsh[ '%sMIN' % strt.upper()], 
                             self.parent.cfgHsh[ '%sMAX' % strt.upper()]))
            else:
                print( "attractorHelperWidget.makeCbPushUp: something is wrong with %s " % strt.upper())

            self.strtHsh[ strt][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( strt, getattr( self.parent, strt)))
            self.strtHsh[ strt][ 'LineEdit'].setText( "%g" % ( getattr( self.parent, strt)))
            self.parent.apply()
            
            return 
        return f

    def makeCbIncrCombo( self, strt):
        def f( i):
            self.strtHsh[ strt][ 'Increment'] = int( INCREMENTS[i])
            return
        return f

    def makeCbPushButtonApply( self, strt):
        def f():
            setattr( self.parent, strt, float( self.strtHsh[ strt][ 'LineEdit'].text()))
            self.strtHsh[ strt][ 'SliderLabel'].setText( "%s: %10.4f" %
                                                       ( strt.upper(),
                                                         float( self.strtHsh[ strt][ 'LineEdit'].text())))

            if '%sMIN' % strt.upper() in self.parent.cfgHsh[self.var]: 
                self.strtHsh[ strt][ 'Slider'].setValue(
                    self.posToSliderIndex( getattr( self.parent, strt), 
                                           self.parent.cfgHsh[self.var][ '%sMIN' % strt.upper()], 
                                           self.parent.cfgHsh[self.var][ '%sMAX' % strt.upper()]))
            elif '%sMIN' % strt.upper() in self.parent.cfgHsh: 
                self.strtHsh[ strt][ 'Slider'].setValue(
                    self.posToSliderIndex( getattr( self.parent, strt), 
                                           self.parent.cfgHsh[ '%sMIN' % strt.upper()], 
                                           self.parent.cfgHsh[ '%sMAX' % strt.upper()]))
            self.parent.apply()
            
            return
        return f
    #
    # === the status bar
    #
    def prepareStatusBar( self): 
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)
        #
        # reset
        #
        reset = QPushButton("&Reset")
        reset.clicked.connect( self.cb_reset)       
        self.statusBar.addPermanentWidget( reset)
        #
        # quit
        #
        quit = QPushButton("&Quit")
        quit.clicked.connect( self.cb_close)       
        self.statusBar.addPermanentWidget( quit)
        return 
    #
    #  === callbacks
    #
    def cb_close( self):
        self.parent.oneShotOnOff = False
        self.parent.setCurrentIndices()
        self.parent.restart()
        self.close()
        return

    def posToSliderIndex( self, pos, min, max):
        """
        index/RESOLUTION = (pos - min)/ (max - min)
        index = (pos - min)/ (max - min)* RESOLUTION
        """
        return int( (pos - min)/ (max - min)*RESOLUTION)

    def sliderIndexToPos( self, index, min, max):
        """
        index/RESOLUTION = (pos - min)/ (max - min)
        index = (pos - min)/ (max - min)*RESOLUTION
        pos = index/RESOLUTION*(max - min) + min
        """
        return float( index)/ float(RESOLUTION)*(max - min) + min

    #
    # reset
    #
    def cb_reset( self):

        for strt in [ 'xStart', 'yStart', 'zStart']:
            if strt.upper() in self.parent.cfgHsh[self.var]: 
                setattr( self.parent, strt, self.parent.cfgHsh[self.var][ strt.upper()])
                self.strtHsh[ strt][ 'Slider'].setValue(
                    self.posToSliderIndex( getattr( self.parent, strt), 
                                           self.parent.cfgHsh[self.var][ '%sMIN' % strt.upper()], 
                                           self.parent.cfgHsh[self.var][ '%sMAX' % strt.upper()]))
            elif strt.upper() in self.parent.cfgHsh: 
                setattr( self.parent, strt, self.parent.cfgHsh[ strt.upper()])
                self.strtHsh[ strt][ 'Slider'].setValue(
                    self.posToSliderIndex( getattr( self.parent, strt), 
                                           self.parent.cfgHsh[ '%sMIN' % strt.upper()], 
                                           self.parent.cfgHsh[ '%sMAX' % strt.upper()]))
            else:
                print( "attractorHelperWidgets.startValues.cb_reset: something is wrong")
                
            self.strtHsh[ strt][ 'SliderLabel'].setText( "%s: %10.4f" % ( strt, getattr( self.parent, strt)))
            self.strtHsh[ strt][ 'LineEdit'].setText( "%g" % getattr( self.parent, strt))

        self.parent.apply()
        return


    



    
