from distutils.core import Extension, setup
from Cython.Build import cythonize

ext = Extension(name="cythonfile", sources =["cythonfile.pyx"])
setup(ext_modules=cythonize(ext))