# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 09:14:07 2016

@author: ngoldberger
"""

import pandas as pd
import numpy as np
import arch
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from tia.bbg import LocalTerminal
from pandas.tseries.offsets import BDay
from pandas.tools.plotting import lag_plot
from pandas.tools.plotting import autocorrelation_plot
from statsmodels.stats.diagnostic import acorr_ljungbox



class forecastGARCH(object):

    def __init__(self, idx = ['SPX Index']):
        self.idx = idx

    def downloadData(self,tw):
        self.tw = tw
        self.d = pd.datetools.BDay(-self.tw).apply(pd.datetime.now())
        self.m = pd.datetools.BMonthBegin(-2).apply(pd.datetime.now())
        self.response = LocalTerminal.get_historical(self.idx, ['px_last'], start=self.d)
        return self.response.as_frame()

    def getReturns(self,prices, freq = 1):
        returns = (np.log(prices) - np.log(prices.shift(freq))).fillna(0)
#        x['pct_chg'] = (x['price'].pct_change()).fillna(0)
        return returns

# The GARCH model follows the form: \sigma^2_t = \omega + \alpha*a^2_{t-1} +\beta*sigma^2_{t-1}

    def garchModel(self, returns):
        model = arch.arch_model(returns)
#        model = arch.arch_model(returns, dist = 'StudentsT') # Switch to T-Students distribution
        results = model.fit(update_freq=5)
        parameters = results.params
        return parameters, results, model
    
    def garchForecast(self, omega, alpha, beta, sigma, t):
        VL = omega/(1-alpha-beta)
        T = np.array(range(0,t+1))
        forecast = VL + (sigma**2 - VL)*(alpha + beta)**T
        return forecast**0.5
    
    def testLjungBox(self, resids, conditionalVol):
        df = pd.DataFrame(acorr_ljungbox(resids/conditionalVol)[1])
        df.columns = ['p-value']
        ax = df.plot(title = 'Lljung Box Test', fontsize = 12, figsize = (12, 7))
        ax.title.set_fontsize(16)
        return ax

    def lagPlot(self, series):
        fig, ax = plt.subplots(1,1,figsize=(12,7))         
        ax = lag_plot(series)
        ax.set_title('Lag Scatter Plot')
        ax.title.set_fontsize(16)
        return ax
    
    def autoCorr(self, series):
        fig, ax = plt.subplots(1,1,figsize=(12,7))
        ax = autocorrelation_plot(series)
        ax.set_title('Autocorrelation Plot')
        ax.title.set_fontsize(16)
        return ax
    
    def testPlots(self, resids, conditionalVol):
        self.testLjungBox(resids, conditionalVol)
        self.lagPlot(resids/conditionalVol)
        self.autoCorr(resids/conditionalVol)
    
    def plotForecastedVolatility(self, results, model, forecast_window = 20):
        sigma = np.array(results.conditional_volatility)[-1]
        omega, alpha, beta = np.array(parameters[1:4])        
        fDate = results.conditional_volatility.index[-1]
        dates = pd.date_range(fDate, periods = forecast_window + 1, freq=BDay())        
        forecast = pd.DataFrame(self.garchForecast(omega, alpha, beta, sigma, forecast_window), index = dates)
        df = pd.DataFrame(results.conditional_volatility, index = np.concatenate([results.conditional_volatility.index, dates]))
        df.loc[:, 'LT_Volatility'] = (omega/(1-alpha-beta))**0.5
        df = pd.concat([df, forecast], axis = 1)
        df.columns = ['Conditional','Long Term','Forecasted']
        ax = df.plot(title = 'Volatility', fontsize = 12, figsize = (12, 7))
        ax.title.set_fontsize(16)
        years = mdates.YearLocator()
        months = mdates.MonthLocator()
        yearsFmt = mdates.DateFormatter('%Y')
        monthsFmt = mdates.DateFormatter('%b')
        ax.grid(which = 'Both')
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)
        ax.xaxis.set_minor_locator(months)
        plt.setp(ax.get_xticklabels(), rotation=0, horizontalalignment='center')
        return ax


if __name__ == '__main__':
    g = forecastGARCH()
    ts = g.getReturns(g.downloadData(1000),1)
    parameters, results, model = g.garchModel(ts)
#    forecast = model.simulate(np.array(parameters),500)
    ax = g.plotForecastedVolatility(results,model, forecast_window=22)
#    g.testPlots(results.resid, results.conditional_volatility)