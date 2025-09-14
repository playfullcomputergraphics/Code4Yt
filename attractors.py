#!/usr/bin/env python3
#   
import os, sys, time, math,  random, signal
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import matplotlib 
matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt 
import numpy as np
import matplotlib.colors as colors
import matplotlib.cm as cmx
from scipy.integrate import solve_ivp
import utils
import attractorHelperWidgets

EROTATES = [ '-0.5', '-0.2', '-0.1', '-0.05', '0', '0.05', '0.1', '0.2', '0.5']   
NPTS = [ 1, 2, 3, 5, 10, 20, 50, 100, 200]
SCALES = [ 0.9, 0.5, 0.6, 0.7, 0.8, 0.85, 0.95, 1.0, 1.05, 1.1, 1.2, 1.5, 2., 3., 5., 10] 
MAX_TIMES= [ 100, 10, 20, 30, 50, 200, 250, 300, 350, 400, 500]
LINE_WIDTHS= [ 0.5, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1, 2, 3, 4, 5]
MARKER_SIZES= [ 0.5, 0.1, 0.2, 0.3, 0.7, 1, 2, 3, 4, 5]
MAX_POINTS = [ 10000, 1000, 2000, 5000, 20000, 30000, 50000, 100000]
NLINES = [ 10, 1, 2, 3, 5, 7, 10, 20, 30, 50, 60, 70, 100]
SPREADS= [ 0.1, 0.001, 0.01, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 2., 3., 4., 5., 10., 15., 20, 100.]
ELEVS =[ -90, -75, -60, -45, -30, -15, 0., 15., 30., 45., 60., 75., 90.]
AZIMS =[ -180, -150, -120, -90, -60, -30.,0., 30., 60., 90., 120., 150., 180.]
EVENT_TIMEOUTS = [ 10, 1, 5, 20, 30, 50, 60, 70, 100, 500, 1000]
TAIL_LENGTHS = [ 10, 50, 100, 200, 300, 500, 1000, 1500, 2000]

PLOT_MODES = [ 'Classic', 'MovingMarkers', 'Tails'] 
PRIMITIVES = [ 'Lines', 'Markers'] 

ATTRACTORS = [ 'Lorenz', 'BoualiTyp3', 'RabinovichFabrikant',
               'Aizawa', 'Arneodo',
               'ChenLee', 'Halvorsen', 'Dadras', 'FourWing', 'Roessler',
               'TSUCS1','Thomas', 'SprottLinzF', 
               'Sakarya','NoseHoover', 
               'Separator',
               'PeterDeJong', 'Clifford',
               'GumowskiMira', 'Hopalong', 'PolynomA', 
               'CoupledLogisticMap', 'SineMap', 'Ushiki', 'BurgersMap',
               'Svensson', 'Ikeda', 
               'Pickover', 
               'Cathala', 'Tinkerbell', 'MultifoldHenon']

