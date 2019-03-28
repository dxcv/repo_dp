import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scipy.optimize
from pylab import *
from arch.univariate import arch_model,EWMAVariance,ConstantMean
from pandas.tseries.offsets import BDay
from scipy import stats as scistats


#Function that calculates returns from asset prices
def getReturns(prices, freq = 1):
    returns = (np.log(prices) - np.log(prices.shift(freq))).fillna(0)
    return returns

#Function that calculates the simple mean for a set of returns
def computeAssetsMeanVariance(data):
    mu = data.mean()
    omega = data.cov()
    corr=data.corr()
    return mu, omega,corr

#Funcion that calculates the posterior Black-Litterman distribution, given the market weight, Covariance Matrix,
#view matrix P and Q, and lambda.
def BL(w_mkt,CovMat_mkt,P,Q,tau,lmda):
    pi_Prior=lmda*np.dot(CovMat_mkt,w_mkt) # Implied excess equilibrium return: Pi=lambda*CovMat*w_mkt
    omega=np.zeros([len(Q),len(Q)])
    var_Views=np.asarray([np.dot(P.loc[n],np.dot(CovMat_mkt,np.transpose(P.loc[n]))) for n in range(0,len(Q))])
    np.fill_diagonal(omega,var_Views*tau)
    omega_inv=np.linalg.inv(omega)
    CovMat_Posterior=np.linalg.inv((np.linalg.inv(tau*CovMat_mkt)+np.dot(np.dot(np.transpose(P),omega_inv),P)))
    pi_Posterior=np.dot(CovMat_Posterior,(np.dot(np.linalg.inv(tau*CovMat_mkt),pi_Prior)+np.dot(np.dot(np.transpose(P),omega_inv),Q)))
    w_bl=np.dot(np.linalg.inv(lmda*CovMat_mkt),pi_Posterior)
    return pi_Prior,pi_Posterior,w_bl,CovMat_Posterior

#Function that calculates the different volatility processes for a given set of returns
def XgarchModel(returns):
    modelE = arch_model(returns, vol='EGARCH', p=1, o=1, q=1, dist='Normal')
    modelG = arch_model(returns, vol='GARCH', p=1, q=1, dist='Normal')
    modelA = arch_model(returns, vol='ARCH', p=5, dist='Normal')
    modelW = ConstantMean(returns, volatility=EWMAVariance(lam=0.94))
    resultsE = modelE.fit()
    resultsG = modelG.fit()
    resultsA = modelA.fit()
    resultsW = modelW.fit()
    return resultsE,resultsG, resultsA, resultsW, modelE, modelG, modelA, modelW

#Function that calculates the min variance for portfolio optimization
def MinVariance(weights,mu,omega,lmda):
    return lmda*np.dot(np.dot(np.transpose(weights),omega),weights) - np.dot(np.transpose(weights),mu)

#Function that calculates the min VaR for a given lambda for portfolio optimization
def MinVarianceVaR(weights,mu,omega,lmda,factor):
    return np.sqrt(lmda*np.dot(np.dot(np.transpose(weights),omega),weights))*factor - np.dot(np.transpose(weights),mu)

#Function that calculates the portfolio that maximizes the Sharpe Ratio for a given lambda for portfolio optimization
def MinVarianceSharpe(weights,mu,omega,lmda,rf):
    return (rf - np.dot(np.transpose(weights),mu))/np.sqrt(lmda*np.dot(np.dot(np.transpose(weights),omega),weights))

#Function that uses the optimizer in scipy and calls MinVarianceSharpe function to calculate the portfolio that maximizes the Sharpe Ratio
def wBLSharpe_opt(mu,omega,lmda,rf):
    weights = ones(len(mu))/len(mu)*0.5
    n = len(mu)
    b_ = [(0,1) for i in range(n)]
    c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
    optimized = scipy.optimize.minimize(MinVarianceSharpe, weights, (mu,omega,lmda,rf), method='SLSQP', constraints=c_, bounds=b_,tol=1e-20)
    return optimized.x

