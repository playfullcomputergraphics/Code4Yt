# mandelbrotCython.pyx
cimport cython
import numpy as np
import math
cimport numpy as np
#from mpmath import mp, mpc, mpf
#import gmpy2
#from gmpy2 import mpfr, mpc, get_context, sqrt

@cython.boundscheck(False)
@cython.wraparound(False)
def compute_mandelbrot(int width, int height,
    double xmin, double xmax, double ymin, double ymax, 
    int max_iter, double horizon, int convTest):
    #
    cdef np.ndarray[np.int32_t, ndim=2] result = np.zeros((height, width), dtype=np.int32)
    cdef np.ndarray[np.float64_t, ndim=2] zAbs = np.zeros((height, width), dtype=np.float64)
    cdef int i, j, iter
    cdef double x, y, zx, zy, zx2, zy2
    cdef double zx_prev, zy_prev, epsilon = 1e-6
    with nogil:
        for i in range(height):
            y = ymin + (ymax - ymin) * i / height
            for j in range(width):
                x = xmin + (xmax - xmin) * j / width
                zx, zy = 0.0, 0.0
                iter = 0
                while zx*zx + zy*zy < horizon*horizon and iter < max_iter:
                    if convTest == 1: 
                        zx_prev, zy_prev = zx, zy
                    zx2 = zx*zx - zy*zy + x
                    zy = 2.0*zx*zy + y
                    zx = zx2
                    iter += 1
                    if convTest == 1: 
                       if(zx - zx_prev)**2 + (zy - zy_prev)**2 < epsilon:
                           iter = max_iter
                           break  # orbit has stabilized
                result[i, j] = iter
                #zAbs[i, j] = math.sqrt( zx*zx + zy*zy)
                zAbs[i, j] = zx*zx + zy*zy

    zAbs = np.sqrt( zAbs)                                           
    return result, zAbs

#@cython.boundscheck(False)
#@cython.wraparound(False)
#def compute_mandelbrot_hp(int width, int height, double xmin, double xmax, double ymin, double ymax, int max_iter, double horizon, int precision):
#    cdef np.ndarray[np.int32_t, ndim=2] result = np.zeros((height, width), dtype=np.int32)
#    cdef np.ndarray[np.float64_t, ndim=2] zAbs = np.zeros((height, width), dtype=np.float64)

#    #mp.dps = precision
#    get_context().precision = 20  #200 give ~60 decimal digits
#
#    for x in range(width):
#        real = mpfr(xmin + x * (xmax - xmin) / width)
#        for y in range(height):
#            imag = mpfr(ymin + y * (ymax - ymin) / height)
#            c = mpc(real, imag)
#            z = mpc(0, 0)
#            count = 0
#            while abs(z) <= horizon and count < max_iter:
#                z = z*z + c
#                count += 1
#            result[y, x] = count
#            zAbs[y,x] = abs( z)
#    return result, zAbs

    
# cython: boundscheck=False, wraparound=False, cdivision=True
#import numpy as np
#cimport numpy as np
from libc.math cimport fabs

def compute_julia(np.ndarray[np.float64_t, ndim=2] real_grid,
                  np.ndarray[np.float64_t, ndim=2] imag_grid,
                  double c_real, double c_imag,
                  int max_iter, horizon):

    cdef int height = real_grid.shape[0]
    cdef int width = real_grid.shape[1]
    cdef np.ndarray[np.int32_t, ndim=2] output = np.zeros((height, width), dtype=np.int32)
    cdef np.ndarray[np.float64_t, ndim=2] zAbs = np.zeros((height, width), dtype=np.float64)

    cdef int i, j, iter
    cdef double z_real, z_imag, z_real2, z_imag2
    cdef double horizon_val = horizon

    with nogil:
        for i in range(height):
            for j in range(width):
                z_real = real_grid[i, j]
                z_imag = imag_grid[i, j]
                iter = 0

                while iter < max_iter:
                    z_real2 = z_real * z_real
                    z_imag2 = z_imag * z_imag

                    if z_real2 + z_imag2 > horizon_val:
                        break

                    z_imag = 2.0 * z_real * z_imag + c_imag
                    z_real = z_real2 - z_imag2 + c_real
                    iter += 1

                output[i, j] = iter
                #
                zAbs[i, j] = z_imag*z_imag + z_real*z_real
    zAbs = np.sqrt( zAbs)                                           
    return output, zAbs

# mandelbrot_smooth.pyx
import numpy as np
cimport numpy as np
cimport cython
from libc.math cimport log, fabs

@cython.boundscheck(False)
@cython.wraparound(False)
def mandelbrot_dz(np.ndarray[np.complex128_t, ndim=2] C, int max_iter):
    cdef int height = C.shape[0]
    cdef int width = C.shape[1]
    cdef np.ndarray[np.float64_t, ndim=2] result = np.zeros((height, width), dtype=np.float64)
    cdef np.ndarray[np.complex128_t, ndim=2] Z = np.zeros((height, width), dtype=np.complex128)
    cdef np.ndarray[np.complex128_t, ndim=2] dZ = np.ones((height, width), dtype=np.complex128)
    cdef np.ndarray[np.uint8_t, ndim=2] escaped = np.zeros((height, width), dtype=np.uint8)

    cdef int i, x, y
    cdef double absZ, absDZ, nu, dist

    for i in range(max_iter):
        for y in range(height):
            for x in range(width):
                if escaped[y, x] == 0:
                    Z[y, x] = Z[y, x] * Z[y, x] + C[y, x]
                    dZ[y, x] = 2.0 * Z[y, x] * dZ[y, x] + 1.0
                    absZ = abs(Z[y, x])
                    if absZ > 4.0:
                        absDZ = abs(dZ[y, x])
                        if absDZ != 0.0:
                            nu = i + 1 - log(log(absZ + 1e-8)) / log(2.0)
                            dist = absZ * log(absZ) / absDZ
                            result[y, x] = log(1.0 + nu + log(1.0 + dist))
                        escaped[y, x] = 1
    return result
