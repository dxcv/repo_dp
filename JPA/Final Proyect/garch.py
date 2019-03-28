import pandas as pd
import numpy as np
import arch
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
import pandas_datareader.data as web

from pandas.tseries.offsets import BDay
from pandas.tools.plotting import lag_plot
from pandas.tools.plotting import autocorrelation_plot
from statsmodels.stats.diagnostic import acorr_ljungbox



class forecastGARCH(object):

    def __init__(self, idx = ['AAPL']):
        self.idx = idx

    def downloadData(self,st,en):
        self.st = st
        self.en = en
        data = web.get_data_google(self.idx, start=st, end=en)
        return data

    def getReturns(self,data):
        returns = data['Close'].pct_change().dropna()
        return returns

# The GARCH model follows the form: \sigma^2_t = \omega + \alpha*a^2_{t-1} +\beta*sigma^2_{t-1}

    def garchModel(self, returns):
        model = arch.arch_model(returns, p=1, o=1, q=1)
#        model = arch.arch_model(returns, dist = 'StudentsT') # Switch to T-Students distribution
        results = model.fit()
        parameters = results.params
        return parameters, results, model
    
    def garchForecast(self, omega, alpha, gamma, beta, sigma, t):
        forecast=np.zeros(t)
        vol=sigma**2
        for i in range(0,t):
            forecast[i]=omega+(alpha+gamma/2+beta)*vol
            vol=forecast[i]
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
        omega, alpha, gamma, beta = np.array(parameters[1:5])        
        fDate = results.conditional_volatility.index[-1]
        dates = pd.date_range(fDate, periods = forecast_window, freq=BDay())   
        print(dates)
        forecast = pd.DataFrame(self.garchForecast(omega, alpha, gamma, beta, sigma, forecast_window), index = dates)
        df = pd.DataFrame(results.conditional_volatility, index = np.concatenate([results.conditional_volatility.index, dates]))
        df.loc[:, 'LT_Volatility'] = (omega/(1-alpha-beta-gamma/2))**0.5
        df = pd.concat([df, forecast], axis = 1)
        df.columns = ['Conditional','Long Term','Forecasted']
#        df.columns = ['Conditional','Forecasted']
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
    st = dt.datetime(2007,1,1)
    en = dt.datetime(2017,7,1)
    ts = g.getReturns(g.downloadData(st,en))
    parameters, results, model = g.garchModel(ts)
    print(parameters)
    forecast = model.simulate(np.array(parameters),500)
    ax = g.plotForecastedVolatility(results,model, forecast_window=100)
    g.testPlots(results.resid, results.conditional_volatility)