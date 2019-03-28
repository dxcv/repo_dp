import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import time
from scipy import stats as scistats


# we define N as number of simulations, M as the average window, t_stp as the time number of time steps, ...
# S0 as the starting value for the underlying, and sample as the number of samples we want to do to the paths (if t_stp=sample then we assume continuous ... we sample all times)

def Asian(N,M,t_stp,S0,sample):

    rand = np.random.standard_normal((t_stp+1, N)) # We generate a matrix of standard normal numbers to create paths

    # We initialize our variables
    
    S = np.zeros_like(rand) # we create a matrix S, were each column will be a path simulation
    
    # We define arrays to store the averages for each path (the size of the arrays is the number of paths)
    
    S_arithmetic_average=np.zeros(N) 
    S_geometric_average=np.zeros(N)
    
    # We define arrays to store the payoff of each path (the size of the arrays is the number of paths)
    
    S_floating_arithmetic_call_payoff = np.zeros(N) 
    S_fixed_arithmetic_call_payoff = np.zeros(N)
    S_floating_geometric_call_payoff = np.zeros(N)
    S_fixed_geometric_call_payoff = np.zeros(N)
    
    S_floating_arithmetic_put_payoff = np.zeros(N)
    S_fixed_arithmetic_put_payoff = np.zeros(N)
    S_floating_geometric_put_payoff = np.zeros(N)
    S_fixed_geometric_put_payoff = np.zeros(N)
    
    # We define initial value for the paths and dt

    S[0,:]=S0
    dt = T / t_stp 
    
    # We generate the paths

    for t in range(1,t_stp+1):
        S[t] = S[t-1] * (1 + r * dt + sigma * rand[t] * math.sqrt(dt)) # Euler-Maruyama approximation for path creation
#        S[t] = S[t - 1] * np.exp((r - sigma ** 2 / 2) * dt + sigma * rand[t] * math.sqrt(dt)) # Closed form solution for path creation
        
    Spaths=pd.DataFrame(S) # We define the path matrix as a dataframe for further simplicity in code
    
    # We define variables for the sampling, the idea is to sample each sample path. The number of times sampled is in variable "sample". If sample = t_stp, then is continuous (we sample all time)
    
    freq=int(round((t_stp+1)/(sample+1),0))
    init=freq-1
    end=t_stp+1-freq+1

    # We calculate the averages for an average window of M, and "sample" number of samples
    
    S_arithmetic_average=Spaths.iloc[range(init,end,freq),:].tail(M).mean().values
    S_geometric_average=scistats.gmean(Spaths.iloc[range(init,end,freq),:].tail(M))
    
    # We calculate the payoffs
    
    S_floating_arithmetic_call_payoff = np.maximum(S[t_stp] - S_arithmetic_average, 0)
    S_fixed_arithmetic_call_payoff = np.maximum(S_arithmetic_average-E, 0)
    S_floating_geometric_call_payoff = np.maximum(S[t_stp] - S_geometric_average, 0)
    S_fixed_geometric_call_payoff = np.maximum(S_geometric_average - E, 0)
    
    S_floating_arithmetic_put_payoff = np.maximum(S_arithmetic_average-S[t_stp], 0)
    S_fixed_arithmetic_put_payoff = np.maximum(E-S_arithmetic_average, 0)
    S_floating_geometric_put_payoff = np.maximum(S_geometric_average-S[t_stp], 0)
    S_fixed_geometric_put_payoff = np.maximum(E-S_geometric_average, 0)
    
    
    # We define a payoff matrix for further simplicity in the code
    
    S_payoff = pd.DataFrame(data=[S_floating_arithmetic_call_payoff,S_fixed_arithmetic_call_payoff,
                                  S_floating_geometric_call_payoff,S_fixed_geometric_call_payoff,S_floating_arithmetic_put_payoff,S_fixed_arithmetic_put_payoff,S_floating_geometric_put_payoff,
                                  S_fixed_geometric_put_payoff],index=['Float_Ar_Call','Fixed_Ar_Call','Float_Ge_Call','Fixed_Ge_Call','Float_Ar_Put','Fixed_Ar_Put','Float_Ge_Put','Fixed_Ge_Put']).transpose()
    
    # We discount at the riskfree rate to obtain option value
    
    Op_val=math.exp(-r * T)*S_payoff.mean()            

    return Spaths,S_payoff,Op_val,S_arithmetic_average,S_geometric_average,Spaths.iloc[range(init,end,freq),:]


if __name__=="__main__":
    # we define the parameters
    
    S0 = 100.0 # Today's stock price
    E = 100.0 # Strike price
    T = 1.0 # Time to expiry (T-t)
    sigma = 0.2 # volatility
    r = 0.05 # risk-free constant interest rate rate
    np.random.seed(25000) # Seed for paths. We keep the same for simulations to be comparable
    
    # We call our function
    Sp,Spay,OpV,Saa,Sga,Samp=Asian(10000,1000,1000,S0,10)
    
    # Plotting sample paths
    
