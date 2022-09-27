from distutils.sysconfig import get_python_inc
from distutils.sysconfig import get_python_lib
import sys

print(sys.prefix)
print(get_python_inc())
print(get_python_lib())