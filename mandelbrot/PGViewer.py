#!/usr/bin/env python3
"""
How the three layers differ
Even though they all feel like “the plot”, they serve different roles in the graphics hierarchy.
1. GraphicsLayoutWidget — the container
This is the outermost widget. It manages a grid layout of plots, labels, colorbars, etc.
It does not know anything about world coordinates or mouse interaction.
- Think of it as a “canvas” that holds multiple plots.
- It is a QWidget, not a graphics item.
- It does not draw data.

2. PlotItem — the plotting interface
This is what you get from view.addPlot().
It is a convenience wrapper that contains:
- a ViewBox (the actual coordinate system),
- axes,
- labels,
- title,
- default mouse behavior.
PlotItem is not where your data lives.
It is a manager that forwards drawing to the ViewBox.

3. ViewBox — the real coordinate system
This is the heart of PyQtGraph’s rendering model.
- It defines the world coordinate system.
- It handles zoom, pan, aspect ratio, transforms.
- It is where you add your items (ImageItem, PlotDataItem, polygons, markers).
- It maps between scene coordinates and world coordinates.
When you call:
viewBox.mapSceneToView(...)
you are converting mouse positions into Mandelbrot coordinates.

Why this matters in your viewer
Your Mandelbrot viewer relies on:
- a stable world rectangle,
- a custom image transform,
- overlays (iteration paths, polygons, markers),
- switching interaction modes (MB1/MB2/MB3).
All of these must be attached to the ViewBox, not the PlotItem or the GraphicsLayoutWidget.
If you accidentally mix them:
- items don’t disappear when removed,
- mouse events map to the wrong coordinate system,
- overlays drift or stay behind,
- zoom/pan behave inconsistently.
This is exactly what happened with your polyline:
you removed it from one ViewBox, but it was drawn in another.

A clean mental model
This hierarchy helps keep everything straight:
GraphicsLayoutWidget
└── PlotItem
    ├── AxisItem (left)
    ├── AxisItem (bottom)
    └── ViewBox   ← your world coordinates live here
         ├── ImageItem (Mandelbrot)
         ├── PlotDataItem (iteration path)
         ├── QGraphicsPathItem (polygons)
         └── markers, overlays, etc.


So the rule of thumb is:
- Add all data items to the ViewBox.
- Use PlotItem only for axes and layout.
- Use GraphicsLayoutWidget only as a container.

A quick test to confirm you’re using the right ViewBox
Print the object identity:
print("plot.vb =", self.plot.vb)
print("viewBox =", self.viewBox)
Usefull: 
print("polyLine parent:", self.polyLine.parentItem())
print("Items in ViewBox:", self.viewBox.addedItems)
self.viewBox.update()
self.plot.repaint()

to cleanup:
for item in list(self.viewBox.addedItems):
    if isinstance(item, pg.PlotDataItem):
        self.viewBox.removeItem(item)

Rules: 
1. Always add data items to the ViewBox
Never add them to the PlotItem or the GraphicsLayoutWidget.
viewBox.addItem(item)
2. Always map mouse events through the ViewBox
This gives correct world coordinates:
scenePos = event
mousePoint = viewBox.mapSceneToView(scenePos)
3. Keep a single reference to each overlay item
This prevents “ghost” items that you can’t remove.
4. Remove items from the same ViewBox you added them to
Otherwise they remain visible.
5. Use ignoreBounds=True for overlays
This prevents overlays from changing the zoom.

"""
import sys
sys.path.append( "/home/kracht/gitlabDESY/hasyutils")
import HasyUtils

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import utils
import colorsys
from PyQt5.QtGui import QTransform
import traceback
from PIL import Image
from scipy.ndimage import gaussian_filter

METADATA_MEMBERS = [
    'vmin', 'vmax', 'colorMapName', 'colorPhase', 'flagCyclic', 'flagReversed', 
    'rotateColorMapIndex', 'norm', 'normPar', 'shaded', 'blackFixed', 'smooth',
    'altDeg', 'azDeg', 'vert_exag', 'blendMode', 'debugColoring', 
    ]
