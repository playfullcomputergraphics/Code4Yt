# mandelbrotCython.pyx
# cython: language_level=3
#  ---
#cimport cython
#from gmpy2 import mpfr, mpc, get_context, sqrt
##from mpmath import mp, mpc, mpf
##import gmpy2

# cython: boundscheck=False, wraparound=False, language_level=3

import numpy as np
cimport numpy as np
from cython.parallel import prange

cdef inline bint in_cardioid(double x, double y) nogil:
    cdef double xm = x - 0.25
    cdef double q = xm * xm + y * y
    return q * (q + xm) < 0.25 * y * y

cdef inline bint in_bulb(double x, double y) nogil:
    cdef double xp = x + 1.0
    return xp * xp + y * y < 0.0625  # 1/16

def compute_mandelbrot(int width, int height,
                       double xmin, double xmax,
                       double ymin, double ymax,
                       int max_iter, double horizon, int cardioidBulb):

    cdef np.ndarray[np.int32_t, ndim=2] image = np.zeros((height, width), dtype=np.int32)
    cdef np.ndarray[np.float64_t, ndim=2] zAbs = np.zeros((height, width), dtype=np.float64)
    #
    # typed memoryviews: better c performance, avoid numpy inside nogil, 
    #   indexing image[i, j] would require gil
    #
    #cdef int[:, :] image_view = image
    #cdef double[:, :] zAbs_view = zAbs
    #
    # typed pointers avoids Python indexing, NumPy API calls, bounds checks
    #   shape checks, stride lookups, is gil-free, numpy-free
    #
    cdef np.int32_t* r = &image[0,0]
    cdef np.float64_t* a = &zAbs[0,0]
    
    cdef double dx = (xmax - xmin) / width
    cdef double dy = (ymax - ymin) / height
    cdef double horizon2 = horizon * horizon

    cdef int i, j, iter
    cdef double x, y, zx, zy, zx2

    with nogil:
        for i in range(height):
            y = ymin + dy * i
            for j in range(width):
                x = xmin + dx * j
                zx = 0.0
                zy = 0.0
                iter = 0

                if cardioidBulb == 1:
                    if in_cardioid(x, y) or in_bulb(x, y):
                        #image_view[i, j] = max_iter
                        #zAbs_view[i, j] = 0.0
                        r[i*width + j] = max_iter
                        a[i*width + j] = 0.0
                        continue
                zx2 = zx*zx
                zy2 = zy*zy

                while zx2 + zy2 < horizon2 and iter < max_iter:
                    zy = 2.0*zx*zy + y
                    zx = zx2 - zy2 + x
                    zx2 = zx*zx
                    zy2 = zy*zy
                    iter += 1

                #image_view[i, j] = iter
                #zAbs_view[i, j] = zx*zx + zy*zy
                r[i*width + j] = iter
                a[i*width + j] = zx*zx + zy*zy

    return image, np.sqrt(zAbs)


cdef void compute_row(
        int i,
        int width,
        double xmin, double dx,
        double y,
        int max_iter,
        double horizon2,
        int cardioidBulb, 
        int[:, :] image_view,
        double[:, :] zAbs_view) nogil:

    cdef int j, iter
    cdef double x, zx, zy, zx2

    for j in range(width):
        x = xmin + dx * j
        zx = 0.0
        zy = 0.0
        iter = 0

        if cardioidBulb == 1:
            if in_cardioid(x, y) or in_bulb(x, y):
                image_view[i, j] = max_iter
                zAbs_view[i, j] = 0.0
                continue

        while zx * zx + zy * zy < horizon2 and iter < max_iter:
            zx2 = zx * zx - zy * zy + x
            zy = 2.0 * zx * zy + y
            zx = zx2
            iter += 1

        image_view[i, j] = iter
        zAbs_view[i, j] = zx * zx + zy * zy

def compute_mandelbrot_parallel( int width, int height,
                                 double xmin, double xmax,
                                 double ymin, double ymax,
                                 int max_iter, double horizon, int cardioidBulb):

    cdef np.ndarray[np.int32_t, ndim=2] image = np.zeros((height, width), dtype=np.int32)
    cdef np.ndarray[np.float64_t, ndim=2] zAbs = np.zeros((height, width), dtype=np.float64)

    cdef int[:, :] image_view = image
    cdef double[:, :] zAbs_view = zAbs

    cdef double dx = (xmax - xmin) / width
    cdef double dy = (ymax - ymin) / height
    cdef double horizon2 = horizon * horizon

    cdef int i
    cdef double y
    #
    # prange() (parallel-range) made it necessay to make compute_row() 
    #
    for i in prange(height, nogil=True, schedule='static'):
        y = ymin + dy * i
        compute_row(i, width, xmin, dx, y,
                    max_iter, horizon2, cardioidBulb, 
                    image_view, zAbs_view)

    return image, np.sqrt(zAbs)

"""
@cython.boundscheck(False)
@cython.wraparound(False)
def compute_mandelbrot_hp(int width, int height, double xmin, double xmax, double ymin, double ymax, int max_iter, double horizon, int precision, int cardioidBulb):
    cdef np.ndarray[np.int32_t, ndim=2] image = np.zeros((height, width), dtype=np.int32)
    cdef np.ndarray[np.float64_t, ndim=2] zAbs = np.zeros((height, width), dtype=np.float64)

    #mp.dps = precision
    get_context().precision = 20  #200 give ~60 decimal digits

    for x in range(width):
        real = mpfr(xmin + x * (xmax - xmin) / width)
        for y in range(height):
            imag = mpfr(ymin + y * (ymax - ymin) / height)
            c = mpc(real, imag)
            z = mpc(0, 0)
            count = 0
            while abs(z) <= horizon and count < max_iter:
                z = z*z + c
                count += 1
            image[y, x] = count
            zAbs[y,x] = abs( z)
    return image, zAbs
"""

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
    cdef np.ndarray[np.float64_t, ndim=2] image = np.zeros((height, width), dtype=np.float64)
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
                            image[y, x] = log(1.0 + nu + log(1.0 + dist))
                        escaped[y, x] = 1
    return image
