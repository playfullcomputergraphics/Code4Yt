#!/usr/bin/env python3

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys

import sys
from pathlib import Path
parent = Path(__file__).resolve().parent.parent
sys.path.append(str(parent))
import utils

class smartCallbacks( QMainWindow):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Smart Callbacks")

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
        # Menu: File
        #
        self.fileMenu = self.menuBar.addMenu('&File')
        #
        # clear log widget
        #
        self.clearAction = QAction('Clear log widget', self)        
        self.clearAction.triggered.connect( self.cb_clear)
        self.fileMenu.addAction( self.clearAction)
        #
        # Action: exit
        #
        self.exitAction = QAction('&Exit', self)        
        self.exitAction.triggered.connect( self.cb_close)
        self.fileMenu.addAction( self.exitAction)
        #
        # Colors
        # 
        self.colorsMenu = self.menuBar.addMenu('Colors')
        for colorMapName in utils.CMAPS:
            temp = QAction( colorMapName, self)
            self.colorsMenu.addAction( temp)
            temp.triggered.connect( self.mkColorCb( colorMapName))
        self.colorsMenu.addSeparator()
        for colorMapName in utils.CMAPS_CYCLIC:
            temp = QAction( colorMapName, self)
            self.colorsMenu.addAction( temp)
            temp.triggered.connect( self.mkColorCb( colorMapName))
        #
        # AllColors
        #
        self.allColorsMenu = self.menuBar.addMenu('AllColors')
        for elm in list( utils.CMAPS_DCT.keys()):
            subMenu = self.allColorsMenu.addMenu( elm)
            for colorMapName in utils.CMAPS_DCT[elm]:
                temp = QAction( colorMapName, self)
                self.allColorsMenu.addAction( temp)
                temp.triggered.connect( self.mkColorCb( colorMapName))
        #
        # Menu: Help
        #
        self.menuBarRight = QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarRight, Qt.TopRightCorner)
        self.helpMenu = self.menuBarRight.addMenu('Help')
        self.menuBar.setCornerWidget( self.menuBarRight, Qt.TopRightCorner)
        #
        # Action: Widget
        #
        self.helpWidgetAction = self.helpMenu.addAction(self.tr("Widget"))
        self.helpWidgetAction.triggered.connect( self.cb_helpWidget)

        return

    #    
    # === the central part
    #    
    def prepareCentralPart( self):
        #
        # the central widget
        #
        w = QWidget()
        self.setCentralWidget( w)
        #
        # create a grid layout
        #
        self.gridLayout = QGridLayout()
        w.setLayout( self.gridLayout)

        row = -1
        #
        #
        # reversed
        #
        row += 1
        self.gridLayout.addWidget( QLabel( "Here is a simple example for an ordinary callback"),
                                   row, 0, 1, 2)
        # 
        self.reversedCb = QCheckBox( "Reversed", self) 
        self.reversedCb.clicked.connect( self.cb_reversed)
        row += 1
        col = 0
        self.gridLayout.addWidget( self.reversedCb, row, col)
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        
        row += 1
        self.gridLayout.addWidget( QLabel( "CMAP is set by Colors/AllColors from the menubar"),
                                   row, 0, 1, 2)
        row += 1
        self.gridLayout.addWidget( QLabel( "We have to distinguish between Colors and AllColors"),
                                   row, 0, 1, 2)
        row += 1
        self.gridLayout.addWidget( QLabel( "Colors are frequently used colors, AllColors are all colors"),
                                   row, 0, 1, 2)
        row += 1
        self.gridLayout.addWidget( QLabel( "This way quite a number of colors are nicely organised"),
                                   row, 0, 1, 2)
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)
        #
        # 
        #
        row += 1
        col = 0
        self.cmapLbl = QLabel( "CMAP: hot")
        self.gridLayout.addWidget( self.cmapLbl, row, col)

        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)

        row += 1
        self.gridLayout.addWidget( QLabel( "For demonstration purpose: Colors/AllColors from ComboBoxes"), row, 0, 1, 2)
        
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( "Colors"))
        self.colorCombo = QComboBox()
        for elm in utils.CMAPS:
            self.colorCombo.addItem( str( elm))
        for elm in utils.CMAPS_CYCLIC:
            self.colorCombo.addItem( str( elm))
        self.colorCombo.setCurrentIndex( 0)
        self.colorCombo.activated.connect( self.cb_colorCombo )
        hLayout.addWidget( self.colorCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)

        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( "AllColors"))
        self.allColorCombo = QComboBox()
        for elm in list( utils.CMAPS_DCT.keys()):
            for colorMapName in utils.CMAPS_DCT[elm]:
                self.allColorCombo.addItem( "%s" % (str( colorMapName)))
        self.allColorCombo.activated.connect( self.cb_allColorCombo )
        hLayout.addWidget( self.allColorCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
        self.gridLayout.addWidget(line, row, 0, 1, 2)

        row += 1
        self.gridLayout.addWidget( QLabel( "Conclusion: ComboBoxes are inapropriate for this purpose."), row, 0, 1, 2)
        row += 1
        self.gridLayout.addWidget( QLabel( " -> Need menubar menus with many QActions and many callbacks"), row, 0, 1, 2)
        row += 1
        self.gridLayout.addWidget( QLabel( " -> These callbacks have to created automatically"), row, 0, 1, 2)

        #
        # logWidget
        #
        self.logWidget = QTextEdit()
        self.logWidget.setFixedHeight( 100)
        self.logWidget.setReadOnly( 1)
        row += 1
        col = 0
        self.gridLayout.addWidget( self.logWidget, row, col, 1, 2)

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
        self.statusBar.addPermanentWidget( quit) # right lower corner
        return 
    #
    # the callback functions
    #
    def cb_helpWidget(self):
        QMessageBox.about(self, self.tr("Help Widget"), self.tr(
            "<h3> Help Smart Callbacks</h3>"
            "This widget demonstrates the use of smart callbacks in PyQt5 applications"
                ))

    def cb_close( self):
        self.close()
        print( "cb_close: good bye") 
        return
    
    # 
    def mkColorCb( self, colorMapName):
        def f():
            self.cmapLbl.setText( "CMAP: %s" % colorMapName)
            self.logWidget.append( "mkColorCb: you selected %s" % colorMapName)
            return 
        return f

    def cb_colorCombo( self, i):
        self.cmapLbl.setText( "CMAP %s" % self.colorCombo.currentText())
        self.logWidget.append( "cb_colorCombo: index %d, %s" % ( i, self.colorCombo.currentText()))
        return 

    def cb_allColorCombo( self, i):
        self.cmapLbl.setText( "CMAP %s" % self.allColorCombo.currentText())
        self.logWidget.append( "cb_colorCombo: index %d, %s" % ( i, self.allColorCombo.currentText()))
        return 

    def cb_clear( self):
        self.logWidget.clear()
        return

    # 
    def cb_reversed( self, i):
        self.logWidget.append( "cb_reversed: called with %s" % repr( i)) 
        return 
    
def main(): 
    #
    # QApplication:
    #  - singleton
    #  - initialisations
    #  - sys.argv specifies user preferences: fonts, color themes, etc.
    #  - exec_() starts the event loop, waiting for signals
    #
    app = QApplication( sys.argv)

    sc = smartCallbacks( app)

    sys.exit(app.exec_())
    return 

if __name__ == "__main__": 
    main()

