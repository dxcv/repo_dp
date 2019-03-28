# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 13:37:15 2016

@author: ngoldberger
"""

import numpy as np
#from tia.bbg import LocalTerminal
import pandas as pd
import scipy.optimize
from pylab import *
import seaborn

class resampledAllocation(object):
    
    def __init__(self, tickers = ['WFC US Equity', 'AAPL US Equity', 'KO UN Equity', 'VZ US Equity', 'GOOG US Equity','GS UN Equity'], cap = {}):
        self.tickers = tickers
        
#    def load_data_bbg(self):
#        data, self.symbols = self.downloadData(self.tickers,500)
#        prices_out = data.as_frame()
#        prices_out.columns = prices_out.columns.levels[0] 
#        return self.symbols, prices_out
#
#    def downloadData(self,assets,tw):
#        self.tw = tw
#        self.idx = assets
#        self.d = pd.datetools.BDay(-self.tw).apply(pd.datetime.now())
#        self.response = LocalTerminal.get_historical(self.idx, ['px_last'], start=self.d)
#        data = self.response
#        symbols = []
#        for i in assets:    
#            symbols.append(LocalTerminal.get_reference_data( i, 'ID_BB_SEC_NUM_DES').as_frame()['ID_BB_SEC_NUM_DES'][0])
#        return data, symbols

    def computeAssetsMeanVariance(self,data):
        ret = data.pct_change()
        self.mu = ret.mean()
        self.omega = ret.cov()
        return self.mu, self.omega
        
    def generateSimulations(self,mu,omega):
        ret_hat = pd.DataFrame(np.random.multivariate_normal(mu, omega, 500),columns = self.mu.index)
        mu_hat = ret_hat.mean()
        omega_hat = ret_hat.cov()
        return mu_hat, omega_hat
        
    def portfolioOptimization(self,mu,omega):
        frontier_mean, frontier_var, frontier_weights = [], [], []
        n = len(mu)	# Number of assets in the portfolio
        def portfolioVariance(weights,mu,omega,r):
            return np.dot(np.dot(np.transpose(weights),omega),weights) + 50*abs(r - np.dot(np.transpose(weights),mu))
        for r in linspace(min(mu), max(mu), num=20): # Iterate through the range of returns on Y axis
            weights = ones(len(mu))/len(mu)*0
            b_ = [(0,1) for i in range(n)]
            c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
            optimized = scipy.optimize.minimize(portfolioVariance, weights, (mu,omega,r), method='SLSQP', constraints=c_, bounds=b_)
            frontier_mean.append(sum(optimized.x*mu)*365)               					      # return
            frontier_var.append(np.sqrt(np.dot(np.dot(np.transpose(optimized.x),omega),optimized.x)*365))	# min-variance based on optimized weights
            frontier_weights.append(optimized.x)
        return frontier_mean, frontier_var, frontier_weights
     
    def plotEfficientFrontier(self,mean,volatility,avg_mean,avg_volatility):
        df1 = pd.DataFrame([mean[0:],volatility[0:],zeros(len(volatility))],index = ['Mean','Volatility','Avg']).transpose()
        df2 = pd.DataFrame([avg_mean,avg_volatility,ones(len(avg_volatility))],index = ['Mean','Volatility','Avg']).transpose()
        df = df1.append(df2)
#        seaborn.regplot('Volatility','Mean',data, lowess = True)
        seaborn.lmplot("Volatility", "Mean", data=df, fit_reg=False, hue="Avg", legend = False)
        return True

    def reSampledFrontier(self,mu,omega,nrep):
        MU, SIGMA = [], []
        weights = pd.DataFrame()
        for n in range(0,nrep):
            mu_hat, omega_hat = self.generateSimulations(mu,omega)
#            fron_mean, fron_var, fron_weights = self.portfolioOptimization(mu_hat,omega_hat)
            fron_mean, fron_var, fron_weights = self.portfolioOptimization(mu_hat,omega)
#            fron_mean, fron_var, fron_weights = self.portfolioOptimization(mu,omega_hat)
            weights[n] = fron_weights
            MU.append(fron_mean)
            SIGMA.append(fron_var)
        MU = np.concatenate(MU,axis=0)
        SIGMA = np.concatenate(SIGMA,axis=0)
        avg_w = [weights.transpose()[i].mean() for i in range(0,len(weights))]
        avg_ret = np.array([np.dot(avg_w[i],mu.values*365) for i in range(0,len(avg_w))])
        avg_sigma = np.array([np.sqrt(np.dot(np.dot(avg_w[i],omega.values*365),np.transpose(avg_w[i]))) for i in range(0,len(avg_w))])
        return MU, SIGMA, avg_ret, avg_sigma, avg_w
        

if __name__ == '__main__':
    rA = resampledAllocation()
    s, p = rA.load_data_bbg()
    mu, omega = rA.computeAssetsMeanVariance(p)
#    mu_hat, omega_hat = rA.generateSimulations(mu,omega)
    pr, pv, pw = rA.portfolioOptimization(mu,omega)
    sim_mu, sim_sigma, avg_mu, avg_sigma, avg_w = rA.reSampledFrontier(mu,omega,60)    
    rA.plotEfficientFrontier(sim_mu, sim_sigma, avg_mu, avg_sigma)
    weights_resample = pd.DataFrame(avg_w, columns = s).plot(kind='area', ylim=[0,1])
    
