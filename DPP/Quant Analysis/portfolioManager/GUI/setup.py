# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 09:21:44 2016

@author: mvillalon
"""
from distutils.core import setup
import os
import py2exe
import pandas
import matplotlib
import tia.bbg
import pylab, matplotlib.backends.backend_qt4agg
import matplotlibwidget
import numpy


parentDir = os.path.dirname(__file__)
uiFiles = [('ui Files', [os.path.join(parentDir, 'ui Files/portfolioManager.ui'),
                        os.path.join(parentDir, 'ui Files\\benchmark.ui'),
                        os.path.join(parentDir, 'ui Files\\importPortfolio.ui'),
                        os.path.join(parentDir, 'ui Files\\trades.ui'),
                        os.path.join(parentDir, 'ui Files\\Depo.ui'),
                        os.path.join(parentDir, 'ui Files\\FX.ui'),
                        os.path.join(parentDir, 'ui Files\\FXForward.ui'),
        			 os.path.join(parentDir, 'ui Files\\price.ui')
                        ]
           )]
           
           
imageFiles = [('images', [os.path.join(parentDir, 'images\\mind_blown.png'),
                          os.path.join(parentDir, 'images\\thumbs_up.jpg'),
                          os.path.join(parentDir, 'images\\error.png'),
                          os.path.join(parentDir, 'images\\splash_screen.png')
                          ]
            )]
           
setup(options = {
    "py2exe":
        {
            "includes": ["zmq.backend.cython", "matplotlibwidget", "sip", "pandas", "tia.bbg", "matplotlib", "pylab", "matplotlib.backends.backend_qt4agg"],
            "excludes": ["zmq.libzmq"], 
            "dll_excludes": ["MSVCP90.dll","HID.DLL", "w9xpopen.exe", "libzmq.pyd"]
        }
    },
    data_files = matplotlib.get_py2exe_datafiles() + uiFiles + imageFiles,
    console = ['portfolioManager.py'])