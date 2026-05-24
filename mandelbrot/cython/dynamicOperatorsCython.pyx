# cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False
from cython.parallel cimport prange
cimport cython
import numpy as np
# ---
# cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False
from cython.parallel cimport prange
cimport cython
import numpy as np
import gc
# ---
# cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False
import cython
import numpy as np
cimport numpy as np
from cython.parallel cimport prange

# Tell Cython about NumPy's float32 type
ctypedef np.float32_t float32_t


@cython.cfunc
@cython.inline
cdef float32_t lap_inline(float32_t[:, :] A, int x, int y, int h, int w) nogil:
    cdef int xm1 = x - 1 if x > 0 else h - 1
    cdef int xp1 = x + 1 if x < h - 1 else 0
    cdef int ym1 = y - 1 if y > 0 else w - 1
    cdef int yp1 = y + 1 if y < w - 1 else 0
    return (
        A[xm1, y] + A[xp1, y] +
        A[x, ym1] + A[x, yp1] -
        4.0 * A[x, y]
    )


def grayScott(float32_t[:, :] U_in,
              float32_t[:, :] V_in,
              float32_t Du, float32_t Dv,
              float32_t F, float32_t k,
              int iterations, float32_t dt):

    cdef int h = U_in.shape[0]
    cdef int w = U_in.shape[1]

    # Directly use input buffers (no copies)
    cdef float32_t[:, :] U = U_in
    cdef float32_t[:, :] V = V_in

    cdef float32_t[:, :] U_new = np.empty((h, w), dtype=np.float32)
    cdef float32_t[:, :] V_new = np.empty((h, w), dtype=np.float32)

    cdef int i, x, y
    cdef float32_t uxy, vxy, lapU, lapV, uvv
    cdef float32_t[:, :] tmp

    with nogil:
        for i in range(iterations):
            for x in prange(h, schedule='static'):
                for y in range(w):
                    uxy = U[x, y]
                    vxy = V[x, y]

                    lapU = lap_inline(U, x, y, h, w)
                    lapV = lap_inline(V, x, y, h, w)

                    uvv = uxy * vxy * vxy

                    U_new[x, y] = uxy + dt * (Du * lapU - uvv + F - F * uxy)
                    V_new[x, y] = vxy + dt * (Dv * lapV + uvv - (F + k) * vxy)

            # Swap buffers
            tmp = U
            U = U_new
            U_new = tmp

            tmp = V
            V = V_new
            V_new = tmp

    return np.asarray(U), np.asarray(V)
# ---
@cython.cfunc
@cython.inline
cdef float laplace(float[:, :] A, int x, int y, int h, int w) nogil:
    cdef int xm1 = x - 1 if x > 0 else h - 1
    cdef int xp1 = x + 1 if x < h - 1 else 0
    cdef int ym1 = y - 1 if y > 0 else w - 1
    cdef int yp1 = y + 1 if y < w - 1 else 0
    return (A[xm1, y] + A[xp1, y] + A[x, ym1] + A[x, yp1] - 4.0 * A[x, y])


def grayScottOld(float[:, :] U_in,
              float[:, :] V_in,
              float Du, float Dv, float F, float k,
              int iterations, float dt):

    cdef int h = U_in.shape[0]
    cdef int w = U_in.shape[1]

    # GC nur mit GIL anfassen
    gc.disable()

    cdef float[:, :] U = np.asarray(U_in, dtype=np.float32)
    cdef float[:, :] V = np.asarray(V_in, dtype=np.float32)

    cdef float[:, :] U_new = np.empty((h, w), dtype=np.float32)
    cdef float[:, :] V_new = np.empty((h, w), dtype=np.float32)

    cdef int i, x, y
    cdef float uvv, lapU, lapV
    cdef float uxy, vxy

    with nogil:
        for i in range(iterations):
            for x in prange(h, schedule='static'):
                for y in range(w):
                    uxy = U[x, y]
                    vxy = V[x, y]

                    lapU = laplace(U, x, y, h, w)
                    lapV = laplace(V, x, y, h, w)

                    uvv = uxy * vxy * vxy

                    U_new[x, y] = uxy + dt * (Du * lapU - uvv + F * (1.0 - uxy))
                    V_new[x, y] = vxy + dt * (Dv * lapV + uvv - (F + k) * vxy)

            U, U_new = U_new, U
            V, V_new = V_new, V

    gc.enable()

    return np.asarray(U), np.asarray(V)
# ---
# cython: boundscheck=False, wraparound=False, cdivision=True
import numpy as np
cimport numpy as cnp

from scipy.ndimage import gaussian_filter

def antiDiffusionV1(
        cnp.ndarray[cnp.float64_t, ndim=2] data,
        double sigma,
        double alpha,
        int iterations,
        int normLoop):

    """
    Fully float64 anti-diffusion.
    """

    cdef int i
    cdef double dmin, dmax

    # Ensure contiguous float64 array
    cdef cnp.ndarray[cnp.float64_t, ndim=2] data_f
    data_f = np.ascontiguousarray(data, dtype=np.float64)

    cdef cnp.ndarray[cnp.float64_t, ndim=2] blurred

    for i in range(iterations):

        # Gaussian blur in float64 (matches Python)
        blurred = gaussian_filter(data_f, sigma=(sigma, sigma))

        # Sharpening in float64
        data_f = data_f + alpha * (data_f - blurred)

        # Optional normalization inside loop
        if normLoop == 1:
            dmin = data_f.min()
            dmax = data_f.max()
            data_f = (data_f - dmin) / (dmax - dmin) * 255.0

    # Final normalization if normLoop == 0
    if normLoop == 0:
        dmin = data_f.min()
        dmax = data_f.max()
        data_f = (data_f - dmin) / (dmax - dmin) * 255.0

    # Return uint8 image (same as Python)
    return data_f.astype(np.uint8)