#    plt.figure()
#    Sp.plot(figsize=(12,8),legend=False)
#    plt.xlabel('Time Steps (dt)', fontsize=18)
#    plt.ylabel('S ($)', fontsize=16)
#    plt.show()
    
    #We do some arrangement for graphic results
    
    X=pd.DataFrame(data=[Sp[17],Sp[17].mean()*np.ones(len(Sp[17])),scistats.gmean(Sp[17])*np.ones(len(Sp[17]))]).transpose()
    X.columns=['Sample Path','Continuous Arithmetic Average','Continuous Geometric Average']
    
    ContAAv=Saa[17]*np.ones(len(Sp[17]))
    ContGAv=Sga[17]*np.ones(len(Sp[17]))
    
    plt.figure()
    
    with pd.plot_params.use('x_compat',True):
        X.plot(figsize=(12,8))
        Samp[17].plot(style='ro',label='Samples')
        plt.plot(ContAAv, label='Sampled Arithmetic Average',linestyle=':')
        plt.plot(ContGAv, label='Sampled Geometric Average', linestyle=':')
        plt.legend(loc='best',prop={'size':12})
        plt.xlabel('Time Steps (dt)', fontsize=18)
        plt.ylabel('S ($)', fontsize=16)
        plt.show()

    print(OpV)
    
    
 
#    Code to plot value of options variying Sampling. For "sample"="t_stp" is continuous sampling (we sample all times)

#    i=0
#    Op=pd.DataFrame()
#    
#    for a in range(1,51,1):
#        np.random.seed(25000)
#        Sp,Spay,OpV,Saa,Sga,Samp=Asian(10000,1000,1000,S0,a)
#        Op[i]=OpV
#        i +=1
#        print(a)
#    Op.columns=range(1,51,1)
#    Op=Op.transpose()
#    plt.figure()
#    Op.plot(figsize=(15, 10))
#    plt.legend(prop={'size':15})
#    plt.xlabel('Number of samples', fontsize=18)
#    plt.ylabel('Option Value ($)', fontsize=18)
#    plt.show()

#    Code to plot value of options variying the time steps.

#    i=0
#    Op=pd.DataFrame()
#    Time=np.zeros(len(range(1,100,1)))
#    for a in range(1,100,1):
#        start=time.perf_counter()
#        np.random.seed(25000)
#        Sp,Spay,OpV,Saa,Sga,Samp=Asian(10000,a,a,S0,a)
#        end=time.perf_counter()
#        Time[i]=end-start
#        Op[i]=OpV
#        i +=1
#        print(a)
#    Op.columns=range(1,100,1)
#    Op=Op.transpose()
#    plt.figure()
#    Op.plot(figsize=(12, 8))
#    plt.legend(prop={'size':15})
#    plt.xlabel('Number of time steps', fontsize=18)
#    plt.ylabel('Option Value ($)', fontsize=18)
#    plt.show()
#
#    Time_pd=pd.DataFrame(Time)
#    Time_pd.index=range(1,100,1)
#    Time_pd.plot(figsize=(12, 8),legend=False)
#    plt.xlabel('Number of simulations', fontsize=18)
#    plt.ylabel('Elapsed time (seconds)', fontsize=18)
#    plt.show()
    
#    Code to plot value of options variying M (moving average window) 
 
#    i=0
#    Op=pd.DataFrame()
#    for a in range(1,1000,50):
#        np.random.seed(25000)
#        Sp,Spay,OpV,Saa,Sga,Samp=Asian(10000,int(a),1000,S0,1000)
#        Op[i]=OpV
#        i +=1
#        print(a,OpV)
#    Op.columns=range(1,1000,50)
#    Op=Op.transpose()
#    Op.plot(figsize=(12, 8))
#    plt.legend(loc='best',prop={'size':12})
#    plt.xlabel('Size of average window M', fontsize=18)
#    plt.ylabel('Option Value ($)', fontsize=18)
#    plt.show() 
    
    
#    Code to plot value of options variying N (montecarlo simulations)   
 
#    i=0
#    Op=pd.DataFrame()
#    
#    Time=np.zeros(len(range(10000,100001,10000)))
#    for a in range(10000,100001,10000):
#        start=time.perf_counter()
#        np.random.seed(25000)
#        Sp,Spay,OpV,Saa,Sga,Samp=Asian(a,1000,1000,S0,1000)
#        end=time.perf_counter()
#        Time[i]=end-start
#        Op[i]=OpV
#        print(a, Time[i])
#        i +=1
#    Op.columns=range(10000,100001,10000)
#    Op=Op.transpose()
#    Op.plot(figsize=(12, 8)) 
#    plt.legend(loc='center right',prop={'size':12})
#    plt.xlabel('Number of simulations', fontsize=18)
#    plt.ylabel('Option Value ($)', fontsize=18)
#    plt.show() 
#    
#    Time_pd=pd.DataFrame(Time)
#    Time_pd.index=range(10000,100001,10000)
#    Time_pd.plot(figsize=(12, 8),legend=False)
#    plt.xlabel('Number of simulations', fontsize=18)
#    plt.ylabel('Elapsed time (seconds)', fontsize=18)
#    plt.show()    
    
    
    
#    Code to plot value of options variying S

#    i=0
#    Op=pd.DataFrame()
#    for a in range(0,160,10):
#        Sp,Spay,OpV,Saa,Sga,Samp=Asian(10000,1000,1000,a,1000)
#        Op[i]=OpV
#        i +=1
#        print(a)
#    Op.columns=range(0,160,10)
#    Op=Op.transpose()
#    plt.figure()
#    Op.plot(figsize=(12, 8))
#    plt.legend(prop={'size':15})
#    plt.xlabel('Underlying price S', fontsize=18)
#    plt.ylabel('Option Value ($)', fontsize=18)
#    plt.show()
        
    