#Function that calculates the Black-Litterman allocation constrained to w>0 and sum(w)=1
def wBLConstrained(mu,omega,lmda):
    weights = ones(len(mu))/len(mu)*0
    n = len(mu)
    b_ = [(0,1) for i in range(n)]
    c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
    optimized = scipy.optimize.minimize(MinVariance, weights, (mu,omega,lmda), method='SLSQP', constraints=c_, bounds=b_)
    return optimized.x

#Function that calls MinVarianceVaR function to miminize VaR and calculate the min VaR portfolio
def wBLVaR(mu,omega,lmda,factor):
    weights = ones(len(mu))/len(mu)*0.5
    n = len(mu)
    b_ = [(0,1) for i in range(n)]
    c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
    optimized = scipy.optimize.minimize(MinVarianceVaR, weights, (mu,omega,lmda,factor), method='SLSQP', constraints=c_, bounds=b_,tol=1e-10)
    return optimized.x

#Function that calculates the efficient frontier given returns, covariance matrix and risk aversion lambda
def effFrontier(mu,omega,lmda):
    frontier_mean, frontier_var, frontier_weights = [], [], []
    n = len(mu)	# Number of assets in the portfolio
    def portfolioVariance(weights,mu,omega,lamda,r):
        return lamda*np.dot(np.dot(np.transpose(weights),omega),weights) + 50*abs(r - np.dot(np.transpose(weights),mu))
    def minVarianceWeights(omega): # Calculates the minimum variance portfolio to start the frontier
        return np.dot(np.linalg.inv(omega),np.ones(len(omega)))/(np.dot(np.dot(ones(len(omega)),np.linalg.inv(omega)),ones(len(omega))))
    for r in linspace(np.dot(minVarianceWeights(omega),mu), max(mu), num=20): # Iterate through the range of returns on Y axis, starting in min-var portfolio
        weights = ones(len(mu))/len(mu)*0
        b_ = [(0,1) for i in range(n)]
        c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
        optimized = scipy.optimize.minimize(portfolioVariance, weights, (mu,omega,lmda,r), method='SLSQP', constraints=c_, bounds=b_,tol=1e-20)
        frontier_mean.append(np.dot(np.transpose(np.asarray(optimized.x)),mu)) # return
        frontier_var.append(np.sqrt(np.dot(np.dot(np.transpose(optimized.x),omega),optimized.x)))	# min-variance based on optimized weights
        frontier_weights.append(optimized.x)
    return np.asarray(frontier_mean), np.asarray(frontier_var), np.asarray(frontier_weights)

#Function that plots the efficient frontier
def plotEfficientFrontier(mean,volatility,avg_mean,avg_volatility):
    df1 = pd.DataFrame([mean[0:],volatility[0:],zeros(len(volatility))],index = ['Mean','Volatility','Avg']).transpose()
    df2 = pd.DataFrame([avg_mean,avg_volatility,ones(len(avg_volatility))],index = ['Mean','Volatility','Avg']).transpose()
    df = df1.append(df2)
    sns.lmplot("Volatility", "Mean", data=df, fit_reg=False, hue="Avg", legend = False)
    return True

#Function that plots portfolio weights as "areas" for the efficient frontier
def areaPlot(names,pw,pv):
    average_weight = abs(pd.DataFrame(data = pw, columns = p.columns))
    average_weight = average_weight.transpose()
    tuples = list(zip(names['assetclass'],names['indexname']))
    index = pd.MultiIndex.from_tuples(tuples,names=['Asset Class','Index Name'])
    weights = pd.DataFrame(data=average_weight.values, index=index)
    w_class = weights.groupby(weights.index.get_level_values(0)).sum()
    sns.set_palette('RdBu_r',15)
    w_class.transpose().plot(kind='area', ylim = [0,1])
    return True
    
