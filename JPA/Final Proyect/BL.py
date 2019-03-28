import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scipy.optimize
from pylab import *
from arch.univariate import arch_model
from pandas.tseries.offsets import BDay
from scipy import stats as scistats


def getReturns(prices, freq = 1):
    returns = (np.log(prices) - np.log(prices.shift(freq))).fillna(0)
    return returns

def computeAssetsMeanVariance(data):
    mu = data.mean()
    omega = data.cov()
    corr=data.corr()
#    corrEwma=data.ewm(com=0.5).corr()
    return mu, omega,corr

def BL(w_mkt,CovMat_mkt,P,Q,tau,lmda):
#    vol_mkt=float(np.dot(np.dot(np.transpose(w_mkt),CovMat_mkt),w_mkt))
#    lmda=r_Premium/vol_mkt # lambda=(E(r)-rf)/vol_mkt
    pi_Prior=lmda*np.dot(CovMat_mkt,w_mkt) # Implied excess equilibrium return: Pi=lambda*CovMat*w_mkt
    
    omega=np.zeros([len(Q),len(Q)])
    var_Views=np.asarray([np.dot(P.loc[n],np.dot(CovMat_mkt,np.transpose(P.loc[n]))) for n in range(0,len(Q))])
    np.fill_diagonal(omega,var_Views*tau)
    omega_inv=np.linalg.inv(omega)
    
    CovMat_Posterior=np.linalg.inv((np.linalg.inv(tau*CovMat_mkt)+np.dot(np.dot(np.transpose(P),omega_inv),P)))
    pi_Posterior=np.dot(CovMat_Posterior,(np.dot(np.linalg.inv(tau*CovMat_mkt),pi_Prior)+np.dot(np.dot(np.transpose(P),omega_inv),Q)))
    w_bl=np.dot(np.linalg.inv(lmda*CovMat_mkt),pi_Posterior)
    return pi_Prior,pi_Posterior,w_bl,CovMat_Posterior

def EgarchModel(returns):
    model = arch_model(returns, vol='EGarch', p=1, o=1, q=1, dist='Normal')
#    model = arch.arch_model(returns, dist = 'StudentsT') # Switch to T-Students distribution
    results = model.fit()
    parameters = results.params
    return parameters, results, model

def garchForecast(omega, alpha, gamma, beta, sigma, t):
    forecast=np.zeros(t)
    forecast[0]=np.log(sigma**2)
    for i in range(1,t):
        forecast[i]=omega+np.sqrt(2/np.pi)*alpha+beta*forecast[i-1]
    return np.sqrt(np.exp(forecast))

def plotForecastedVolatility(results, model, forecast_window = 20):
    sigma = np.array(results.conditional_volatility)[-1]
    omega, alpha, gamma, beta = np.array(parameters[1:5])        
    fDate = results.conditional_volatility.index[-1]
    dates = pd.date_range(fDate, periods = forecast_window, freq=BDay())   
    print(dates)
    forecast = pd.DataFrame(garchForecast(omega, alpha, gamma, beta, sigma, forecast_window), index = dates)
    df = pd.DataFrame(results.conditional_volatility, index = np.concatenate([results.conditional_volatility.index, dates]))
    df.loc[:, 'LT_Volatility'] = np.sqrt(np.exp((omega+np.sqrt(2/np.pi)*alpha)/(1-beta)))
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

def MinVariance(weights,mu,omega,lmda):
    return lmda*np.dot(np.dot(np.transpose(weights),omega),weights) - np.dot(np.transpose(weights),mu)

#def MinVarianceVaR(weights,mu,omega,lmda):
#    return lmda*np.dot(np.dot(np.transpose(weights),omega),weights) - np.dot(np.transpose(weights),mu)

def MinVarianceVaR(weights,mu,omega,lmda,factor):
    return np.sqrt(lmda*np.dot(np.dot(np.transpose(weights),omega),weights))*factor - np.dot(np.transpose(weights),mu)

