#!/usr/bin/env python

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import glob, os, math
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
import numpy as np
from PIL import Image

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
        
        self.setWindowTitle("Places (MB-Left reads a file incl. metadata, MB-Right deletes, MB-Middle shows)")
        self.app = app
        self.parent = parent
        geoScreen = QDesktopWidget().screenGeometry(-1)
        self.geoWidth = geoScreen.size().width()
        self.geoHeight = geoScreen.size().height()

        """
        font = QFont( 'Sans Serif')
        if self.geoWidth <= 1920:
            font.setPixelSize( 16)
        else:
            font.setPixelSize( 22)
        self.app.setFont( font)
        """
        self.w = None
        self.gridLayout = None
        self.scrollArea = None

        screens = self.app.screens()
        if len( screens) > 1:
            #self.setFixedSize( 562, 664)
            self.setGeometry( screens[1].geometry().x() + 870,
                              screens[1].geometry().y() + 10, 1000, 500)
        self.show() # placing show() before the next statement is important!
        self.app.processEvents()
        
        self.prepareMenuBar()
        self.prepareCentralPart()
        self.prepareStatusBar()
        self.show()

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

    def clear_layout(self, layout):
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)

            if item.layout():
                self.clear_layout(item.layout())
                item.layout().deleteLater()

            elif item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
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
            self.clear_layout( self.gridLayout) 
                    
        self.thumbnails = glob.glob( "./places/MB_*.png")
        self.thumbnails.sort( key=os.path.getmtime)
        self.thumbnails.reverse()
        #ncol = int( math.sqrt( len( self.thumbnails)))
        ncol = 5

        iOff = 0
        self.setStyleSheet("QLabel { font-size: 10pt; }")
        for i, path in enumerate( self.thumbnails):
            thumb = ClickableThumbnail( path)
            thumb.setPixmap(QPixmap(thumb.image_path).scaled(150, 150))
            thumb.clickedMbLeft.connect( self.mkFileReadCb( path))
            thumb.clickedMbRight.connect( self.mkFileDeleteCb( path))
            thumb.clickedMbMiddle.connect( self.mkShowPngCb( path))
            vLayout = QVBoxLayout()
            vLayout.addWidget( thumb)
            temp = QLabel( path.split('/')[-1])
            vLayout.addWidget( temp)
            
            row = (i // ncol)
            col = i % ncol
            self.gridLayout.addLayout( vLayout, row, col)
            iOff = row

        iOff += 1
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.gridLayout.addWidget(line, iOff, 0, 1, ncol)
        iOff += 1
        
        self.gridLayout.addWidget( QLabel( "Named .png  files"), iOff, 0)
        iOff += 1
        self.thumbnails = glob.glob( "./places/MBN_*.png")
        self.thumbnails.sort( key=os.path.getmtime)
        self.thumbnails.reverse()
        for i, path in enumerate( self.thumbnails):
            thumb = ClickableThumbnail( path)
            thumb.setPixmap(QPixmap(thumb.image_path).scaled( 150, 150))
            thumb.clickedMbLeft.connect( self.mkFileReadCb( path))
            thumb.clickedMbRight.connect( self.mkFileDeleteCb( path))
            thumb.clickedMbMiddle.connect( self.mkShowPngCb( path))
            vLayout = QVBoxLayout()
            vLayout.addWidget( thumb)
            vLayout.addWidget( QLabel( path.split('/')[-1]))
            row = (i // ncol) + iOff
            col = i % ncol
            self.gridLayout.addLayout( vLayout, row, col) 

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
            self.parent.readFile( fName)
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
            if fName.find( "MBN_") > 0:
                self.parent.logWidget.append( "MBN_ files are not deleted this way")
                return
                
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
            self.parent.imM.set( data = img)
            return
        return f

