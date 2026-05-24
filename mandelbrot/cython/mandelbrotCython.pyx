# cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False
from cython.parallel cimport prange
cimport cython
import numpy as np

@cython.cfunc
@cython.inline
cdef bint in_cardioidP(double x, double y) nogil:
    cdef double xm = x - 0.25
    cdef double q = xm * xm + y * y
    return q * (q + xm) < 0.25 * y * y

@cython.cfunc
@cython.inline
cdef bint in_bulbP(double x, double y) nogil:
    cdef double xp = x + 1.0
    return xp * xp + y * y < 0.0625


@cython.cfunc
cdef void mandel_row(int i,
                     int width,
                     double xmin, double dx,
                     double y,
                     int max_iter, double horizon2,
                     int[:, :] image,
                     double[:, :] zAbs) noexcept nogil:
    cdef int j, iter
    cdef double x, zx, zy, zx2, zy2

    for j in range(width):
        x = xmin + dx * j

        if in_bulbP(x, y) or in_cardioidP(x, y):
            image[i, j] = max_iter
            zAbs[i, j] = 0.0
            continue

        zx = 0.0
        zy = 0.0
        zx2 = 0.0
        zy2 = 0.0
        iter = 0

        while zx2 + zy2 < horizon2 and iter < max_iter:
            zy = 2.0 * zx * zy + y
            zx = zx2 - zy2 + x
            zx2 = zx * zx
            zy2 = zy * zy
            iter += 1

        image[i, j] = iter
        zAbs[i, j] = zx2 + zy2


def compute_mandelbrot( int width, int height, double xmin, double xmax,
                        double ymin, double ymax, int max_iter, double horizon):

    cdef double[:, :] zAbs = np.zeros((height, width), dtype=np.float64)
    cdef int[:, :] image = np.zeros((height, width), dtype=np.int32)

    cdef double dx = (xmax - xmin) / width
    cdef double dy = (ymax - ymin) / height
    cdef double horizon2 = horizon * horizon

    cdef int i
    cdef double y

    with nogil:
        for i in prange(height, schedule='static'):
            y = ymin + dy * i
            mandel_row(i, width, xmin, dx, y,
                       max_iter, horizon2,
                       image, zAbs)

    return np.asarray(image), np.sqrt(np.asarray(zAbs))

"""
cdef inline bint in_cardioidS(double x, double y) nogil:
    cdef double xm = x - 0.25
    cdef double q = xm * xm + y * y
    return q * (q + xm) < 0.25 * y * y

cdef inline bint in_bulbS(double x, double y) nogil:
    cdef double xp = x + 1.0
    return xp * xp + y * y < 0.0625  # 1/16

def compute_mandelbrotS(int width, int height,
                       double xmin, double xmax,
                       double ymin, double ymax,
                       int max_iter, double horizon):

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

                if in_cardioidS(x, y) or in_bulbS(x, y):
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
"""
# cython: boundscheck=False, wraparound=False, cdivision=True
#import numpy as np
cimport numpy as np
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