if __name__ == '__main__':
    
    # Prices data reader for asset prices, names and risk free index.
    p = pd.read_excel('BLdata.xlsx', sheetname='prices_short', headers=1, index_col=0)
    rf = pd.read_excel('BLdata.xlsx', sheetname='rf', headers=1, index_col=0)
    names = pd.read_excel('BLdata.xlsx', sheetname='Classif', headers=0)
    
    freq=252/52 # to annualize weekly data

    ret_abs=getReturns(p,1) # getting returns for assets and rf
    ret_rf=getReturns(rf,1)
    ret=pd.DataFrame(index=ret_abs.index,columns=ret_abs.columns)
    for x in names['indexname']:
        ret[x]=(ret_abs[x]-ret_rf['rf']) #calculating excess return

    [mu, omega, corr]=computeAssetsMeanVariance(ret) #calculating historic retunrs, covar matrix and correlations
    
    #initializing variables
    std=pd.DataFrame(np.zeros(len(names)),index=names['indexname'])
    condVolE=pd.DataFrame(np.zeros([len(p),len(names)]),index=p.index,columns=names['indexname'])
    condVolG=pd.DataFrame(np.zeros([len(p),len(names)]),index=p.index,columns=names['indexname'])
    condVolA=pd.DataFrame(np.zeros([len(p),len(names)]),index=p.index,columns=names['indexname'])
    condVolW=pd.DataFrame(np.zeros([len(p),len(names)]),index=p.index,columns=names['indexname'])
    std_filtered_mkt=pd.DataFrame(np.zeros([len(names),len(names)]),index=names['indexname'],columns=names['indexname'])
    
    
    #Calculating volatility through different processes and storing it 
    for x in names['indexname']:
        [resultsE,resultsG, resultsA, resultsW, modelE, modelG, modelA, modelW]=XgarchModel(ret[x])
        condVolE[x]=np.array(resultsE.conditional_volatility)*np.sqrt(252/freq)*100
        condVolG[x]=np.array(resultsG.conditional_volatility)*np.sqrt(252/freq)*100
        condVolA[x]=np.array(resultsA.conditional_volatility)*np.sqrt(252/freq)*100
        condVolW[x]=np.array(resultsW.conditional_volatility)*np.sqrt(252/freq)*100

        std.loc[x,:]=np.array(resultsE.conditional_volatility)[-1]
    
    #Plotting conditional volatility for any desired asset:    
#    asset='CENCOSUD CC Equity'
    asset='Gob CLP Dur 5y+'
    init_date='2000-01-01'
    ConstantVol=pd.DataFrame(np.sqrt(omega[asset][asset])*np.sqrt(252/freq)*np.ones(len(p)),index=p.index)*100
    sns.set_palette("Set1",n_colors=5,desat=.5)
    plt.figure(figsize=(12, 7))    
    condVolE.loc[init_date:,asset].plot(label='EGARCH (1,1,1)')
    condVolG.loc[init_date:,asset].plot(label='GARCH (1,1)')
    condVolA.loc[init_date:,asset].plot(label='ARCH (5)')
    condVolW.loc[init_date:,asset].plot(label='EWMA')
    ConstantVol.loc[init_date:,0].plot(label='Constant hist. volatility')
    plt.legend(loc='best',fontsize=13)
    plt.ylabel('Annualized Volatility (%)', fontsize=16)
    plt.xlabel('Date', fontsize=16)
    plt.show()

    
    #Building covariance matrix with the disered process for volatility and constant correlations
    np.fill_diagonal(std_filtered_mkt.values, std)
    CovMat_filtered_mkt=np.dot(std_filtered_mkt,np.dot(corr,std_filtered_mkt))*252/freq

    # BL data reader for market weight and views
    w_mkt = pd.read_excel('BLdata.xlsx', sheetname='MarketWeight', headers=1, index_col=0)
    P=pd.read_excel('BLdata.xlsx', sheetname='P', headers=1, index_col=0)
    Q=pd.read_excel('BLdata.xlsx', sheetname='Q', headers=1, index_col=0)
    
    #Initializing data for the Black-Litterman model
    Sharpe=1.8 # For Chilean fixed income market
