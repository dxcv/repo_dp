# -*- coding: utf-8 -*-
"""
Created on Fri May 20 16:21:59 2016

@author: ngoldberger
"""
import os
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
import numpy as np
from scipy.cluster.hierarchy import cophenet
from scipy.spatial.distance import pdist
os.chdir('L:\Rates & FX\Quant Analysis\portfolioManager\FXanalysis')
import FXClas as FXClas

fx = FXClas.fxData()
factorsIndex, components, variance = fx.getFactorsReturns(periodicity = 'daily', fxRisk = 'G10')#, start = st, end = en
factorsIndex = (factorsIndex + 1).cumprod()
currencyReturns = fx.getCurrencyBasketFromDB(periodicity = 'daily', fxRisk='G10')
currencyReturns =  currencyReturns[1:]
currencyIndex = (currencyReturns+ 1).cumprod()
# some setting for this notebook to actually show the graphs inline, you probably won't need this
# matplotlib inline
np.set_printoptions(precision=5, suppress=True)  # suppress scientific float notation

# generate the linkage matrix
Z = linkage(currencyReturns, 'ward')
Z = Z[:5273]
#c, coph_dists = cophenet(Z, pdist(currencyReturns))
#c

# calculate full dendrogram
plt.figure(figsize=(25, 10))
plt.title('Hierarchical Clustering Dendrogram')
plt.xlabel('sample index')
plt.ylabel('distance')
dendrogram(
    Z,
    leaf_rotation=90.,  # rotates the x axis labels
    leaf_font_size=8.,  # font size for the x axis labels
)
plt.show()


plt.title('Hierarchical Clustering Dendrogram (truncated)')
plt.xlabel('sample index')
plt.ylabel('distance')
dendrogram(
    Z,
    truncate_mode='lastp',  # show only the last p merged clusters
    p=12,  # show only the last p merged clusters
    show_leaf_counts=False,  # otherwise numbers in brackets are counts
    leaf_rotation=90.,
    leaf_font_size=12.,
    show_contracted=True,  # to get a distribution impression in truncated branches
)
plt.show()