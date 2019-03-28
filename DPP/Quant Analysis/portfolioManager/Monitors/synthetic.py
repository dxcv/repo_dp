# -*- coding: utf-8 -*-
"""
Created on Wed Aug 24 11:10:42 2016

@author: ngoldbergerr
"""

import sys
sys.path.insert(0,"""F:\Quant Analysis\portfolioManager""")
sys.path.insert(0,"""C:\Python27\Lib\site-packages""")

#from securities import security
#from yieldCurve import nelsonSiegel, lineal_curve
import datetime
import pandas as pd
import datetime as dt
import numpy as np
from tia.bbg import v3api
#import itertools
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm


class forwardSwap(object):
    def __init__(self):
        x = []

### Daily Table
    #Annual Total Return, Period Total Return, USD On-Shore Implicit Rate

    def get_swap_curves(self,currency):
        bbg_ticker = {'CLP':'YCSW0193 Index','COP':'YCSW0329 Index','BRL':'YCMM0119 Index','MXN':'YCSW0083 Index',
                      'USD':'YCSW0023 Index','JPY':'YCSW0013 Index','EUR':'YCSW0045 Index','AUD':'YCSW0001 Index'}
                      
        LocalTerminal = v3api.Terminal('localhost', 8194)   
        try:
            response = LocalTerminal.get_reference_data(bbg_ticker[currency], ['CURVE_TENOR_RATES'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False

        data_retrieved = response.as_frame()['CURVE_TENOR_RATES'][0]
        swap_curve = pd.DataFrame(data = [data_retrieved['Ask Yield'], data_retrieved['Mid Yield'], data_retrieved['Bid Yield']]).transpose()
        swap_curve.index = [1,90,180,270,360,18*30,2*360,3*360,4*360,5*360,6*360,7*360,8*360,9*360,10*360,15*360,20*360]
        sc = pd.DataFrame(data = swap_curve, index = np.arange(1,20*360))
        sc = sc.interpolate(method = 'linear')
        return sc

    def get_zero_swaps(self):
        self.chile = ['S0193Z 2D BLC2 Curncy','S0193Z 1W BLC2 Curncy',
                 'S0193Z 2W BLC2 Curncy','S0193Z 1M BLC2 Curncy','S0193Z 2M BLC2 Curncy','S0193Z 3M BLC2 Curncy',
                 'S0193Z 4M BLC2 Curncy','S0193Z 5M BLC2 Curncy','S0193Z 6M BLC2 Curncy',
                 'S0193Z 7M BLC2 Curncy','S0193Z 8M BLC2 Curncy','S0193Z 9M BLC2 Curncy','S0193Z 10M BLC2 Curncy',
                 'S0193Z 11M BLC2 Curncy','S0193Z 1Y BLC2 Curncy','S0193Z 15M BLC2 Curncy','S0193Z 18M BLC2 Curncy',
                 'S0193Z 21M BLC2 Curncy','S0193Z 2Y BLC2 Curncy','S0193Z 33M BLC2 Curncy','S0193Z 3Y BLC2 Curncy',
                 'S0193Z 4Y BLC2 Curncy','S0193Z 5Y BLC2 Curncy','S0193Z 6Y BLC2 Curncy','S0193Z 7Y BLC2 Curncy',
                 'S0193Z 8Y BLC2 Curncy','S0193Z 9Y BLC2 Curncy','S0193Z 10Y BLC2 Curncy','S0193Z 15Y BLC2 Curncy']

        self.us = ['USDR2T   Curncy','US0001W  Index','US0001M  Index','US0002M  Index','G0052Z 3M BLC2 Curncy',
              'G0052Z 6M BLC2 Curncy','G0052Z 1Y BLC2 Curncy','G0052Z 2Y BLC2 Curncy','G0052Z 3Y BLC2 Curncy','G0052Z 4Y BLC2 Curncy',
              'G0052Z 5Y BLC2 Curncy','G0052Z 6Y BLC2 Curncy','G0052Z 7Y BLC2 Curncy','G0052Z 8Y BLC2 Curncy','G0052Z 9Y BLC2 Curncy',
              'G0052Z 10Y BLC2 Curncy','G0052Z 15Y BLC2 Curncy']
        
        LocalTerminal = v3api.Terminal('localhost', 8194)   
        try:
            response_cl = LocalTerminal.get_reference_data(self.chile, ['PX_ASK'], ignore_security_error = 1, ignore_field_error = 1)
            response_us = LocalTerminal.get_reference_data(self.us, ['PX_BID'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return False

        data_cl = response_cl.as_frame()
        chile = pd.DataFrame(data_cl['PX_ASK'])
        chile.columns = ['Swap Spread']
        chile['days'] = [10*30,10*12*30,11*30,15*30,15*12*30,18*30,1*30,7,1*12*30,21*30,2,2*30,14,2*12*30,33*30,3*30,3*12*30,4*30,4*12*30,5*30,5*12*30,6*30,6*12*30,7*30,7*12*30,8*30,8*12*30,9*30,9*12*30]        
        chile.index = chile['days']
        chile = chile.sort_values(['days'])
        del chile['days']

        data_us = response_us.as_frame()
        usa = pd.DataFrame(data_us['PX_BID'])
        usa.columns = ['Swap Spread']
        usa['days'] = [10*12*30,15*12*30,1*12*30,2*12*30,3*30,3*12*30,4*12*30,5*12*30,6*30,6*12*30,7*12*30,8*12*30,9*12*30,1*30,7,2*30,2]
        usa.index = usa['days']
        usa = usa.sort_values(['days'])
        del usa['days']

        swap_spreads = chile - usa
        swap_spreads = swap_spreads.reindex(index = np.arange(min(swap_spreads.index),max(swap_spreads.index)+1))
        swap_spreads = swap_spreads.interpolate()
        usa = usa.reindex(index = np.arange(min(usa.index),max(usa.index)+1))
        usa = usa.interpolate()
        chile = chile.reindex(index = np.arange(min(chile.index),max(chile.index)+1))
        chile = chile.interpolate()
        return swap_spreads, chile, usa

    def getForwardReturn(self,currency_short,currency_long):        
        cross = currency_short+currency_long
        if cross == 'USDCLP' or cross == 'CLPUSD':
            tickers = ['CHN1W LAST Curncy','CHN1M LAST Curncy','CHN2M LAST Curncy',
                       'CHN3M LAST Curncy','CHN6M LAST Curncy','CHN9M LAST Curncy','CHN12M LAST Curncy',
                       'CHN18M LAST Curncy','CHN2Y LAST Curncy','CHN3Y LAST Curncy','CHN5Y LAST Curncy']
            ccy_ticker = ['USDCLP Curncy']

        LocalTerminal = v3api.Terminal('localhost', 8194)
        try:
            response = LocalTerminal.get_reference_data(tickers, ['PX_BID','PX_ASK','DAYS_TO_MTY'], ignore_security_error = 1, ignore_field_error = 1)
            ccy_response = LocalTerminal.get_reference_data(ccy_ticker, ['PX_MID'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return False

        fx_cross = ccy_response.as_frame()
        fx_data_retrieved = response.as_frame().sort_values('DAYS_TO_MTY')
        fx_data_retrieved['PX_BID'] = fx_data_retrieved['PX_BID']/fx_cross['PX_MID'].values*360/fx_data_retrieved['DAYS_TO_MTY']
        fx_data_retrieved['PX_ASK'] = fx_data_retrieved['PX_ASK']/fx_cross['PX_MID'].values*360/fx_data_retrieved['DAYS_TO_MTY']
        fx_data_retrieved.index = fx_data_retrieved['DAYS_TO_MTY']
        del fx_data_retrieved['DAYS_TO_MTY']
        return fx_data_retrieved

    def getTotalReturns(self):
#        swap_curves = self.get_swap_curves('CLP')
        swap_spread, chile, usa = self.get_zero_swaps()
        forward_returns = self.getForwardReturn('USD','CLP')
        forward_returns.index = [int(forward_returns.index[i]) for i in range(0,len(forward_returns))]
#        total_return = pd.DataFrame(data = [forward_returns['PX_BID'], swap_spread[swap_spread.index == forward_returns.index]['PX_BID']])
        total_return = pd.DataFrame(data = forward_returns['PX_BID']*100)
        total_return['Spread'] = swap_spread['Swap Spread']
        total_return.columns = ['FX','Spread']
        total_return['Annual Total Return'] = total_return['FX'] - total_return['Spread']
        total_return['Period Total Return'] = total_return['Annual Total Return']/total_return.index
        total_return['USD On-Shore Implicit Rate'] = chile['Swap Spread']-total_return['FX']
        return total_return[1:]
        
### Historical Data
    def histSpread(self, dateInitial = '2015-10-02', dateFinal = dt.datetime.today()):
       cl = ['S0193Z 1M BLC2 Curncy','S0193Z 2M BLC2 Curncy','S0193Z 3M BLC2 Curncy','S0193Z 6M BLC2 Curncy','S0193Z 1Y BLC2 Curncy',
             'S0193Z 2Y BLC2 Curncy','S0193Z 3Y BLC2 Curncy','S0193Z 4Y BLC2 Curncy','S0193Z 5Y BLC2 Curncy']
       us = ['US0001M  Index','US0002M  Index','G0052Z 3M BLC2 Curncy','G0052Z 6M BLC2 Curncy','G0052Z 1Y BLC2 Curncy','G0052Z 2Y BLC2 Curncy','G0052Z 3Y BLC2 Curncy','G0052Z 4Y BLC2 Curncy',
              'G0052Z 5Y BLC2 Curncy']
       LocalTerminal = v3api.Terminal('localhost', 8194)
       try:
           response_cl = LocalTerminal.get_historical(cl, ['PX_ASK'], ignore_security_error = 1, ignore_field_error = 1, start = dateInitial, end = dateFinal)
           response_us = LocalTerminal.get_historical(us, ['PX_LAST'], ignore_security_error = 1, ignore_field_error = 1, start = dateInitial, end = dateFinal)
       except:
           print("Unexpected error:", sys.exc_info()[0])   
           return False       

       rates_cl = response_cl.as_frame()
       rates_cl.columns = rates_cl.columns.levels[0]
       rates_cl = self.set_column_sequence(rates_cl,['S0193Z 1M BLC2 Curncy','S0193Z 2M BLC2 Curncy','S0193Z 3M BLC2 Curncy',
                                                     'S0193Z 6M BLC2 Curncy','S0193Z 1Y BLC2 Curncy','S0193Z 2Y BLC2 Curncy',
                                                     'S0193Z 3Y BLC2 Curncy','S0193Z 4Y BLC2 Curncy','S0193Z 5Y BLC2 Curncy'])
       rates_cl.columns = ['1M','2M','3M','6M','1Y','2Y','3Y','4Y','5Y']
       rates_us = response_us.as_frame()
       rates_us.columns = rates_us.columns.levels[0]
       rates_us = self.set_column_sequence(rates_us,['US0001M  Index','US0002M  Index','G0052Z 3M BLC2 Curncy','G0052Z 6M BLC2 Curncy',
                                                     'G0052Z 1Y BLC2 Curncy','G0052Z 2Y BLC2 Curncy','G0052Z 3Y BLC2 Curncy',
                                                     'G0052Z 4Y BLC2 Curncy','G0052Z 5Y BLC2 Curncy'])
       rates_us.columns = ['1M','2M','3M','6M','1Y','2Y','3Y','4Y','5Y']
       spread = pd.DataFrame(rates_cl - rates_us)
       spread = spread.interpolate()
       return spread, rates_cl, rates_us
       
       
    def histForwardReturn(self,currency_short,currency_long, dateInitial = '2015-10-02', dateFinal = dt.datetime.today()):
        cross = currency_short+currency_long
        if cross == 'USDCLP' or cross == 'CLPUSD':
            tickers = ['CHN1M LAST Curncy','CHN2M LAST Curncy','CHN3M LAST Curncy',
                       'CHN6M LAST Curncy','CHN12M LAST Curncy','CHN18M LAST Curncy',
                       'CHN2Y LAST Curncy','CHN3Y LAST Curncy','CHN5Y LAST Curncy']
            ccy_ticker = ['USDCLP Curncy']

        LocalTerminal = v3api.Terminal('localhost', 8194)
        try:
            response = LocalTerminal.get_historical(tickers, ['PX_BID'], ignore_security_error = 1, ignore_field_error = 1, start = dateInitial, end = dateFinal)
            ccy_response = LocalTerminal.get_historical(ccy_ticker, ['PX_MID'], ignore_security_error = 1, ignore_field_error = 1, start = dateInitial, end = dateFinal)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return False

        fx_spot = ccy_response.as_frame()
        fx_spot.columns = [cross]
        
        fwd_points = response.as_frame()
        fwd_points.columns = fwd_points.columns.levels[0]
        fwd_points = self.set_column_sequence(fwd_points,['CHN1M LAST Curncy','CHN2M LAST Curncy','CHN3M LAST Curncy',
                                                          'CHN6M LAST Curncy','CHN12M LAST Curncy','CHN18M LAST Curncy',
                                                          'CHN2Y LAST Curncy','CHN3Y LAST Curncy','CHN5Y LAST Curncy'])
        fwd_spot_matrix = pd.DataFrame([fx_spot[cross].values]*9).transpose()
        fwd_spot_matrix.columns = fwd_points.columns
        fwd_spot_matrix.index = fx_spot.index
        fwd_points.reindex(index=fwd_spot_matrix.index)
        
        days = [30,60,90,180,360,18*30,24*30,36*30,60*30]
        fwd_days_matrix = pd.DataFrame(np.tile(days,(len(fwd_points),1)))
        fwd_days_matrix.columns = fwd_points.columns
        fwd_days_matrix.index = fwd_points.index
        
        fwd_return = fwd_points/fwd_spot_matrix*360/fwd_days_matrix
        
        return fwd_return

    def historicalReturn(self,dateInitial = '2015-10-02', dateFinal = dt.datetime.today()):
        historical_spread, rates_cl, rates_us = self.histSpread()
        historical_fwd = self.histForwardReturn('USD','CLP')*100
        historical_fwd.columns = historical_spread.columns
        historical_return = historical_fwd - historical_spread
        historical_return = historical_return.interpolate()
        return historical_return

    def historicalUSDimplicitRate(self,dateInitial = '2015-10-02', dateFinal = dt.datetime.today()):
        historical_spread, rates_cl, rates_us = self.histSpread()
        historical_fwd = self.histForwardReturn('USD','CLP')*100
        historical_fwd.columns = rates_cl.columns
        historical_USD_onshore = rates_cl - historical_fwd
        historical_USD_onshore = historical_USD_onshore.interpolate()
        return historical_USD_onshore       
### Support Functions

    def set_column_sequence(self, dataframe, seq, front=True):
        '''Takes a dataframe and a subsequence of its columns,
           returns dataframe with seq as first columns if "front" is True,
           and seq as last columns if "front" is False.
        '''
        cols = seq[:] # copy so we don't mutate seq
        for x in dataframe.columns:
            if x not in cols:
                if front: #we want "seq" to be in the front
                    #so append current column to the end of the list
                    cols.append(x)
                else:
                    #we want "seq" to be last, so insert this
                    #column in the front of the new column list
                    #"cols" we are building:
                    cols.insert(0, x)
        return dataframe[cols]

    def plotTimeSeriesUSDrates(self, timeSeries):
#        years = mdates.YearLocator()   # every year
        months = mdates.MonthLocator()  # every month
#        yearsFmt = mdates.DateFormatter('%Y')
#        monthsFmt = mdates.DateFormatter('%m / %y')        
        
        f, axarr = plt.subplots(2, sharex=True)
        plt.style.use('bmh')
        f.set_size_inches(15, 10)
        axarr[0].plot(timeSeries.index, timeSeries.loc[:,'1M':'6M'])
        axarr[0].set_xlim(0,310)
        axarr[0].set_title('USD On-Shore Synthetic Rate', fontsize = 16)
        axarr[0].legend(['1M','2M','3M','6M'],loc=4)
        axarr[1].plot(timeSeries.index, timeSeries.loc[:,'1Y':'5Y'])
        axarr[1].legend(['1Y','2Y','3Y','4Y','5Y'],loc=4)
        axarr[1].set_xlabel('Date', fontsize = 14)
        axarr[0].set_ylabel('Rate (%)', fontsize = 14)
        axarr[1].set_ylabel('Rate (%)', fontsize = 14)
#        axarr[1].xaxis.set_major_locator(years)
#        axarr[1].xaxis.set_major_formatter(yearsFmt)
        axarr[1].xaxis.set_minor_locator(months)
#        axarr[1].xaxis.set_minor_formatter(monthsFmt)

        datemin = datetime.date(timeSeries.index.min().year, timeSeries.index.min().month, timeSeries.index.min().day)
        datemax = datetime.date(timeSeries.index.max().year, timeSeries.index.min().month+2, timeSeries.index.min().day)
        axarr[1].set_xlim(datemin, datemax)

        plt.show()
        return True

    def plotTimeSeriesUSDshortRate(self, timeSeries):
        months = mdates.MonthLocator()  # every month

        LocalTerminal = v3api.Terminal('localhost', 8194)   
        try:
            response = LocalTerminal.get_historical(['US0003M Index'], ['PX_LAST'], ignore_security_error = 1, ignore_field_error = 1, start = timeSeries.index.min(), end = timeSeries.index.max())
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False

        libor = response.as_frame()
        del timeSeries['1Y']
        del timeSeries['2Y']
        del timeSeries['3Y']
        del timeSeries['4Y']
        del timeSeries['5Y']

        timeSeries['LIBOR 3M'] = libor.interpolate(method = 'linear')

        f, axarr = plt.subplots(1, sharex=True)
        plt.style.use('bmh')
        f.set_size_inches(12, 8)
        axarr.plot(timeSeries.index, timeSeries.loc[:,'1M':'LIBOR 3M'])
        axarr.set_xlim(0,310)
        axarr.set_title('USD On-Shore Synthetic Rate', fontsize = 16)
        axarr.legend(['1M','2M','3M','6M','3M LIBOR USD'],loc=4)
        axarr.set_ylabel('Rate (%)', fontsize = 14)

        axarr.xaxis.set_minor_locator(months)

        datemin = datetime.date(timeSeries.index.min().year, timeSeries.index.min().month, timeSeries.index.min().day)
        datemax = datetime.date(timeSeries.index.max().year, timeSeries.index.min().month+2, timeSeries.index.min().day)
        axarr.set_xlim(datemin, datemax)

        plt.show()
        return True


if __name__ == '__main__':
    fs = forwardSwap()
#    total = fs.getTotalReturns() # Tabla con el retorno y tasa implicita en USD on-shore para el dia
#    hisTotal = fs.historicalReturn() # Retorno historico de sinteticos a distintos plazos
    histUSDonshore = fs.historicalUSDimplicitRate() # Tasa USD on-shore implicita a distintos plazos
    cycle, trend = sm.tsa.filters.hpfilter(histUSDonshore, 2)
    fs.plotTimeSeriesUSDrates(trend)
#    fs.plotTimeSeriesUSDshortRate(histUSDonshore)
#    fs.plotTimeSeriesUSDrates(hisTotal)
    
    