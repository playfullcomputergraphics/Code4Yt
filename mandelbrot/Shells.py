#!/use/bin/env python3

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import PGViewer
import MPLViewer
import numpy as np
import matplotlib 

class ViewerShell(QWidget):
    
    clickedMB1 = pyqtSignal(float, float)
    clickedShiftMB1 = pyqtSignal( int, int, float, float, str)
    clickedMB2 = pyqtSignal(float, float)
    clickedMB3 = pyqtSignal( float, float)
    deltaLbl = pyqtSignal( str)
    coloringOutput = pyqtSignal( np.ndarray, matplotlib.image.AxesImage) 
    
    def __init__(self, parent = None, app = None, colorPars = None, title = ""):
        super().__init__()
        self.name = "ViewerShell"
        self.parent = parent
        self.title = title
        #print( "%s.__init__() parent.name %s title %s" % ( self.name, self.parent.name, title))
        self.pg = PGViewer.Viewer( parent = self, app = app, colorPars = colorPars)
        self.mpl = MPLViewer.Viewer( parent = self, app = app, colorPars = colorPars)

        self.stack = QStackedLayout()
        self.stack.addWidget(self.pg)
        self.stack.addWidget(self.mpl)

        layout = QVBoxLayout()
        layout.addLayout(self.stack)
        self.setLayout(layout)

        self.current = "pg"
        self.setWindowTitle( "%s (PG)" % self.title)
        self._connect_engine_signals()

    def _connect_engine_signals(self):
        # PG → Shell
        self.pg.clickedMB1.connect(self.clickedMB1)
        self.pg.clickedShiftMB1.connect(self.clickedShiftMB1)
        self.pg.clickedMB2.connect(self.clickedMB2)
        self.pg.clickedMB3.connect(self.clickedMB3)
        self.pg.deltaLbl.connect(self.deltaLbl)
        #self.pg.coloringOutput.connect(self.coloringOutput)

        # MPL → Shell
        self.mpl.clickedMB1.connect(self.clickedMB1)
        self.mpl.clickedShiftMB1.connect(self.clickedShiftMB1)
        self.mpl.clickedMB2.connect(self.clickedMB2)
        self.mpl.clickedMB3.connect(self.clickedMB3)
        self.mpl.deltaLbl.connect(self.deltaLbl)
        self.mpl.coloringOutput.connect(self.coloringOutput)
        
    def showPG(self):
        self.current = "pg"
        self.stack.setCurrentWidget( self.pg)
        self.setWindowTitle( "%s (PG)" % self.title)
        self.show()

    def showMPL(self):
        self.current = "mpl"
        self.stack.setCurrentWidget( self.mpl)
        self.setWindowTitle( "%s (MPL)" % self.title)
        self.show()

    def updateImage(self, data):
        if self.current == "pg":
            self.pg.updateImage(data)
        else:
            self.mpl.updateImage(data)

    def setColor(self):
        if self.current == "pg":
            self.pg.setColor()
        else:
            self.mpl.setColor()

    def setResetMarkerColor(self, color):
        if self.current == "pg":
            self.pg.setResetMarkerColor( color)
        else:
            self.mpl.setResetMarkerColor( color)

    def setResetMarker(self):
        if self.current == "pg":
            self.pg.setResetMarker()
        else:
            self.mpl.setResetMarker()

    def clearResetMarker(self):
        if self.current == "pg":
            self.pg.clearResetMarker()
        else:
            self.mpl.clearResetMarker()

    def setDebugColoring( self, temp):
        if self.current == "pg":
            self.pg.setDebugColoring( temp)
        else:
            self.mpl.setDebugColoring( temp)

    def addMarker(self, item, layer="default", ignoreBounds=True):
        if self.current == "pg":
            #if layer not in self.pg._layers:
            #    self._layers[layer] = []
            #self.pg._layers[layer].append(item)
            self.pg.viewBox.addItem(item, ignoreBounds=ignoreBounds)

    def removeItem( self, temp): 
        self.pg.plot.getViewBox().removeItem( temp)
            
    def addText( self, x, y, txt, color='cyan', fontsize = 20, horizontalalignment='center', verticalalignment='center'):
        if self.current == "mpl":
            t = self.mpl.fig.text( x, y, txt,
                                   color='cyan',
                                   fontsize = 20, 
                                   horizontalalignment='center', 
                                   verticalalignment='center',
                                   transform = self.mpl.ax.transData) 
            self.mpl.canvas.draw()
            return t

    def connectOnMouseMoved( self, flag):
        if self.current == "mpl":
            self.mpl.connectOnMouseMoved( flag)
        else: 
            self.pg.connectOnMouseMoved( flag)
            
        return 
            
