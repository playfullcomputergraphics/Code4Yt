#!/usr/bin/env python3
"""
"""
import sys
sys.path.append( "/home/kracht/gitlabDESY/hasyutils")
import HasyUtils

import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import utils
import colorsys
from PyQt5.QtGui import QTransform
import traceback
from scipy.ndimage import gaussian_filter
from PIL import Image
import matplotlib 
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

#
# beware of typos, check whether a member is in the list of known members
#
METADATA_MEMBERS = []
VIEWER_Attrs = METADATA_MEMBERS + \
    [ 'parent', 'name', 'app', 'modeOperation', 'screen', 'dpi', 'screenWidthIn',
      'screenHeightIn', 'figSizeC', 'figSizeHuge', 'figSizeLarge', 'figSizeBig',
      'figSizeMedium', 'figSizeSmall', 'figSizeTiny', 'figSizeM', 'figSizeJ',
      'figSize3D', 'fig', 'ax', 'mgr', 'geoM', 'mandelbrotKeyclick', 'image', 
      'resetMarker', 'textTitle', 'backgroundColor', 'xmin', 'xmax', 'ymin', 'ymax',
      'canvas', 'cbar', 'colorPars', 'axDebugColoring', 'iterPath', 'mouseMoved',
      'debugColoring', 
     ]