def MinVarianceSharpe(weights,mu,omega,lmda,rf):
    return (rf*np.ones(len(mu)) - np.dot(np.transpose(weights),mu))/np.sqrt(lmda*np.dot(np.dot(np.transpose(weights),omega),weights))

def wBLSharpe(mu,omega,rf):
    return np.dot(np.linalg.inv(omega),(mu[:,0]-rf*np.ones(len(mu))))/(np.dot(np.dot(np.ones(len(mu)),np.linalg.inv(omega)),(mu[:,0]-rf*np.ones(len(mu)))))

def wBLSharpe_opt(mu,omega,lmda,rf):
    weights = ones(len(mu))/len(mu)*0
    n = len(mu)
    b_ = [(0,1) for i in range(n)]
    c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
    optimized = scipy.optimize.minimize(MinVarianceSharpe, weights, (mu,omega,lmda), method='SLSQP', constraints=c_, bounds=b_,tol=1e-10)
    return optimized.x

def wBLConstrained(mu,omega,lmda):
    weights = ones(len(mu))/len(mu)*0
    n = len(mu)
    b_ = [(0,1) for i in range(n)]
    c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
    optimized = scipy.optimize.minimize(MinVariance, weights, (mu,omega,lmda), method='SLSQP', constraints=c_, bounds=b_)
    return optimized.x

#def wBLVaR(mu,omega,lmda,const):
#    weights = ones(len(mu))/len(mu)*0
#    n = len(mu)
#    b_ = [(0,1) for i in range(n)]
#    c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. },{'type':'eq', 'fun': lambda weights: const-float(np.sqrt(lmda*np.dot(np.dot(np.transpose(weights),omega),weights))) })
#    optimized = scipy.optimize.minimize(MinVarianceVaR, weights, (mu,omega,lmda), method='SLSQP', constraints=c_, bounds=b_,tol=1e-20)
##    optimized = scipy.optimize.minimize(MinVarianceVaR, weights, (mu,omega,lmda), method='SLSQP', constraints=c_,tol=1e-20)
#    return optimized.x

def wBLVaR(mu,omega,lmda,factor):
    weights = ones(len(mu))/len(mu)*0
    n = len(mu)
    b_ = [(0,1) for i in range(n)]
    c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
    optimized = scipy.optimize.minimize(MinVarianceVaR, weights, (mu,omega,lmda,factor), method='SLSQP', constraints=c_, bounds=b_,tol=1e-10)
    return optimized.x

def effFrontier(mu,omega,lmda):
    frontier_mean, frontier_var, frontier_weights = [], [], []
    n = len(mu)	# Number of assets in the portfolio
    def portfolioVariance(weights,mu,omega,lamda,r):
        return lmda*np.dot(np.dot(np.transpose(weights),omega),weights) + 50*abs(r - np.dot(np.transpose(weights),mu))
    def minVarianceWeights(omega):
        return np.dot(np.linalg.inv(omega),np.ones(len(omega)))/(np.dot(np.dot(ones(len(omega)),np.linalg.inv(omega)),ones(len(omega))))
    for r in linspace(np.dot(minVarianceWeights(omega),mu), max(mu), num=20): # Iterate through the range of returns on Y axis, starting in min-var portfolio
#    for r in linspace(min(mu)*0, max(mu), num=20): # Iterate through the range of returns on Y axis
        weights = ones(len(mu))/len(mu)*0
        b_ = [(0,1) for i in range(n)]
        c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
        optimized = scipy.optimize.minimize(portfolioVariance, weights, (mu,omega,lmda,r), method='SLSQP', constraints=c_, bounds=b_,tol=1e-20)
        print(optimized.x)
        frontier_mean.append(np.dot(np.transpose(np.asarray(optimized.x)),mu))             					      # return
        frontier_var.append(np.sqrt(np.dot(np.dot(np.transpose(optimized.x),omega),optimized.x)))	# min-variance based on optimized weights
        frontier_weights.append(optimized.x)
    return np.asarray(frontier_mean), np.asarray(frontier_var), np.asarray(frontier_weights)

