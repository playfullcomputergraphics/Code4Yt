from setuptools import setup
from Cython.Build import cythonize
import numpy
#
# python3 setup.py build_ext --inplace
#
setup(
    ext_modules=cythonize("mandelbrotCython.pyx"),
    include_dirs=[numpy.get_include()]
)
