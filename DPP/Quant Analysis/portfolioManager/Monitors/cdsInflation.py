# -*- coding: utf-8 -*-
"""
Created on Thu Sep 15 13:19:21 2016

@author: ngoldbergerr
"""
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import pylab
import numpy as np
from tia.bbg import v3api
from matplotlib import rc
import datetime as dt
rc('mathtext', default='regular')

class multigraphs(object):
    
    def __init__(self, path = 'L:\Rates & FX\Quant Analysis\portfolioManager\Monitors'):
        self.path = path

    def getHistDataFromBloomberg(self, tickers, init = dt.datetime.today()-dt.timedelta(weeks=104), end = dt.datetime.today()-dt.timedelta(days=1)):
            
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        try:
            response = LocalTerminal.get_historical(tickers, ['PX_LAST'], ignore_security_error=1, ignore_field_error=1, start = init, end = end, period='MONTHLY')
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False

        bloombergData = response.as_frame()
        
        return bloombergData
        

    def plotLines(self,series):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        plt.style.use('bmh') # fivethirtyeight, dark_background, bmh, grayscale
        
        ax.plot(series.index, series)  

        fig.set_size_inches(12, 8)
        plt.subplots_adjust(top=0.85)
        plt.xlabel('Fecha', fontsize=13)
        plt.xticks(fontsize=13)
        plt.ylabel('Spread (%)', fontsize=13)
        plt.yticks(fontsize=13)
        plt.title('Evolucion Diferencial Tasa Real y CDS (10Y)', fontsize=18, y=1.05)
        plt.legend(series.columns, loc='lower left', bbox_to_anchor=(1,0))
        
        plt.show()

    def plotBars(self,real,cds):
        fig = plt.figure()
#        ax = fig.add_subplot(111)
        plt.style.use('bmh') # fivethirtyeight, dark_background, bmh, grayscale

#        fig.set_size_inches(12, 8)
#        plt.subplots_adjust(top=0.85)
#        plt.xlabel('Fecha', fontsize=13)
#        plt.xticks(fontsize=13)
#        plt.ylabel('Spread (%)', fontsize=13)
#        plt.yticks(fontsize=13)
#        plt.title('Evolucion Diferencial Tasa Real y CDS (10Y)', fontsize=18, y=1.05)
#        plt.legend(real.columns, loc='lower left', bbox_to_anchor=(1,0))

        barcolor_real = '#d75b27'
        fig = plt.figure();
        ax = real.iloc[-1].plot(kind='bar', color = barcolor_real, figsize = (12,8), fontsize = 16)
        plt.ylabel('CDS | Tasa Real (%)',fontsize = 16)
        plt.yticks(fontsize = 13)
        plt.xlabel('',fontsize = 13)
        
        barcolor_cds = '#597b7c'
        ax2 = (-cds.iloc[-1]).plot(kind='bar', color = barcolor_cds, figsize = (12,8))
#        plt.ylabel('CDS',fontsize = 13)
        plt.yticks(fontsize = 16)

        plt.show()

if __name__ == '__main__':

    real = ['RR10CUS Index', 'RR10CMX Index', 'RR10CCL Index', 'RR10CPE  Index', 'RR10CCO  Index',
            'RR10CBR Index', 'RR10CAU Index']
    cds = ['MEX CDS USD SR 10Y D14 Corp', 'CHILE CDS USD SR 10Y D14 Corp',
           'PERU CDS USD SR 10Y D14 Corp', 'COLOM CDS USD SR 10Y D14 Corp',
           'BRAZIL CDS USD SR 10Y D14 Corp', 'AUSTLA CDS USD SR 5Y D14 Corp',
           'US731011AR30 Govt']
    swap = ['CHSWPC Curncy','CHSWPF Curncy','CHSWPI Curncy','CHSWP1 Curncy','CHSWP1F Curncy',
            'CHSWP2 Curncy','CHSWP3 Curncy','CHSWP4 Curncy','CHSWP5 Curncy','CHSWP6 Curncy',
            'CHSWP7 Curncy','CHSWP8 Curncy','CHSWP9 Curncy','CHSWP10 Curncy','CHSWP15  Curncy',
            'CHSWP20  Curncy']

           
    mg = multigraphs()
    real_rates = mg.getHistDataFromBloomberg(real)
    real_rates.columns = ['Chile','EE.UU.','Mexico','Brasil','Peru','Australia','Colombia']
    real_rates = real_rates.fillna(method='ffill')
    cds_rates = mg.getHistDataFromBloomberg(cds)/100
    cds_rates.columns = ['Chile','Brasil','Mexico','Peru','Colombia','EE.UU.','Australia']
    cds_rates['EE.UU.'] = 0
    cds_rates = cds_rates.fillna(method='backfill')
    diff_rate = real_rates - cds_rates
    mg.plotLines(diff_rate)
    mg.plotBars(real_rates,cds_rates)


    
    swapRatesChile = mg.getHistDataFromBloomberg(swap)
    swapRatesChile.columns = ['2','0.75','5','7','4','3','0.5','15','20','9','10','1.5','8','1','0.25','6']
#    swapRatesChile = [['0.25','0.5','0.75','1','2','3','4','5','6','7','8','9','10','15','20']]
    mg.plotLines(swapRatesChile)

#    response = LocalTerminal.get_historical(FX, ['px_last'], start=d)
##    print response.as_frame()
#    t = [pd.datetools.BDay(-i).apply(pd.datetime.now()) for i in range(31)]
#    x = pd.DataFrame(columns = ['price', 'returns'])
#    x['price'] = response.as_frame()['eurusd curncy']['px_last']
#    x['returns'] = np.log(x.price) - np.log(x.price.shift(1))
#    
##    plt.plot(t,x.price,t,x.returns)
##    plt.show()
#    
#    fig, ax1 = plt.subplots()
#    ax1.plot(t,x.price,'b-')
#    for tl in ax1.get_yticklabels():
#        tl.set_color('b')
##    ax2 = ax1.twinx()
##    ax2.plot(t,x.returns,'r-')
##    for tl in ax2.get_yticklabels():
##        tl.set_color('r')
#    fig.autofmt_xdate()
#    fig.set_size_inches(12, 8)
#    
#    plt.show()