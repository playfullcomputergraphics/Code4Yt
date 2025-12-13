#!/usr/bin/env python

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import glob, os, math
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
import numpy as np

CMAP_MAX = 1024 # appears also in mandelbrot.py

class ClickableThumbnail(QLabel):
    clickedMbLeft = pyqtSignal(str)  # Emit the image path
    clickedMbRight = pyqtSignal(str)  # Emit the image path
    clickedMbMiddle = pyqtSignal(str)  # Emit the image path

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
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

class places( QMainWindow):
    def __init__(self, app, parent=None):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle("Places")
        self.app = app
        self.parent = parent
        geoScreen = QDesktopWidget().screenGeometry(-1)
        self.geoWidth = geoScreen.size().width()
        self.geoHeight = geoScreen.size().height()

        font = QFont( 'Sans Serif')
        if self.geoWidth <= 1920:
            font.setPixelSize( 16)
        else:
            font.setPixelSize( 22)
        self.app.setFont( font)

        self.w = None
        self.gridLayout = None
        self.scrollArea = None

        screens = self.app.screens()
        if len( screens) > 1:
            #self.setFixedSize( 562, 664)
            self.setGeometry( screens[1].geometry().x() + 870,
                              screens[1].geometry().y() + 10, 500, 500)
            self.show() # placing show() before the next statement is important!
            self.app.processEvents()
        self.show()
        self.parent.logWidget.append( "self.geometry() %s" %
                               ( repr( self.geometry())))
        
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
        #
        # Widget
        #
        self.widgetAction = self.helpMenu.addAction(self.tr("Widget"))
        self.widgetAction.triggered.connect( self.cb_helpWidget)
        return
    #    
    # === the central part
    #    
    def prepareCentralPart( self):

        if self.scrollArea is None: 
            self.scrollArea = QScrollArea()
            self.scrollArea.setWidgetResizable(True)
            self.scrollArea.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
            self.scrollArea.setMinimumWidth( 800)

        if self.w is None: 
            self.w = QWidget()
            self.scrollArea.setWidget(self.w)
            self.setCentralWidget(self.scrollArea)

        if self.gridLayout is None:
            self.gridLayout = QGridLayout()
            self.w.setLayout( self.gridLayout)
        else:
            # Clear existing thumbnails
            while self.gridLayout.count():
                item = self.gridLayout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                    
        self.thumbnails = glob.glob( "./places/*.png")
        self.thumbnails.sort( key=os.path.getmtime)
        self.thumbnails.reverse()
        ncol = int( math.sqrt( len( self.thumbnails)))
        for i, path in enumerate( self.thumbnails):
            thumb = ClickableThumbnail( path)
            thumb.setPixmap(QPixmap(thumb.image_path).scaled(150, 150))
            thumb.clickedMbLeft.connect( self.mkFileReadCb( path))
            thumb.clickedMbRight.connect( self.mkFileDeleteCb( path))
            thumb.clickedMbMiddle.connect( self.mkShowPngCb( path))
            self.gridLayout.addWidget( thumb, i // ncol, i % ncol) 

        return 
    #
    # === the status bar
    #
    def prepareStatusBar( self): 
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)
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
    def cb_helpWidget(self):
        QMessageBox.about(self, self.tr("Help Widget"), self.tr(
            "<h3> Help</h3>"
            "The Places feature displays .png files that have been created by mandelbrot.py. The files contain meta data that can be loaded into mandelbot.py to fully restore the state of the program at the specific place"
            "<ul>"
            "<li> MB-left - Read the meta data from .png and load then into the application.</li>"
            "<li> MB-right - Delete .png file</li>"
            "<li> MB-middle - Display .png file as image</li>"
            "</ul>" 
                ))
    def cb_close( self):
        self.close()
        return

    def mkFileReadCb( self, fName):
        def f():
            image = Image.open(fName)
            hsh = image.info
            image.close()
            self.parent.logWidget.append( "Reading %s" % ( fName))
            print( "Reading %s" % ( fName))
            for elm in hsh:
                print( "  %-14s : %s" % ( elm, hsh[ elm]))
            print( "Reading Done")

            self.parent.cxM = float( hsh[ 'cxM'])
            self.parent.cyM = float( hsh[ 'cyM'])
            self.parent.deltaM = float( hsh[ 'deltaM'])

            self.parent.colorMapName = hsh[ 'colorMapName']
            try: 
                self.parent.rotateColorMapIndex = int( hsh[ 'rotateColorMapIndex'])
            except: 
                try: 
                    self.parent.rotateColorMapIndex = int( hsh[ 'rotateColorMap'])
                except:
                    self.parent.rotateColorMapIndex = 0
                    
            self.parent.flagReversed = "False"
            try: 
                self.parent.flagReversed = hsh[ 'flagReversed']
            except:
                pass

            self.parent.norm = hsh[ 'norm']
            if self.parent.norm == "LinNormR":
                self.parent.norm = "LinNorm"
                self.parent.flagReversed = "True"
                
            self.parent.normPar = float( hsh[ 'normPar'])
            
            self.parent.band = "False"
            try: 
                self.parent.band = hsh[ 'band']
            except:
                pass

            self.parent.setColor( self.parent.colorMapName,
                                  self.parent.rotateColorMapIndex,
                                  self.parent.band)
            
            self.parent.widthM = int( hsh[ 'widthM'])
            self.parent.widthJ = int( hsh[ 'widthJ'])
            self.parent.modulo = int( hsh[ 'modulo'])
            self.parent.smooth = hsh[ 'smooth']
            self.parent.maxIterM = int( hsh[ 'maxIterM'])
            self.parent.maxIterJ = int( hsh[ 'maxIterJ'])
            self.parent.power = int( hsh[ 'power'])
            

            self.parent.clip = "False"
            try: 
                self.parent.clip = hsh[ 'clip']
            except:
                pass
            self.parent.vmin = 0
            try: 
                self.parent.vmin = float( hsh[ 'vmin'])
            except:
                pass
            self.parent.vmax = 1024
            try: 
                self.parent.vmax = float( hsh[ 'vmax'])
            except:
                pass
            self.parent.shaded = hsh[ 'shaded']
            self.parent.scanCircle = hsh[ 'scanCircle']
            self.parent.vert_exag = 1.
            try: 
                self.parent.vert_exag = float( hsh[ 'vert_exag'])
            except:
                pass
            self.parent.interpolation = hsh[ 'interpolation']
            self.parent.blendMode = hsh[ 'blendMode']
            self.parent.azDeg = int( hsh[ 'azDeg'])
            self.parent.altDeg = int( hsh[ 'altDeg'])

            
            #self.parent.colorMap = plt.get_cmap( self.parent.colorMapName)
            #frac = 1. - float( self.parent.rotateColorMapIndex)/float( CMAP_MAX - 1)
            #self.parent.colorMapCurrent = self.parent.shiftCmap( self.parent.colorMap, frac)

            self.parent.setCurrentIndices()        

            self.parent.calcMandelbrotSet()
            self.parent.showMandelbrotSet()
            self.parent.calcJuliaSet()
            self.parent.showJuliaSet()
            
            return
        return f

    def clearGridLayout( self):
        print( "clearGrid ") 
        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        print( "clearGrid DONE")
        return 
                
    def mkFileDeleteCb( self, fName):
        def f():
            yesNo = QMessageBox()
            ret = yesNo.question(self,'', "Delete %s" % fName, yesNo.Yes | yesNo.No)
            if ret == yesNo.Yes:
                os.remove( fName)
                self.parent.logWidget.append( "Deleted %s" % fName)
                self.prepareCentralPart()
                
            else: 
                self.parent.logWidget.append( "Aborted")
                       
            return
        return f
                
    def mkShowPngCb( self, fName):
        def f():
            plt.figure(1) 
            img = np.asarray(Image.open( fName))

            self.parent.imageMandelbrotSet.set( data = img)
            return
        return f

