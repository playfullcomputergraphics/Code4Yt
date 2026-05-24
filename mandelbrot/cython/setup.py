from setuptools import setup
from Cython.Build import cythonize
import numpy
#
# python3 setup.py build_ext --inplace
#
#setup(
#    ext_modules=cythonize("mandelbrotCython.pyx"),
#    include_dirs=[numpy.get_include()],
#    extra_compile_args=["-O3", "-march=native", "-fopenmp"],
#    extra_link_args=["-fopenmp"],
#)

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

ext1 = Extension(
    name="mandelbrotCython",
    sources=["mandelbrotCython.pyx"],
    include_dirs=[np.get_include()],
    extra_compile_args=["-fopenmp"],
    extra_link_args=["-fopenmp"],
)

ext2 = Extension(
    name="",
    sources=["dynamicOperatorsCython.pyx"],
    extra_compile_args=["-fopenmp"],
    extra_link_args=["-fopenmp"],
)

ext3 = Extension(
    name="omp_test",
    sources=["omp_test.pyx"],
    extra_compile_args=["-fopenmp"],
    extra_link_args=["-fopenmp"],
)

setup(
    ext_modules=cythonize(
        [ext1, ext2, ext3],
        compiler_directives={"language_level": "3"},
    )
)
