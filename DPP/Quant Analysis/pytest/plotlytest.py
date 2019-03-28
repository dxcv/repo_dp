# -*- coding: utf-8 -*-
"""
Created on Tue Feb 09 16:35:45 2016

@author: ngoldberger
"""

import plotly.plotly as py
import plotly.graph_objs as go

# Create random data with numpy
import numpy as np

N = 500
random_x = np.linspace(0, 1, N)
random_y = np.random.randn(N)

# Create a trace
trace = go.Scatter(
    x = random_x,
    y = random_y
)

data = [trace]

# Plot and embed in ipython notebook!
#py.iplot(data, filename='basic-line')

plot_url = py.plot(data, filename='basic-line')