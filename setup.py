from setuptools import setup, find_packages
import os, sys
import subprocess

# Define version
__version__ = 0.02

setup( name             = 'illuminate'
     , version          = __version__
     , description      = 'Illuminate LED Array Controller Library'
     , license          = 'BSD'
     , packages         = find_packages()
     , include_package_data = True
     , install_requires = ['pyserial', 'numpy']
     )