#---
# cython: boundscheck=False, wraparound=False, cdivision=True, nonecheck=False, language_level=3
from cython.parallel import prange
import numpy as np
cimport numpy as cnp
from libc.math cimport exp

# ------------------------------------------------------------
# Build 1D Gaussian kernel
# ------------------------------------------------------------
cdef double[:] build_kernel(double sigma):
    cdef int radius = int(3 * sigma)
    if radius < 1:
        radius = 1
    cdef int size = 2 * radius + 1
    cdef double[:] kernel = np.empty(size, dtype=np.float64)

    cdef int i
    cdef double s2 = 2.0 * sigma * sigma
    cdef double sumv = 0.0

    for i in range(size):
        kernel[i] = exp(-((i - radius) * (i - radius)) / s2)
        sumv += kernel[i]

    for i in range(size):
        kernel[i] /= sumv

    return kernel


# ------------------------------------------------------------
# Per-pixel horizontal Gaussian
# ------------------------------------------------------------
cdef inline double gaussian_h_pixel(
        double[:, :] src,
        double[:] kernel,
        int i,
        int j,
        int r) nogil:

    cdef double acc = 0.0
    cdef int t
    cdef int w = src.shape[1]

    for t in range(-r, r+1):
        if 0 <= j+t < w:
            acc += src[i, j+t] * kernel[t+r]

    return acc


# ------------------------------------------------------------
# Per-pixel vertical Gaussian
# ------------------------------------------------------------
cdef inline double gaussian_v_pixel(
        double[:, :] src,
        double[:] kernel,
        int i,
        int j,
        int r) nogil:

    cdef double acc = 0.0
    cdef int t
    cdef int h = src.shape[0]

    for t in range(-r, r+1):
        if 0 <= i+t < h:
            acc += src[i+t, j] * kernel[t+r]

    return acc


# ------------------------------------------------------------
# Horizontal Gaussian convolution (OpenMP)
# ------------------------------------------------------------
cdef void gaussian_h(
        double[:, :] src,
        double[:, :] dst,
        double[:] kernel) nogil:

    cdef int h = src.shape[0]
    cdef int w = src.shape[1]
    cdef int k = kernel.shape[0]
    cdef int r = k // 2
    cdef int i, j

    for i in prange(h, schedule='static'):
        for j in range(w):
            dst[i, j] = gaussian_h_pixel(src, kernel, i, j, r)


# ------------------------------------------------------------
# Vertical Gaussian convolution (OpenMP)
# ------------------------------------------------------------
cdef void gaussian_v(
        double[:, :] src,
        double[:, :] dst,
        double[:] kernel) nogil:

    cdef int h = src.shape[0]
    cdef int w = src.shape[1]
    cdef int k = kernel.shape[0]
    cdef int r = k // 2
    cdef int i, j

    for j in prange(w, schedule='static'):
        for i in range(h):
            dst[i, j] = gaussian_v_pixel(src, kernel, i, j, r)


# ------------------------------------------------------------
# Full separable Gaussian blur (OpenMP)
# ------------------------------------------------------------
cdef void gaussian_blur(
        double[:, :] src,
        double[:, :] tmp,
        double[:, :] dst,
        double[:] kernel) nogil:

    gaussian_h(src, tmp, kernel)
    gaussian_v(tmp, dst, kernel)


# ------------------------------------------------------------
# Anti-diffusion with parallel Gaussian blur
# ------------------------------------------------------------
def antiDiffusionV2(
        cnp.ndarray[cnp.float64_t, ndim=2] data,
        double sigma,
        double alpha,
        int iterations,
        int normLoop):

    cdef double[:, :] data_f = np.ascontiguousarray(data, dtype=np.float64)
    cdef double[:, :] tmp = np.zeros_like(data_f)
    cdef double[:, :] blurred = np.zeros_like(data_f)

    cdef double[:] kernel = build_kernel(sigma)

    cdef int h = data_f.shape[0]
    cdef int w = data_f.shape[1]
    cdef int it, y, x

    cdef double dmin, dmax, scale

    for it in range(iterations):

        # Gaussian blur (parallel)
        with nogil:
            gaussian_blur(data_f, tmp, blurred, kernel)

        # Sharpening (parallel)
        with nogil:
            for y in prange(h, schedule='static'):
                for x in range(w):
                    data_f[y, x] += alpha * (data_f[y, x] - blurred[y, x])

        # Optional normalization
        if normLoop == 1:
            dmin = data_f[0,0]
            dmax = data_f[0,0]

            for y in range(h):
                for x in range(w):
                    if data_f[y,x] < dmin:
                        dmin = data_f[y,x]
                    if data_f[y,x] > dmax:
                        dmax = data_f[y,x]

            scale = 255.0 / (dmax - dmin)

            with nogil:
                for y in prange(h, schedule='static'):
                    for x in range(w):
                        data_f[y,x] = (data_f[y,x] - dmin) * scale

    # Final normalization
    if normLoop == 0:
        dmin = data_f[0,0]
        dmax = data_f[0,0]

        for y in range(h):
            for x in range(w):
                if data_f[y,x] < dmin:
                    dmin = data_f[y,x]
                if data_f[y,x] > dmax:
                    dmax = data_f[y,x]

        scale = 255.0 / (dmax - dmin)

        with nogil:
            for y in prange(h, schedule='static'):
                for x in range(w):
                    data_f[y,x] = (data_f[y,x] - dmin) * scale

    return np.asarray(data_f, dtype=np.uint8)
