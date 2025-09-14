#!/bin/env python3

CMAPS = [ 'hot', 'gnuplot2', 'nipy_spectral', 'jet', 'prism', 
          'turbo', 'flag', 'rainbow', 'gist_rainbow', 
          'plasma', 'hsv', 'viridis', 
          'Greys', 'Greys_r', 'RdPu', 'OrRd', 'spring', 
          'summer', 'autumn', 'winter', 'cool', 'Paired', 'Accent', 'Set1',
          'PiYG', 'bwr', 'RdYlBu', 'RdYlGn', 'Spectral', 'seismic',
         ]

BACKGROUND_CMAPS = [ 'white', 'black', 'lightyellow', 'lightcyan', 'azure',
                      'dimgrey', 'grey', 'lightgrey', 'whitesmoke']

import numpy as np

def findCurrentIndex( x, X):
    '''
        return the position as index of x in X
        used to setup combo boxes
        '''
    for i in range( len( X)): 
        if x == X[ i]:
            return i
    print( "findCurrentIndex: failed for %s in %s" % (repr( x), repr( X)))
    return None

def derivative( x, y):
    '''
    '''

    x = np.array( x)
    x = x - x[0]
    y = np.array( y)
    ty = np.array( y)

    npoint = len( x)

    for i in range( 1, npoint - 1):
      det = (x[i]*x[i+1]*x[i+1] - x[i+1]*x[i]*x[i] - 
             x[i-1]*x[i+1]*x[i+1] + x[i+1]*x[i-1]*x[i-1] + 
             x[i-1]*x[i]*x[i] - x[i]*x[i-1]*x[i-1])
      if det == 0.:
        raise ValueError( "calc.derivative: det == 0.")

      za1 = (y[i]*x[i+1]*x[i+1] - y[i+1]*x[i]*x[i] -
             y[i-1]*x[i+1]*x[i+1] + y[i+1]*x[i-1]*x[i-1] +
             y[i-1]*x[i]*x[i] - y[i]*x[i-1]*x[i-1])
      za2 = (x[i]*y[i+1] - x[i+1]*y[i] -
             x[i-1]*y[i+1] + x[i+1]*y[i-1] +
             x[i-1]*y[i] - x[i]*y[i-1])

      if i == 1:
          ty[0]   = (za1 + 2.0*za2*x[0])/det

      if i == (npoint - 2):
          ty[ npoint - 1] = (za1 + 2.0*za2*x[npoint -1])/det

      ty[i] = (za1 + 2.0*za2*x[i])/det
 
    return ty