def effFrontierVar(mu,omega,lmda,const):
    frontier_mean, frontier_var, frontier_weights = [], [], []
    n = len(mu)	# Number of assets in the portfolio
    def portfolioVariance(weights,mu,omega,lamda,r):
        return lmda*np.dot(np.dot(np.transpose(weights),np.linalg.inv(omega)),weights) + 50*abs(r - np.dot(np.transpose(weights),mu))
    def minVarianceWeights(omega):
        return np.dot(np.linalg.inv(omega),np.ones(len(omega)))/(np.dot(np.dot(ones(len(omega)),np.linalg.inv(omega)),ones(len(omega))))
    for r in linspace(np.dot(minVarianceWeights(omega),mu), max(mu), num=20): # Iterate through the range of returns on Y axis, starting in min-var portfolio
#    for r in linspace(min(mu)*0, max(mu), num=20): # Iterate through the range of returns on Y axis
        weights = ones(len(mu))/len(mu)*0
        b_ = [(0,1) for i in range(n)]
        c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. },{'type':'ineq', 'fun': lambda weights: const-float(np.sqrt(lmda*np.dot(np.dot(np.transpose(weights),np.linalg.inv(omega)),weights))) })
        optimized = scipy.optimize.minimize(portfolioVariance, weights, (mu,omega,lmda,r), method='SLSQP', constraints=c_, bounds=b_,tol=1e-20)
#        optimized = scipy.optimize.minimize(portfolioVariance, weights, (mu,omega,lmda,r), method='SLSQP', constraints=c_,tol=1e-20)
        print(optimized.x)
        frontier_mean.append(np.dot(np.transpose(np.asarray(optimized.x)),mu))           					      # return
        frontier_var.append(np.sqrt(lmda*np.dot(np.dot(np.transpose(optimized.x),np.linalg.inv(omega)),optimized.x)))
#        frontier_var.append(np.sqrt(np.dot(np.dot(np.transpose(optimized.x),omega),optimized.x)))	# min-variance based on optimized weights
        frontier_weights.append(optimized.x)
    return np.asarray(frontier_mean), np.asarray(frontier_var), np.asarray(frontier_weights)

#def effFrontierVar(mu,omega,lmda,const):
#    frontier_mean, frontier_var, frontier_weights = [], [], []
#    n = len(mu)	# Number of assets in the portfolio
#    def portfolioVariance(weights,mu,omega,lamda,r,const):
#        return np.sqrt(lmda*np.dot(np.dot(np.transpose(weights),np.linalg.inv(omega)),weights))*const + 50*abs(r - np.dot(np.transpose(weights),mu))
#    def minVarianceWeights(omega):
#        return np.dot(np.linalg.inv(omega),np.ones(len(omega)))/(np.dot(np.dot(ones(len(omega)),np.linalg.inv(omega)),ones(len(omega))))
#    for r in linspace(np.dot(minVarianceWeights(omega),mu), max(mu), num=20): # Iterate through the range of returns on Y axis, starting in min-var portfolio
##    for r in linspace(min(mu)*0, max(mu), num=20): # Iterate through the range of returns on Y axis
#        weights = ones(len(mu))/len(mu)*0
#        b_ = [(0,1) for i in range(n)]
#        c_ = ({'type':'eq', 'fun': lambda weights: sum(weights)-1. })
#        optimized = scipy.optimize.minimize(portfolioVariance, weights, (mu,omega,lmda,r,const), method='SLSQP', constraints=c_, bounds=b_,tol=1e-20)
##        print(optimized.x)
#        frontier_mean.append(np.dot(np.transpose(np.asarray(optimized.x)),mu))             					      # return
#        frontier_var.append(np.sqrt(np.dot(np.dot(np.transpose(optimized.x),omega),optimized.x)))	# min-variance based on optimized weights
#        frontier_weights.append(optimized.x)
#    return frontier_mean, frontier_var, frontier_weights

