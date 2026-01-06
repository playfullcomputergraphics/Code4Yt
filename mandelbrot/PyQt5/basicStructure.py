#!/usr/bin/env python3

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys

class basicStructure( QMainWindow):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Basic Structure")

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
        
        row = 0
        col = 0
        self.gridLayout.addWidget( QLabel( "Hello"), row, col)

        col = 1
        self.gridLayout.addWidget( QLabel( "World"), row, col)

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
            "<h3> Help Widget</h3>"
            "This widget demonstrates the basic structure of a PyQt5 application including"
            "<ul>"
            "<li> Menubar with File and Help </li>"
            "<ul>"
            "<li> File </li>"
            "<li> Help </li>"
            "</ul>"
            "<li> Central part with </li>"
            "<ul>"
            "<li> grid layout</li>"
            "<li> label widget</li>"
            "<li> log widget</li>"
            "</ul>"
            "<li> Statusbar with Quit, shortcut Alt-q</li>"
            "</ul>"
                ))

    def cb_close( self):
        self.close()
        print( "cb_close: good bye") 
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