#
# beware of typos, check whether a member is in the list of known members
#
VIEWER_Attrs = METADATA_MEMBERS + \
    [ 'app', 'hud', 'view', 'plot', 'viewBox', 'img', 'lut', 'autoLevels',
      'resetMarker', 'polyLine', 'idxmap', 'parent', 'name', 
      'rotateWaitTime', 'colorRotateValue', 'colorPars', 
      'xmin', 'xmax', 'ymin', 'ymax', 'H', 'W', 'idxmaxp', 
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
    def __init__(self,
                 parent = None,
                 app = None,
                 colorPars = None,
                 colormap="hot"):

        super().__init__()

        self.parent = parent
        self.name = "PGViewer"
        self.colorPars = colorPars
        self.app = app

        #print( "%s.__init__(): title %s" % ( self.name, title))
        #print( "PGViewer.__init__(): self.parent.name %s" % self.parent.name)
        self.hud = None
        
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setContentsMargins(0, 0, 0, 0)
        
        # --- Graphics area ---
        self.view = pg.GraphicsLayoutWidget()
        layout.addWidget(self.view)

        # Entfernt GraphicsLayout-Margins
        self.view.ci.layout.setContentsMargins(0, 0, 0, 0)

        # Entfernt den GRAUEN Rahmen
        self.view.ci.setBorder(None)

        self.plot = self.view.addPlot()
        self.plot.setAspectLocked(True)
        self.plot.hideAxis('left')
        self.plot.hideAxis('bottom')
        
        # Entfernt PlotItem-Margins
        self.plot.setContentsMargins(0, 0, 0, 0)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()

        # Entfernt ViewBox-Margins
        self.viewBox = self.plot.getViewBox()
        self.viewBox.setContentsMargins(0, 0, 0, 0)
        self.viewBox.setDefaultPadding(0)
        self.viewBox.disableAutoRange()

        # Image
        self.img = pg.ImageItem()
        self.plot.addItem(self.img)
        #
        # Disable right-click menu
        #self.viewBox.setMenuEnabled(False)
        self.plot.scene().sigMouseClicked.connect( self.onMouseClicked)

        # --- Colormap ---
        self.setColormap(colormap)

        self.autoLevels = False

        self.initMembers()

        self.setDefaults()

        self.setColor()
        #
        # make sure MBS_ATTR is not polluted
        # +++
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
            print( " unknown attribute (PGViewer): '%s'," %  name)
            super( Viewer, self).__setattr__(name, value)
            #raise ValueError( "PGViewer.__setattr__: unknown attribute %s" % ( name))

    def setDefaults( self):
        
        return 
    
    def initMembers( self):

        self.debugColoring = False
        self.resetMarker = None
        self.polyLine = None
        self.xmin = None

        return 

    def mapToWorld(self, event):
        pos = event.pos()  # ViewBox-local

        self.setWorldRect()
        
        # scene - view - pixel coords
        scenePos = self.viewBox.mapToScene(pos)
        viewPos  = self.viewBox.mapSceneToView(scenePos)
        
        wx = viewPos.x()
        wy = viewPos.y()
        
        rx = (wx - self.xmin)/( self.xmax - self.xmin) 
        ry = (wy - self.ymin)/( self.ymax - self.ymin)

        pxmin, pxmax = 0, self.W
        pymin, pymax = 0, self.H
        px = int( pxmin + rx*(pxmax - pxmin))
        py = int( pymin + ry*(pymax - pymin))
        
        return wx, wy, px, py

    def onMouseClicked(self, event):

        #
        # has updateImage been called yet?
        #
        if self.xmin is None:
            return
        
        mousePoint = self.viewBox.mapSceneToView(event.scenePos())
        wx, wy, px, py = self.mapToWorld( event)
        
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            h, w = self.img.image.shape[:2]
            if 0 <= int(py) < h and 0 <= int(px) < w:
                pixel = self.img.image[int(px), int(py)]
            else:
                print( "Viewer: px, py outside limts %d %d " % (px, py))
                return

            #self.parent.parent.deltaLbl.setText( "Delta: %.2e" % (self.parent.parent.deltaM))
            if hasattr( self.parent.parent, "deltaM"):
                self.deltaLbl.emit( "Delta: %.2e" % (self.parent.parent.deltaM))
            if type( pixel) == np.float32:
                self.clickedShiftMB1.emit( px, py, wx, wy, "%.5g" % pixel)
            elif type( pixel) == np.ndarray:
                self.clickedShiftMB1.emit( px, py, wx, wy, repr( list( pixel)))

            #self.updateHUD(px, py, wx, wy, pixel)
            return
        
        elif modifiers == Qt.ControlModifier:
            print('Control+Click')
        elif modifiers == Qt.AltModifier:
            print('Alt+Click')
        elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
            print('Control+Shift+Click')

        btn = event.button()
        if btn == Qt.LeftButton:
            self.clickedMB1.emit(wx, wy)
        elif btn == Qt.MiddleButton:
            self.clickedMB2.emit(wx, wy)
        elif btn == Qt.RightButton:
            self.clickedMB3.emit( wx, wy)

        return 

    def handleIterPath( self, event):
        mousePoint = self.plot.vb.mapSceneToView( event)
        #
        # Z**2 = (x**2 - y**2) + i*x*y
        #
        x = []
        y = []
        x.append( mousePoint.x())
        y.append( mousePoint.y())
        for n in range( 100):
            x.append( x[n-1]**2 - y[n-1]**2 + mousePoint.x())
            y.append( 2.*x[n-1]*y[n-1] + mousePoint.y())
            if (x[-1]**2 + y[-1]**2) > 20:
                break

        if self.polyLine is None: 
            self.polyLine = pg.PlotDataItem( x, y, pen=pg.mkPen( 'w', width=1))
            self.polyLine.setZValue(20)
            self.viewBox.addItem( self.polyLine, ignoreBounds=True)
        else:
            self.polyLine.setData([], [])
            self.polyLine.setData( x, y)
            
        return
    
    def connectOnMouseMoved(self, flag):
        print("connectOnMouseMoved %s" % repr(flag))

        if flag:
            self.plot.scene().sigMouseMoved.connect(self.onMouseMoved)

        else:
            self.plot.scene().sigMouseMoved.disconnect(self.onMouseMoved)
            #print("plot.vb =", self.plot.vb)
            #print("viewBox =", self.viewBox)

            if self.polyLine is not None:
                self.polyLine.setData([], [])          # clear geometry
                self.viewBox.removeItem(self.polyLine) # remove from scene
                self.polyLine = None                   # reset reference
        return 
    
    def onMouseMoved(self, event):
        mousePoint = self.plot.vb.mapSceneToView( event)
        #print( "onMouseMoved %g %g " % (mousePoint.x(), mousePoint.y()))
        
        if self.parent.parent.flagIterPath == "True": 
            self.handleIterPath( event)
            return 

        return 
        
    def prepareHUD( self):
        self.hud = QLabel(self)
        self.hud.setStyleSheet("""
        QLabel {
        background-color: rgba(0, 0, 0, 120);
        color: white;
        padding: 4px;
        border-radius: 4px;
        font-family: Consolas, monospace;
        font-size: 11pt;
        }
        """)
        self.hud.move(25, 25)
        self.hud.resize(300, 120)
        self.hud.setText("HUD initialized")
        self.hud.show()
            
    def updateHUD(self, ix, iy, wx, wy, pixel):

        if self.hud is None:
            self.prepareHUD()
            
        mode = "Mandelbrot"

        
        if pixel is None:
            ptext = "—"
        else:
            if pixel.ndim == 0:  # grayscale
                ptext = f"{pixel}"
            else:                # RGB
                ptext = f"{pixel[0]}, {pixel[1]}, {pixel[2]}"

        text = (
            f"Mode: {mode}\n"
            f"Pixel: ({ix:d}, {iy:d})\n"
            f"World: ({wx:+.12f}, {wy:+.12f})\n"
            f"Value: {ptext}"
        )

        self.hud.setText(text)


    # ------------------------------------------------------------
    # Colormap handling
    # ------------------------------------------------------------

    def make_exp_lut( self, lut, gamma):
        N = lut.shape[0]                 # number of colors in the LUT
        x = np.linspace(0, 1, N)         # normalized axis
        t = x ** gamma                   # apply PowerNorm
        self.idxmap = (t * (N - 1)).astype(int)  # map t back to LUT indices
        return lut[ self.idxmap], self.idxmap                  # build new LUT by sampling

    #def make_linear_lut(self, lut):     # 
    #    return lut.copy()

    def make_linear_lut( self, lut):
        N = lut.shape[0]
        x = np.linspace(0, 1, N)
        self.idxmap = (x * (N - 1)).astype(int)
        return lut[ self.idxmap], self.idxmap

    def make_log_lut( self, lut, a=100):
        #
        # a = 10 - gentle
        # a = 100 - strong
        # a = 1000 - very strong

        N = lut.shape[0]
        x = np.linspace(0, 1, N)

        # avoid log(0)
        eps = 1e-12
        t = np.log(1 + a * x + eps) / np.log(1 + a)

        self.idxmap = (t * (N - 1)).astype(int)
        return lut[ self.idxmap], self.idxmap

    def make_invlog_lut( self, lut, a=100):
        N = lut.shape[0]
        x = np.linspace(0, 1, N)

        eps = 1e-12
        t = 1 - np.log(1 + a * (1 - x) + eps) / np.log(1 + a)

        self.idxmap = (t * (N - 1)).astype(int)
        return lut[ self.idxmap], self.idxmap

    @pyqtSlot()
    def setColor( self):
        """
        """
        #print( "%s.setColor %s" % ( self.name, self.parent.title))
        #
        # local copy because we might add '_r' 
        #
        colorMapName = self.colorPars.colorMapName
        if self.colorPars.flagReversed == "True":
            colorMapName += '_r'

        cmap = pg.colormap.getFromMatplotlib( colorMapName)
        self.lut = cmap.getLookupTable( nPts = utils.CMAP_MAX)

        if self.colorPars.flagCyclic == "True":
            repeats = 16
            self.lut = np.tile( self.lut, ( repeats, 1))
            self.lut = np.roll( self.lut, shift = - self.colorPars.rotateColorMapIndex, axis = 0)
        else: 
            if self.colorPars.blackFixed == "True": 
                # black to the end
                self.lut = np.roll( self.lut, shift=( utils.CMAP_MAX - 1), axis=0)
                # rotate the rest of the LUT
                if self.colorPars.shaded == "False":
                    rotatable = self.lut[:-1]
                    fixed = self.lut[-1:]
                    rotated = np.roll( rotatable, shift = - self.colorPars.rotateColorMapIndex, axis = 0)
                    self.lut = np.vstack( (rotated, fixed))
            else:
                if self.colorPars.shaded == "False":
                    self.lut = np.roll( self.lut, shift = - self.colorPars.rotateColorMapIndex, axis = 0)

        if self.colorPars.norm == "PowerNorm":
            self.lut, self.idxmap = self.make_exp_lut( self.lut, self.colorPars.normPar)
        elif self.colorPars.norm == "LinNorm": 
            self.lut, self.idxmap = self.make_linear_lut( self.lut)
        elif self.colorPars.norm == "LogNorm": 
            self.lut, self.idxmap = self.make_log_lut( self.lut, a = self.colorPars.normPar)
        elif self.colorPars.norm == "InvLogNorm": 
            self.lut, self.idxmap = self.make_invlog_lut( self.lut, a = self.colorPars.normPar)
        else:
            print( "self.colorPars.setColor: failed to identify norm %s" % self.colorPars.norm)

        self.img.setLookupTable( self.lut)

        return

    def setColormap( self, name):
        cmap = pg.colormap.getFromMatplotlib(name)
        self.lut = cmap.getLookupTable( nPts = utils.CMAP_MAX)
        self.lut = np.roll( self.lut, shift=(utils.CMAP_MAX - 1), axis=0)  
        self.img.setLookupTable( self.lut)
        return 

    def extractViewerParameters( self, hsh):
                
        self.colorPars.colorMapName = hsh[ 'colorMapName']
        del hsh[ 'colorMapName']
        
        try: 
            self.colorPars.colorPhase = float( hsh[ 'colorPhase'])
            del hsh[ 'colorPhase']
        except: 
            pass
                
        try: 
            self.colorPars.rotateColorMapIndex = int( hsh[ 'rotateColorMapIndex'])
            del hsh[ 'rotateColorMapIndex']
        except: 
            try: 
                self.colorPars.rotateColorMapIndex = int( hsh[ 'rotateColorMap'])
                del hsh[ 'rotateColorMap']
            except:
                self.colorPars.rotateColorMapIndex = 0

        self.colorPars.rotateWaitTime = utils.ROTATEWAITTIME_VALUES[0]
        try:
            self.colorPars.rotateWaitTime = float( hsh[ 'rotateWaitTime'])
            del hsh[ 'rotateWaitTime']
        except:
            pass
        
        self.colorPars.colorRotateValue = utils.COLORROTATE_VALUES[0]
        try:
            self.colorPars.colorRotateValue = float( hsh[ 'colorRotateValue'])
            del hsh[ 'colorRotateValue']
        except:
            pass
        
        self.colorPars.flagReversed = "False"
        try: 
            self.colorPars.flagReversed = hsh[ 'flagReversed']
            del hsh[ 'flagReversed']
        except:
            pass
        
        self.colorPars.norm = hsh[ 'norm']
        del hsh[ 'norm'] 
        if self.colorPars.norm == "LinNormR":
            self.colorPars.norm = "LinNorm"
            self.colorPars.flagReversed = "True"
        self.colorPars.normPar = float( hsh[ 'normPar'])
        del hsh[ 'normPar']
        
        self.colorPars.flagCyclic = "False"
        try: 
            self.colorPars.flagCyclic = hsh[ 'flagCyclic']
            del hsh[ 'flagCyclic'] 
        except:
            pass
        
        self.colorPars.smooth = hsh[ 'smooth']
        del hsh[ 'smooth'] 
        
        self.colorPars.vmin = 0
        try: 
            self.colorPars.vmin = float( hsh[ 'vmin'])
            del hsh[ 'vmin'] 
        except:
            pass
        
        self.colorPars.vmax = 1024
        try: 
            self.colorPars.vmax = float( hsh[ 'vmax'])
            del hsh[ 'vmax'] 
        except:
            pass
        
        self.colorPars.shaded = hsh[ 'shaded']
        del hsh[ 'shaded']
        
        self.colorPars.blackFixed = "True"
        try: 
            self.colorPars.blackFixed = hsh[ 'blackFixed']
            del hsh[ 'blackFixed'] 
        except:
            pass
        
        self.colorPars.vert_exag = 1.
        try: 
            self.colorPars.vert_exag = float( hsh[ 'vert_exag'])
            del hsh[ 'vert_exag'] 
        except:
            pass
        if hsh[ 'Version'] == "MPL_1.0.0":
            print( "%s.extractViewerParams: changed vert_exag from %g to 1." %
                   ( self.name, self.colorPars.vert_exag)) 
            self.colorPars.vert_exag = 1.
            
        try: 
            self.colorPars.interpolation = hsh[ 'interpolation']
            del hsh[ 'interpolation'] 
        except:
            pass
        if self.parent.parent.version == "MPL_1.0.0":
            print( "%s.extractViewerParams: changed interpolation from %s to %s" %
                   ( self.name, self.colorPars.interpolation, utils.PG_INTERPOLATION_VALUES[0])) 
            self.colorPars.interpolation = utils.PG_INTERPOLATION_VALUES[0]

        try: 
            self.colorPars.blendMode = hsh[ 'blendMode']
            del hsh[ 'blendMode'] 
        except:
            pass
        if self.parent.parent.version == "MPL_1.0.0":
            print( "%s.extractViewerParams: changed blendMode from %s to lum" %
                   ( self.name, self.colorPars.blendMode)) 
            self.colorPars.blendMode = "lum"
        
        self.colorPars.azDeg = int( float( hsh[ 'azDeg']))
        del hsh[ 'azDeg'] 

        self.colorPars.altDeg = int( float( hsh[ 'altDeg'])) # '90.0' gave trouble
        del hsh[ 'altDeg'] 

        self.setColor()
        return
        
    def debugColoring( self, M):

        # Create window and plots only once
        if self.parent.parent.winDebugColoring is None:
            self.parent.parent.winDebugColoring = pg.GraphicsLayoutWidget()
            self.parent.parent.winDebugColoring.setWindowTitle("Coloring Debug")
            
            # --- Plot 1: Raw Histogram ---
            self.p1 = self.parent.parent.winDebugColoring.addPlot(title="Raw Histogram")
            self.curve1 = self.p1.plot(stepMode=True, fillLevel=0, pen='b')
            
            # --- Plot 2: LUT Mapping Curve ---
            self.parent.parent.winDebugColoring.nextRow()
            self.p2 = self.parent.parent.winDebugColoring.addPlot(title="LUT Mapping Curve")
            self.curve2 = self.p2.plot( pen='b')
            
            # --- Plot 3: Histogram after LUT Mapping ---
            self.parent.parent.winDebugColoring.nextRow()
            self.p3 = self.parent.parent.winDebugColoring.addPlot(title="Histogram after LUT Mapping")
            self.curve3 = self.p3.plot(stepMode=True, fillLevel=0, pen='b')
            
            self.parent.parent.winDebugColoring.show()

        # --- Update Plot 1 ---
        flat = M.ravel()
        hist, edges = np.histogram(flat, bins=utils.CMAP_MAX)
        y = np.log1p(hist)
        self.curve1.setData(edges, y)
        
        # --- Update Plot 2 ---
        brightness = self.lut.mean(axis=1)
        x = np.linspace(0, utils.CMAP_MAX - 1, len(self.lut))
        self.curve2.setData(x, brightness)
        
        # --- Update Plot 3 ---
        N = self.lut.shape[0]

        # normalize M to [0,1]
        M_norm = (M - M.min()) / (M.max() - M.min())

        # map to raw LUT indices
        raw_idx = (M_norm * (N - 1)).astype(int)

        # apply LUT index mapping
        mapped_idx = self.idxmap[raw_idx]

        flat2 = mapped_idx.ravel()
        hist2, edges2 = np.histogram(flat2, bins=N)
        self.curve3.setData(edges2, np.log1p(hist2))

        return

    def map_mpl_to_pg( self, vert_exag, blendMode):
        # Gradient scaling
        grad_scale = vert_exag * 1.5
        
        # Shading strength
        strength = 0.8 + 0.4 * vert_exag
        
        # Height boost (neu!)
        height_boost = 500 * vert_exag
        
        # Blend mode mapping
        if blendMode == "overlay":
            ambient = 0.15
            shade_gain = 2.0
        elif blendMode == "soft":
            ambient = 0.25
            shade_gain = 1.0
        elif blendMode == "rgb":
            ambient = 0.05
            shade_gain = 3.0
        elif blendMode == "lum":
            ambient = 0.35
            shade_gain = 0.7
        else:
            ambient = 0.2
            shade_gain = 1.5

        #print( "%s.map_mpl_to_pg: vert_exag %g blend %s to grad_scale %g, strength %g, shade_gain %g, ambient %g, height_boost %g" %
        #       ( self.name, vert_exag, blendMode, grad_scale, strength, shade_gain, ambient, height_boost))
        return grad_scale, strength, shade_gain, ambient, height_boost,
    
    def colorize_and_shade( self, 
            escape_count,
            max_iter,
            lut,                 # shape (N, 3), uint8
            phase,               # 0..1, Colormap-Phase
            az_deg, alt_deg     # Licht-Richtung
    ):
        """
        escape_count : 2D array (int)
        max_iter     : int
        lut          : (N, 3) uint8
        returns      : rgb_shaded (H, W, 3) uint8
        """

        grad_scale, strength, shade_gain, ambient, height_exp =\
            self.map_mpl_to_pg( self.colorPars.vert_exag, self.colorPars.blendMode)
        
        esc = escape_count.astype(float)

        # --- Hintergrundmaske (alles "weit draußen") ---
        mask_bg = (esc <= 2)

        # --- Normalisierung für Farbcodierung (nur Nicht-Hintergrund) ---
        # hier einfache lineare Normierung, ggf. anpassen
        #M_norm = np.clip(esc / max_iter, 0.0, 1.0)
        M_norm = np.clip(esc / esc.max(), 0.0, 1.0)

        # --- Phasenverschiebung im Datenraum statt LUT-Roll ---
        N = lut.shape[0]
        M_phase = (M_norm + phase) % 1.0
        idx = (M_phase * (N - 1)).astype(int)

        rgb = lut[idx].astype(np.uint8)

        # Hintergrund explizit schwarz setzen
        rgb[mask_bg] = (0, 0, 0)

        # =========================
        #       SHADING-TEIL
        # =========================
        
        # --- Licht-Richtung ---
        az = np.radians(az_deg)
        el = np.radians(alt_deg)
        L = np.array([
            np.cos(az) * np.cos(el),
            np.sin(az) * np.cos(el),
            np.sin(el)
        ], dtype=float)
        L /= np.linalg.norm(L)
        
        # --- Height-Field aus M_norm (nur Struktur, kein Hintergrund) ---
        height_exp = 1.0
        H = (M_norm ** height_exp)*2000.
        H = gaussian_filter(H, sigma=1.0) # smoothing
        H[mask_bg] = 0.0
        
        # --- Gradienten ---
        dx = np.gradient(H, axis=1) * grad_scale
        dy = np.gradient(H, axis=0) * grad_scale
        
        # --- Normals ---
        Nvec = np.dstack((-dx, -dy, np.ones_like(H)))
        Nnorm = np.linalg.norm(Nvec, axis=2, keepdims=True)
        Nnorm[Nnorm == 0] = 1.0
        Nvec /= Nnorm
        
        # --- Lambertian ---
        shade = np.clip(np.sum(Nvec * L, axis=2), 0.0, 1.0)
        
        # Kein globales Re-Normalisieren → realistischere Beleuchtung
        shade = np.clip(shade, 0.0, 1.0)
        
        # --- Ambient ---
        shade = ambient + (1.0 - ambient) * shade
        
        # --- Kontrast ---
        shade = 0.5 + (shade - 0.5) * shade_gain
        shade = np.clip(shade, 0.0, 1.0)
        
        # --- Centered modulation ---
        shade_centered = 1.0 + strength * (shade - 0.5)
        
        # Hintergrund nicht schattieren
        shade_centered[mask_bg] = 1.0
        
        # --- Shading direkt im RGB-Raum anwenden ---
        rgb_float = rgb.astype(float)
        rgb_float *= shade_centered[..., None]
        rgb_shaded = np.clip(rgb_float, 0, 255).astype(np.uint8)

        return rgb_shaded

    def displayPng( self, fName):
        pil = Image.open(fName).convert("RGBA")
        #arr = np.array(pil, dtype=np.float32)
        arr = np.array(pil, dtype=np.uint8)
        img = np.ascontiguousarray( arr)
        #M = np.transpose( M, (1, 2, 0))
        self.updateImage( img) 
        return

    def setDebugColoring( self, temp):
        self.debugColoring = temp
        return
    
    # ------------------------------------------------------------
    # Update image (fast path)
    # ------------------------------------------------------------
    def updateImage(self, M):

        #print( "%s.updateImage, M %s" % ( self.name, repr( M.shape)))
        #
        # the julia set might not exist
        #
        if M is None:
            print( "self.colorPars.updateImage: M == None, return ")
            for line in  HasyUtils.getTraceBackList():
                print( "%s" % line)
            return
        #
        # created by us
        #
        if M.ndim == 3:
            # RGBA → direkt anzeigen, ohne LUT, ohne Levels
            self.img.setImage( M, levels=None, lut=None, autoLevels=False)
            # image dimensions
            self.H, self.W, temp = M.shape
            # world coordinates
            self.setWorldRect()
            # the visible rangfe corresponds to world coordinates
            self.viewBox.setRange( xRange=( self.xmin, self.xmax),
                                   yRange=( self.ymin, self.ymax), padding=0)
            # puts the png inot the fractal space
            tr = QTransform()
            tr.translate( self.xmin, self.ymin)
            sx = ( self.xmax - self.xmin) / self.W
            sy = ( self.ymax - self.ymin) / self.H
            tr.scale( sx, sy)
            self.img.setTransform(tr)

            return
        
        if self.debugColoring == "True":
            self.debugColoring( M)

        #self.parent.parent.deltaLbl.setText( "Delta: %.2e" % (self.parent.parent.deltaM))
        if hasattr( self.parent.parent, "deltaM"):
            self.deltaLbl.emit( "Delta: %.2e" % (self.parent.parent.deltaM))
            
        M = np.ascontiguousarray(M.T, dtype=np.float32)

        # Clip to vmin/vmax (Matplotlib behavior)
        M = np.clip(M, self.colorPars.vmin, self.colorPars.vmax)

        # Explicit levels (important!)
        levels = (self.colorPars.vmin, self.colorPars.vmax)

        if self.colorPars.shaded == "True":
            if self.colorPars.interpolation == "Gauss03": 
                M = gaussian_filter(M, sigma=0.3)
            elif self.colorPars.interpolation == "Gauss04": 
                M = gaussian_filter(M, sigma=0.4)
            elif self.colorPars.interpolation == "Gauss05": 
                M = gaussian_filter(M, sigma=0.5)
            elif self.colorPars.interpolation == "Gauss06": 
                M = gaussian_filter(M, sigma=0.6)

            if self.parent.parent.name == "MBSMainWindow":
                temp = self.parent.parent.maxIterM
            else:
                temp = M.max()
                
            rgb_shaded = self.colorize_and_shade(
                escape_count=M,
                max_iter=temp,
                lut=self.lut,
                phase=self.colorPars.colorPhase,
                az_deg=self.colorPars.azDeg,
                alt_deg=self.colorPars.altDeg
            )
            self.img.setImage( rgb_shaded)
        else: 
            if self.parent.parent.name == "MBSMainWindow":
                if self.colorPars.interpolation == "Gauss03": 
                    M = gaussian_filter(M, sigma=0.3)
                elif self.colorPars.interpolation == "Gauss04": 
                    M = gaussian_filter(M, sigma=0.4)
                elif self.colorPars.interpolation == "Gauss05": 
                    M = gaussian_filter(M, sigma=0.5)
                elif self.colorPars.interpolation == "Gauss06": 
                    M = gaussian_filter(M, sigma=0.6)
                self.img.setImage( M, autoLevels=False, levels=levels)
            elif self.parent.parent.name == "DynOp":
                levels = (M.min(), M.max())
                self.img.setImage(M, autoLevels=False, levels=levels)
            else:
                print( "PGViewer.updateImage: parent not identified %s" % self.parent.parent.name)
                sys.exit( 255)

        self.H, self.W = M.shape
            
        self.setWorldRect()

        #print( "%s.updateImage: xmin/max %g/%g, ymin/max %g/%g" %
        #       (self.name, self.xmin, self.xmax, self.ymin, self.ymax))
        self.viewBox.setRange( xRange=( self.xmin, self.xmax),
                               yRange=( self.ymin, self.ymax), padding=0)

        tr = QTransform()
        tr.translate( self.xmin, self.ymin)
        sx = ( self.xmax - self.xmin) / self.W
        sy = ( self.ymax - self.ymin) / self.H
        tr.scale( sx, sy)
        self.img.setTransform(tr)

        return 

    def updateImageKSP(self, M):

        #M = np.ascontiguousarray(M.T, dtype=np.float32)

        img_rgba = np.transpose(M, (1, 2, 0)).copy()

        h, w, c = img_rgba.shape

        qimg = QImage(
            img_rgba.data,
            w,
            h,
            4 * w,                     # bytes per line
            QImage.Format_RGBA8888
        )
        self.label = QLabel()
        pix = QPixmap.fromImage(qimg)
        self.label.setPixmap(pix)
        self.label.show()
        #self.img.setImage( M, autoLevels = True)

        return 
    #
    # ===
    #
    @pyqtSlot()
    def cb_timeout( self):
        print( "Viewer: tmo")
        return

    def setWorldRect(self):

        if self.parent.parent.name == "MBSMainWindow":
            self.xmin = self.parent.parent.cxM - self.parent.parent.deltaM/2.  
            self.xmax = self.parent.parent.cxM + self.parent.parent.deltaM/2.  
            self.ymin = self.parent.parent.cyM - self.parent.parent.deltaM/2.  
            self.ymax = self.parent.parent.cyM + self.parent.parent.deltaM/2.
        
        else:
            self.xmin = 0
            self.xmax = 1
            self.ymin = 0
            self.ymax = 1

        return 
    #
    # ResetMarker
    #
    def clearResetMarker(self):
        if self.resetMarker is not None:
            self.viewBox.removeItem(self.resetMarker)
            self.resetMarker = None
        return
    
    def setResetMarker( self):
        x = self.parent.parent.cxM 
        y = self.parent.parent.cyM
        
        if self.parent.parent.deltaM < 2: 
            if self.resetMarker is None:
                self.resetMarker = pg.TextItem( "+", color='w', anchor=(0.5, 0.5))
                self.resetMarker.setZValue(10)
                self.resetMarker.setPos( x, y)
                self.viewBox.addItem( self.resetMarker, ignoreBounds=True)
                font = QFont()
                font.setPointSize(17)   
                self.resetMarker.setFont( font)
            else:
                self.resetMarker.show()
                self.resetMarker.setPos( x, y)
        else:
            self.clearResetMarker()
            # or self.resetMarker.hide()

        return 

    #
    # MPL: k and w
    #
    def setResetMarkerColor( self, rmColor):
        #print( "%s.setResetMarkerColor: %s" % ( self.name, rmColor))
        if self.resetMarker is not None:
            self.resetMarker.setColor( rmColor)
        return 
    
class SpiralDebugView( QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # --- Graphics area ---
        self.view = pg.GraphicsLayoutWidget()
        layout.addWidget(self.view)

        # Create plot inside the graphics layout
        self.plot = self.view.addPlot()
        self.plot.setAspectLocked(True)

        # Scatter plot for the animated points
        self.scatter = pg.ScatterPlotItem(
            size=6,
            brush=pg.mkBrush(50, 200, 255, 180)
        )
        self.plot.addItem(self.scatter)
        self.scatterX = []
        self.scatterY = []
        """
        # Spiral overlay curve
        self.spiral_curve = pg.PlotCurveItem(
            pen=pg.mkPen((200, 200, 200, 120), width=1)
        )
        self.plot.addItem(self.spiral_curve)

        # Storage for velocity arrows
        self._arrows = []

        # Optional: store last frame
        self.last_points = None
        """
        return

    def updateScatter( self, x, y):
        self.scatter.setData( x, y)
        return
    
    def update_frame(self, points, velocities=None, t=None):
        self.last_points = points

        # Update scatter
        self.scatter.setData(points[:, 0], points[:, 1])

        # Update spiral overlay (example: Archimedean spiral)
        if t is not None:
            theta = np.linspace(0, 6*np.pi, 800)
            a, b = 0.0, 0.1
            r = a + b * theta
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            self.spiral_curve.setData(x, y)

        # Update velocity arrows
        if velocities is not None:
            self._update_velocity_arrows(points, velocities)

    def _update_velocity_arrows(self, points, velocities):
        # Remove old arrows
        for item in self._arrows:
            self.plot.removeItem(item)
        self._arrows = []

        # Add new arrows
        for p, v in zip(points, velocities):
            angle = np.degrees(np.arctan2(v[1], v[0]))
            arrow = pg.ArrowItem(
                pos=p,
                angle=angle,
                brush=(255, 180, 0, 180),
                headLen=8
            )
            self.plot.addItem(arrow)
            self._arrows.append(arrow)    

# maybe move to utils like jpgViewer?
class PngViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.labelFk = ClickableLabel( self)
        self.name = "PngViewer"
        layout = QVBoxLayout()
        layout.addWidget(self.labelFk)
        self.setLayout(layout)
        
        self.setWindowTitle("Png Viewer")
        #self.resize(w, h)
        self.labelFk.setMinimumSize(1, 1)
        self.labelFk.setScaledContents(True)
        self.resize( 450, 450)

        return

    def closeEvent( self, event):
        self.hide()
        event.ignore()
        return
    
    def setData( self, img):
        img = img.T
        img = np.rot90(img, k=1, axes=(1, 2))
        # Convert (C, H, W) → (H, W, C)
        img = np.transpose(img, (1, 2, 0)).copy()
        h, w, c = img.shape

        # Select QImage format
        if c == 4:
            fmt = QImage.Format_RGBA8888
            bytes_per_line = 4 * w
        elif c == 3:
            fmt = QImage.Format_RGB888
            bytes_per_line = 3 * w
        else:
            raise ValueError("Only 3 or 4 channel images are supported")

        # Create QImage
        qimg = QImage(img.data, w, h, bytes_per_line, fmt)

        # Convert to QPixmap
        pixmap = QPixmap.fromImage(qimg)

        self.labelFk.setPixmap(pixmap)

        self.w = 450
        self.h = 450
        self.resize( self.w, self.h)
        self.xmin = 0.03
        self.xmax = 0.070
        self.ymin = 0.0
        self.ymax = 0.1
        return

    """    
    def mouseMoveEvent(self, event):
        self.cursor_pos = event.pos()
        #self.update()   # triggers repaint
        
        x = event.pos().x()
        xtemp = x / float(self.parent.parent.w) * \
            (self.parent.parent.xmax - self.parent.parent.xmin) + self.parent.parent.xmin

        y = event.pos().y()
        y = self.parent.parent.h - y
        ytemp = y / float(self.parent.parent.h) * \
            (self.parent.parent.ymax - self.parent.parent.ymin) + self.parent.parent.ymin

        # Debug print (optional)
        print("%s.mouseMoveEvent x %g y %g" % (self.name, xtemp, ytemp))

        self.moved.emit(xtemp, ytemp)
        return 
    """    

    

