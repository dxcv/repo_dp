# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 11:02:08 2016

@author: ngoldberger
"""

from numpy import matrix, array, zeros, empty, sqrt, ones, dot, append, mean, cov, transpose, linspace, nan_to_num, log
from numpy.linalg import inv, pinv
from tia.bbg import LocalTerminal
import pandas as pd
from pylab import *
import scipy.optimize

class frontier(object):
    
    def __init__(self, tickers = ['WFC US Equity', 'AAPL US Equity', 'KO UN Equity', 'VZ US Equity', 'GOOG US Equity'], cap = {}):
#       cap = {'^GSPC':14.90e12, 'XOM':403.02e9, 'AAPL':392.90e9, 'MSFT':283.60e9, 'JNJ':243.17e9, 'GE':236.79e9, 'GOOG':292.72e9, 'CVX':231.03e9, 'PG':214.99e9, 'WFC':218.79e9}
        self.tickers = tickers
        self.caps = cap
        
    def load_data_bbg(self):
        data, symbols = self.downloadData(self.tickers,500)
        prices_out = data.as_frame()
        caps_out = []
        if bool(self.caps):
            for s in symbols:
                caps_out.append(self.caps[s])

        return symbols, prices_out, caps_out

    def downloadData(self,assets,tw):
        self.tw = tw
        self.idx = assets
        self.d = pd.datetools.BDay(-self.tw).apply(pd.datetime.now())
        self.m = pd.datetools.BMonthBegin(-2).apply(pd.datetime.now())
        self.response = LocalTerminal.get_historical(self.idx, ['px_last'], start=self.d)
        data = self.response
        symbols = []
        for i in assets:    
            symbols.append(LocalTerminal.get_reference_data( i, 'ID_BB_SEC_NUM_DES').as_frame()['ID_BB_SEC_NUM_DES'][0])
        return data, symbols

    # Function takes historical stock prices together with market capitalizations and calculates
    # names       - array of assets' names
    # prices      - array of historical (daily) prices
    # caps	      - array of assets' market capitalizations
    # returns:
    # names       - array of assets' names
    # expreturns  - expected returns based on historical data
    # covars	  - covariance matrix between assets based on historical data
    def assets_meanvar(self, names, prices, caps = []):

      returns = transpose(nan_to_num(array(log(prices[1:])) - array(log(prices[:-1]))))
      rows, cols = returns.shape
      expreturns = array([])
      for r in range(rows):
    		expreturns = append(expreturns, mean(returns[r]))
      covars = cov(returns)			      # calculate covariances	
      expreturns = (1+expreturns)**250-1	# Annualize expected returns
      covars = covars * 250				# Annualize covariances
      names = prices.columns.levels[0]
      return names, expreturns, covars

    # Calculates portfolio mean return
    def port_mean(self, W, R):
    	return sum(R*W)

    # Calculates portfolio variance of returns
    def port_var(self, W, C):
    	return dot(dot(W, C), W)

    # Combination of the two functions above - mean and variance of returns calculation
    def port_mean_var(self, W, R, C):
    	return self.port_mean(W, R), self.port_var(W, C)

    # Given risk-free rate, assets returns and covariances, this function calculates
    # mean-variance frontier and returns its [x,y] points in two arrays
    def solve_frontier(self, R, C, rf):
    	def fitness(W, R, C, r):
    		# For given level of return r, find weights which minimizes
    		# portfolio variance.
    		mean, var = self.port_mean_var(W, R, C)
    		# Big penalty for not meeting stated portfolio return effectively serves as optimization constraint
    		penalty = 50*abs(mean-r)
    		return var + penalty
    	frontier_mean, frontier_var, frontier_weights = [], [], []
    	n = len(R)	# Number of assets in the portfolio
    	for r in linspace(min(R), max(R), num=20): # Iterate through the range of returns on Y axis
    		W = ones([n])/n		# start optimization with equal weights
    		b_ = [(0,1) for i in range(n)]
    		c_ = ({'type':'eq', 'fun': lambda W: sum(W)-1. })
    		optimized = scipy.optimize.minimize(fitness, W, (R, C, r), method='SLSQP', constraints=c_, bounds=b_)	
    		if not optimized.success: 
    			raise BaseException(optimized.message)
    		# add point to the min-var frontier [x,y] = [optimized.x, r]
    		frontier_mean.append(r)							# return
    		frontier_var.append(self.port_var(optimized.x, C))	# min-variance based on optimized weights
    		frontier_weights.append(optimized.x)
    	return array(frontier_mean), array(frontier_var), frontier_weights

    # Given risk-free rate, assets returns and covariances, this 
    # function calculates weights of tangency portfolio with respect to 
    # sharpe ratio maximization
    def solve_weights(self, R, C, rf):
    	def fitness(W, R, C, rf):
    		mean, var = self.port_mean_var(W, R, C)	# calculate mean/variance of the portfolio
    		util = (mean - rf) / sqrt(var)		# utility = Sharpe ratio
    		return 1/util					# maximize the utility, minimize its inverse value
    	n = len(R)
    	W = ones([n])/n						# start optimization with equal weights
    	b_ = [(0.,1.) for i in range(n)]	# weights for boundaries between 0%..100%. No leverage, no shorting
    	c_ = ({'type':'eq', 'fun': lambda W: sum(W)-1. })	# Sum of weights must be 100%
    	optimized = scipy.optimize.minimize(fitness, W, (R, C, rf), method='SLSQP', constraints=c_, bounds=b_)	
    	if not optimized.success: 
    		raise BaseException(optimized.message)
    	return optimized.x
     
    def optimize_and_display(self, names, R, C, rf, color = 'black'):
      W = self.solve_weights(R, C, rf)
      mean, var = self.port_mean_var(W, R, C)				      # calculate tangency portfolio
      f_mean, f_var, f_weights = self.solve_frontier(R, C, rf)		# calculate min-var frontier
    	# display min-var frontier
      n = len(names)
      fig, ax = plt.subplots()
      scatter([C[i,i]**.5 for i in range(n)], R, marker='x',color=color)  # draw assets   
      for i in range(n): 								    # draw labels
          text(C[i,i]**.5, R[i], '  %s'%names[i], verticalalignment='center', color='blue') 
      scatter(var**.5, mean, marker='o', color='red')			# draw tangency portfolio
      plot(f_var**.5, f_mean, color=color)					# draw min-var frontier
      xlabel('Volatility ($\sigma$)', fontsize = 16), ylabel('Expected Return ($r$)', fontsize = 16)
      xlim(0, max(f_mean)*2.5)
      fig.set_size_inches(11.5, 7.5)
      grid(True)
      plt.show()
    
if __name__ == '__main__':
        f = frontier()
        s,p,c = f.load_data_bbg()
        names, expreturns, covars = f.assets_meanvar(s,p,c)
        f.optimize_and_display(names, expreturns, covars, 0)