def plotEfficientFrontier(mean,volatility,avg_mean,avg_volatility):
    df1 = pd.DataFrame([mean[0:],volatility[0:],zeros(len(volatility))],index = ['Mean','Volatility','Avg']).transpose()
    df2 = pd.DataFrame([avg_mean,avg_volatility,ones(len(avg_volatility))],index = ['Mean','Volatility','Avg']).transpose()
    df = df1.append(df2)
    sns.lmplot("Volatility", "Mean", data=df, fit_reg=False, hue="Avg", legend = False)
    return True

def areaPlot(names,pw,pv):
    average_weight = abs(pd.DataFrame(data = pw, columns = p.columns))
    average_weight = average_weight.transpose()
    tuples = list(zip(names['assetclass'],names['indexname']))
    index = pd.MultiIndex.from_tuples(tuples,names=['Asset Class','Index Name'])
    weights = pd.DataFrame(data=average_weight.values, index=index)
    w_class = weights.groupby(weights.index.get_level_values(0)).sum()
#    w_class_c = pd.DataFrame(data=w_class.values,columns=pv)
#    print(w_class_c)
    
#    sns.palplot(sns.color_palette("Set3", 20))
    sns.set_palette('RdBu_r',15)
    w_class.transpose().plot(kind='area', ylim = [0,1])
    return True

#    print(w_bl_constrained)
#    print(parameters)
#    plt.plot(condVol*np.sqrt(252)*100)
#    plt.show()
#    print(results.summary())

    
if __name__ == '__main__':
    
    # Prices data reader
    p = pd.read_excel('BLdata.xlsx', sheetname='prices_short', headers=1, index_col=0)
    rf = pd.read_excel('BLdata.xlsx', sheetname='rf', headers=1, index_col=0)
    names = pd.read_excel('BLdata.xlsx', sheetname='Classif', headers=0)
    
    freq=252/52
#    freq=1
    ret_abs=getReturns(p,1)
    ret_rf=getReturns(rf,1)
    ret=pd.DataFrame(index=ret_abs.index,columns=ret_abs.columns)
    for x in names['indexname']:
        ret[x]=(ret_abs[x]-ret_rf['rf'])

    [mu, omega, corr]=computeAssetsMeanVariance(ret)
    std=pd.DataFrame(np.zeros(len(names)),index=names['indexname'])
    condVol=pd.DataFrame(np.zeros([len(p),len(names)]),index=p.index,columns=names['indexname'])
    std_filtered_mkt=pd.DataFrame(np.zeros([len(names),len(names)]),index=names['indexname'],columns=names['indexname'])
    for x in names['indexname']:
        [parameters, results, model]=EgarchModel(ret[x])
        condVol[x]=np.array(results.conditional_volatility)*np.sqrt(252/freq)
        std.loc[x,:]=np.array(results.conditional_volatility)[-1]
   
    np.fill_diagonal(std_filtered_mkt.values, std)
    CovMat_filtered_mkt=np.dot(std_filtered_mkt,np.dot(corr,std_filtered_mkt))*252/freq
    
    # BL data reader
#    S=pd.read_excel('BLdata.xlsx', sheetname='StdMatrix', headers=1, index_col=0)
#    C=pd.read_excel('BLdata.xlsx', sheetname='CorrelMatrix', headers=1, index_col=0)
#    CovMat_mkt=np.dot(S,np.dot(C,S))
    w_mkt = pd.read_excel('BLdata.xlsx', sheetname='MarketWeight', headers=1, index_col=0)
    P=pd.read_excel('BLdata.xlsx', sheetname='P', headers=1, index_col=0)
    Q=pd.read_excel('BLdata.xlsx', sheetname='Q', headers=1, index_col=0)
    
    Sharpe=0.5
    tau=1/len(p)
    vol_mkt=np.sqrt(float(np.dot(np.dot(np.transpose(w_mkt['w_mkt']),CovMat_filtered_mkt),w_mkt['w_mkt'])))
    lmda=Sharpe/vol_mkt # Neutral lambda aasuming sharpe 0.5