class Viewer(QWidget):
    """
    High‑performance PyQtGraph viewer for Mandelbrot / Gray‑Scott fields.
    Drop‑in replacement for your matplotlib imshow pipeline.
    """
    clickedMB1 = pyqtSignal(float, float)
    clickedShiftMB1 = pyqtSignal( int, int, float, float, str)
    clickedMB2 = pyqtSignal(float, float)
    clickedMB3 = pyqtSignal( float, float)
    deltaLbl = pyqtSignal( str)
    coloringOutput = pyqtSignal( np.ndarray, matplotlib.image.AxesImage) 
    def __init__(self,
                 parent=None,
                 colorPars = None,
                 app =  None,
                 modeOperation = None,
                 colormap="hot",
                 title = ""):

        super().__init__()

        self.parent = parent
        self.name = "MPLViewer"
        self.app = app
        self.modeOperation = modeOperation
        self.colorPars = colorPars
        self.setWindowTitle( "%s (MPL)" % title)
        #print( "MPLViewer.__init__(): self.parent.name %s self.parent.parent %s title %s" %
        #       (self.parent.name, self.parent.parent.name, title))

        self.findFigSizes()
        #
        # matplotlib interactive mode
        #
        plt.ion()

        self.initMembers()
        self.setDefaults()

        self.setColor()

        self.prepareFigure()
        
        #self.show()
        # '#efefef'
        self.backgroundColor = self.palette().color( self.backgroundRole()).name()

        #self.setGeometry(50, 50, 500, 500)
        """
        if self.modeOperation.lower() == 'demo': 
            screens = self.app.screens()
            if len( screens) < 2:
                print( "\n__init__(): demo mode only at DownPc, exiting\n") 
                sys.exit( 255) 
            #self.setFixedSize( 562, 664)
            self.setGeometry( screens[1].geometry().x() + 870,
                              screens[1].geometry().y() + 10, 586, 650)
            self.show() # placing show() before the next statement is important!

            self.operatorWidget.setGeometry(5149, 923, 580, 630)
            self.app.processEvents()
        """
        
        #
        # make sure MBS_ATTR is not polluted
        # 
        for name in VIEWER_Attrs:
            try:
                temp = getattr( self, name)
            except:
                #print( "__init__: %s is not in self" % name)
                pass
        
        return

    def __setattr__( self, name, value):
        """
        +++
        this function protects agains typos. members can only be set, 
        if they have been defined
        """
        #print( "mandelbrotSetWidget.__setattr__: name %s, value %s" % (name, value))
        if name in VIEWER_Attrs: \
            super( Viewer, self).__setattr__(name, value)
        else:
            print( " unknown attribute (MPLViewer): '%s'," %  name)
            super( Viewer, self).__setattr__(name, value)
            #raise ValueError( "MPLViewer.__setattr__: unknown attribute %s" % ( name))

    def setDefaults( self):
        
        return 
    
    def initMembers( self):

        self.axDebugColoring = None
        self.cbar = None
        self.fig = None
        self.image = None
        self.iterPath = None
        self.debugColoring = False
        
        return 
    #
    # === callbacks
    #
    def closeEvent( self, event):
        #print( "%s.closeEvent parent %s" % ( self.name, self.parent.name))
        plt.close( self.fig)
        self.fig = None
        
        #self.hide()
        #event.ignore()
        return

    def on_key_press(self, event):
        print(f"Matplotlib key pressed: {event.key}")

    def cb_onMouseClicked(self, event):
        wx = event.xdata
        wy = event.ydata
        #print( "%s.cb_onMouseClicked: wx %g wy %g" % ( self.name, wx, wy))
        #
        # MB-Left: Zoom-in
        #
        if event.button is MouseButton.LEFT:
            self.clickedMB1.emit(wx, wy)
        elif event.button is MouseButton.MIDDLE:
            self.clickedMB2.emit(wx, wy)
        elif event.button is MouseButton.RIGHT:
            self.clickedMB3.emit(wx, wy)
        
        return

    def connectOnMouseMoved(self, flag):
        
        #print("%s.connectOnMouseMoved %s" % ( self.name, repr(flag)))

        if flag:
            self.mouseMoved = self.fig.canvas.mpl_connect( 'motion_notify_event', 
                                                           self.cb_onMouseMoved)

        else:
            self.fig.canvas.mpl_disconnect( self.mouseMoved)
            if self.iterPath is not None:
                self.iterPath.remove()
                self.iterPath = None
                self.ax.figure.canvas.draw_idle()            

        return 
    
    def cb_onMouseMoved(self, event):

        if event is None: 
            return
        if event.inaxes is None:
            return
        
        wx = event.xdata
        wy = event.ydata
        #print( "%s.cb_onMouseMoved: wx %g wy %g" % ( self.name, wx, wy))
        self.handleIterPath( event) 
        return

    def handleIterPath( self, event):
        wx = event.xdata
        wy = event.ydata
        #
        # Z**2 = (x**2 - y**2) + i*x*y
        #
        x = []
        y = []
        x.append( wx)
        y.append( wy)
        for n in range( 100):
            x.append( x[n-1]**2 - y[n-1]**2 + wx)
            y.append( 2.*x[n-1]*y[n-1] + wy)
            if (x[-1]**2 + y[-1]**2) > 20:
                break

        if self.iterPath is None: 
            self.iterPath, = self.ax.plot( x, y, linewidth = 0.75, color = 'white')
            x0 = self.parent.parent.cxM - self.parent.parent.deltaM/2.
            x1 = self.parent.parent.cxM + self.parent.parent.deltaM/2.
            y0 = self.parent.parent.cyM - self.parent.parent.deltaM/2.
            y1 = self.parent.parent.cyM + self.parent.parent.deltaM/2.
            
            #self.ax.set_xlim([ self.parent.parent.cxM - self.parent.parent.deltaM/2.,
            #                   self.parent.parent.cxM + self.parent.parent.deltaM/2.])
            #self.ax.set_ylim([ self.parent.parent.cyM - self.parent.parent.deltaM/2.,
            #                   self.parent.parent.cyM + self.parent.parent.deltaM/2.])
        else: 
            self.iterPath.set_data( x, y)
        self.ax.figure.canvas.draw_idle()            
        return
    
    def rotateColorMapFunc( self, shiftIndex):
        #
        # rotate only the first 1023 colors, leaving black, the last one, in place
        #
        rotatable = self.colorPars.colorMap.colors[:-1]
        fixed = self.colorPars.colorMap.colors[-1:]
        rotated = np.roll( rotatable, shift = shiftIndex, axis = 0)
        rotated_colors = np.vstack( (rotated, fixed))
        self.colorPars.colorMap = matplotlib.colors.ListedColormap( rotated_colors)
        return

    def getNormFunc( self, M):

        if self.colorPars.vmax <= self.colorPars.vmin:
            temp = QMessageBox()
            ret = temp.question(self,'',
                                "getNormFunc: vmax %g <= vmin %g " % (self.colorPars.vmin, self.colorPars.vmax), 
                                temp.Ok )
            return None
        #
        # [vmin, vmax] -> [0, 255]
        #
        if self.colorPars.norm == 'LinNorm':
            normFunc = utils.LinNorm( vmin=self.colorPars.vmin, vmax=self.colorPars.vmax, 
                                      clip = ( self.colorPars.clip == "True"))
        elif self.colorPars.norm == 'TwoSlopeNorm':
            normFunc = colors.TwoSlopeNorm( self.colorPars.normPar, vmin=self.colorPars.vmin, vmax=self.colorPars.vmax)

        elif self.colorPars.norm == 'AsinhNorm':
            normFunc = colors.AsinhNorm( linear_width = self.colorPars.normPar, 
                                         vmin=self.colorPars.vmin, vmax=self.colorPars.vmax, 
                                      clip = ( self.colorPars.clip == "True"))

        elif self.colorPars.norm == "PowerNorm":
            normFunc = colors.PowerNorm( gamma = self.colorPars.normPar,
                                         vmin=self.colorPars.vmin, vmax=self.colorPars.vmax, 
                                         clip = ( self.colorPars.clip == "True"))
        elif self.colorPars.norm == "LogNorm":
            temp = self.colorPars.vmin
            if temp <= 0.:
                temp = 0.1
            normFunc = colors.LogNorm( vmin=temp, vmax=self.colorPars.vmax,
                                       clip = ( self.colorPars.clip == "True"))
        elif self.colorPars.norm == "HistNorm":
            vmin, vmax = np.percentile(M, [self.colorPars.normPar, 100. - self.colorPars.normPar])
            normFunc = utils.LinNorm( vmin=vmin, vmax=vmax,
                                       clip = ( self.colorPars.clip == "True"))
        elif self.colorPars.norm == "StretchNorm":
            self.colorPars.logWidget.append( "StretchNorm: min, %g, max %g" %
                                   ( M.min(), M.max()))
            temp = (M - np.mean(M)) * self.colorPars.normPar
            temp = temp - temp.min()
            self.colorPars.logWidget.append( "StretchNorm: vmin %g, vmax %g, min, %g, max %g" %
                                   ( self.colorPars.vmin, self.colorPars.vmax, temp.min(), temp.max()))
            M = np.clip( temp, self.colorPars.vmin, self.colorPars.vmax, out = M)
            normFunc = utils.LinNorm( vmin=self.colorPars.vmin, vmax=self.colorPars.vmax,
                                       clip = ( self.colorPars.clip == "True"))
        else:
            print( "getNormFunc: Failed to identify norm, %s, exit" % self.colorPars.norm)
            sys.exit( 255)
        return normFunc

    def setResetMarker( self):
        
        if self.parent.parent.deltaM < 2: 
            self.resetMarker.set( text = '+',
                                  x = self.parent.parent.cxM, y = self.parent.parent.cyM,
                                  transform = self.ax.transData)
            self.canvas.draw()
        return 

    def clearResetMarker( self):
        self.resetMarker.set( text = '')
        self.canvas.draw()
        return
    #
    # MPL: k and w
    #
    def setResetMarkerColor( self, rmColor):
        #print( "%s.setResetMarkerColor: %s" % ( self.name, rmColor))
        self.resetMarker.set_color( rmColor)
        return 

    def setWorldRect(self):
        return
    
        self.xmin = self.parent.parent.cxM - self.parent.parent.deltaM/2.
        self.xmax = self.parent.parent.cxM + self.parent.parent.deltaM/2. 
        self.ymin = self.parent.parent.cyM - self.parent.parent.deltaM/2. 
        self.ymax = self.parent.parent.cyM + self.parent.parent.deltaM/2.

        return 
    
    #
    # === callbacks END
    #
    def prepareFigure(self):

        if self.fig is not None:
            return

        self.fig = Figure(figsize=self.figSizeM, dpi=self.dpi)
        self.ax = self.fig.add_subplot(111)

        # Axes auf volle Fläche
        self.ax.set_position([0, 0, 1, 1])
        self.ax.set_axis_off()
        self.ax.set_autoscale_on(False)
        self.canvas = FigureCanvas(self.fig)

        # WICHTIG: Canvas muss expandieren dürfen
        self.canvas.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # WICHTIG: Layout ohne Ränder
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Events
        self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.canvas.mpl_connect("button_press_event", self.cb_onMouseClicked)
        #self.mouseMoved = self.fig.canvas.mpl_connect( 'motion_notify_event', 
        #                                               self.cb_onMouseMoved)

        #
        # mark the position where 'reset' was called
        #
        self.resetMarker = self.fig.text( 0., 0., '',
                                          transform = self.ax.transData, 
                                          color='white',
                                          #fontweight = 'semibold', 
                                          ha='center',
                                          va = 'top', 
                                          size = 20)

        # Titel
        #self.textTitle = self.fig.text(
        #    0.02, 0.99,
        #    r'$z_{n+1} = z_n^2 + c, z_0 = 0$',
        #    color='white', fontname='monospace', size=12,
        #    ha='left', va='top',
        #    bbox=dict(fill=False, edgecolor='white', linewidth=1)
        #)
        return

    def findFigSizes( self): 

        #screen = QDesktopWidget().screenGeometry(-1)
        cm = 1/2.54  # centimeters in inches
        self.screen = self.app.primaryScreen()
        """
        - 96 DPI → Windows baseline, what Qt reports as “physical”.
        - 100 DPI → Matplotlib’s default assumption if you don’t override.
        - 120 DPI → Windows scaling at 125%, common on HiDPI monitors.
        """
        dpi_x = self.screen.physicalDotsPerInchX() # 96
        dpi_y = self.screen.physicalDotsPerInchY() # 96
        self.dpi = utils.DPI
        self.screenWidthIn  = self.screen.size().width()/dpi_x # just for informational purpose
        self.screenHeightIn = self.screen.size().height()/dpi_y

        self.figSizeC = ( 15*cm, 18*cm)
        """
        if self.modeOperation.lower() == 'demo': 
            self.figSizeC = ( 11*cm, 16*cm)
        """

        # width = WIDTH_VALUES[0] # 1000
        width = 1000 # because always want to have the same fig size
        """
          note: use setGeometry only for positioning the figure
                self.mgr.window.setGeometry( 50, 50, self.geomM.width(), self.geomM.height())
        """
        figSizeInch = width / self.dpi
        self.figSizeHuge = ( figSizeInch*1.7, figSizeInch*1.7)
        self.figSizeLarge = ( figSizeInch*1.2, figSizeInch*1.2)
        self.figSizeBig = ( figSizeInch*0.85, figSizeInch*0.85)
        self.figSizeMedium = ( figSizeInch*0.7, figSizeInch*0.7)
        self.figSizeSmall = ( figSizeInch*0.5, figSizeInch*0.5)
        self.figSizeTiny = ( figSizeInch*0.35, figSizeInch*0.35)
            
        self.figSizeM = self.figSizeBig
        self.figSizeJ = self.figSizeBig
        self.figSize3D = self.figSizeBig
        return 

    def setColor( self):
        """
        yes, in general the paramters exist in self already. However,
        they are required as a reminder that they have to exist before
        this function is executed.
        """
        #print( "%s.setColor: colorMapName %s %d" % 
        #       ( self.name, self.colorPars.colorMapName, id( self.colorPars.colorMapName)))

        if hasattr( self.parent.parent, 'colorWidget'): 
            if self.parent.parent.colorWidget.cmapLbl is not None:
                self.parent.parent.colorWidget.cmapLbl.setText( "CMAP: %s" % self.colorPars.colorMapName)

        colorMapName = self.colorPars.colorMapName
        if self.colorPars.flagReversed == "True":
            colorMapName += '_r'

        #
        # prism and flag are already cyclic
        #
        if self.colorPars.flagCyclic == "True" and \
           colorMapName != 'flag' and \
           colorMapName != 'prism':
            self.colorPars.colorMap = plt.get_cmap( colorMapName, self.colorPars.nColorCyclic)
            rot_temp = self.colorPars.colorMap( np.linspace( 0, 1, self.colorPars.nColorCyclic))
            self.colorPars.colorMap = matplotlib.colors.ListedColormap( np.tile( rot_temp, (16, 1)))
        else: 
            self.colorPars.colorMap = plt.get_cmap( colorMapName, utils.CMAP_MAX)
            #
            # we shift black to the end to paint pixels containing maxIter black
            # and thereby we create a ListedColormap
            #
            temp = self.colorPars.colorMap( np.arange( utils.CMAP_MAX))
            #
            # shift black to index (CMAP_MAX - 1)
            #
            rot_temp = np.roll( temp, shift=( utils.CMAP_MAX - 1), axis=0)  
            self.colorPars.colorMap = matplotlib.colors.ListedColormap( rot_temp)
        #
        # the rotate slider need a ListedColormap
        #
        #if self.cmapRotateSlider is not None: 
        #    self.cmapRotateSlider.setValue( rotateColorMapIndex)

        self.rotateColorMapFunc( self.colorPars.rotateColorMapIndex)
        
        if self.colorPars.band == "True": 
            colorsArr = self.colorPars.colorMap(np.linspace(0, 1, utils.CMAP_MAX))
            for i in range( len( colorsArr)): 
                if i % 2 == 0: 
                    colorsArr[i] = [0.123, 0.123, 0.123, 1]
            self.colorPars.colorMap = colors.ListedColormap(colorsArr)
        return

    def setDebugColoring( self, temp):
        #print( "%s.setDebugColoring: flag %s" % ( self.name, repr( temp)))
        if temp: 
            self.debugColoring = "True"
        else:
            self.debugColoring = "False"
        return
    
    def createDebugColoringOutput( self, M, image):

        #print( "%s.createDebugColoringOutput, title %s, flag %s" % ( self.name, self.parent.title, repr( self.debugColoring)))

        if self.debugColoring == "False":
            print( "%s.createDebugColoringOutput early return" % ( self.name))
            return 

        if self.axDebugColoring is None: 
            print( "%s.createDebugColoringOutput: creating axes" % self.name) 
            self.axDebugColoring = [self.fig.add_subplot(4, 1, i+1) for i in range(4)]        
        
        self.axDebugColoring[0].clear()
        flat_data = M.ravel()
        self.axDebugColoring[0].hist( flat_data, bins = 256, log = True) 
        self.axDebugColoring[0].set_title( "Escape Counts")

        normFunc = self.getNormFunc( M)
        x = np.linspace(0, utils.DATA_NORM, utils.DATA_NORM)
        y = normFunc( x)
        self.axDebugColoring[1].clear()
        self.axDebugColoring[1].plot( x, y)
        self.axDebugColoring[1].set_title( "%s, normPar %g, vmin %g, vmax %g" % 
                              (self.colorPars.norm, self.colorPars.normPar,
                               self.colorPars.vmin, self.colorPars.vmax))
        
        self.axDebugColoring[2].clear()
        M1 = normFunc( M)
        flat_data = M1.ravel()
        self.axDebugColoring[2].hist( flat_data, bins = 256, log = True) 
        self.axDebugColoring[2].set_title( "Normalized Data (no shader)")
        """
        if self.cbar is not None:
            self.cbar.remove() # this also destroys the axes, has to be re-created
            self.axDebugColoring[3] = self.figDebugColoring.add_axes([0.125, 0.11, 0.775, 0.167])
            self.cbar = None
        """
        
        if self.cbar is None: 
            self.cbar = self.fig.colorbar( image,
                                           orientation = 'horizontal', 
                                           cax = self.axDebugColoring[3])
            self.cbar.ax.set_title("Colorbar")
            self.canvas.draw()
        else:
            self.cbar.update_normal( image)
            self.fig.canvas.draw_idle()

        return

    def displayPng( self, fName):
        img = np.asarray(Image.open( fName))
        img = np.flipud( img)
        self.updateImage( img) 
        return
        
    def updateImage(self, M):

        if self.fig is None:
            return

        #print( "%s.updateImage, shape %s title %s" %
        #       ( self.name, M.shape, self.parent.title))
        
        if self.parent.parent.name == "MBSMainWindow":
            x0 = self.parent.parent.cxM - self.parent.parent.deltaM/2.
            x1 = self.parent.parent.cxM + self.parent.parent.deltaM/2.
            y0 = self.parent.parent.cyM - self.parent.parent.deltaM/2.
            y1 = self.parent.parent.cyM + self.parent.parent.deltaM/2.
        else:
            x0 = 0
            x1 = 1
            y0 = 0
            y1 = 1

        extentArr = [x0, x1, y0, y1]

        self.ax.set_xlim([ x0, x1])
        self.ax.set_ylim([ y0, y1])

        normFunc = self.getNormFunc(M)

        if self.colorPars.shaded == 'True':
            light = colors.LightSource(azdeg=self.colorPars.azDeg, altdeg=self.colorPars.altDeg)
            M = light.shade(
                M,
                cmap=self.colorPars.colorMap,
                norm=normFunc,
                vert_exag=self.colorPars.vert_exag,
                blend_mode=self.colorPars.blendMode
            )
            cmapTemp = None
            normTemp = None
        else:
            cmapTemp = self.colorPars.colorMap
            normTemp = normFunc

        if self.image is None:
            self.ax.set_axis_off()

            self.image = self.ax.imshow(
                M,
                origin='lower',
                cmap=cmapTemp,
                norm=normTemp,
                extent=extentArr,
                interpolation=self.colorPars.interpolation,
                aspect='equal'   # mathematisch korrekt
            )
        else:
            self.image.set_data(M)
            self.image.set_extent(extentArr)
            self.image.set_interpolation(self.colorPars.interpolation)
            
            if self.colorPars.shaded != 'True':
                self.image.set_norm(normFunc)
                self.image.set_cmap( self.colorPars.colorMap)

            self.image.changed()
            self.canvas.draw()

            if self.debugColoring == "True":
                self.coloringOutput.emit( M, self.image)
            else: 
                self.parent.parent.viewerDebugColoring.mpl.hide()

        if hasattr( self.parent.parent, "deltaM"):
            self.deltaLbl.emit( "Delta: %.2e" % self.parent.parent.deltaM)

        self.canvas.draw()
        self.app.processEvents()
        return 

    def updateImageNew(self, M):

        if self.fig is None:
            return

        if self.parent.parent.name == "MBSMainWindow":
            x0 = self.parent.parent.cxM - self.parent.parent.deltaM/2.
            x1 = self.parent.parent.cxM + self.parent.parent.deltaM/2.
            y0 = self.parent.parent.cyM - self.parent.parent.deltaM/2.
            y1 = self.parent.parent.cyM + self.parent.parent.deltaM/2.
        else:
            x0, x1, y0, y1 = 0, 1, 0, 1

        extentArr = [x0, x1, y0, y1]

        self.ax.set_xlim([x0, x1])
        self.ax.set_ylim([y0, y1])

        normFunc = self.getNormFunc(M)

        if self.colorPars.shaded == 'True':

            # 1. Norm auf Rohdaten
            M_norm = normFunc(M)
            
            # 2. Colormap anwenden (RGB)
            cmap = plt.get_cmap(self.colorPars.colorMap)
            rgb = cmap(M_norm)[..., :3]   # nur RGB
            
            # 3. Shading anwenden
            light = colors.LightSource(
                azdeg=self.colorPars.azDeg,
                altdeg=self.colorPars.altDeg
            )
            
            M_display = light.shade_rgb(
                rgb,
                M,   # Höhenfeld
                vert_exag=self.colorPars.vert_exag,
                blend_mode=self.colorPars.blendMode
            )
            
            # Shading erzeugt fertiges RGB → keine Norm/Cmap mehr im imshow
            cmapTemp = None
            normTemp = None

        else:
            # Kein Shading → normale Darstellung
            M_display = M
            cmapTemp = self.colorPars.colorMap
            normTemp = normFunc

        if self.image is None:
            self.ax.set_axis_off()

            self.image = self.ax.imshow(
                M_display,
                origin='lower',
                cmap=cmapTemp,
                norm=normTemp,
                extent=extentArr,
                interpolation=self.colorPars.interpolation,
                aspect='equal'
            )

        else:
            # Reihenfolge ist wichtig!
            self.image.set_extent(extentArr)
            self.image.set_interpolation(self.colorPars.interpolation)
            self.image.set_data(M_display)
            
            if self.colorPars.shaded != 'True':
                self.image.set_norm(normFunc)
                self.image.set_cmap(self.colorPars.colorMap)
                
            self.image.changed()
            self.canvas.draw()

        if self.debugColoring == "True":
            self.coloringOutput.emit(M, self.image)
        else:
            self.parent.parent.viewerDebugColoring.mpl.hide()

        if hasattr(self.parent.parent, "deltaM"):
            self.deltaLbl.emit("Delta: %.2e" % self.parent.parent.deltaM)

        self.canvas.draw()
        self.app.processEvents()
