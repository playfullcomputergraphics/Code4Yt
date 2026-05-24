#!/usr/bin/env python

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import glob, os, math
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
import numpy as np
import utils

THUMB_SIZE = 180


class places( QMainWindow):
    def __init__(self, app, parent=None, prefix = None, viewerFk = None):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle("Places (MB-Left reads a file incl. metadata, MB-Right deletes, MB-Middle shows)")
        self.app = app
        self.name = "places"
        self.parent = parent
        self.prefix = prefix
        self.viewerFk = viewerFk
        if self.prefix is None:
            self.prefix = "MB"
        geoScreen = QDesktopWidget().screenGeometry(-1)
        self.geoWidth = geoScreen.size().width()
        self.geoHeight = geoScreen.size().height()

        self.w = None
        self.gridLayout = None
        self.scrollArea = None

        screens = self.app.screens()
        if len( screens) > 1:
            #self.setFixedSize( 562, 664)
            self.setGeometry( screens[1].geometry().x() + 870,
                              screens[1].geometry().y() + 10, 1000, 500)
        else:
            self.setFixedSize( 1000, 630)
            
        self.app.processEvents()

        if self.prefix == "DynOp":
            self.path2Lbl = {}
        else:
            self.path2Lbl = None
        
        self.prepareMenuBar()
        self.prepareCentralWidget()
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
    def prepareCentralWidget( self):

        if self.scrollArea is None: 
            self.scrollArea = QScrollArea()
            self.scrollArea.setWidgetResizable(True)
            #self.scrollArea.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
            #self.scrollArea.setMinimumWidth( 1000)

        if self.w is None: 
            self.w = QWidget()
            self.scrollArea.setWidget(self.w)
            self.setCentralWidget(self.scrollArea)

        if self.viewerFk is not None and len( self.viewerFk.arrFkPath) > 0:
            for elm in self.viewerFk.arrFkPath:
                elm.setParent( None)
            self.viewerFk.arrFkPath = []
            
        if self.gridLayout is None:
            self.gridLayout = QGridLayout()
            self.w.setLayout( self.gridLayout)
        else:
            self.clear_layout( self.gridLayout) 
        #
        # find the temporary files: MB_, DynOp_
        #
        self.thumbnails = glob.glob( "./places/%s_*.png" % self.prefix)
        self.thumbnails.sort( key=os.path.getmtime)
        self.thumbnails.reverse()
        #ncol = int( math.sqrt( len( self.thumbnails)))
        ncol = 5

        iOff = 0
        row = 0
        self.checkBoxes = []
        self.setStyleSheet("QLabel { font-size: 10pt; }")
        # +++
        for i, path in enumerate( self.thumbnails):
            thumb = utils.ClickableThumbnail( path, parent = self)
            thumb.setPixmap(QPixmap(thumb.image_path).scaled( THUMB_SIZE, THUMB_SIZE))
            thumb.clickedMbLeft.connect( self.mkFileReadCb( path))
            thumb.clickedMbRight.connect( self.mkFileDeleteCb( path))
            thumb.clickedMbMiddle.connect( self.mkShowPngCb( path))
            vLayout = QVBoxLayout()
            vLayout.addWidget( thumb)
            temp = QCheckBox( utils.formatThumbLabel( path))
            self.checkBoxes.append( (temp, path))
            vLayout.addWidget( temp) 
            row = (i // ncol)
            col = i % ncol
            self.gridLayout.addLayout( vLayout, row, col)
            if self.prefix == "DynOp":
                lbl = utils.handleFeedAndKillRate( path, self.viewerFk)
                self.path2Lbl[ path] = lbl
        iOff = row

        iOff += 1
        #
        # horizontal line
        # named files
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.gridLayout.addWidget(line, iOff, 0, 1, ncol)
        iOff += 1
        
        self.gridLayout.addWidget( QLabel( "Named .png  files"), iOff, 0)
        iOff += 1
        #
        # find the named files: MBN_, DynOpN_
        #
        self.thumbnails = glob.glob( "./places/%sN_*.png" % self.prefix)
        #self.thumbnails.sort( key=os.path.getmtime)
        self.thumbnails.sort()
        #self.thumbnails.reverse()
        for i, path in enumerate( self.thumbnails):
            thumb = utils.ClickableThumbnail( path, parent = self)
            thumb.setPixmap(QPixmap(thumb.image_path).scaled( THUMB_SIZE, THUMB_SIZE))
            thumb.clickedMbLeft.connect( self.mkFileReadCb( path))
            thumb.clickedMbRight.connect( self.mkFileDeleteCb( path))
            thumb.clickedMbMiddle.connect( self.mkShowPngCb( path))
            vLayout = QVBoxLayout()
            vLayout.addWidget( thumb)
            vLayout.addWidget( QLabel( path.split('/')[-1]))
            row = (i // ncol) + iOff
            col = i % ncol
            self.gridLayout.addLayout( vLayout, row, col) 
            if self.prefix == "DynOp":
                lbl = utils.handleFeedAndKillRate( path, self.viewerFk)
                self.path2Lbl[ path] = lbl
        iOff = row

        iOff += 1
        #
        # horizontal line
        # named and published files
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.gridLayout.addWidget(line, iOff, 0, 1, ncol)
        iOff += 1
        
        self.gridLayout.addWidget( QLabel( "Named and published files"), iOff, 0)
        iOff += 1
        #
        # find the published files: MBNP_, DynOpNP_
        #
        self.thumbnails = glob.glob( "./places/%sNP_*.png" % self.prefix)
        self.thumbnails.sort( key=os.path.getmtime)
        self.thumbnails.reverse()
        for i, path in enumerate( self.thumbnails):
            thumb = utils.ClickableThumbnail( path, parent = self)
            thumb.setPixmap(QPixmap(thumb.image_path).scaled( THUMB_SIZE, THUMB_SIZE))
            thumb.clickedMbLeft.connect( self.mkFileReadCb( path))
            thumb.clickedMbRight.connect( self.mkFileDeleteCb( path))
            thumb.clickedMbMiddle.connect( self.mkShowPngCb( path))
            vLayout = QVBoxLayout()
            vLayout.addWidget( thumb)
            vLayout.addWidget( QLabel( path.split('/')[-1]))
            row = (i // ncol) + iOff
            col = i % ncol
            self.gridLayout.addLayout( vLayout, row, col) 
            if self.prefix == "DynOp":
                lbl = utils.handleFeedAndKillRate( path, self.viewerFk)
                self.path2Lbl[ path] = lbl

        return 
    #
    # === the status bar
    #
    def prepareStatusBar( self): 
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)
        #
        # Delete
        #
        temp = QPushButton("Delete")
        temp.clicked.connect( self.cb_delete)       
        self.statusBar.addWidget( temp)
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
    def cb_delete( self):
        for elm in self.checkBoxes:
            if elm[0].isChecked():
                os.remove( elm[1])
                self.parent.logWidget.append( "Deleted %s" % elm[1])
        self.prepareCentralWidget()

        return
    
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
        #self.close()
        self.hide()
        return

    def mkFileReadCb( self, fName):
        #print( "%s.mkFileReadCb for %s" % (self.name, fName))
        def f():
            self.cb_close()

            if self.parent.name == "MBSMainWindow":
                mbsObj = self.parent
                dynOpObj = self.parent.operatorWidget
                colorWidgetObj = self.parent.colorWidget
                colorParsObj = self.parent.colorPars
            else: 
                mbsObj = None
                dynOpObj = self.parent
                colorWidgetObj = self.parent.colorWidget
                colorParsObj = self.parent.colorPars
                
            utils.readPng( fName,
                           MBSObj = mbsObj, 
                           DynOpObj = dynOpObj,
                           ColorWidgetObj = colorWidgetObj,
                           ColorParsObj = colorParsObj)
            
            return
        return f

    def clearGridLayout( self):
        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        return 
                
    def mkFileDeleteCb( self, fName):
        def f():
            yesNo = QMessageBox()
            ret = yesNo.question(self,'', "Delete %s" % fName, yesNo.Yes | yesNo.No)
            if ret == yesNo.Yes:
                if fName.find( "MBN_") > 0 or fName.find( "MBNP_") > 0:
                    ret = yesNo.question(self,'', "Really delete a MBN_ or MBNP_ file",
                                         yesNo.Yes | yesNo.No)
                    if ret == yesNo.No:
                        return 

                os.remove( fName)
                self.parent.logWidget.append( "Deleted %s" % fName)
                self.prepareCentralWidget()
                
            else: 
                self.parent.logWidget.append( "Aborted")
                       
            return
        return f
                
    def mkShowPngCb( self, fName):
        def f():
            self.parent.viewerMain.displayPng( fName)
            return

        return f


            

