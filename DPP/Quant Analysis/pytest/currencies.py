# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 11:06:13 2015

@author: ngoldberger
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tia.bbg import LocalTerminal
from matplotlib import rc
rc('mathtext', default='regular')

if __name__ == '__main__':
    d = pd.datetools.BDay(-30).apply(pd.datetime.now())
    m = pd.datetools.BMonthBegin(-2).apply(pd.datetime.now())

    FX = ['eurusd curncy', 'audusd curncy','cadusd curncy']
    response = LocalTerminal.get_historical(FX, ['px_last'], start=d)
#    print response.as_frame()
    t = [pd.datetools.BDay(-i).apply(pd.datetime.now()) for i in range(31)]
    x = pd.DataFrame(columns = ['price', 'returns'])
    x['price'] = response.as_frame()['eurusd curncy']['px_last']
    x['returns'] = np.log(x.price) - np.log(x.price.shift(1))
    
#    plt.plot(t,x.price,t,x.returns)
#    plt.show()
    
    fig, ax1 = plt.subplots()
    ax1.plot(t,x.price,'b-')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')
#    ax2 = ax1.twinx()
#    ax2.plot(t,x.returns,'r-')
#    for tl in ax2.get_yticklabels():
#        tl.set_color('r')
    fig.autofmt_xdate()
    fig.set_size_inches(12, 8)
    
    plt.show()
