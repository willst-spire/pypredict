from distutils.core import setup, Extension

#pypredict_module = Extension('pypredict', sources= ['pypredict.c'])
#
#setup(name = 'PyPredict',
#      version = '0.0',
#      description = 'A python port of the predict satellite tracking library',
#      ext_modules = [pypredict_module])

from distutils.core import setup, Extension
setup(name='predict', version='1.0',  \
      ext_modules=[Extension('predict', ['predict.c'])])