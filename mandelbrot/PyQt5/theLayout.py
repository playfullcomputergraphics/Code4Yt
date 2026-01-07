#!/usr/bin/env python3
"""
"""
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys

class basicStructure( QMainWindow):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.setWindowTitle("The Layout")

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
        row += 1
        col = 0
        self.gridLayout.addWidget( QLabel( "cell(0,0)"), row, col)
        col = 1
        self.gridLayout.addWidget( QLabel( "cell(0,1)"), row, col)
        row += 1
        col = 0
        self.gridLayout.addWidget( QLabel( "cell(1,0)"), row, col)
        col = 1
        self.gridLayout.addWidget( QLabel( "cell(1,1)"), row, col)
        row += 1
        col = 0
        self.gridLayout.addWidget( QLabel( "Next line: only column 0 is populated with a QHLayout filled with a label and 2 checkboxes"), row, col, 1, 2)
        #
        # create a horizontal layout
        #
        hLayout = QHBoxLayout()
        #
        # add a label to the hlayout
        #
        self.cmapLbl = QLabel( "CMAP: hot")
        hLayout.addWidget( self.cmapLbl)
        #
        # add some extra space
        #
        hLayout.addStretch()
        #
        # add a checkbox
        #
        self.reversedCb = QCheckBox( "Reversed", self)
        hLayout.addWidget( self.reversedCb)
        #
        # and another checkbox
        #
        self.cyclicCb = QCheckBox( "Cyclic", self)
        hLayout.addWidget( self.cyclicCb)

        row += 1
        col = 0
        #
        # add the hlayout to the grid
        #
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        row += 1
        col = 0
        self.gridLayout.addWidget( QLabel( "Next line: addStretch() is inserted before or after the ComboBox"), row, col, 1, 2)
        #
        # maxIterM
        #
        self.maxIterMCombo = QComboBox()
        for elm in [ 512, 1024, 2048]:
            self.maxIterMCombo.addItem( str( elm))
        self.maxIterMCombo.setCurrentIndex( 0)
        self.maxIterMCombo.activated.connect( self.cb_maxIterMCombo )
        hLayout.addWidget( QLabel( 'MaxIterM'))
        hLayout.addStretch()
        hLayout.addWidget( self.maxIterMCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        hLayout = QHBoxLayout()
        #
        # maxIterJ
        #
        self.maxIterJCombo = QComboBox()
        for elm in [ 512, 1024, 2048]:
            self.maxIterJCombo.addItem( str( elm))
        self.maxIterJCombo.setCurrentIndex( 0)
        self.maxIterJCombo.activated.connect( self.cb_maxIterJCombo )
        hLayout.addWidget( QLabel( 'MaxIterJ'))
        hLayout.addWidget( self.maxIterJCombo)
        hLayout.addStretch()
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        row += 1
        col = 0
        self.gridLayout.addWidget( QLabel( "Next line: addStretch() is inserted after the slider"), row, col)
        # 
        # label and slider
        #
        hLayout = QHBoxLayout()
        self.cmapRotateSliderLbl = QLabel( "C-Index: %-4d" % 0)
        self.cmapRotateSliderLbl.setFixedWidth( 80)
        hLayout.addWidget( self.cmapRotateSliderLbl)

        self.cmapRotateSlider = QSlider(Qt.Horizontal)
        self.cmapRotateSlider.valueChanged.connect( self.cb_cmapRotateSlider)
        self.cmapRotateSlider.setMinimum( 0) 
        self.cmapRotateSlider.setMaximum( 1000)
        self.cmapRotateSlider.setFixedWidth( 350)
        hLayout.addWidget( self.cmapRotateSlider)
        hLayout.addStretch()

        row += 1 
        col = 0
        #
        # add the hlayout to the grid, using column span 2
        #
        self.gridLayout.addLayout( hLayout, row, col, 1, 2)
        hLayout = QHBoxLayout()

        #
        # horizontal line
        #
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        row += 1
        col = 0
        self.gridLayout.addWidget(line, row, col, 1, 2)
        #
        # add 2 label
        #
        row += 1
        col = 0
        self.gridLayout.addWidget( QLabel( "A string below the horizontal line"), row, col)

        #
        # logWidget
        #
        self.logWidget = QTextEdit()
        self.logWidget.setFixedHeight( 100)
        self.logWidget.setReadOnly( 1)
        row += 1
        col = 0
        self.gridLayout.addWidget( self.logWidget, row, col, 1, 2)

        self.logWidget.append( "mandelbrot.py uses a grid layout to organize widgets") 
        self.logWidget.append( "A grid cell can be filled with widgets or with layouts containing widgets") 
        self.logWidget.append( "A widget or a layout can span across several columns") 
        self.logWidget.append( "addSeparator() specifies where unused space is put") 
        self.logWidget.append( "A horizontal line divides the screen into groups of widgets") 
        self.logWidget.append( "This GUI has been created by theLayout.py") 
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
            "<h3> Help Widget</h3>"
            "This widget demonstrates the layout concept used in my PyQt5 applications"
            "<ul>"
            "<li> The overall structure is a QGridLayout </li>"
            "<li> QHBoxLayout widgets are used to collect widgets to be inserted in a cell </li>"
            "<li> Horizontal lines are useful to separate groups of widgets </li>"
            "</ul>"
                ))

    def cb_close( self):
        self.close()
        print( "cb_close: good bye") 
        return 

    def cb_cmapRotateSlider( self, colorIndex):
        self.rotateColorMapIndex = colorIndex
        self.cmapRotateSliderLbl.setText( "C-Index: %-4d" % colorIndex)
        return

    def cb_maxIterMCombo( self, i):
        self.logWidget.append( "cb_maxIterMCombo: %s, %s" %
                               (str( i), self.maxIterMCombo.currentText()))
        return 

    def cb_maxIterJCombo( self, i):
        self.logWidget.append( "cb_maxIterJCombo: %s, %s" %
                               (str( i), self.maxIterJCombo.currentText()))
        return
    
    def cb_clear( self):
        self.logWidget.clear()
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

    bs = basicStructure( app)

    sys.exit(app.exec_())
    return 

if __name__ == "__main__": 
    main()

