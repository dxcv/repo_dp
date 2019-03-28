# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 18:07:23 2016

@author: ngoldbergerr
"""

import sys
import numpy as np
import pandas as pd
import datetime as dt
from tia.bbg import v3api
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from garch import forecastGARCH

class hedgingStrategies(object):
    
    def __init__(self):
        x = 0
    
    
    def getHistDataFromBloomberg(self, tickers, init = dt.datetime.today()-dt.timedelta(weeks=104), end = dt.datetime.today()-dt.timedelta(days=1)):
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        try:
            response = LocalTerminal.get_historical(tickers, ['PX_LAST'], ignore_security_error=1, ignore_field_error=1, start = init, end = end)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return False
        bloombergData = response.as_frame()
        bloombergData.columns = bloombergData.columns.levels[0]
        return bloombergData
        
        
    def getReturns(self, prices):
        x = (prices.pct_change()).fillna(0)
        return x


    def getER(self,returns,freq='d'):
        multiplier = {'d': 252, 'w': 52, 'm': 12}
        eret = float(returns.mean().values)*multiplier[freq]
        return eret


    def portfolioReturns(self,instruments,weights):
        omega = pd.DataFrame(np.tile(weights,(len(instruments),1)))
        omega.index = instruments.index
        omega.columns = instruments.columns
        portfolioReturn = omega*instruments
        return portfolioReturn

    
    def getShortfall(self,returns,alpha=0.05):
        ret_sorted = returns.sort_values()
        x = int(np.round(alpha*len(returns)))
        ES = float(ret_sorted.iloc[:x].mean().values)
        return ES


    def getVolatility(self,returns,freq='d'):
        multiplier = {'d': np.sqrt(252), 'w': np.sqrt(52), 'm': np.sqrt(12)}
        volatility = float(returns.std().values)*multiplier[freq]
        return volatility
    
    
    def maxDrawDown(self, returns, window = 20):
        returns = returns
        mReturns = pd.rolling_sum(returns,window)
        maxDD = float(mReturns.min().values)
        return maxDD   

    def plotSeries(self,level,returns):
        months = mdates.MonthLocator()
        f, axarr = plt.subplots(2, sharex=True)
        plt.style.use('bmh')
        f.set_size_inches(15, 10)
        axarr[0].plot(level.index, level[level.columns[0]])
        axarr[0].set_title('Time Series ('+level.columns[0]+')', fontsize = 16)
        axarr[0].legend([level.columns[0]+' Level'],loc=4)
        axarr[1].plot(level.index, returns[returns.columns[0]]*100)
        axarr[1].set_xlabel('Date', fontsize = 14)
        axarr[0].set_ylabel('Level', fontsize = 14)
        axarr[1].set_ylabel('Return (%)', fontsize = 14)
        axarr[1].xaxis.set_minor_locator(months)
        datemin = dt.date(level.index.min().year, level.index.min().month, level.index.min().day)
        datemax = dt.date(level.index.max().year, level.index.min().month, level.index.min().day)
        axarr[1].set_xlim(datemin, datemax)
        plt.show()        

        return True
#    def plotCorrelations(self):
        
        
if __name__ == '__main__':
    
    hs = hedgingStrategies()
    idx = hs.getHistDataFromBloomberg(['BEMC Index'])
    returnSeries = hs.getReturns(idx)
    expectedReturn = hs.getER(returnSeries)
    volatility = hs.getVolatility(returnSeries)
    maxDrawDown = hs.maxDrawDown(returnSeries)
    hs.plotSeries(idx,returnSeries)



    