ATTRACTOR_DICT = { 
    'Lorenz': 
    { 'NPAR': 3,
      'Var1': { 
          'P1': 28., 'P1MIN': -10., 'P1MAX': 90.,
          'P2': 10., 'P2MIN':  0., 'P2MAX': 100.,
          'P3': 2.667, 'P3MIN': 0., 'P3MAX': 10.,
          'BackgroundColor': 'lightyellow', 
          'LineWidth': 1.0,
          'NPts': 1,
      },
      'Var2': { 
          'P1': 28., 'P1MIN': -10., 'P1MAX': 90.,
          'P2': 10., 'P2MIN':  0., 'P2MAX': 100.,
          'P3': 2.667, 'P3MIN': 0., 'P3MAX': 10., 
          'PlotMode': 'MovingMarkers',
          'NLines': 20,
          'ColorMap': 'hot',
          'NPts': 1,
      },
      'Var3': { 
          'P1': 28., 'P1MIN': 10., 'P1MAX': 100.,
          'P2': 10., 'P2MIN':  0., 'P2MAX': 50.,
          'P3': 2.667, 'P3MIN': 0., 'P3MAX': 6., 
          'PlotMode': 'Tails',
          'NLines': 30,
          'ColorMap': 'hot',
          'LineWidth': 1.0,
          'EventTimeout': 10, 
          'NPts': 1,
          'TailLength': 500,
      },
      'Var4': { 
          'P1': 28., 'P1MIN': -10., 'P1MAX': 90.,
          'P2': 10., 'P2MIN':  0., 'P2MAX': 100.,
          'P3': 0.12, 'P3MIN': 0., 'P3MAX': 10.,
          'ColorMap': 'plasma',
      },
      'PlotMode': 'Classic',
      'BackgroundColor': 'black', 
      'MaxTime': 20,
      'OneShot': False, 
      'LineWidth': 1.0,
      'is3D': True,
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.01, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 12., 'ZSTARTMIN': -20., 'ZSTARTMAX': 30.,
     }, 
    'BoualiTyp3': 
    { 'NPAR': 4,
      'Var1': { 
          'P1': 3.0, 'P1MIN':-10., 'P1MAX': 10.,
          'P2': 2.2, 'P2MIN':-10., 'P2MAX': 10.,
          'P3': 1.0, 'P3MIN':-10., 'P3MAX': 10.,
          'P4': 0.001, 'P4MIN': -10., 'P4MAX': 10.,
          'PlotMode': 'Classic', 
          'NLines': 20,
          'LineWidth': 0.3, 
          'NPts': 5., 
          'Elev': 10.0,
          'Azim': -93,
      },
      'Var2': { 
          'P1': 3.0, 'P1MIN':-10., 'P1MAX': 10.,
          'P2': 1.7, 'P2MIN':-10., 'P2MAX': 10.,
          'P3': 0.798, 'P3MIN':-10., 'P3MAX': 10.,
          'P4': 1.2, 'P4MIN': -10., 'P4MAX': 10.,
          'PlotMode': 'Classic', 
          'NLines': 10, 
          'NPts': 1,
          'ColorMap': 'plasma', 
          'Elev': 20.,
          'Azim': -240,
      },
      'Var3': { 
          'P1': 3.0, 'P1MIN':-10., 'P1MAX': 10.,
          'P2': -0.8, 'P2MIN':-10., 'P2MAX': 10.,
          'P3': 1.0, 'P3MIN':-10., 'P3MAX': 10.,
          'P4': 0.001, 'P4MIN': -10., 'P4MAX': 10.,
          'PlotMode': 'Classic', 
          'NLines': 10, 
          'NPts': 1,
          'ColorMap': 'gist_rainbow', 
          'LineWidth': 0.5, 
          'Elev': 20.,
          'Azim': -240,
      },
      'Var4': { 
          'P1': 3.0, 'P1MIN':-10., 'P1MAX': 10.,
          'P2': -1.1, 'P2MIN':-10., 'P2MAX': 10.,
          'P3': 1.0, 'P3MIN':-10., 'P3MAX': 10.,
          'P4': 0.001, 'P4MIN': -10., 'P4MAX': 10.,
          'PlotMode': 'Classic', 
          'NLines': 10, 
          'NPts': 1,
          'ColorMap': 'gist_rainbow', 
          'LineWidth': 0.5, 
          'Elev': 20.,
          'Azim': -240,
      },
      'Var5': { 
          'P1': 3.0, 'P1MIN':-10., 'P1MAX': 10.,
          'P2': 2.2, 'P2MIN':-10., 'P2MAX': 10.,
          'P3': 1.0, 'P3MIN':-10., 'P3MAX': 10.,
          'P4': 0.00, 'P4MIN': -10., 'P4MAX': 10.,
          'PlotMode': 'Classic', 
          'NLines': 10, 
          'NPts': 1,
          'ColorMap': 'gist_rainbow', 
          'LineWidth': 0.5, 
          'Elev': 20.,
          'Azim': -240,
      },
      'Primitive': 'Lines',
      'NLines': 10, 
      'LineWidth': 0.3, 
      'LeadingMarkers': True,
      'BackgroundColor': 'black', 
      'ColorMap': 'hot', 
      'MaxTime': 250,
      'MaxPoints': 20000,
      'Elev': 35.29,
      'Azim': -93,
      'NPts': 10, 
      'is3D': True,
      'XSTART': 1., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 1., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'RabinovichFabrikant':
    { 'NPAR': 2,
      'Var1': { 
          'P1': 0.14, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.1, 'P2MIN':  -10., 'P2MAX': 10.,
          'PlotMode': 'Classic', 
      }, 
      'Var2': { 
          'P1': 0.14, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.1, 'P2MIN':  -10., 'P2MAX': 10.,
          'PlotMode': 'Tails',
          'TailLength': 1000, 
          'NLines': 30, 
      },
      'Var3': { 
          'P1': 0.14, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.04, 'P2MIN':  -10., 'P2MAX': 10.,
          'PlotMode': 'Tails',
          'TailLength': 1000, 
          'NLines': 30, 
      },
      'Var4': { 
          'P1': 0.14, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.04, 'P2MIN':  -10., 'P2MAX': 10.,
          'PlotMode': 'Tails',
          'TailLength': 1000, 
          'NLines': 30, 
          'XSTART': -2., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
          'YSTART': 2.5, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
          'ZSTART': 0.2, 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
      },
      'ColorMap': 'gist_rainbow',  
      'BackgroundColor': 'black', 
      'NLines': 10, 
      'LineWidth': 1.0, 
      'MaxTime': 100,
      'is3D': True, 
      # 'xyzs': [ 0., -1.2 + dI, 0.2]
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 2.5, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0.2, 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Aizawa': 
    { 'NPAR': 6,
      'Var1': { 
          'P1': 0.95, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.7, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 0.6, 'P3MIN': -10., 'P3MAX': 10.,
          'P4': 3.5, 'P4MIN': -10., 'P4MAX': 10.,
          'P5': 0.25, 'P5MIN': -10., 'P5MAX': 10.,
          'P6': 0.1, 'P6MIN':  -10., 'P6MAX': 10.,
          'BackgroundColor': 'lightyellow', 
          'LineWidth': 0.5, 
      },
      'Var2': { 
          'P1': 0.95, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.7, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 0.6, 'P3MIN': -10., 'P3MAX': 10.,
          'P4': 3.5, 'P4MIN': -10., 'P4MAX': 10.,
          'P5': 0.25, 'P5MIN': -10., 'P5MAX': 10.,
          'P6': 0.1, 'P6MIN':  -10., 'P6MAX': 10.,
          'ColorMap': 'plasma',
          'LineWidth': 1, 
          'BackgroundColor': 'black', 
      },
      'Var3': { 
          'P1': 0.95, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.7, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 0.6, 'P3MIN': -10., 'P3MAX': 10.,
          'P4': 3.5, 'P4MIN': -10., 'P4MAX': 10.,
          'P5': 0.25, 'P5MIN': -10., 'P5MAX': 10.,
          'P6': 2.1, 'P6MIN':  -10., 'P6MAX': 10.,
          'ColorMap': 'plasma',
          'LineWidth': 1, 
          'BackgroundColor': 'black', 
      },
      'Var4': { 
          'P1': 0.95, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.7, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 0.6, 'P3MIN': -10., 'P3MAX': 10.,
          'P4': 3.5, 'P4MIN': -10., 'P4MAX': 10.,
          'P5': 10., 'P5MIN': -10., 'P5MAX': 10.,
          'P6': 0.1, 'P6MIN':  -10., 'P6MAX': 10.,
          'ColorMap': 'plasma',
          'LineWidth': 1, 
          'BackgroundColor': 'black', 
      },
      'Var5': { 
          'P1': 0.95, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 1.74, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 0.6, 'P3MIN': -10., 'P3MAX': 10.,
          'P4': 3.5, 'P4MIN': -10., 'P4MAX': 10.,
          'P5': 10., 'P5MIN': -10., 'P5MAX': 10.,
          'P6': 0.1, 'P6MIN':  -10., 'P6MAX': 10.,
          'ColorMap': 'plasma',
          'LineWidth': 1, 
          'BackgroundColor': 'black', 
      },
      'PlotMode': 'Classic', 
      'NPts': 1., 
      'is3D': True,
      'XSTART': 0.1, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'PeterDeJong': 
    { 'NPAR': 4,
      'Var1': { 
          'P1': 0.4, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 60., 'P2MIN': 0., 'P2MAX': 100.,
          'P3': 10., 'P3MIN': 0., 'P3MAX': 20.,
          'P4': 1.6, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var2': { 
          'P1': 1.641, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': 1.902, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 0.316, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': 1.525, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var3': { 
          'P1': 0.070, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': -1.899, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 1.381, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': -1.506, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var4': { 
          'P1': 1.4, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': -2.3, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 2.4, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': -2.1, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var5': { 
          'P1': 2.01, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': -2.53, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 1.61, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': -0.33, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var6': { 
          'P1': -2.7, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': -0.09, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': -0.86, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': -2.2, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var7': { 
          'P1': -0.827, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': -1.637, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 1.659, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': -0.943, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var8': { 
          'P1': -2.24, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': 0.43, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': -0.65, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': -2.43, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var9': { 
          'P1': -2., 'P1MIN': -5., 'P1MAX': 5.,
          'P2': -2., 'P2MIN': -5., 'P2MAX': 5.,
          'P3': -1.2, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': 2.0, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var10': { 
          'P1': -0.709, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': 1.638, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 0.452, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': 1.740, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'ColorMap': 'prism', 
      'Primitive': 'Markers', 
      'MarkerSize': 0.2, 
      'LeadingMarkers': False,
      'BackgroundColor': 'black',
      'MaxPoints': 20000, 
      'MaxTime': 100,
      'NPts': 100., 
      'Elev': 90.,
      'Azim': -90.,
      'is3D': False, 
      'XSTART': 0.1, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Clifford': 
    { 'NPAR': 4,
      'Var1': { 
          'P1': -1.4, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 1.6, 'P2MIN': -5., 'P2MAX': 0.,
          'P3': 1.0, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': 0.7, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var2': { 
          'P1': 1.6, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': -0.6, 'P2MIN': -5., 'P2MAX': 0.,
          'P3': -1.2, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': 1.6, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var3': { 
          'P1': 1.7, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 1.7, 'P2MIN': -5., 'P2MAX': 0.,
          'P3': 0.6, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': 1.2, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var4': { 
          'P1': 1.5, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': -1.8, 'P2MIN': -5., 'P2MAX': 0.,
          'P3': 1.6, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': 0.9, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var5': { 
          'P1': -1.7, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 1.3, 'P2MIN': -5., 'P2MAX': 0.,
          'P3': -0.1, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': -1.2, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var5': { 
          'P1': -1.7, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 1.8, 'P2MIN': -5., 'P2MAX': 0.,
          'P3': -1.9, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': -0.4, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var6': { 
          'P1': -1.8, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': -2.0, 'P2MIN': -5., 'P2MAX': 0.,
          'P3': -0.5, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': -0.9, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var7': { 
          'P1': 2.0, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 2.0, 'P2MIN': -5., 'P2MAX': 0.,
          'P3': 1., 'P3MIN': 0., 'P3MAX': 5.,
          'P4': -1., 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'ColorMap': 'viridis', 
      'Primitive': 'Markers', 
      'MarkerSize': 0.1, 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'MaxPoints': 50000,
      'MaxTime': 100,
      'NPts': 100, 
      'Elev': 90.,
      'Azim': -90., 
      'is3D': False, 
      'XSTART': 0.1, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'GumowskiMira': 
    { 'NPAR': 2,
      'Var1': { 
          'P1': 0.92, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 0.84, 'P2MIN':  -2., 'P2MAX': 2.,
      },
      'Var2': { 
          'P1': -0.144, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 0.84, 'P2MIN':  -2., 'P2MAX': 2.,
      },
      'Var3': { 
          'P1': 0.92, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 0., 'P2MIN':  -2., 'P2MAX': 2.,
      },
      'Var4': { 
          'P1': -0.1, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 1.0005, 'P2MIN':  -2., 'P2MAX': 2.,
      },
      'Var5': { 
          'P1': -0.77, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 0.932, 'P2MIN':  -2., 'P2MAX': 2.,
      },
      'Var6': { 
          'P1': -0.77, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 0.812, 'P2MIN':  -2., 'P2MAX': 2.,
      },
      'Primitive': 'Markers', 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'MarkerSize': 0.2, 
      'ColorMap': 'jet', 
      'MaxPoints': 30000,
      'MaxTime': 100,
      'NPts': 100., 
      'Elev': 90,
      'Azim': -90, 
      'is3D': False, 
      'XSTART': 0.1, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Halvorsen': 
    { 'NPAR': 1,
      'Var1': {
          'P1': 1.4, 'P1MIN': -10., 'P1MAX': 10.,
      },
      'Var2': {
          'P1': 1.4, 'P1MIN': -10., 'P1MAX': 10.,
          'PlotMode': 'Tails', 
          'NLines': 20,
          'TailsLength': 1000,
      },
      'is3D': True,
      'Elev': -20,
      'Azim': -132, 
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
      }, 
    'Thomas': 
    { 'NPAR': 1,
      'Var1': {
          'P1': 0.208186, 'P1MIN': -10., 'P1MAX': 10.,
          },
      'MaxTime': 200, 
      'is3D': True,
      'XSTART': 0.1, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
      },
    'NoseHoover': 
    { 'NPAR': 1,
      'Var1': {
          'P1': 1.5, 'P1MIN': 0., 'P1MAX': 2.,
      },
      'ColorMap': 'hot', 
      'BackgroundColor': 'black', 
      'NLines': 50,
      'MaxTime': 500,
      'LineWidth': 0.5,
      'Elev': 60,
      'Azim': 50, 
      'is3D': True, 
      'XSTART': 1.0, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
      },
    'SprottLinzF': 
    { 'NPAR': 1,
      'Var1': {
        'P1': 0.5, 'P1MIN': -1., 'P1MAX': 0.7,
          },
      'Elev': 24,
      'Azim': -90, 
      'is3D': True, 
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 1., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
      },
    'Sakarya': 
    { 'NPAR': 2,
      'Var1': { 
          'P1': 0.4, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.3, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'MaxTime': 20,
      'Elev': -96,
      'Azim': -46, 
      'is3D': False, 
      'XSTART': 1.0, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': -1.0, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'SineMap': 
    { 'NPAR': 2,
      'Var1': { 
          'P1': 2.0, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.5, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Var2': { 
          'P1': 1.8, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.3, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Primitive': 'Markers', 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'ColorMap': 'hot', 
      'MaxTime': 100,
      'NPts': 100., 
      'Elev': 90,
      'Azim': -90, 
      'is3D': False, 
      'XSTART': 0.1, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'MultifoldHenon': 
    { 'NPAR': 2,
      'Var1': { 
          'P1': 4.9, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.9, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Var2': { 
          'P1': 2.88, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.82, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Primitive': 'Markers', 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'MarkerSize': 0.2, 
      'ColorMap': 'hot', 
      'MaxTime': 100,
      'NPts': 100., 
      'Elev': 90,
      'Azim': -90, 
      'is3D': False, 
      'XSTART': 1.0, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 1.0, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Cathala': 
    { 'NPAR': 2,
      'Var1': { 
          'P1': 0.7, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': -0.82, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Var2': { 
          'P1': -0.02, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': -0.82, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Primitive': 'Markers', 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'MarkerSize': 0.2, 
      'ColorMap': 'hot', 
      'MaxTime': 100,
      'NPts': 100., 
      'Elev': 90,
      'Azim': -90, 
      'is3D': False,
      'XSTART': 0.5, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.5, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,

     },
    'CoupledLogisticMap': 
    { 'NPAR': 2,
      'Var1': { 
          'P1': 0.012, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 3.7, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Var2': { 
          'P1': 0.012, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 3.62, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Var3': { 
          'P1': 0.014, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 3.7, 'P2MIN':  -10., 'P2MAX': 10.,
      },
      'Primitive': 'Markers', 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'ColorMap': 'hot', 
      'MaxTime': 100,
      'MaxPoints': 20000, 
      'MarkerSize': 0.2, 
      'NPts': 100., 
      'Elev': 90,
      'Azim': -90, 
      'is3D': False, 
      'XSTART': 0.3, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Ikeda': 
    { 'NPAR': 2,
      'Var1': {
          'P1': 0., 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.97, 'P2MIN':  -10., 'P2MAX': 10.,
      }, 
      'Var2': {
          'P1': 0.4, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.9, 'P2MIN':  -10., 'P2MAX': 10.,
      }, 
      'Var3': {
          'P1': 0.1100, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.9840, 'P2MIN':  -10., 'P2MAX': 10.,
      }, 
      'Var4': {
          'P1': 0.1180, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.998, 'P2MIN':  -10., 'P2MAX': 10.,
      }, 
      'BackgroundColor': 'black', 
      'ColorMap': 'hot', 
      'Primitive': 'Markers', 
      'LeadingMarkers': False,
      'MaxTime': 100,
      'Elev': -96,
      'Azim': -46, 
      'is3D': False,
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'BurgersMap': 
    { 'NPAR': 2,
      'Var1': {
          'P1': 0.4, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.78, 'P2MIN':  -10., 'P2MAX': 10.,
          }, 
      'Var2': {
          'P1': 0.95, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.95, 'P2MIN':  -10., 'P2MAX': 10.,
          }, 
      'Var3': {
          'P1': 1.5, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.85, 'P2MIN':  -10., 'P2MAX': 10.,
          }, 
      'Primitive': 'Markers', 
      'BackgroundColor': 'black', 
      'ColorMap': 'hot', 
      'MarkerSize': 0.2, 
      'NPts': 100., 
      'LeadingMarkers': False,
      'MaxTime': 100,
      'Elev': 90.,
      'Azim': -90., 
      'is3D': False, 
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.5, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'FourWing': 
    { 'NPAR': 3,
      'Var1': { 
          'P1': 0.2, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.01, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': -0.4, 'P3MIN': -10., 'P3MAX': 10.
      },
      'MaxTime': 200,
      'Elev': 31.,
      'Azim': 10.,
      'LineWidth': 1, 
      'is3D': True,
      'XSTART': 1., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 1., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Hopalong': 
    { 'NPAR': 3,
      'Var1': { 
          'P1': 0.4, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 1.1, 'P2MIN': -2., 'P2MAX': 2.,
          'P3': -0.1, 'P3MIN': -2., 'P3MAX': 2.},
      'Var2': { 
          'P1': 0.1, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 0.5, 'P2MIN': -2., 'P2MAX': 2.,
          'P3': 0.45, 'P3MIN': -2., 'P3MAX': 2.},
      'Var3': { 
          'P1': 0.4, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': -0.024, 'P2MIN': -2., 'P2MAX': 2.,
          'P3': -0.1, 'P3MIN': -2., 'P3MAX': 2.
      },
      'Primitive': 'Markers', 
      'BackgroundColor': 'black', 
      'ColorMap': 'hot', 
      'MarkerSize': 0.2, 
      'NPts': 100., 
      'LeadingMarkers': False,
      'MaxTime': 100,
      'Elev': 90.,
      'Azim': -90., 
      'is3D': False,
      'XSTART': 0.5, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.5, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
      },
    'PolynomA': 
    { 'NPAR': 3,
      'Var1': { 
          'P1': 1.586, 'P1MIN': 1.0 , 'P1MAX': 2.,
          'P2': 1.124, 'P2MIN': 0.5 , 'P2MAX': 1.5,
          'P3': 0.281, 'P3MIN': 0., 'P3MAX': 0.5,
      },
      'Primitive': 'Markers', 
      'MarkerSize': 0.3, 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'MaxTime': 100,
      'Elev': -15,
      'Azim': 23, 
      'is3D': False,
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Roessler': 
    { 'NPAR': 3,
      'Var1': { 
          'P1': 0.2, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 0.2, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 5.7, 'P3MIN': -10., 'P3MAX': 10.,
      },
      'BackgroundColor': 'black', 
      'NLines': 30,
      'is3D': True,
      'Spread': 2, 
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 1., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 1., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Arneodo': 
    { 'NPAR': 3,
      'Var1': { 
          'P1': -5.5, 'P1MIN': -10., 'P1MAX': 0.,
          'P2': 3.5, 'P2MIN': -5., 'P2MAX': 10.,
          'P3': -1, 'P3MIN':  -10., 'P3MAX': 10.,
      }, 
      'Var2': { 
          'P1': -5.5, 'P1MIN': -10., 'P1MAX': 0.,
          'P2': 3.5, 'P2MIN': -5., 'P2MAX': 10.,
          'P3': -1, 'P3MIN':  -10., 'P3MAX': 10.,
          'BackgroundColor': 'black', 
          'ColorMap': 'viridis', 
          'NLines': 30,
          'LineWidth': 1,
          'Scale': 0.7,
          'Spread': 1, 
      }, 
      'Elev': 61.,
      'Azim': -190,
      'is3D': True,
      'XSTART': 1., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 1., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'ChenLee': 
    { 'NPAR': 3,
      'Var1': { 
          'P1': 5., 'P1MIN': 0., 'P1MAX': 10.,
          'P2': -10., 'P2MIN': -20., 'P2MAX': 0.,
          'P3': -0.38, 'P3MIN':  -5., 'P3MAX': 5.,
      }, 
      'Var2': { 
          'P1': 5., 'P1MIN': 0., 'P1MAX': 10.,
          'P2': -10., 'P2MIN': -20., 'P2MAX': 0.,
          'P3': -0.38, 'P3MIN':  -5., 'P3MAX': 5.,
          'PlotMode': 'Tails',
          'TailLength': 1000,
          'NPts': 3, 
      }, 
      'Elev': 27.,
      'Azim': -70.,
      'is3D': True,
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 1., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 2., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Tinkerbell': 
    { 'NPAR': 4,
      'Var1': { 
          'P1': 0.9, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': -0.601, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 2.0, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': 0.5, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Var2': { 
          'P1': 0.9, 'P1MIN': -5., 'P1MAX': 5.,
          'P2': -0.31, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 2.0, 'P3MIN': -5., 'P3MAX': 5.,
          'P4': 0.5, 'P4MIN':  -5., 'P4MAX': 5.,
      },
      'Primitive': 'Markers', 
      'ColorMap': 'hot', 
      'MarkerSize': 0.3, 
      'NPts': 100., 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'MaxTime': 100,
      'Elev': 90.,
      'Azim': -90., 
      'is3D': False,
      'XSTART': -0.72, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': -0.64, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Ushiki': 
    { 'NPAR': 4,
      'Var1': { 
          'P1': 3.7, 'P1MIN': 0., 'P1MAX': 10.,
          'P2': 0.1, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 3.7, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': 0.15, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var2': { 
          'P1': 3.5, 'P1MIN': 0., 'P1MAX': 10.,
          'P2': 0.1, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 3.7, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': 0.15, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Var3': { 
          'P1': 3.7, 'P1MIN': 0., 'P1MAX': 10.,
          'P2': 0.18, 'P2MIN': -5., 'P2MAX': 5.,
          'P3': 3.7, 'P3MIN': 0., 'P3MAX': 5.,
          'P4': 0.15, 'P4MIN':  -5., 'P4MAX': 3.,
      },
      'Primitive': 'Markers', 
      'MarkerSize': 0.3, 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'ColorMap': 'hot', 
      'MaxTime': 100,
      'NPts': 100., 
      'Elev': 90.,
      'Azim': -90., 
      'is3D': False,
      'XSTART': 0.1, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Pickover': 
    { 'NPAR': 4,
      'Var1': { 
          'P1': -0.759, 'P1MIN': -2., 'P1MAX': 2.,
          'P2': 2.449, 'P2MIN': 1., 'P2MAX': 4.,
          'P3': 1.253, 'P3MIN': 0., 'P3MAX': 3.,
          'P4': 1.5, 'P4MIN':  0., 'P4MAX': 3.,
      },
      'Primitive': 'Markers', 
      'MarkerSize': 0.3, 
      'LeadingMarkers': False,
      'BackgroundColor': 'lightyellow', 
      'MaxTime': 100,
      'Elev': 20.,
      'Azim': -90., 
      'is3D': False,
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Svensson': 
    { 'NPAR': 4,
      'Var1': { 
          'P1': 1.4, 'P1MIN': 0., 'P1MAX': 5.,
          'P2': 1.6, 'P2MIN': 0., 'P2MAX': 5.,
          'P3': -1.4, 'P3MIN': -3., 'P3MAX': 3.,
          'P4': 1.5, 'P4MIN': -2., 'P4MAX': 3.,
      }, 
      'Var2': { 
          'P1': 1.3, 'P1MIN': 0., 'P1MAX': 5.,
          'P2': 1.3, 'P2MIN': 0., 'P2MAX': 5.,
          'P3': 1.3, 'P3MIN': -3., 'P3MAX': 3.,
          'P4': 1.3, 'P4MIN': -2., 'P4MAX': 3.,
      }, 
      'Var3': { 
          'P1': 1.4, 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 1.56, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 1.4, 'P3MIN': -10., 'P3MAX': 10.,
          'P4': 6.56, 'P4MIN': -10., 'P4MAX': 10.,
      }, 
      'Primitive': 'Markers', 
      'MarkerSize': 0.3, 
      'LeadingMarkers': False,
      'BackgroundColor': 'black', 
      'ColorMap': 'hot', 
      'MaxTime': 200,
      'Elev': 90.,
      'Azim': -90., 
      'NPts': 100., 
      'is3D': False,
      'XSTART': 0.1, 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 0.1, 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'Dadras': 
    { 'NPAR': 5,
      'Var1': {       
          'P1': 3., 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 2.7, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 1.7, 'P3MIN': -10., 'P3MAX': 10.,
          'P4': 2.0, 'P4MIN': -10., 'P4MAX': 10.,
          'P5': 9.0, 'P5MIN':  0., 'P5MAX': 20.,
      },
      'Var2': {       
          'P1': 3., 'P1MIN': -10., 'P1MAX': 10.,
          'P2': 2.7, 'P2MIN': -10., 'P2MAX': 10.,
          'P3': 1.7, 'P3MIN': -10., 'P3MAX': 10.,
          'P4': 2.0, 'P4MIN': -10., 'P4MAX': 10.,
          'P5': 9.0, 'P5MIN':  0., 'P5MAX': 20.,
          'PlotMode': 'Tails', 
          'NLines': 20,
          'TailsLength': 1000,
      },
      'NPts': 1., 
      'is3D': True,
      'XSTART': 1., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 1., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': 0., 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
    'TSUCS1': 
    { 'NPAR': 5,
      'Var1': { 
          'P1': 40., 'P1MIN': 35., 'P1MAX': 45.,
          'P2': 0.833, 'P2MIN': 0., 'P2MAX': 1.5,
          'P3': 0.5, 'P3MIN': 0., 'P3MAX': 1.,
          'P4': 0.65, 'P4MIN': 0., 'P4MAX': 1.5,
          'P5': 20., 'P5MIN':  10., 'P5MAX': 30.,
      },
      'Primitive': 'Markers',
      'ColorMap': 'hot', 
      'BackgroundColor': 'black', 
      'Elev': -22,
      'Azim': 0, 
      'NPts': 1., 
      'is3D': True,
      'XSTART': 0., 'XSTARTMIN': -10., 'XSTARTMAX': 10.,
      'YSTART': 7., 'YSTARTMIN': -10., 'YSTARTMAX': 10.,
      'ZSTART': -0.1, 'ZSTARTMIN': -10., 'ZSTARTMAX': 10.,
     },
}

class TMO( Exception):
    def __init__( self, *argin):
        self.value = argin
    def __str__( self): 
        return repr( self.value)

def handlerALRM( signum, frame):
    raise TMO( "tmo-exception")

# +++
class mainWidget( QMainWindow):
    def __init__(self, app, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("Attraction")
        self.app = app

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
        self.colorMap = utils.CMAPS[8]
        self.nLines = NLINES[0]
        self.axesOnOff = False
        self.oneShot = False
        self.backgroundColor = utils.BACKGROUND_CMAPS[2]
        self.primitive = PRIMITIVES[0]
        self.maxPoints = MAX_POINTS[0]
        self.maxTime = MAX_TIMES[0]
        self.timerBusy = False
        self.lineWidth = LINE_WIDTHS[0]
        self.markerSize = MARKER_SIZES[0]
        self.attractor = ATTRACTORS[ 0]
        self.cfgHsh = ATTRACTOR_DICT[ self.attractor]
        self.eRotString = '0'
        self.aRotString = '0'
        self.scale = SCALES[0]
        self.spread = SPREADS[0]
        self.timeoutCount = 0
        self.eventTimeout = EVENT_TIMEOUTS[ 0]
        self.leadingMarkers = True
        self.calledFromApply = False
        self.calledFromCreateImage = False
        self.nPts = 1
        self.var = 'Var1'
        self.is3D = self.cfgHsh[ 'is3D']
        self.parameterWidget = None
        self.startValuesWidget = None
        self.tailLength = TAIL_LENGTHS[0]
        self.plotMode = 'Classic'
        self.sliderBusy = False
        #
        # tell setCurrentIndices() that the Combos
        # have not yet been created to far 
        #
        self.maxPointsCombo = None
        self.elev = 30
        self.azim = -60
        self.elevLabel = None
        self.azimLabel = None
        self.ax = None
        self.timer = None
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.p4 = None
        self.p5 = None
        self.p6 = None
        
        self.prepareMenuBar()
        self.prepareCentralPart()
        self.prepareStatusBar()

        self.logWidget.append( "Attractor %s" % self.attractor)
        
        self.setViewingParameters()
        self.prepareAttraction()
        self.setViewingParameters()
        self.handle3DWidgets()
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timeoutEvent)
        self.timer.start( self.eventTimeout)
        self.i = 1
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
        # png
        #
        self.pngAction = QAction('Create png file', self)        
        self.pngAction.triggered.connect( self.cb_png)
        self.fileMenu.addAction( self.pngAction)
        #
        # pdf
        #
        self.pdfAction = QAction('Create pdf file', self)        
        self.pdfAction.triggered.connect( self.cb_pdf)
        self.fileMenu.addAction( self.pdfAction)
        #
        # test
        #
        self.testAction = QAction('Test', self)        
        self.testAction.triggered.connect( self.cb_test)
        self.fileMenu.addAction( self.testAction)
        #
        # help
        #
        self.menuBarRight = QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarRight, QtCore.Qt.TopRightCorner)
        self.helpMenu = self.menuBarRight.addMenu('Help')
        self.menuBar.setCornerWidget( self.menuBarRight, QtCore.Qt.TopRightCorner)
        #
        # Lorenz
        #
        self.lorenzAction = self.helpMenu.addAction(self.tr("Lorenz"))
        self.lorenzAction.triggered.connect( self.cb_helpLorenz)
        #
        # PeterDeJong
        #
        self.peterDeJongAction = self.helpMenu.addAction(self.tr("PeterDeJong"))
        self.peterDeJongAction.triggered.connect( self.cb_helpPeterDeJong)
        #
        # Clifford
        #
        self.cliffordAction = self.helpMenu.addAction(self.tr("Clifford"))
        self.cliffordAction.triggered.connect( self.cb_helpClifford)
        return
    #    
    # === the central part
    #    
    def prepareCentralPart( self):

        w = QWidget()
        self.setCentralWidget( w)
        #
        # start with a vertical layout
        #
        self.vLayout = QVBoxLayout()
        w.setLayout( self.vLayout)
        self.gridLayout = QGridLayout()
        self.vLayout.addLayout( self.gridLayout)
        #
        # attractors
        #
        self.attractorCombo = QComboBox()
        for elm in ATTRACTORS:
            if elm == 'Separator': 
                self.attractorCombo.insertSeparator( 1000)
                continue
            self.attractorCombo.addItem( str( elm))
        self.attractorCombo.setCurrentIndex( 0)
        self.attractorCombo.activated.connect( self.cb_attractorCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Attractor'))
        hLayout.addWidget( self.attractorCombo)

        row = 0
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # variation
        #
        self.varCombo = QComboBox()
        self.varCombo.setToolTip( "Different sets of parameters (a, b, ...)")
        for i in range( 1, 10):
            var = "Var%d" % i
            if var in self.cfgHsh:
                if 'PlotMode' in self.cfgHsh[ var]:
                    temp = "%s (%s)" % ( var, self.cfgHsh[ var][ 'PlotMode'])
                elif 'PlotMode' in self.cfgHsh:
                    temp = "%s (%s)" % ( var, self.cfgHsh[ 'PlotMode'])
                else:
                    temp = "%s (Classic)" % ( var)
                self.varCombo.addItem( temp)
        self.varCombo.setCurrentIndex( 0)
        self.varCombo.activated.connect( self.cb_varCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Variant'))
        hLayout.addWidget( self.varCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # background color
        #
        self.backgroundCombo = QComboBox()
        for elm in utils.BACKGROUND_CMAPS:
            self.backgroundCombo.addItem( str( elm))
        self.backgroundCombo.setCurrentIndex( 2)
        self.backgroundCombo.activated.connect( self.cb_backgroundCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Background'))
        hLayout.addWidget( self.backgroundCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)

        #
        # color maps
        #
        self.cmapCombo = QComboBox()
        for elm in utils.CMAPS:
            self.cmapCombo.addItem( str( elm))
        self.cmapCombo.setCurrentIndex( 8)
        self.cmapCombo.activated.connect( self.cb_cmapCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'ColorMap'))
        hLayout.addWidget( self.cmapCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)

        #
        # max points
        #
        self.maxPointsCombo = QComboBox()
        self.maxPointsCombo.setToolTip(
            "Length of the line, marker arrays, \nincrease to make the lines smoother.")
        for elm in MAX_POINTS: 
            self.maxPointsCombo.addItem( str( elm))
        self.maxPointsCombo.setCurrentIndex( 0)
        self.maxPointsCombo.activated.connect( self.cb_maxPointsCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'MaxPoints'))
        hLayout.addWidget( self.maxPointsCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # max T
        #
        self.maxTimesCombo = QComboBox()
        self.maxTimesCombo.setToolTip( "Integration time limit")
        for elm in MAX_TIMES: 
            self.maxTimesCombo.addItem( str( elm))
        self.maxTimesCombo.setCurrentIndex( 0)
        self.maxTimesCombo.activated.connect( self.cb_maxTimesCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'MaxTime'))
        hLayout.addWidget( self.maxTimesCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # max lines
        #
        self.nLinesCombo = QComboBox()
        for elm in NLINES: 
            self.nLinesCombo.addItem( str( elm))
        self.nLinesCombo.setCurrentIndex( 0)
        self.nLinesCombo.activated.connect( self.cb_maxLinesCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'No. of Lines'))
        hLayout.addWidget( self.nLinesCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # lines/markers
        #
        self.primitiveCombo = QComboBox()
        for elm in PRIMITIVES: 
            self.primitiveCombo.addItem( elm)
        self.primitiveCombo.setCurrentIndex( 0)
        self.primitiveCombo.activated.connect( self.cb_primitiveCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Primitive'))
        hLayout.addWidget( self.primitiveCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # line width
        #
        self.lineWidthCombo = QComboBox()
        for elm in LINE_WIDTHS: 
            self.lineWidthCombo.addItem( str( elm))
        self.lineWidthCombo.setCurrentIndex( 0)
        self.lineWidthCombo.activated.connect( self.cb_lineWidthCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Line Width'))
        hLayout.addWidget( self.lineWidthCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)

        #
        # marker size
        #
        self.markerSizeCombo = QComboBox()
        for elm in MARKER_SIZES: 
            self.markerSizeCombo.addItem( str( elm))
        self.markerSizeCombo.setCurrentIndex( 0)
        self.markerSizeCombo.activated.connect( self.cb_markerSizeCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Marker Size'))
        hLayout.addWidget( self.markerSizeCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # nPts
        #
        self.nPtsCombo = QComboBox()
        self.nPtsCombo.setToolTip(
            "nPts no. of points added during update, \nincrease to have the attractor plotted faster")
        for elm in NPTS: 
            self.nPtsCombo.addItem( str( elm))
        self.nPtsCombo.setCurrentIndex( 0)
        self.nPtsCombo.activated.connect( self.cb_nPtsCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'NPts'))
        hLayout.addWidget( self.nPtsCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # spread
        #
        self.spreadCombo = QComboBox()
        self.spreadCombo.setToolTip( "Spread of the lines start position")
        for elm in SPREADS: 
            self.spreadCombo.addItem( str( elm))
        self.spreadCombo.setCurrentIndex( 0)
        self.spreadCombo.activated.connect( self.cb_spreadCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Spread'))
        hLayout.addWidget( self.spreadCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # elev
        #
        self.elevSlider = QSlider()
        self.elevSlider.setToolTip( "Change elevation")
        self.elevSlider.sliderMoved.connect( self.cb_elevSlider)
        self.elevSlider.setMinimum( 0)
        self.elevSlider.setMaximum( 1000)
        self.elevSlider.setValue( int( (self.elev + 90)/180.*1000.))
        self.elevSlider.setOrientation( 1) # 1 horizontal, 2 vertical
        self.elevLabel = QLabel( "Elev %6.2f" % self.elev)
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.elevLabel)
        hLayout.addWidget( self.elevSlider)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # azim
        #
        self.azimSlider = QSlider()
        self.azimSlider.setToolTip( "Change azimutal")
        self.azimSlider.sliderMoved.connect( self.cb_azimSlider)
        self.azimSlider.setMinimum( 0)
        self.azimSlider.setMaximum( 1000)
        self.azimSlider.setValue( int((self.azim + 180.)/360.*1000))
        self.azimSlider.setOrientation( 1) # 1 horizontal, 2 vertical
        self.azimLabel = QLabel( "Azim %6.2f" % self.azim)
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.azimLabel)
        hLayout.addWidget( self.azimSlider)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # eRotate
        #
        self.eRotCombo = QComboBox()
        self.eRotCombo.setToolTip( "Rotate elevation, units per timeout")
        for elm in EROTATES: 
            self.eRotCombo.addItem( str( elm))
        self.eRotCombo.setCurrentIndex( 4)
        self.eRotCombo.activated.connect( self.cb_eRotCombo )
        self.eRotLabel = QLabel( 'ERot')
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.eRotLabel) 
        hLayout.addWidget( self.eRotCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # aRotate
        #
        self.aRotCombo = QComboBox()
        self.aRotCombo.setToolTip( "Rotate azimut, units per timeout")
        for elm in EROTATES: 
            self.aRotCombo.addItem( str( elm))
        self.aRotCombo.setCurrentIndex( 4)
        self.aRotCombo.activated.connect( self.cb_aRotCombo )
        self.aRotLabel = QLabel( 'ARot')
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.aRotLabel)
        hLayout.addWidget( self.aRotCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # scale
        #
        self.scaleCombo = QComboBox()
        self.scaleCombo.setToolTip( "Scale plot")
        for elm in SCALES: 
            self.scaleCombo.addItem( str( elm))
        self.scaleCombo.setCurrentIndex( 0)
        self.scaleCombo.activated.connect( self.cb_scaleCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Scale'))
        hLayout.addWidget( self.scaleCombo)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # plotMode
        #
        self.plotModeCombo = QComboBox()
        self.plotModeCombo.setToolTip( "PlotMode plot")
        for elm in PLOT_MODES: 
            self.plotModeCombo.addItem( str( elm))
        self.plotModeCombo.setCurrentIndex( 0)
        self.plotModeCombo.activated.connect( self.cb_plotModeCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'PlotMode'))
        hLayout.addWidget( self.plotModeCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # oneShot on/off
        #
        self.oneShotCb = QCheckBox( "OneShot", self)
        self.oneShotCb.clicked.connect( self.cb_oneShot)
        row += 1
        col = 0
        self.gridLayout.addWidget( self.oneShotCb, row, col)
        #
        # tailLength
        #
        self.tailLengthCombo = QComboBox()
        self.tailLengthCombo.setToolTip( "Length of the tail, if in 'Tails' mode")
        for elm in TAIL_LENGTHS: 
            self.tailLengthCombo.addItem( str( elm))
        self.tailLengthCombo.setCurrentIndex( 0)
        self.tailLengthCombo.activated.connect( self.cb_tailLengthCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'TailLength'))
        hLayout.addWidget( self.tailLengthCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # paused
        #
        self.pausedCb = QCheckBox( "Paused", self)
        self.pausedCb.clicked.connect( self.cb_paused)
        row += 1
        col = 0
        self.gridLayout.addWidget( self.pausedCb, row, col)
        #
        # timer interval
        #
        self.eventTimeoutCombo = QComboBox()
        self.eventTimeoutCombo.setToolTip( "Display timer time-out")
        for elm in EVENT_TIMEOUTS: 
            self.eventTimeoutCombo.addItem( str( elm))
        self.eventTimeoutCombo.setCurrentIndex( 0)
        self.eventTimeoutCombo.activated.connect( self.cb_eventTimeoutCombo )
        hLayout = QHBoxLayout()
        hLayout.addWidget( QLabel( 'Event timeout [msec]'))
        hLayout.addWidget( self.eventTimeoutCombo)
        col = 1
        self.gridLayout.addLayout( hLayout, row, col)
        #
        # progress slider
        #
        self.pointsSlider = QSlider()
        self.pointsSlider.setToolTip( "Slide through the result arrays")
        self.pointsSlider.sliderMoved.connect( self.cb_pointsSlider)
        self.pointsSlider.setMinimum( 0)
        self.pointsSlider.setMaximum( 1000)
        self.pointsSlider.setOrientation( 1) # 1 horizontal, 2 vertical
        self.sliderLabel = QLabel( "Index")
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.sliderLabel)
        hLayout.addWidget( self.pointsSlider)
        row += 1
        col = 0
        self.gridLayout.addLayout( hLayout, row, 0, row, 3)
        #
        # log widget
        #
        self.logWidget = QTextEdit()
        self.logWidget.setMaximumHeight( 80)
        self.logWidget.setReadOnly( 1)
        hLayout = QHBoxLayout()
        hLayout.addWidget( self.logWidget)
        self.vLayout.addLayout( hLayout)

        return

    #
    # === the status bar
    #
    def prepareStatusBar( self): 
        self.statusBar = QStatusBar()
        self.setStatusBar( self.statusBar)
        #
        # StartValues
        #
        startValuesBtn = QPushButton("StartValues")
        startValuesBtn.clicked.connect( self.cb_startValues)       
        startValuesBtn.setToolTip( "Select start values")
        self.statusBar.addWidget( startValuesBtn)
        #
        # parameters
        #
        parBtn = QPushButton("Parameters")
        parBtn.clicked.connect( self.cb_params)       
        parBtn.setToolTip( "Change parameters")
        self.statusBar.addWidget( parBtn)
        #
        # axes on/off
        #
        axesOnOffCb = QCheckBox( "Axes", self)
        axesOnOffCb.clicked.connect( self.cb_axesOnOff)
        self.statusBar.addWidget( axesOnOffCb)

        #
        # reset
        #
        resetBtn = QPushButton("&Reset")
        resetBtn.setToolTip( "Reset the parameters")
        resetBtn.clicked.connect( self.cb_reset)       
        self.statusBar.addPermanentWidget( resetBtn)
        #
        # restart
        #
        restartBtn = QPushButton("&Restart")
        restartBtn.setToolTip( "Restart the plot")
        restartBtn.clicked.connect( self.restart)       
        self.statusBar.addPermanentWidget( restartBtn)
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
    def apply( self):
        # called from attratorParWidgets
        self.setHeaderText()
        self.calledFromApply = True
        self.restart()
        self.calledFromApply = False
        return
    
    def cb_close( self):
        plt.close()
        self.close()
        return

    def cb_reset( self):

        self.backgroundColor = 'lightyellow'
        self.ax.set_facecolor( self.backgroundColor)

        self.colorMap = 'gist_rainbow'
        self.maxPoints = 10000
        self.primitive = "Lines"
        self.markerSize = 0.5
        self.lineWidth = 0.5
        self.leadingMarkers = True
        self.maxTime = 100
        self.eRotString = '0'
        self.aRotString = '0'
        self.elev = 30
        self.azim = -60
        self.setElevSlider()
        self.setAzimSlider()

        self.setCurrentIndices()
        self.app.processEvents()
        
        self.restart()
        return

    def createImageFile( self, ext):
        plt.close()
        self.timer.stop()
        self.oneShot = True
        self.fig = None
        self.calledFromCreateImage = True
        self.prepareAttraction()
        self.calledFromCreateImage = False
        if not os.path.exists( './images'):
            os.mkdir( './images') 
        fName = "./images/%s_%s.%s" % ( self.attractor, self.var, ext)
        if os.path.exists( fName): 
            if os.path.exists( './vrsn'): 
                os.system( "./vrsn -s %s" % fName)
            else:
                self.logWidget.append( "%s exists, please rename." % fName)
                self.logWidget.append( "  or copy 'vrsn' to your PWD")
                return 
        plt.savefig(fName)
        self.logWidget.append( "created %s" % fName)
        plt.close( self.fig)
        self.fig = None
        self.restart()
        return
    
    def cb_png( self):
        self.createImageFile( 'png')
        return

    def cb_pdf( self):
        self.createImageFile( 'pdf')
        return
    
    def cb_test( self):
        print( "cb_test: ax.elev %g ax.azim %g " % (self.ax.elev, self.ax.azim))
        return

    def cb_varCombo( self, i):
        self.var = "Var%d" % (i + 1)
        self.setAttractorParameters( i)
        self.setViewingParameters()
        self.restart()
        return
    
    def setLimits( self, x = None, y = None, z = None):

        xMin = self.xMin*self.scale
        xMax = self.xMax*self.scale
        yMin = self.yMin*self.scale
        yMax = self.yMax*self.scale
        zMin = self.zMin*self.scale
        zMax = self.zMax*self.scale

        if zMin == zMax:
            zMin = -10.
            zMax = 10.
        try: 
            self.ax.axes.set_xlim3d( xMin, xMax)
            self.ax.axes.set_ylim3d( yMin, yMax)
            self.ax.axes.set_zlim3d( zMin, zMax)
        except Exception as e:
            self.logWidget.append( "setLimits: caucht exception: %s" % repr( e))
            self.ax.axes.set_xlim3d( -10., 10.)
            self.ax.axes.set_ylim3d( -10., 10.)
            self.ax.axes.set_zlim3d( -10., 10.)

        self.elev = self.ax.elev
        self.azim = self.ax.azim
        self.elevLabel.setText( "Elev: %6.2f" % self.elev)
        self.azimLabel.setText( "Azim: %6.2f" % self.azim)
        self.textLineDistViewLimits.set_text( "Start Values: x %g y %g z %g, Spread %g \
\nMaxPoints %d, MaxTime: %g,  NLines %d\
\nElev %7.2f, Azim %7.2f\
\nLimits: %.3g, %.3g, %.3g, %.3g, %.3g, %.3g" % 
                                              ( self.xStart, self.yStart, self.zStart, self.spread, 
                                                self.maxPoints, self.maxTime, self.nLines,
                                                self.elev, self.azim, 
                                                xMin, xMax, yMin, yMax, zMin, zMax))

        return
    
    def cb_nPtsCombo( self, i): 
        self.nPts = ( NPTS[ i])
        
        return

    def cb_eRotCombo( self, i):
        self.eRotString = ( EROTATES[ i])
        return

    def cb_aRotCombo( self, i):
        self.aRotString = ( EROTATES[ i])
        return

    def cb_scaleCombo( self, i):
        self.scale = SCALES[i]
        #self.restart()
        self.timeoutEvent()
        return

    def cb_aRotate( self, i):
        if i: 
            self.aRotFlag = True
        else: 
            self.aRotFlag = False
        return

    def cb_startValues( self):
        return
    
    def cb_startValues( self):
        self.oneShot = True
        self.maxTime = 20
        self.setCurrentIndices()
        self.oneShotCb.setChecked( True)
        self.restart()
        if self.startValuesWidget is not None:
            self.startValuesWidget.close()
        self.startValuesWidget = attractorHelperWidgets.startValuesWidget( self.app, parent = self)
        self.startValuesWidget.show()
        return 
    
    def cb_params( self):
        self.oneShot = True
        self.maxTime = 20
        self.setCurrentIndices()
        self.oneShotCb.setChecked( True)
        self.restart()
        if self.parameterWidget is not None:
            self.parameterWidget.close()
        self.parameterWidget = attractorHelperWidgets.parWidget( self.app, parent = self)
        self.parameterWidget.show()
        return 

    def handle3DWidgets( self):
        if self.is3D:
            self.elevSlider.show()
            self.elevLabel.show()
            self.azimSlider.show()
            self.azimLabel.show()
            self.eRotCombo.show()
            self.eRotLabel.show()
            self.aRotCombo.show()
            self.aRotLabel.show()
        else:
            self.elevSlider.hide()
            self.elevLabel.hide()
            self.azimSlider.hide()
            self.azimLabel.hide()
            self.eRotCombo.hide()
            self.eRotLabel.hide()
            self.aRotCombo.hide()
            self.aRotLabel.hide()
        return 
            
    def cb_attractorCombo( self, i):
        self.attractor = ATTRACTORS[i]
        if self.parameterWidget is not None:
            self.parameterWidget.close()
            self.parameterWidget = None
        self.cfgHsh = ATTRACTOR_DICT[ self.attractor]
        self.is3D = self.cfgHsh[ 'is3D']
        self.handle3DWidgets()
        self.varCombo.clear()

        for i in range( 1, 10):
            var = "Var%d" % i
            if var in self.cfgHsh:
                if 'PlotMode' in self.cfgHsh[ var]:
                    temp = "%s (%s)" % ( var, self.cfgHsh[ var][ 'PlotMode'])
                elif 'PlotMode' in self.cfgHsh:
                    temp = "%s (%s)" % ( var, self.cfgHsh[ 'PlotMode'])
                else:
                    temp = "%s (Classic)" % ( var)
                self.varCombo.addItem( temp)
        self.varCombo.setCurrentIndex( 0)
                    
        self.setAttractorParameters( 0)
        self.setViewingParameters()
        self.logWidget.append( "Attractor %s, %s " % (self.attractor, self.plotMode))
        self.restart()
        return 

    def cb_primitiveCombo( self, i):
        self.primitive = PRIMITIVES[i]
        for j in range( len(self.cfg)):
            if self.primitive == 'Lines': 
                self.line[j].set_linewidth( self.lineWidth)
                self.line[j].set_markersize( 0.)
            else: 
                self.line[j].set_marker( 'o')
                self.line[j].set_markersize( self.lineWidth)
                self.line[j].set_linewidth( 0)
         
        #self.restart()
        return 

    def cb_backgroundCombo( self, i):
        self.backgroundColor = utils.BACKGROUND_CMAPS[i]
        self.ax.set_facecolor( self.backgroundColor)
        return 
        
    def cb_paused( self, i):
        if i:
            self.timer.stop()
        else:
            self.timer.start( self.eventTimeout)
        return
    
    def cb_axesOnOff( self, i): 
        if i: 
            self.axesOnOff = True
            self.ax.set_axis_on()
        else: 
            self.axesOnOff = False
            self.ax.set_axis_off()
        return 
    
    def cb_plotModeCombo( self, i): 
        self.plotMode = PLOT_MODES[ i]
        self.setAttractorParameters()
        self.setViewingParameters( fixedPlotMode = True)
        self.restart()
        return 
    
    def cb_tailLengthCombo( self, i): 
        self.tailLength = TAIL_LENGTHS[ i]
        return 
    
    def cb_oneShot( self, i): 
        if i: 
            self.oneShot = True
        else: 
            self.oneShot = False
        self.setCurrentIndices()
        self.restart()
        return 
    
    def cb_cmapCombo( self, i):
        self.colorMap = utils.CMAPS[i]
        self.updateLines()
        return

    def cb_maxLinesCombo( self, i):
        self.nLines = NLINES[ i]
        self.restart()
        return

    def cb_maxPointsCombo( self, i):
        self.maxPoints = int( MAX_POINTS[ i])
        self.restart()
        return

    def setElevSlider( self):
        self.elevLabel.setText( "Elev %6.2f" % self.elev)
        self.elevSlider.setValue( int((self.elev + 90.)/180.*1000))
        return 

    def setAzimSlider( self): 
        self.azimLabel.setText( "Azim: %6.2f" % self.azim)
        self.azimSlider.setValue( int((self.azim + 180.)/360.*1000))
        return 
    
    def cb_elevSlider( self, i):
        self.elev = float(i)/1000.*180. - 90
        self.elevLabel.setText( "Elev: %6.2f" % self.elev)
        self.ax.view_init( elev = self.elev, azim = self.azim)
        self.timeoutEvent()
        return

    def cb_azimSlider( self, i):
        self.azim = float(i)/1000.*360. - 180
        self.azimLabel.setText( "Azim: %6.2f" % self.azim)
        self.ax.view_init( elev = self.elev, azim = self.azim)
        self.timeoutEvent()
        return

    def cb_maxTimesCombo( self, i):
        self.maxTime = int( MAX_TIMES[ i])
        self.restart()
        return

    def cb_lineWidthCombo( self, i):
        self.lineWidth = float( LINE_WIDTHS[ i])
        self.updateLines()
        return

    def cb_spreadCombo( self, i):
        self.spread = float( SPREADS[ i])
        self.restart()
        return

    def cb_markerSizeCombo( self, i):
        self.markerSize = float( MARKER_SIZES[ i])
        self.updateLines()
        return

    def cb_eventTimeoutCombo( self, i):
        self.eventTimeout = int( EVENT_TIMEOUTS[ i])
        self.timer.stop()
        self.timer.start( self.eventTimeout)
        self.updateLines()
        return
    
    def cb_pointsSlider( self):
        # i from 0 to 1000
        
        if self.sliderBusy:
            return

        self.sliderBusy = True
        
        self.timer.stop()
        self.pausedCb.setChecked( True)
        
        i = self.pointsSlider.value()
        self.sliderLabel.setText( "Progress: %d/%d" % (self.i, self.maxPoints))
        ii = int( float( i)/1000.*self.maxPoints)
        self.i = ii
        self.timeoutEvent()
        self.app.processEvents()
        #self.timer.start()
        self.sliderBusy = False
        return 
    
    def restart( self):
        self.i = 1
        self.pausedCb.setChecked( False)
        if self.fig is not None: 
            self.fig.clear()
        self.calledFromApply = True
        self.prepareAttraction()
        self.calledFromApply = False
        self.timer.start( self.eventTimeout)
        return 

    def findColorValue( self, i):
        cm = plt.get_cmap(self.colorMap) 
        cNorm  = colors.Normalize(vmin=0, vmax=self.nLines)
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
        colorValue = scalarMap.to_rgba(i)
        return colorValue
    
    def updateLines( self):
        for j in range( len(self.cfg)):
            colorValue = self.findColorValue( j)
            self.line[j].set_color( colorValue)
            self.line[j].set_linewidth( self.lineWidth)
            self.line[j].set_markersize( self.markerSize)
            if not self.oneShot and self.leadingMarkers: 
                self.leadingMarker[j].set_color( colorValue)
                self.leadingMarker[j].set_linewidth( self.lineWidth)

        return 

    def lengthVector( self, j, ii):
        temp = math.sqrt( (self.xValues[j][self.i + ii] - self.xValues[j][self.i - 1])**2 + \
                          (self.yValues[j][self.i + ii] - self.yValues[j][self.i - 1])**2 + \
                          (self.zValues[j][self.i + ii] - self.zValues[j][self.i - 1])**2 )
        return temp
        
    def setData( self, j):
        if j == 0:
            ii = int( self.nPts)
            if (self.i + ii) >=  (self.maxPoints - 1):
                ii = self.maxPoints - 1 - self.i
            self.i += ii
        # +++
        if self.plotMode == 'Classic':
            self.line[j].set_data_3d( self.xValues[j][:self.i], 
                                      self.yValues[j][:self.i],
                                      self.zValues[j][:self.i], )
        elif self.plotMode == 'Tails':
            if self.i > self.tailLength: 
                self.line[j].set_data_3d( self.xValues[j][(self.i-self.tailLength):self.i], 
                                          self.yValues[j][(self.i-self.tailLength):self.i],
                                          self.zValues[j][(self.i-self.tailLength):self.i], )
            else: 
                self.line[j].set_data_3d( self.xValues[j][:self.i], 
                                          self.yValues[j][:self.i],
                                          self.zValues[j][:self.i], )

        if self.leadingMarkers: 
            self.leadingMarker[j].set_data_3d( [self.xValues[j][self.i]], 
                                               [self.yValues[j][self.i]], 
                                               [self.zValues[j][self.i]]) 

        self.setLimits() 
        return

    def timeoutEvent(self):

        self.timeoutCount += 1
        
        if self.timerBusy:
            self.logWidget.append( "timeoutEvent %d: timer busy i = %s" % 
                                   (self.timeoutCount, self.i))
            return 
        
        self.timerBusy = True
        #
        # rotate the plot, even if it has fully been displayed
        #
        if self.eRotString != '0' or self.aRotString != '0':
            deltaERot = float( self.eRotString) 
            deltaARot = float( self.aRotString)
            self.elev += deltaERot
            self.azim += deltaARot
            self.setElevSlider() 
            self.setAzimSlider() 
            self.ax.view_init( elev = self.elev, azim = self.azim) 
        
        self.i += 1
        if self.i >= ( self.maxPoints - 1): 
            self.setLimits()
            self.timerBusy = False
            return 

        if self.oneShot:
            self.timerBusy = False
            return
        
        if (self.i % 10) == 0:
            self.pointsSlider.setValue( int( float( self.i)/self.maxPoints*1000))
            self.sliderLabel.setText( "Progress: %d/%d" % (self.i, self.maxPoints))

        for j in range( len(self.line)):
            self.setData( j)

        self.timerBusy = False

        return 

    def setCurrentIndices( self): 
        #
        if self.maxPointsCombo is None:
            return
        self.backgroundCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.backgroundColor, utils.BACKGROUND_CMAPS))
        self.cmapCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.colorMap, utils.CMAPS))

        self.maxPointsCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.maxPoints, MAX_POINTS))
        self.maxTimesCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.maxTime, MAX_TIMES))
 
        self.nLinesCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.nLines, NLINES))
        self.primitiveCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.primitive, PRIMITIVES))

        self.lineWidthCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.lineWidth, LINE_WIDTHS))
        self.markerSizeCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.markerSize, MARKER_SIZES))

        self.nPtsCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.nPts, NPTS))
        self.spreadCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.spread, SPREADS))

        self.aRotCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.aRotString, EROTATES))
        self.eRotCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.eRotString, EROTATES))

        self.scaleCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.scale, SCALES))

        self.tailLengthCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.tailLength, TAIL_LENGTHS))

        self.plotModeCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.plotMode, PLOT_MODES))

        if self.oneShot:
            self.oneShotCb.setChecked( True)
        else: 
            self.oneShotCb.setChecked( False)

        self.eventTimeoutCombo.setCurrentIndex( 
            utils.findCurrentIndex( self.eventTimeout, EVENT_TIMEOUTS))
 
        return 

    def setAttractorParameters( self, i = None):
        #
        # execute before all widgets have been created
        #
        if i is not None:
            mod = "Var%d" % (int( i) + 1)
            self.var = mod
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.p4 = None
        self.p5 = None
        self.p6 = None
        if self.var in self.cfgHsh:
            if 'P1' in self.cfgHsh[ self.var]:
                self.p1 = self.cfgHsh[ self.var][ 'P1']
            if 'P2' in self.cfgHsh[ self.var]:
                self.p2 = self.cfgHsh[ self.var][ 'P2']
            if 'P3' in self.cfgHsh[ self.var]:
                self.p3 = self.cfgHsh[ self.var][ 'P3']
            if 'P4' in self.cfgHsh[ self.var]:
                self.p4 = self.cfgHsh[ self.var][ 'P4']
            if 'P5' in self.cfgHsh[ self.var]:
                self.p5 = self.cfgHsh[ self.var][ 'P5']
            if 'P6' in self.cfgHsh[ self.var]:
                self.p6 = self.cfgHsh[ self.var][ 'P6']
        else:
            self.logWidget.append( " %s not in dictionary" % mod)

        self.xStart = None
        self.yStart = None
        self.zStart = None
        if 'XSTART' in self.cfgHsh[ self.var]:
            self.xStart = self.cfgHsh[ self.var][ 'XSTART']
        elif 'XSTART' in self.cfgHsh:
            self.xStart = self.cfgHsh[ 'XSTART']
        if 'YSTART' in self.cfgHsh[ self.var]:
            self.yStart = self.cfgHsh[ self.var][ 'YSTART']
        elif 'YSTART' in self.cfgHsh:
            self.yStart = self.cfgHsh[ 'YSTART']
        if 'ZSTART' in self.cfgHsh[ self.var]:
            self.zStart = self.cfgHsh[ self.var][ 'ZSTART']
        elif 'ZSTART' in self.cfgHsh:
            self.zStart = self.cfgHsh[ 'ZSTART']
        return 

    def setViewingParameters( self, fixedPlotMode = False):
        #
        # execute after all widgets have been created
        #
        if self.timer is not None: 
            self.timer.stop()

        if self.ax is not None: 
            self.backgroundColor = 'lightyellow'
            if 'BackgroundColor' in self.cfgHsh[ self.var]:
                self.backgroundColor = self.cfgHsh[ self.var][ 'BackgroundColor']
            elif 'BackgroundColor' in self.cfgHsh:
                self.backgroundColor = self.cfgHsh[ 'BackgroundColor']
            self.ax.set_facecolor( self.backgroundColor)

        self.colorMap = 'gist_rainbow'
        if 'ColorMap' in self.cfgHsh[ self.var]:
            self.colorMap = self.cfgHsh[ self.var][ 'ColorMap']
        elif 'ColorMap' in self.cfgHsh:
            self.colorMap = self.cfgHsh[ 'ColorMap']
            
        self.maxPoints = 10000
        if 'MaxPoints' in self.cfgHsh[ self.var]:
            self.maxPoints = self.cfgHsh[ self.var][ 'MaxPoints']
        elif 'MaxPoints' in self.cfgHsh:
            self.maxPoints = self.cfgHsh[ 'MaxPoints']
            
            
        #self.plotMode = 'Classic'
        if not fixedPlotMode: 
            if 'PlotMode' in self.cfgHsh[ self.var]:
                self.plotMode = self.cfgHsh[ self.var][ 'PlotMode']
            elif 'PlotMode' in self.cfgHsh:
                self.plotMode = self.cfgHsh[ 'PlotMode']

        if self.plotMode == 'Classic': 
            self.maxTime = 100
        else: 
            self.maxTime = 20
            
        if 'MaxTime' in self.cfgHsh[ self.var]:
            self.maxTime = self.cfgHsh[ self.var][ 'MaxTime']
        elif 'MaxTime' in self.cfgHsh:
            self.maxTime = self.cfgHsh[ 'MaxTime']
            
        self.nLines = 10
        if 'NLines' in self.cfgHsh[ self.var]:
            self.nLines = self.cfgHsh[ self.var][ 'NLines']
        elif 'NLines' in self.cfgHsh:
            self.nLines = self.cfgHsh[ 'NLines']

        self.primitive = "Lines"
        if 'Primitive' in self.cfgHsh[ self.var]:
            self.primitive = self.cfgHsh[ self.var][ 'Primitive']
        elif 'Primitive' in self.cfgHsh:
            self.primitive = self.cfgHsh[ 'Primitive']
            
        self.lineWidth = 0.5
        if 'LineWidth' in self.cfgHsh[ self.var]:
            self.lineWidth = self.cfgHsh[ self.var][ 'LineWidth'] 
        elif 'LineWidth' in self.cfgHsh:
            self.lineWidth = self.cfgHsh[ 'LineWidth'] 

        self.markerSize = 0.5
        if 'MarkerSize' in self.cfgHsh[ self.var]:
            self.markerSize = self.cfgHsh[ self.var][ 'MarkerSize']
        elif 'MarkerSize' in self.cfgHsh:
            self.markerSize = self.cfgHsh[ 'MarkerSize']

        self.nPts = 1
        if 'NPts' in self.cfgHsh[ self.var]:
            self.nPts = self.cfgHsh[ self.var][ 'NPts']
        elif 'NPts' in self.cfgHsh:
            self.nPts = self.cfgHsh[ 'NPts']

        self.spread = 0.1
        if 'Spread' in self.cfgHsh[ self.var]:
            self.spread = self.cfgHsh[ self.var][ 'Spread']
        elif 'Spread' in self.cfgHsh:
            self.spread = self.cfgHsh[ 'Spread']
            
        if self.ax is not None: 
            self.elev = 30
            if 'Elev' in self.cfgHsh[ self.var]:
                self.elev = self.cfgHsh[ self.var][ 'Elev']
                self.ax.view_init( elev = self.elev, azim = self.azim) 
                self.setElevSlider()
            elif 'Elev' in self.cfgHsh:
                self.elev = self.cfgHsh[ 'Elev']
                self.ax.view_init( elev = self.elev, azim = self.azim) 
                self.setElevSlider()

            self.azim = -60
            if 'Azim' in self.cfgHsh[ self.var]:
                self.azim = self.cfgHsh[ self.var][ 'Azim']
                self.ax.view_init( elev = self.elev, azim = self.azim) 
                self.setAzimSlider()
            elif 'Azim' in self.cfgHsh:
                self.azim = self.cfgHsh[ 'Azim']
                self.ax.view_init( elev = self.elev, azim = self.azim) 
                self.setAzimSlider()
            
        self.eRotString = '0'
        if 'ERotString' in self.cfgHsh[ self.var]:
            self.eRotString = self.cfgHsh[ self.var][ 'ERotString']
        elif 'ERotString' in self.cfgHsh:
            self.eRotString = self.cfgHsh[ 'ERotString']
            
        self.aRotString = '0'
        if 'ARotString' in self.cfgHsh[ self.var]:
            self.aRotString = self.cfgHsh[ self.var][ 'ARotString']
        elif 'ARotString' in self.cfgHsh:
            self.aRotString = self.cfgHsh[ 'ARotString']
            
        self.scale = 0.9
        if 'Scale' in self.cfgHsh[ self.var]:
            self.scale = self.cfgHsh[ self.var][ 'Scale']
        elif 'Scale' in self.cfgHsh:
            self.scale = self.cfgHsh[ 'Scale']
            
        self.oneShotOn = False
        if 'OneShot' in self.cfgHsh[ self.var]:
            self.oneShot = self.cfgHsh[ self.var][ 'OneShot']
        elif 'OneShot' in self.cfgHsh:
            self.oneShot = self.cfgHsh[ 'OneShot']
            
        self.tailLength = 100
        if 'TailLength' in self.cfgHsh[ self.var]:
            self.tailLength = self.cfgHsh[ self.var][ 'TailLength']
        elif 'TailLength' in self.cfgHsh:
            self.tailLength = self.cfgHsh[ 'TailLength']
            
        self.leadingMarkers = True
        if 'LeadingMarkers' in self.cfgHsh[ self.var]:
            self.leadingMarkers = self.cfgHsh[ self.var][ 'LeadingMarkers']
        elif 'LeadingMarkers' in self.cfgHsh:
            self.leadingMarkers = self.cfgHsh[ 'LeadingMarkers']
            
        self.eventTimeout = 10
        if 'EventTimeout' in self.cfgHsh[ self.var]:
            self.eventTimeout = self.cfgHsh[ self.var][ 'EventTimeout']
        elif 'EventTimeout' in self.cfgHsh:
            self.eventTimeout = self.cfgHsh[ 'EventTimeout']
        
        # this happends in __init__() after the combo boxes have been created
        # and also here...
        self.setCurrentIndices()

        if self.timer is not None: 
            self.timer.start( self.eventTimeout)
        
        return
    
    def createHeaderText( self):


        self.textHeader = plt.gcf().text(0.01, 0.99, "n.n.", 
                                         color = ( 0.3, 0.3, 0.3), fontname = 'monospace', size = 10,
                                         horizontalalignment='left', verticalalignment='top', 
                                         bbox=dict( fill=True, facecolor=( 0.7, 0.7, 0.7),
                                                    edgecolor=( 0.9, 0.9, 0.9), linewidth=1))
        
        self.textLineDistViewLimits = plt.gcf().text(0.01, 0.01,
                                             "n.n.",
                                             color = ( 0.3, 0.3, 0.3), fontname = 'monospace', size = 10,
                                             horizontalalignment='left', verticalalignment='bottom', 
                                             bbox=dict( fill=True, facecolor=( 0.7, 0.7, 0.7),
                                                        edgecolor=( 0.9, 0.9, 0.9), linewidth=1))
        self.setHeaderText()
        return

    def setHeaderText( self):

        if self.attractor == 'Aizawa': 
            self.textHeader.set_text(  "Aizawa/%s ( a %g, b %g, c %g, c %g, d %g, e %g):\
\ndx/dt = (z-b)*x - d*y\
\ndy/dt = d*x + (z-b)*y\
\ndz/dt = c + a*z - z**3/3 - (x**2 + y**2)(1+e*z) + f*z*x**3" % 
                                       ( self.var, self.p1, self.p2, self.p3, self.p4, self.p5, self.p6))
            
        elif self.attractor == 'Arneodo': 
            self.textHeader.set_text( "Arneodo/%s ( a %g, b %g, c %g):\
\ndx/dt = y\
\ndy/dt = z\
\ndz/dt = -a*x - b*y + c*x**3" % ( self.var, self.p1, self.p2, self.p3)) 

        elif self.attractor == 'BoualiTyp3': 
            self.textHeader.set_text( "BoualiTyp3/%s ( a %g, b %g, c %g, d %g) \
\ndx/dt = ax(1 - y) - bz\
\ndy/dt = -cy(1 - x**2)\
\ndz/dt = cx" % ( self.var, self.p1, self.p2, self.p3, self.p4)) 

        elif self.attractor == 'BurgersMap': 
            self.textHeader.set_text( "BurgersMap/%s ( a %g, b %g):\
\n$x_{n+1}$ = (1 - a)*$x_n$ - $y_n^2$\
\n$y_{n+1}$ = (1 + b)*$y_n$ - $x_n$*$y_n$" % ( self.var, self.p1, self.p2)) 

        elif self.attractor == 'Cathala': 
            self.textHeader.set_text( "Cathala/%s ( a %g, b %g):\
\n$x_{n+1}$ = a$x_n$ + $y_n$\
\n$y_{n+1}$ = b + $x_n^2$" % ( self.var, self.p1, self.p2))
                    
        elif self.attractor == 'ChenLee': 
            self.textHeader.set_text( "ChenLee/%s ( a %g, b %g, c %g):\
\ndx/dt = a*x - y*z\
\ndy/dt = b*y + x*z\
\ndz/dt = c*z + x*y/3" % ( self.var, self.p1, self.p2, self.p3))

        elif self.attractor == 'Clifford': 
            self.textHeader.set_text( "Clifford/%s ( a %g, b %g, c %g, c %g) \
\n$x_{n+1}$ = sin( a*$y_n$) + c*cos( a*$x_n$)\
\n$y_{n+1}$ = sin( b*$x_n$) + c*cos( b*$y_n$)" % ( self.var, self.p1, self.p2, self.p3, self.p4)) 

        elif self.attractor == 'CoupledLogisticMap': 
            self.textHeader.set_text( "CoupledLogisticMap/%s ( a %g, b %g):\
\n$x_{n+1}$ = (1-a)b$x_n$(1-$x_n$) + ab$y_n$(1-$y_n$)\
\n$y_{n+1}n$ = (1-a)b$y_n$(1-$y_n$) + ab$x_n$(1-$x_n$)" % ( self.var, self.p1, self.p2))

        elif self.attractor == 'Dadras': 
            self.textHeader.set_text( "Dadras/%s ( a %g, b %g, c %g, c %g, d %g) \
\ndx/dt = y - a*x + b*y*z\
\ndy/dt = c*y - x*z + z\
\ndz/dt = d*x*y - e*z" % ( self.var, self.p1, self.p2, self.p3, self.p4, self.p5)) 

        elif self.attractor == 'FourWing': 
            self.textHeader.set_text( "FourWing/%s ( a %g, b %g, c %g):\
\ndx/dt = a*x + y*z\
\ndy/dt = b*x + c*y -x*z\
\ndz/dt = -z - x*y" % ( self.var, self.p1, self.p2, self.p3)) 

        elif self.attractor == 'GumowskiMira': 
            self.textHeader.set_text( "GumowskiMira/%s ( a %g, b %g):\
\nf(x) = bx+2(1-b)$x^2$/(1+$x^2$)\
\n$x_{n+1}$ = $y_n$ + a(1-0.05$y_n^2$) + f($x_n$)\
\n$y_{n+1}$ = -$x_n$ + f($x_{n+1}$)" % ( self.var, self.p1, self.p2))

        elif self.attractor == 'Halvorsen': 
            self.textHeader.set_text( "Halvorsen/%s ( a %g):\
\ndx/dt = -a*x - 4*y - 4*z - y**2\
\ndy/dt = -a*y -4*z -4*x -z**2\
\ndz/dt = -a*z - 4*x - 4*y - x**2" % ( self.var, self.p1)) 

        elif self.attractor == 'Hopalong': 
            self.textHeader.set_text( "Hopalong/%s ( a %g, b %g, c %g):\
\n$x_{n+1}$= $y_n$-sign($x_n$)sqrt(abs(b$x_n$-c))\
\n$y_{n+1}$ = a - $x_n$" % ( self.var, self.p1, self.p2, self.p3)) 
                
        elif self.attractor == 'Ikeda': 
            self.textHeader.set_text( "Ikeda/%s ( a %g, b %g): \
\n t = a-6/(1+$x_n^2$+$y_n^2$) \
\n $x_{n+1}$ = 1+b*($x_n$*cos(t)-$y_n$*sin(t))\
\n $y_{n+1}$ = b*($x_n$*cos(t)-$y_n$*sin(t))" %  ( self.var, self.p1, self.p2)) 

        elif self.attractor == 'Lorenz': 
            self.textHeader.set_text(  "Lorenz/%s ( a %g, b %g, c %g)\
\ndx/dt = a(y-x)\
\ndy/dt = bx-y-xz\
\ndz/dt = xy-cz" % ( self.var, self.p1, self.p2, self.p3)) 
                                                   
        elif self.attractor == 'MultifoldHenon': 
            self.textHeader.set_text( "MultifoldHenon/%s ( a %g, b %g):\
\n$x_{n+1}$ = 1 - asin($x_n$)+b$y_n$\
\n$y_{n+1}$ = $x_n$" % ( self.var, self.p1, self.p2))

        elif self.attractor == 'NoseHoover': 
            self.textHeader.set_text( "NoseHoover/%s ( a %g):\
\ndx/dt = y\
\ndy/dt = -x + y*z\
\ndz/dt = a - y*y" % ( self.var, self.p1)) 

        elif self.attractor == 'PeterDeJong': 
            self.textHeader.set_text( "PeterDeJong/%s ( a %g, b %g, c %g, d %g) \
\n$x_{n+1}$ = sin(a$y_n$) - cos(b$x_n$)\
\n$y_{n+1}$ = sin(c$x_n$) - cos(c$y_n$)" % ( self.var, self.p1, self.p2, self.p3, self.p4)) 

        elif self.attractor == 'Pickover': 
            self.textHeader.set_text( "Pickover/%s ( a %g, b %g, c %g, c %g) \
\n$x_{n+1}$ = sin( a*$y_n$) - cos( b*$x_n$)\
\n$y_{n+1}$ = sin( c*$x_n$) - cos( c*$y_n$)" % ( self.var, self.p1, self.p2, self.p3, self.p4)) 

        elif self.attractor == 'PolynomA': 
            self.textHeader.set_text( "PolynomA/%s ( a %g, b %g, c %g):\
\n$x_{n+1}$ = a+$y_n$-$y_n$$z_n$\
\n$y_{n+1}$ = b+$z_n$-$x_n$$z_n$\
\n$z_{n+1}$ = c+$x_n$-$x_ny_n$" % ( self.var, self.p1, self.p2, self.p3))
            
        elif self.attractor == 'RabinovichFabrikant': 
            self.textHeader.set_text( "RabinovichFabrikant/%s ( a %g, b %g):\
\ndx/dt = y(z - 1 + x**2) + bx\
\ndy/dt = x(3z + 1 - x**2) + by\
\ndz/dt = -2x( a + xy)" % ( self.var, self.p1, self.p2))
                
        elif self.attractor == 'Roessler': 
            self.textHeader.set_text( "Roessler/%s ( a %g, b %g, c %g):\
\ndx/dt = -y - z\
\ndy/dt = x + a*y\
\ndz/dt = b + z*(x-c)" % ( self.var, self.p1, self.p2, self.p3)) 

        elif self.attractor == 'Sakarya': 
            self.textHeader.set_text( "Sakarya/%s ( a %g, b %g):\
\ndx/dt = -x + y + y*z\
\ndy/dt = -x - y + a*x*z\
\ndz/dt = z - b*x*y" % ( self.var, self.p1, self.p2))

        elif self.attractor == 'SineMap': 
            self.textHeader.set_text( "SineMap/%s ( a %g, b %g):\
\n$x_{n+1}$ = $y_n$\
\n$y_{n+1}$ = asin( $x_n$) + b$y_n$" % ( self.var, self.p1, self.p2))

        elif self.attractor == 'Svensson': 
            self.textHeader.set_text( "Svensson/%s ( a %g, b %g, c %g, c %g) \
\n$x_{n+1}$ = c*sin( a*$x_n$) - sin( b*$y_n$)\
\n$y_{n+1}$ = c*cos( a*$x_n$) + cos( b*$y_n$)" % ( self.var, self.p1, self.p2, self.p3, self.p4)) 

        elif self.attractor == 'SprottLinzF': 
            self.textHeader.set_text( "Sprottlinzf/%s ( a %g):\
\ndx/dt = y + z\
\ndy/dt = -x + a*y\
\ndz/dt = x**2 - z" % ( self.var, self.p1)) 

        elif self.attractor == 'Thomas': 
            self.textHeader.set_text( "Thomas/%s ( a %g):\
\ndx/dt = sin(y) - a*x\
\ndy/dt = sin(z) - a*y\
\ndz/dt = sin(x) - a*z" % ( self.var, self.p1)) 

        elif self.attractor == 'Tinkerbell': 
            self.textHeader.set_text( "Tinkerbell/%s ( a %g, b %g, c %g, c %g) \
\n$x_{n+1}$ = $x_n^2$-$y_n^2$+a$x_n$+b$y_n$\
\n$y_{n+1}$ = 2$x_n$$y_n$+c$x_n$+d$y_n$" % ( self.var, self.p1, self.p2, self.p3, self.p4)) 

        elif self.attractor == 'TSUCS1': 
            self.textHeader.set_text( "TSUCS1/%s ( a %g, b %g, c %g, c %g, d %g) \
\ndx/dt = a*(y-x) + c*x*z\
\ndy/dt = e*y - x*z\
\ndz/dt = b*z + x*y - c*x**2" % ( self.var, self.p1, self.p2, self.p3, self.p4, self.p5))

        elif self.attractor == 'Ushiki': 
            self.textHeader.set_text( "Ushiki/%s ( a %g, b %g, c %g, c %g) \
\n$x_{n+1}$ = (a-$x_n$-b$y_n$)$x_n$\
\n$y_{n+1}$ = (c-$y_n$-c$x_n$)$y_n$" % ( self.var, self.p1, self.p2, self.p3, self.p4)) 

        return
    
    def prepareAttraction( self):
        # +++
        plt.ion() 

        cm = 1/2.54  # centimeters in inches
        if self.fig is None:
            if self.geoWidth > 1920:
                self.fig = plt.figure( figsize=( 48*cm, 48*cm), facecolor="black")
            else:
                self.fig = plt.figure( figsize=( 24*cm, 24*cm), facecolor="black")
        self.fig.canvas.manager.set_window_title( self.attractor)
        self.ax = self.fig.add_subplot(projection='3d')
        self.ax.view_init( elev = self.elev, azim = self.azim) 
        self.ax.set_facecolor( self.backgroundColor)
        self.ax.set_xlabel( "x-Axis") 
        self.ax.set_ylabel( "y-Axis") 
        self.ax.set_zlabel( "z-Axis")

        if self.axesOnOff: 
            self.ax.set_axis_on()
        else: 
            self.ax.set_axis_off()

        plt.subplots_adjust(bottom=0.0, left=0.0, right=1.0, top=1.0)

        # 
        # set P1, P2, etc.
        # 
        if not self.calledFromApply and not self.calledFromCreateImage: 
            self.setAttractorParameters( 0)

        self.createHeaderText()

        self.cfg = []
        delta = 2.*self.spread/self.nLines
        for i in range( self.nLines):
            colorVal = self.findColorValue( i)
            dIx = -self.spread + delta*i
            dIy = -self.spread + delta*i
            dIz = -self.spread + delta*i
            self.cfg.append( { 'color': colorVal, 
                               'xyzs': [ self.xStart + dIx, self.yStart + dIy, self.zStart + dIz]})
        self.line = []
        self.xValues = []
        self.yValues = []
        self.zValues = []
        self.leadingMarker = []
        self.xMin = 100
        self.xMax = -100
        self.yMin = 100
        self.yMax = -100
        self.zMin = 100
        self.zMax = -100
        for j in range( len( self.cfg)):

            #
            # produce a SIGALRM after 1s.
            #
            signal.alarm(3)
            try:
                x, y, z = getattr( self, self.attractor)( *self.cfg[j][ 'xyzs'])
            except TMO as e:
                self.logWidget.append( "prepareAttraction: tmo detected, returning") 
                return             
            signal.alarm(0)
            
            if np.min( x) < self.xMin:
                self.xMin = np.min( x)
            if np.max( x) > self.xMax:
                self.xMax = np.max( x)
            if np.min( y) < self.yMin:
                self.yMin = np.min( y)
            if np.max( y) > self.yMax:
                self.yMax = np.max( y)
            if np.min( z) < self.zMin:
                self.zMin = np.min( z)
            if np.max( z) > self.zMax:
                self.zMax = np.max( z)
            
            if not self.oneShot and self.leadingMarkers: 
                ptTemp, = self.ax.plot( x[0], y[0], z[0],'o',
                                        markersize = 5, 
                                        c=self.cfg[j][ 'color'])
                self.leadingMarker.append( ptTemp)

            clr = self.cfg[j]['color']
            if self.primitive == 'Lines':
                if self.oneShot:
                    lnTemp, = self.ax.plot( x, y, z,
                                            c=clr, linewidth=self.lineWidth)
                else:
                    lnTemp, = self.ax.plot([], [], [],
                                           c=clr, linewidth=self.lineWidth)
            elif self.primitive == 'Markers':
                if self.oneShot: 
                    lnTemp, = self.ax.plot( x, y, z, 'o',
                                            markersize=self.markerSize, c=clr)
                else: 
                    lnTemp, = self.ax.plot([], [], [], 'o',
                                           markersize=self.markerSize, c=clr)
            self.line.append( lnTemp)
            self.xValues.append( x)
            self.yValues.append( y)
            self.zValues.append( z)

        self.maxPoints = len(x)
        self.setLimits()
        
        #self.fig.canvas.draw()
        #self.fig.canvas.flush_events()
        plt.show()

        # +++
        if self.plotMode == 'MovingMarkers': 
            step = int( len( self.cfg)/5.)
            for j in range( 0, len( self.cfg), step):
                self.line[j].set_data_3d( self.xValues[j],
                                          self.yValues[j],
                                          self.zValues[j])

        #self.app.processEvents()
        return 

    def cb_helpLorenz(self):
        QMessageBox.about(self, self.tr("Help Lorenz"), self.tr(
                "<h3> The Lorenz System</h3>"
                "<ul>"
            "From Wikipedia.org"
                "<li> The Lorenz system is a set of three ordinary differential equations, first developed by the meteorologist Edward Lorenz while studying atmospheric convection. It is a classic example of a system that can exhibit chaotic behavior, meaning its output can be highly sensitive to small changes in its starting conditions. </li>"
            "<li>For certain values of its parameters, the system's solutions form a complex, looping pattern known as the Lorenz attractor. The shape of this attractor, when graphed, is famously said to resemble a butterfly. The system's extreme sensitivity to initial conditions gave rise to the popular concept of the butterfly effect—the idea that a small event, like the flap of a butterfly's wings, could ultimately alter large-scale weather patterns. While the system is deterministic—its future behavior is fully determined by its initial conditions—its chaotic nature makes long-term prediction practically impossible. </li>"
                "</ul>" 
                ))

    def cb_helpPeterDeJong(self):
        QMessageBox.about(self, self.tr("Help Peter de Jong"), self.tr(
        "<h3> The Peter de Jong attractor</h3>"
            "<ul>"
            "<li>This attractor was first published 1987 in Scientific American in an article by A. K. Dewdney as a reader submission</li>"
            "<li>There is a nice documentation by Paul Bourke: https://paulbourke.net/fractals/peterdejong/</li>"
            "</ul>" 
                ))
    def cb_helpClifford(self):
        QMessageBox.about(self, self.tr("Help Clifford"), self.tr(
        "<h3> The Clifford attractor</h3>"
            "<ul>"
            "<li>Attributed to Cliff Pickover</li>"
            "<li>There is a nice documentation by Paul Bourke: https://paulbourke.net/fractals/clifford/</li>"
            "</ul>" 
                ))
    
    def LorenzFunc( self, t, X, r, s, b):
        x, y, z = X
        x_dot =s*(y - x)
        y_dot = r*x - y - x*z
        z_dot = x*y - b*z
        return x_dot, y_dot, z_dot
    
    def Lorenz( self, xs, ys, zs, r=28, s=10,  b=2.667 ):

        r = self.p1
        s = self.p2
        b = self.p3

        soln =solve_ivp( self.LorenzFunc,
                         (0, self.maxTime),
                         (xs, ys, zs),
                         args=(r, s, b),
                         dense_output=True)
            
        arryTime=np.linspace(0, self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z
    
    def RabinovichFabrikantFunc( self, t, X, alpha, gamma):
        x, y, z = X
        x_dot = y*(z - 1 + x**2) + gamma*x
        y_dot = x*(3*z + 1 - x**2) + gamma*y
        z_dot = -2*z*( alpha + x*y)
        return x_dot, y_dot, z_dot
    
    def RabinovichFabrikant( self, xs, ys, zs, alpha = 0.14, gamma = 0.1 ):

        alpha = self.p1
        gamma = self.p2
        
        soln =solve_ivp( self.RabinovichFabrikantFunc, 
                         (0, self.maxTime),(xs, ys, zs),  args=( alpha, gamma), dense_output=True)

        arryTime=np.linspace(0, self.maxTime, self.maxPoints)

        #print(soln.sol( arryTime).shape)         

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def SakaryaFunc( self, t, X, a, b):
        x, y, z = X
        x_dot = -x + y + y*z
        y_dot = -x - y + a*x*z
        z_dot = z - b*x*y
        return x_dot, y_dot, z_dot
    
    def Sakarya( self, xs, ys, zs, a = 0.4, b = 0.3 ):

        a = self.p1
        b = self.p2
        
        soln =solve_ivp( self.SakaryaFunc, 
                         (0, self.maxTime),(xs, ys, zs),  args=( a, b), dense_output=True)

        arryTime=np.linspace(0, self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def RoesslerFunc( self, t, X, a, b, c):
        x, y, z = X
        x_dot = -y -z
        y_dot = x + a*y
        z_dot = b + z*(x-c)
        return x_dot, y_dot, z_dot
    
    def Roessler( self, xs, ys, zs, a = 0.2, b = 0.2, c = 5.7 ):

        a = self.p1
        b = self.p2
        c = self.p3
        
        soln =solve_ivp( self.RoesslerFunc, (0, self.maxTime),(xs, ys, zs),  args=( a, b, c), dense_output=True)

        arryTime=np.linspace(0, self.maxTime, self.maxPoints)

        #print(soln.sol( arryTime).shape)         

        x,y,z=soln.sol( arryTime)
        return x, y, z
        

    def AizawaFunc( self, t, X, a, b, c, d, e, f):
        x, y, z = X                           
        x_dot = (z - b)*x - d*y
        y_dot = d*x + (z-b)*y
        z_dot = c + a*z - z**3/3. - (x**2 + y**2)*(1.+e*z) + f*z*x**3
        return x_dot, y_dot, z_dot

    def Aizawa( self, xs, ys, zs, a=0.95, b=0.7, c=0.6, d=3.5, e=0.25, f=0.1):
        a = self.p1
        b = self.p2
        c = self.p3
        d = self.p4
        e = self.p5
        f = self.p6

        soln =solve_ivp( self.AizawaFunc, (0, self.maxTime),(xs, ys, zs),  args=(a, b, c, d, e, f), dense_output=True)

        arryTime=np.linspace( 0, self.maxTime, self.maxPoints)

        #print(soln.sol( arryTime).shape)         

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def ArneodoFunc( self, t, X, a, b, d):
        x, y, z = X                           
        x_dot = y
        y_dot = z
        z_dot = -a*x - b*y -z + d*x**3
        return x_dot, y_dot, z_dot

    def Arneodo( self, xs, ys, zs, a = -5.5, b = 3.5, d = -1):

        a = self.p1
        b = self.p2
        c = self.p3
        
        soln =solve_ivp( self.ArneodoFunc, ( 0, self.maxTime),(xs, ys, zs),  args=(a, b, d), dense_output=True)

        arryTime=np.linspace(0,self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def DadrasFunc( self, t, X, p, o, r, c, e):
        x, y, z = X                           
        x_dot = y - p*x + o*y*z
        y_dot = r*y - x*z + z
        z_dot = c*x*y - e*z
        return x_dot, y_dot, z_dot

    def Dadras( self, xs, ys, zs, p = 3, o = 2.7, r = 1.7, c = 2, e = 9):

        p = self.p1
        o = self.p2
        r = self.p3
        c = self.p4
        e = self.p5
        
        soln =solve_ivp( self.DadrasFunc, ( 0, self.maxTime),(xs, ys, zs),  args=( p, o, r, c, e), dense_output=True)

        arryTime=np.linspace( 0, self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def TSUCS1Func( self, t, X, a, c, d, e, f):
        x, y, z = X                           
        x_dot = a*(y-x) + d*x*z
        y_dot = f*y - x*z
        z_dot = c*z + x*y - e*x*x
        return x_dot, y_dot, z_dot

    def TSUCS1( self, xs, ys, zs, a = 40, c = 0.833, d = 0.5, e = 0.65, f = 20.):

        a = self.p1
        c = self.p2
        d = self.p3
        e = self.p4
        f = self.p5

        soln =solve_ivp( self.TSUCS1Func, ( 0, self.maxTime),(xs, ys, zs),  args=( a, c, d, e, f), dense_output=True)

        arryTime=np.linspace( 0, self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def FourWingFunc( self, t, X, a, b, c):
        x, y, z = X                           
        x_dot = a*x + y*z
        y_dot = b*x + c*y - x*z
        z_dot = -z - x*y
        return x_dot, y_dot, z_dot

    def FourWing( self, xs, ys, zs, a = 0.2, b = 0.01, c = -0.4):

        a = self.p1
        b = self.p2
        c = self.p3
        soln =solve_ivp( self.FourWingFunc, 
                         ( 0, self.maxTime),(xs, ys, zs),  args=( a, b, c), dense_output=True)

        arryTime=np.linspace( 0, self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z
    

    def BoualiTyp3Func( self, t, X, a, b, c, d):
        x, y, z = X                           
        x_dot = a*x*(1-y) - b*z
        y_dot = -c*y*(1 - x*x)
        z_dot = d*x
        return x_dot, y_dot, z_dot

    def BoualiTyp3( self, xs, ys, zs, a = 3.0, b = 2.2, c = 1.0, d = 0.001):

        a = self.p1
        b = self.p2
        c = self.p3
        d = self.p4
        soln =solve_ivp( self.BoualiTyp3Func, 
                         ( 0, self.maxTime),(xs, ys, zs),  args=( a, b, c, d), dense_output=True)

        arryTime=np.linspace( 0, self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def BurgersMap( self, xs, ys, zs, a = 0.4, b = 0.78):

        a = self.p1
        b = self.p2
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = (1. - a)*x[i-1] - y[i-1]*y[i-1]
            y[i] = (1 + b)*y[i-1] + x[i-1]*y[i-1]
            z[i] = 0.
        return x, y, z

    def PolynomA( self, xs, ys, zs, a = 1.586, b = 1.124, c = 0.281):

        a = self.p1
        b = self.p2
        c = self.p3
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = a + y[i-1] - y[i-1]*z[i-1]
            y[i] = b + z[i-1] - x[i-1]*z[i-1]
            z[i] = c + x[i-1] - x[i-1]*y[i-1]
        return x, y, z

    def sign( self, x):
        if x >= 0:
            return 1
        else:
            return -1
        
    def Hopalong( self, xs, ys, zs, a = 0.4, b = 1.0, c = 0.):

        a = self.p1
        b = self.p2
        c = self.p3
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = a + y[i-1] - self.sign( x[i-1])*math.sqrt( abs( b*x[i-1] - c))
            y[i] = a - x[i-1]
            z[i] = 0.
        return x, y, z
    
    def Svensson( self, xs, ys, zs, a = 1.4, b = 1.6, c = -1.4, d = 1.5):

        a = self.p1
        b = self.p2
        c = self.p3
        d = self.p4
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = d*math.sin( a*x[i-1]) - math.sin( b*y[i-1])
            y[i] = c*math.cos( a*x[i-1]) + math.cos( b*y[i-1])
            z[i] = 0.
        return x, y, z
    
    def Ikeda( self, xs, ys, zs, a = 0., b = 0.97):

        a = self.p1
        b = self.p2
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            t = a - 6./(1. + x[i-1]*x[i-1] + y[i-1]*y[i-1])
            x[i] = 1. + b*(x[i-1]*math.cos( t) - y[i-1]*math.sin(t))
            y[i] = b*(x[i-1]*math.sin( t) + y[i-1]*math.cos(t))
            z[i] = 0.
        return x, y, z
    
    def SineMap( self, xs, ys, zs, a = 2.0, b = 0.5):

        a = self.p1
        b = self.p2
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = y[i-1]
            y[i] = a*math.sin( x[i-1]) + b*y[i-1]
            z[i] = 0.
        return x, y, z
    
    def GumowskiMira( self, xs, ys, zs, a = 0.93, b = 0.5):

        a = self.p1
        b = self.p2
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        def f( x):
            return b*x + 2.*(1-b)*x*x/(1+x*x)
        
        for i in range( 1, self.maxPoints):
            x[i] = y[i-1] + a*(1-0.005*y[i-1]**2) + f(x[i-1])
            y[i] = -x[i-1] + f(x[i])
            z[i] = 0.
            
        return x, y, z
    
    def MultifoldHenon( self, xs, ys, zs, a = 4.0, b = 0.9):

        a = self.p1
        b = self.p2
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs
        
        for i in range( 1, self.maxPoints):
            x[i] = 1. - a*math.sin( x[i-1]) + b*y[i-1]
            y[i] = x[i-1]
            z[i] = 0.
            
        return x, y, z
    
    def Cathala( self, xs, ys, zs, a = 0.7, b = -0.82):

        a = self.p1
        b = self.p2
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs
        
        for i in range( 1, self.maxPoints):
            x[i] = a*x[i-1] + y[i-1]
            y[i] = b + x[i-1]**2
            z[i] = 0.
            
        return x, y, z
    
    def CoupledLogisticMap( self, xs, ys, zs, a = 0.012, b = 3.7):

        a = self.p1
        b = self.p2
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = (1.-a)*b*x[i-1]*(1.-x[i-1]) + a*b*y[i-1]*(1.-y[i-1])
            y[i] = (1.-a)*b*y[i-1]*(1.-y[i-1]) + a*b*x[i-1]*(1.-x[i-1])
            z[i] = 0.
        return x, y, z
    
    def Clifford( self, xs, ys, zs, a = 1.3, b = -2., c = 2., d = -1.35):

        a = self.p1
        b = self.p2
        c = self.p3
        d = self.p4
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = math.sin( a*y[i-1]) + c*math.cos( a*x[i-1])
            y[i] = math.sin( b*x[i-1]) + d*math.cos( b*y[i-1])
            z[i] = 0.
        return x, y, z
    
    def Tinkerbell( self, xs, ys, zs, a = 0.9, b = -0.601, c = 2.0, d = 0.5):

        a = self.p1
        b = self.p2
        c = self.p3
        d = self.p4
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = x[i-1]**2-y[i-1]**2+a*x[i-1]+b*y[i-1]
            y[i] = 2.*x[i-1]*y[i-1]+c*x[i-1]+d*y[i-1]
            z[i] = 0.
        return x, y, z
    
    def Ushiki( self, xs, ys, zs, a = 3.7, b = 0.1, c = 3.7, d = 0.15):

        a = self.p1
        b = self.p2
        c = self.p3
        d = self.p4
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = (a - x[i-1] - b*y[i-1])*x[i-1]
            y[i] = (c - y[i-1] - d*x[i-1])*y[i-1]
            z[i] = 0.
        return x, y, z
    
    
    def PeterDeJong( self, xs, ys, zs, a = 0.4, b = 60., c = 10., d = 1.6):

        a = self.p1
        b = self.p2
        c = self.p3
        d = self.p4
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = math.sin( a*y[i-1]) - math.cos( b*x[i-1])
            y[i] = math.sin( c*x[i-1]) - math.cos( d*y[i-1])
            z[i] = 0.
        return x, y, z
    
    
    def Pickover( self, xs, ys, zs, a = -0.759, b = 2.449, c = 1.253, d = 1.5):

        a = self.p1
        b = self.p2
        c = self.p3
        d = self.p4
        x = np.zeros( self.maxPoints)
        y = np.zeros( self.maxPoints)
        z = np.zeros( self.maxPoints)

        x[0] = xs
        y[0] = ys
        z[0] = zs

        for i in range( 1, self.maxPoints):
            x[i] = math.sin( a*y[i-1]) - z[i-1]*math.cos( b*x[i-1])
            y[i] = z[i-1]*math.sin( c*x[i-1]) - math.cos( d*y[i-1])
            z[i] = math.sin( x[i-1])
        return x, y, z
    
    def ChenLeeFunc( self, t, X, a, b, d):
        x, y, z = X                           
        x_dot = a*x - y*z
        y_dot = b*y + x*z
        z_dot = d*z + x*y/3
        return x_dot, y_dot, z_dot

    def ChenLee( self, xs, ys, zs, a=5., b=-10, d=-0.38):
        
        a = self.p1
        b = self.p2
        d = self.p3
        
        soln =solve_ivp( self.ChenLeeFunc, ( 0, self.maxTime),(xs, ys, zs), method = 'RK45', 
                         args=(a, b, d), dense_output=True)

        arryTime=np.linspace(0,self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def HalvorsenFunc( self, t, X, a):
        x, y, z = X                           
        x_dot = -a*x-4*y-4*z-y**2
        y_dot = -a*y -4*z -4*x-z**2
        z_dot = -a*z-4*x-4*y-x**2
        return x_dot, y_dot, z_dot

    def Halvorsen( self, xs = 1, ys = 1, zs = 2, a=1.4):

        a = self.p1
        soln =solve_ivp( self.HalvorsenFunc, (0, self.maxTime),(xs, ys, zs),  args=(a,), dense_output=True)

        arryTime=np.linspace(0,self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def SprottLinzFFunc( self, t, X, a):
        x, y, z = X                           
        x_dot = y + z
        y_dot = -x + a*y
        z_dot = x**2 - z
        return x_dot, y_dot, z_dot

    def SprottLinzF( self, xs, ys, zs, a = 0.5):

        a = self.p1
        soln =solve_ivp( self.SprottLinzFFunc, 
                         (0, self.maxTime),(xs, ys, zs),  args=( a,), dense_output=True)

        arryTime=np.linspace(0,self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z

    def ThomasFunc( self, t, X, b):
        x, y, z = X                           
        x_dot = math.sin( y) - b*x
        y_dot = math.sin( z) - b*y
        z_dot = math.sin( x) - b*z

        return x_dot, y_dot, z_dot

    def Thomas( self, xs, ys, zs, b = 0.208186):

        b = self.p1
        soln =solve_ivp( self.ThomasFunc, 
                         (0, self.maxTime),(xs, ys, zs),  args=( b,), dense_output=True)

        arryTime=np.linspace(0,self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z
    
    def NoseHooverFunc( self, t, X, a):
        x, y, z = X                           
        x_dot = y
        y_dot = -x + y*z
        z_dot = a - y*y

        return x_dot, y_dot, z_dot

    def NoseHoover( self, xs, ys, zs, a = 1.5):

        a = self.p1
        soln =solve_ivp( self.NoseHooverFunc, 
                         (0, self.maxTime),(xs, ys, zs),  args=( a,), dense_output=True)

        arryTime=np.linspace(0,self.maxTime, self.maxPoints)

        x,y,z=soln.sol( arryTime)
        return x, y, z
    
def main():
    #
    #
    #
    if len( sys.argv) > 1:
        metric = float( sys.argv[1])

    app = QApplication(sys.argv)

    w = mainWidget( app)
    w.show()
    #
    # connect SIGARLM to handlerALRM
    #
    signal.signal( signal.SIGALRM, handlerALRM)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
