"""
Created on Thu Dex 22 11:00:00 2017

@author: Fernando Suarez
"""
from math import sqrt
from scipy.stats import norm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.animation as animation
import pylab
import time



def plot_curves(curves):
    '''
    Grafica dos curvas.
    '''
    plt.rcParams["figure.figsize"] = [20,9]
    sns.set_style("darkgrid")
    dat=[100]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlim([0,len(curves[0])])
    ax.set_ylim([80,140])
    plt.title('100 Simulations Geometric Brownian Motion IPSA', fontsize=20)
    plt.xlabel('$days$')
    plt.ylabel('$return$')
    plt.ion()
    plt.show()

    lns = []
    dats = []
    for curve in curves:
        Ln, = ax.plot(dat,linestyle='-', color=np.random.rand(3,), linewidth=1)
        lns.append(Ln)
        dats.append([100])
    for i in range (len(curves[0])):
        #print("i:" + str(i))
        for j in range(len(curves)):
            #print("j:" + str(j))
            dats[j].append(curves[j].values[i])
            lns[j].set_xdata(range(len(dats[j])))
            lns[j].set_ydata(dats[j])
        plt.pause(0.000001)


def simulate_ipsa():
    '''
    Grafica dos curvas.
    '''
    date_inic = "2018-01-01"
    date_end = "2018-12-31"
    u = 0.15
    sig = 0.1
    n = 50
    series  = []

    for i in range(n):
        serie = simulate_serie(date_inic, date_end, u, sig)
        series.append(serie)

    plot_curves(series)

def plot_curvesFIX(curves):
    '''
    Grafica dos curvas.
    '''
    plt.rcParams["figure.figsize"] = [20,9]
    tenors = curves[0].index
    sns.set_style("darkgrid")
    plt.title('Brownian Motion IPSA', fontsize=20)

    for curve in curves:
        plt.plot(tenors, curve, linestyle='-', color=np.random.rand(3,), linewidth=1)
    plt.xlabel('$x$')
    plt.ylabel('$y$')
    plt.show()

def simulate_serie(date_inic, date_end, u, sig):
    '''
    Simula una serie
    '''
    dates = pd.date_range(date_inic, date_end).tolist()
    serie = pd.Series(index=dates)
    serie = serie.apply(lambda x: np.random.randn())
    serie = u/365 + (serie*sig/sqrt(365))
    serie.loc[serie.index[0]] = 0.0
    serie = (1.0+serie).cumprod()*100 
    return serie


simulate_ipsa()