#    Sharpe=0.5 # For Chilean equity market
    tau=1/len(p)
    vol_mkt=np.sqrt(float(np.dot(np.dot(np.transpose(w_mkt['w_mkt']),CovMat_filtered_mkt),w_mkt['w_mkt'])))
    lmda=Sharpe/vol_mkt # Neutral lambda aasuming given sharpe
    
    #Calling the Black-Litterman model
    [pi_Prior,pi_Posterior,w_bl,CovMat_Posterior]=BL(w_mkt,CovMat_filtered_mkt,P,Q,tau,lmda)
    
    #Plotting the efficient frontier for prior and posterior distributions
    [pr_post, pv_post, pw_post]=effFrontier(pi_Posterior,CovMat_filtered_mkt,lmda)
    [pr_prior, pv_prior, pw_prior]=effFrontier(pi_Prior,CovMat_filtered_mkt,lmda)
    sns.set_palette("Set1",n_colors=5,desat=.5)
    plt.figure(figsize=(12, 7))
    plt.plot(pv_post*100,pr_post*100,'o', label='Posterior Efficient Frontier')
    plt.plot(pv_prior*100,pr_prior*100,'o',label='Prior Efficient Frontier')
    plt.legend(loc='best',fontsize=13)
    plt.xlabel('Volatility (%)', fontsize=16)
    plt.ylabel('Expected Return (%)', fontsize=16)
    plt.show()
  
    # Plotting the portfolios on the efficient frontier as an area plot     
    areaPlot(names,pw_prior,pv_prior)
    areaPlot(names,pw_post,pv_post)
    
    #Calculating the optimum portfolio using posterior BL results, but constrained with w>0 and sum(w)=1
    w_bl_constrained=wBLConstrained(pi_Posterior,CovMat_filtered_mkt,lmda)
    
    #Calculating optimal portfolio that maximises the sharpe ratio using posterior and prior returns
    w_bl_sharpe=np.zeros([len(names),2])
    w_bl_sharpe[:,0]=wBLSharpe_opt(pi_Prior,CovMat_filtered_mkt,lmda,0.025)
    w_bl_sharpe[:,1]=wBLSharpe_opt(pi_Posterior,CovMat_filtered_mkt,lmda,0.025)

    #Calculating optimal portfolio that minimizes the VaR using different factors
    VarFactor=[0.05,0.1,0.2,0.3,0.5,1,1.5,2,2.33]
    VaR =np.zeros(len(VarFactor))

        
    w_bl_VaR=np.transpose(pd.DataFrame(np.asarray([wBLVaR(pi_Posterior,CovMat_filtered_mkt,lmda,n) for n in VarFactor]),index=VarFactor))
    u_bl_VaR=pd.DataFrame(np.asarray([np.dot(np.transpose(pi_Posterior),wBLVaR(pi_Posterior,CovMat_filtered_mkt,lmda,n)) for n in VarFactor]),index=VarFactor)

    for n in range(0,len(VarFactor)):
        VaR[n]=np.sqrt(lmda*np.dot(np.dot(np.transpose(w_bl_VaR.iloc[:,n]),CovMat_filtered_mkt),w_bl_VaR.iloc[:,n]))*VarFactor[n]
        
    #Plotting the results for the VaR optimization
    plt.figure()
    plt.plot(VarFactor,u_bl_VaR*100,'o')
    plt.xlabel('VaR factor: $\Phi^{-1}(1-c)$', fontsize=16)
    plt.ylabel('Expected Return (%)', fontsize=16)
    plt.show()
    
    

    
    
    
    
    
    
    
        