# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 14:34:59 2015

@author: ngoldberger
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tia.bbg import LocalTerminal
from matplotlib import rc
rc('mathtext', default='regular')

class turbulence(object):

    def __init__(self, idx = ['eurusd curncy', 'audusd curncy','cadusd curncy','jpyusd curncy','brlusd curncy']):
        self.idx = idx
        
    def downloadData(self,tw):
        self.tw = tw
        self.d = pd.datetools.BDay(-self.tw).apply(pd.datetime.now())
        self.m = pd.datetools.BMonthBegin(-2).apply(pd.datetime.now())
        self.response = LocalTerminal.get_historical(self.idx, ['px_last'], start=self.d)
    
    def getReturns(self,prices, freq = 1):
        x = {}
        x['price'] = prices
        x['returns'] = (np.log(x['price']) - np.log(x['price'].shift(freq))).fillna(0).values
        x['pct_chg'] = (x['price'].pct_change()).fillna(0).values
        return x
    
    def mahalanobis(self, x):
        mu = np.average(x['returns'],0)
        Sigma = np.cov(np.transpose(x['returns'])) 
        sigmainv = np.linalg.inv(Sigma)
        turbulenceData = (np.dot((x['returns'][-1]-mu),(np.dot(sigmainv,(x['returns'][-1]-mu)))))**0.5
        return turbulenceData

    def graph(self,data):
        t = [pd.datetools.BDay(-i).apply(pd.datetime.now()) for i in range(len(data))]
        t.reverse()
        fig, ax1 = plt.subplots(1,1,figsize=(10,6))
        new_data = pd.DataFrame()
        new_data['Turbulence'] = data
        new_data['Average'] = pd.rolling_mean(new_data['Turbulence'],60)
        
        
#        ax1.bar(t[60:],new_data[60:].values)
#        ax1.set_ylabel('Turbulence', fontsize = 14)
#        ax1.set_title('Turbulence Level', fontsize = 16)
#        ax1.xaxis.set_tick_params(labelsize=12)
#        ax1.yaxis.set_tick_params(labelsize=12)
#        fig.autofmt_xdate(rotation=0, ha= 'center')
#        
        
        fig = plt.figure()
        ax  = new_data['Turbulence'].plot(kind='bar')
#        ax2 = ax.twinx()
#        ax2.plot(ax.get_xticks(),new_data['Average'])
        
        plt.show()
        return new_data

    def computeTurbulenceAndPlot(self,freq):
        df = self.response.as_frame()
        self.turbulenceRollingData = self.getRollingTurbulenceData(df, freq)
        self.graph(self.turbulenceRollingData)
        
    def getRollingTurbulenceData(self, df, freq, rollingWindow = 251):
        data = []        
        for i in range(0,len(df)-rollingWindow):
            try:
                data.append(self.getTurbulenceData(df[0+i:rollingWindow+i],freq))
            except:
                print('Error computing turbulence data.')
                pass
        return data
        
    def getTurbulenceData(self,df,freq):
        x = self.getReturns(df,freq)
        turbulenceData = self.mahalanobis(x)
        return turbulenceData
        
if __name__ == '__main__':  

    idx= ['BUSG Index','BUHY Index','BUSC Index','BNDX Index','CRY Index',
          'SPX Index','BGER Index','BERC Index','BEUH Index','DAX Index',
          'BJPN Index','BJPY Index','NKY Index','BRIT Index','BGBP Index',
          'BGBH Index','UKX Index','BAUS Index','BAUD Index','AS51 Index',
          'BEMS Index','BIEM Index','BEAC Index','VEIEX US Equity']
    turbo = turbulence(idx)
    turbo.downloadData(2500)
    turbo.computeTurbulenceAndPlot(1)