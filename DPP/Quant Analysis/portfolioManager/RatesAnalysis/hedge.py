# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 10:51:07 2016

@author: ngoldbergerr
"""

import sys
import numpy as np
import pandas as pd
import datetime as dt
from tia.bbg import v3api
#import matplotlib.pyplot as plt

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


    def portfolioReturns(self,instruments):
        weights = np.arange(0,1.01,0.01)
        omega = pd.DataFrame(np.tile(weights,(len(instruments),1)))
        omega.index = instruments.index
        omega.columns = omega.iloc[0]*100
        a_r = pd.DataFrame(data = np.tile(ret[ret.columns[0]].values,(len(omega.columns),1)).transpose())
        a_r.columns = omega.columns
        a_r.index = omega.index
        c_r = pd.DataFrame(data = np.tile(ret[ret.columns[1]].values,(len(omega.columns),1)).transpose())
        c_r.columns = omega.columns
        c_r.index = omega.index
        portfolioReturn = a_r + c_r*(1-omega)
        return portfolioReturn

    
    def getShortfall(self,returns,alpha=0.05):
        ret_sorted = returns.sort_values()
        x = int(np.round(alpha*len(returns)))
        ES = ret_sorted.iloc[:x].mean()
        return ES

        
    def optimalHedgeLevel(self,returns):
        ExpectedShortfall = pd.DataFrame(0, index = ['ES'], columns = returns.columns)
        for i in returns.columns:
            ExpectedShortfall[i].iloc[0] = self.getShortfall(returns[i])
        
        return ExpectedShortfall.transpose()
    
#    def plotCorrelations(self):
        
        
if __name__ == '__main__':
    
    hs = hedgingStrategies()
#    idx = hs.getHistDataFromBloomberg(['EMUSTRUU Index','USDCLP Curncy'])
    idx = hs.getHistDataFromBloomberg(['BSEZTRUU Index','USDCLP Curncy'])
    ret = hs.getReturns(idx)
    port_ret = hs.portfolioReturns(ret)
#    ES = hs.getShortfall(port_ret[50])
    oh = hs.optimalHedgeLevel(port_ret)
    