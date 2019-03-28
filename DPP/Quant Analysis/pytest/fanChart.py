# -*- coding: utf-8 -*-
"""
Created on Fri Dec 18 11:11:52 2015

@author: ngoldberger
"""

import matplotlib.pyplot as plt
import numpy as np

N = 1000
x = np.linspace(0, 10, N)
y = x**2
ones = np.ones(N)

vals = [50, 25, 10, 2] # Values to iterate over and add/subtract from y.

fig, ax = plt.subplots()

for i, val in enumerate(vals):
    alpha = 0.5*(i+1)/len(vals) # Modify the alpha value for each iteration.
    ax.fill_between(x, y+ones*val, y-ones*val, color='blue', alpha=alpha)

ax.plot(x, y, color='cyan') # Plot the original signal

plt.show()