#    lmda=2
    
    [pi_Prior,pi_Posterior,w_bl,CovMat_Posterior]=BL(w_mkt,CovMat_filtered_mkt,P,Q,tau,lmda)
    
    w_bl_constrained=wBLConstrained(pi_Posterior,CovMat_filtered_mkt,lmda)
    

    
    w_bl_sharpe=np.zeros([len(names),2])
    w_bl_sharpe[:,0]=wBLSharpe(pi_Prior,CovMat_filtered_mkt,0.001)
    w_bl_sharpe[:,1]=wBLSharpe(pi_Posterior,CovMat_filtered_mkt,0.001)



    [pr_post, pv_post, pw_post]=effFrontier(pi_Posterior,CovMat_filtered_mkt,lmda)
    [pr_prior, pv_prior, pw_prior]=effFrontier(pi_Prior,CovMat_filtered_mkt,lmda)
    plt.figure()
    plt.plot(pv_post*100,pr_post*100,'o')
    plt.plot(pv_prior*100,pr_prior*100,'o')
    plt.xlabel('Volatility (%)', fontsize=16)
    plt.ylabel('Expected Return (%)', fontsize=16)
    
    plt.show()
    
    
    VarLim=[0.01,0.1,0.5,1,1.5,2,2.3]
    VaR =np.zeros(len(VarLim))

        
    w_bl_VaR=np.transpose(pd.DataFrame(np.asarray([wBLVaR(pi_Posterior,CovMat_filtered_mkt,lmda,n) for n in VarLim]),index=VarLim))
    u_bl_VaR=pd.DataFrame(np.asarray([np.dot(np.transpose(pi_Posterior),wBLVaR(pi_Posterior,CovMat_filtered_mkt,lmda,n)) for n in VarLim]),index=VarLim)

    for n in range(0,len(VarLim)):
        VaR[n]=np.sqrt(lmda*np.dot(np.dot(np.transpose(w_bl_VaR.iloc[:,n]),CovMat_filtered_mkt),w_bl_VaR.iloc[:,n]))*VarLim[n]
        
#    w_bl_VaR.plot(kind='area', ylim = [0,1])
#    plt.show()
    plt.figure()
    plt.plot(VaR,u_bl_VaR*100,'o')
    plt.xlabel('VaR (%)', fontsize=16)
    plt.ylabel('Expected Return (%)', fontsize=16)
    plt.show()
    
#    VarLim=0.5
#    [pr_post, pv_post, pw_post]=effFrontierVar(pi_Prior,CovMat_filtered_mkt,lmda,VarLim)
#    [pr_prior, pv_prior, pw_prior]=effFrontierVar(pi_Prior,CovMat_filtered_mkt,lmda,VarLim/2)
#    plt.figure()
#    plt.plot(pv_prior,pr_prior,'o')
#    plt.plot(pv_post,pr_post,'o')
#    plt.xlabel('Volatility (%)', fontsize=16)
#    plt.ylabel('Expected Return (%)', fontsize=16)
#    plt.show()
    
    areaPlot(names,pw_prior,pv_prior)
    areaPlot(names,pw_post,pv_post)
    
#    plotEfficientFrontier(pr, pv, pr, pv)
    print(w_bl_constrained)
    print(parameters)
#    plt.plot(condVol*np.sqrt(252)*100)
#    plt.show()
    print(results.summary())

    

    
    
    
    
    
    
    
    
    
    
#    ax = plotForecastedVolatility(results, model , forecast_window=100)
    








#    Corr_mkt=pd.read_excel('BLdata.xlsx', sheetname='CorrelMatrix', headers=1, index_col=0)
#    Std_mkt=pd.read_excel('BLdata.xlsx', sheetname='StdMatrix', headers=1, index_col=0)
#    CovMat_mkt=pd.read_excel('BLdata.xlsx', sheetname='CovarianceMatrix', headers=1, index_col=0)
#    CovMat_mkt=np.dot(Std_mkt,np.dot(Corr_mkt,Std_mkt))

    
#    r_Premium=0.03 # E(r)-rf

    
    

    
    
    
    
    
    
    
        