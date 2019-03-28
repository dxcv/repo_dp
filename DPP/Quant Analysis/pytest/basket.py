# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 17:25:09 2017

@author: ngoldbergerr
"""

#import pandas as pd
import bloomberg
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats, integrate
from scipy.optimize import minimize


b = bloomberg.bloomberg()
currencies = b.getHistDataFromBloomberg(['AUDUSD Curncy','BRLUSD Curncy','CADUSD Curncy','CLPUSD Curncy','CNYUSD Curncy','COPUSD Curncy', 'EURUSD Curncy', 'KRWUSD Curncy',
                                         'GBPUSD Curncy','JPYUSD Curncy','MXNUSD Curncy','NZDUSD Curncy','TRYUSD Curncy','ZARUSD Curncy', 'PENUSD Curncy', 'CHFUSD Curncy',
                                         'DKKUSD Curncy','NOKUSD Curncy','PLNUSD Curncy', 'SEKUSD Curncy','ARSUSD Curncy'], init = '2017-01-01', end = '2017-06-05')
FXreturns = currencies.pct_change().fillna(0)

def portRisk(w,assets):
    Sigma = assets.cov().values
    volatility = np.sqrt(np.dot(np.dot(np.transpose(w),Sigma),w))
    MCR = Sigma.dot(w)/volatility
    CTR = np.transpose(w)*MCR
    return volatility, CTR

def portCTR(assets,w):
    vol, CTR = portRisk(assets,w)
    return sum(np.abs(np.diff(CTR)))

def riskParity(assets):
    N = len(np.transpose(assets))
    x0 = np.ones(N)/N
    cons = ({'type':'eq', 'fun': lambda x: sum(x) - 1})
    rpw = minimize(portCTR, x0, args = assets, method='Nelder-Mead', constraints = cons, 
                   options={'xtol':1e-8, 'disp':True, 'maxiter': N*500})
    weights = rpw.x/sum(rpw.x)
    return weights

def clusterBuilder(assets, dates):
    w = riskParity(assets)
    cluster = pd.DataFrame(data = np.dot(assets,w), index = dates, columns = ['Basket'])
    return cluster, w

def basketBuilder(cluster_long,cluster_short):
    basket = cluster_long - cluster_short
    return basket

def graphIndex(basket, longLeg, shortLeg, style = 'fivethirtyeight'):
    sns.set_style("darkgrid")
    plt.figure(figsize=(14,8))
    plt.plot(basket.index, basket.cumsum()*100,linewidth = 1.0, color = [0.90625,0.48828125,0.1171875])
    plt.ylabel('Total Return (%)', fontsize = 14)
    plt.xticks(fontsize = 14)
    plt.yticks(fontsize = 14)
    plt.title('%s vs. %s Basket' % (' '.join(longLeg), ' '.join(shortLeg)), fontsize = 14 )
    plt.show()
    return True

def graphDistribution(basket, longLeg, shortLeg, style = 'fivethirtyeight'):
    sns.distplot(basket*100, kde=False, fit=stats.gamma)
    return True

def defineCluster(FXreturns, currencies):
    fxdict = {'AUD':'AUDUSD Curncy', 'BRL':'BRLUSD Curncy', 'CAD':'CADUSD Curncy', 'CLP':'CLPUSD Curncy', 'CNY':'CNYUSD Curncy', 'COP':'COPUSD Curncy', 
              'KRW':'KRWUSD Curncy', 'GBP':'GBPUSD Curncy', 'JPY':'JPYUSD Curncy', 'MXN':'MXNUSD Curncy', 'NZD':'NZDUSD Curncy', 'TRY':'TRYUSD Curncy', 
              'ZAR':'ZARUSD Curncy', 'PEN': 'PENUSD Curncy', 'EUR': 'EURUSD Curncy', 'CHF': 'CHFUSD Curncy', 'DKK': 'DKKUSD Curncy', 'NOK': 'NOKUSD Curncy',
              'PLN': 'PLNUSD Curncy', 'SEK': 'SEKUSD Curncy', 'ARS':'ARSUSD Curncy'}   
    tickers = [fxdict[currencies[i]] for i in range(0,len(currencies))]
    cluster_data = FXreturns[tickers].copy()
    cluster, weights = clusterBuilder(cluster_data, FXreturns.index)
    return cluster, weights

def basketAnalysis(longLeg, shortLeg, graphs = True):
    clusterLong, weightsLong = defineCluster(FXreturns, longLeg)
    clusterShort, weightsShort = defineCluster(FXreturns, shortLeg)
    basket = basketBuilder(clusterLong, clusterShort)
    if graphs:
        graphIndex(basket, longLeg, shortLeg)
        graphDistribution(basket, longLeg, shortLeg)
        print('Total return %f bps') % (basket.cumsum().tail(1).values[0][0]/len(basket)*252*10000)
        
    return basket, clusterLong, weightsLong, clusterShort, weightsShort

def basketComparison(basket_one, basket_two):
    data = basket_one*100
    data.columns = ['Basket One']
    data['Basket Two'] = basket_two*100
    sns.jointplot(x="Basket One", y="Basket Two", data=data, kind="kde" , xlim = [-2,2], ylim = [-2,2]);
    return data
    
def histogramComparison(basket_one, basket_two):
    data = basket_one*100
    data.columns = ['Basket One']
    data['Basket Two'] = basket_two*100
    sns.set(color_codes = True)
#    sns.set(style='white', palette = 'muted')
#    for col_id in data.columns:
#        sns.distplot(data[col_id], kde_kws={"label": col_id})
    return data
    

# Clusters de monedas:
c1 = ['AUD', 'CLP', 'KRW', 'NZD']
c2 = ['BRL', 'COP', 'ZAR']
c3 = ['CAD', 'CNY', 'GBP', 'JPY', 'PEN']
c4 = ['CHF', 'DKK', 'EUR', 'NOK', 'PLN', 'SEK']
c5 = ['MXN', 'TRY']


basket_one, clusterLong, weightsLong, clusterShort, weightsShort = basketAnalysis(['MXN','BRL','PEN'],['CLP'], graphs = False)
basket_two, clusterLong2, weightsLong2, clusterShort2, weightsShort2 = basketAnalysis(['CLP'],[], graphs = False)
data = basketComparison(basket_one, basket_two)
data = histogramComparison(basket_one, basket_two)

basket, clusterLong, wightsLong, clusterShort, weightsShort = basketAnalysis(['BRL','MXN','PEN'],['CLP'])
