
#In [1]: import omp_test
#In [2]: omp_test.test_prange( 200)
#Out[2]: 1084

from libc.stdlib cimport rand
from cython.parallel cimport prange, threadid
cimport cython

def test_prange(int n):
    cdef int x
    cdef int tid
    cdef int acc = 0
    with nogil:
        for x in prange(n, schedule='static'):
            tid = threadid()
            acc += tid  # keine GIL, keine Python-Objekte
    return acc