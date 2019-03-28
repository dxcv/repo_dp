import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import time
import scipy.optimize as sop
from scipy import stats as scistats


# As instructed, we define volatility functions as calibrated on the HJM model in excel 

def Vol_1(Tau):
    fact1 = 0.0064306548 #first vol factor simplified to flat
    return fact1

def Vol_2(Tau):
    fact2 = -0.0035565431 + Tau * (-0.0005683999) + (Tau ** 2) * 0.0001181915 + (Tau ** 3) * (-0.0000035939)
    return fact2

def Vol_3(Tau):
    fact3 = -0.0047506715 + Tau * 0.0017541783 + (Tau ** 2) * (-0.0001415249) + (Tau ** 3) * (0.0000031274)
    return fact3

def M(Tau):
    
    #This funciton calculates the HJM drift for simulating the SDE
    #It carries out integration for all principal factors. It uses the fact that volatility is function of time in HJM model
    
    if Tau == 0:
        Ml = 0
    else:
        dTau = 0.01                                     #initial step
        N = int(Tau / dTau)
        #print(N)
        dTau = Tau / N                                  #step for Tau
            
        #using trapezium rule to compute M1
        M1 = 0.5 * Vol_1(0)
        
        # IN EXCEL, "FOR" IS UP TO N-1, Y PYTHON WE CORRECT AND IS UP TO N FOR EQUIVALENCE!
        for i in range(1,N,1):
            M1 = M1 + Vol_1(i * dTau) #not adjusted by *0.5 because of repeating terms x1...xn-1 - see trapezoidal rule
        #print(i)
        M1 = M1 + 0.5 * Vol_1(Tau)
        M1 = M1 * dTau
        M1 = Vol_1(Tau) * M1 #Vol_1 represents v_i(t,T) and M1 represents the result of numerical integration
        
        #using trapezium rule to compute M2
        M2 = 0.5 * Vol_2(0)
        for i in range(1,N,1):
            M2 = M2 + Vol_2(i * dTau)
        M2 = M2 + 0.5 * Vol_2(Tau)
        M2 = M2 * dTau
        M2 = Vol_2(Tau) * M2
        
        #using trapezium rule to compute M3
        M3 = 0.5 * Vol_3(0)
        for i in range(1,N,1):
            M3 = M3 + Vol_3(i * dTau)
        M3 = M3 + 0.5 * Vol_3(Tau)
        M3 = M3 * dTau
        M3 = Vol_3(Tau) * M3
        
        Ml = M1 + M2 + M3 #sum for multi-factor
    return Ml


def SimFRA(FRA_t0,dt,years_sim):
    
    #FRA=pd.DataFrame()
    
    N=int(years_sim/dt)
    #print(N)
    
    #np.random.seed(25000) # Seed for paths. We keep the same for simulations to be compared
    rand = np.random.standard_normal((N+1, 3)) # 3 indepent sources of randomness for the SDE simulation
    #print(rand)
    
    # We define aour FRA matrix
    FRA=np.zeros([N+1,len(FRA_t0)])
    
    # We simulate the SDEs
    FRA[0,:]=FRA_t0
    for i in range(1, N+1):
        for j in range(0,len(FRA_t0)):
            if j==len(FRA_t0)-1:
                FRA[i,j]=FRA[i-1,j]+M(j/2)*dt+(Vol_1(j/2)*rand[i,0]+Vol_2(j/2)*rand[i,1]+Vol_3(j/2)*rand[i,2])*math.sqrt(dt)+((FRA[i-1,j]-FRA[i-1,j-1])/((j/2-(j-1)/2)))*dt # in last tenor we use backward derivative
            else:
                FRA[i,j]=FRA[i-1,j]+M(j/2)*dt+(Vol_1(j/2)*rand[i,0]+Vol_2(j/2)*rand[i,1]+Vol_3(j/2)*rand[i,2])*math.sqrt(dt)+((FRA[i-1,j+1]-FRA[i-1,j])/(((j+1)/2-j/2)))*dt
    
    
    return FRA


def Floorlet(T1,T2,K,FRA_matrix,dt,OIS_spread):
    
    tau_sim=T2-T1
    Lib_0612=1/tau_sim*(np.exp(FRA_matrix[50,1]*tau_sim)-1)
    DF=np.exp(-(sum(FRA_matrix[0:101,0]*dt)-OIS_spread*len(FRA_matrix[0:101,0])*dt/10000))
    
    Floor=np.maximum(K-Lib_0612,0)*DF*tau_sim
    
    init_sigma=0.20
    DF_BS=np.exp(-(sum(FRA_matrix[0:51,0]*dt)-OIS_spread*len(FRA_matrix[0:51,0])*dt/10000))      
    
    B=Floorlet_Vol(init_sigma,K,Lib_0612,DF_BS,tau_sim,Floor)
    
#    print(Lib_0612)
#    print(DF)
#    print(DF_BS)
#    print(B)
#    print(Cap)
    
    return Floor,B


def BS_Floorlet(K,L,sigma,DF,tau):
    d1=(math.log(L/K)+0.5*tau*(sigma**2))/(sigma*math.sqrt(tau))
    d2=(math.log(L/K)-0.5*tau*(sigma**2))/(sigma*math.sqrt(tau))
    BS=DF*tau*(K*scistats.norm.cdf(-d2)-L*scistats.norm.cdf(-d1))#/(1+L*tau)
#    print(sigma,K,L,tau, DF,d1, d2,scistats.norm.cdf(-d2),scistats.norm.cdf(-d1))
#    print(BS)
    return BS


def FloorletVolErrorFunction(sigma, *args):
    K=args[0]
    L=args[1]
    DF=args[2]
    tau=args[3]
    Floor=args[4]
    sigma_2=sigma[0]
    Dif=abs(BS_Floorlet(K,L,sigma_2,DF,tau)-Floor)
    return Dif

def Floorlet_Vol(sigma,K,L,DF,tau,Floor):
#    opt = sop.fmin(FloorletVolErrorFunction, sigma, args=(K,L,DF,tau,Floor),xtol=0.0000000001,ftol=0.0000000001, maxiter=750, maxfun=1500)
    opt = sop.minimize(FloorletVolErrorFunction, sigma, args=(K,L,DF,tau,Floor))
    sol=opt['x'][0]
    #sol=ret[0]
    
    return sol
    
if __name__=="__main__":
    
    # We set up our initial variable o t=0 for the FRA matrix. Is the last observed forward curve (from last row in HJM PCA file/BOE data).
    
    FRA_0=np.array([0.046138361,0.045251174,0.042915805,0.04283311,0.043497719,0.044053792,0.044439518,0.044708496,0.04490347,0.045056615,0.045184474,0.045294052,0.045386152,0.045458337,0.045507803,0.045534188,0.045541867,0.045534237,0.045513128,0.045477583,0.04542292,0.045344477,0.04523777,0.045097856,0.044925591,0.04472353,0.044494505,0.044242804,0.043973184,0.043690404,0.043399223,0.043104398,0.042810688,0.042522852,0.042244909,0.041978295,0.041723875,0.041482518,0.04125509,0.041042459,0.040845492,0.040665047,0.040501255,0.040353009,0.040219084	,0.040098253,0.039989288,0.039890964,0.039802053,0.039721437,0.03964844])

    # We call our function SimFRA to build the FRA matrix. We gave the t=0 input, dt, and number of years forward it is desirable to simulate  
    # Then we value the caplet
    
    
    dt=0.01
    years=1
    
    T1=0.5
    T2=1
    K=0.06
    OIS_spread=80
    
    sims=2000
    Floor=np.zeros(sims)
    Vol=np.zeros(sims)
    Avg_Floor=np.zeros(sims)
    Avg_Vol=np.zeros(sims)
    
    for i in range (0,sims):
        print(i)
        FRA_matrix=SimFRA(FRA_0,dt,years)
        [Floor[i],Vol[i]]=Floorlet(T1,T2,K,FRA_matrix,dt,OIS_spread)
        if i==0:
            Avg_Floor[i]=Floor[i]
            Avg_Vol[i]=Vol[i]
        else:
            Avg_Floor[i]=np.mean(Floor[0:i])
            Avg_Vol[i]=np.mean(Vol[0:i])

    
    plt.figure()
    plt.plot(Avg_Floor, label='Convergence of Floorlet Price')
    plt.xlabel('Number of simulations of MC', fontsize=16)
    plt.ylabel('Running average of Floorlet prices', fontsize=16)
    plt.show()
    
    plt.figure()
    plt.plot(Avg_Vol, label='Convergence of Implied Volatilty')
    plt.xlabel('Number of simulations of MC', fontsize=16)
    plt.ylabel('Implied Volatility of Floorlet in BS', fontsize=16)
    plt.show()
    
    # Let's calculate the Vol using BS and solver
    

    
    
    
    
        #FRA_0=pd.DataFrame(data=[0.046138361,0.045251174,	0.042915805,0.04283311,0.043497719,0.044053792,0.044439518,0.044708496,0.04490347,0.045056615,0.045184474,0.045294052,0.045386152,0.045458337,0.045507803,0.045534188,0.045541867,0.045534237,	0.045513128,0.045477583,0.04542292,0.045344477,0.04523777,0.045097856,0.044925591,0.04472353,0.044494505,0.044242804,0.043973184,0.043690404,0.043399223,0.043104398,0.042810688,0.042522852,0.042244909,0.041978295,0.041723875,0.041482518,0.04125509,0.041042459,0.040845492,0.040665047,0.040501255,0.040353009,0.040219084	,0.040098253,0.039989288,0.039890964,0.039802053,0.039721437,0.03964844],
    #                   index=[x * 0.5 for x in range(0, 51)])
    #FRA_0=FRA_0.transpose()
    
#    plt.figure()
#    plt.plot(b[:,0], label='Sampled Arithmetic Average',linestyle=':')
#    plt.plot(b[:,10], label='Sampled Arithmetic Average',linestyle=':')
#    plt.plot(b[:,20], label='Sampled Arithmetic Average',linestyle=':')
#    plt.plot(b[:,40], label='Sampled Arithmetic Average',linestyle=':')
#    plt.legend(loc='best',prop={'size':12})
#    plt.xlabel('Time Steps (dt)', fontsize=18)
#    plt.ylabel('S ($)', fontsize=16)
#    plt.ylim([0,0.1])
#    plt.show()
#    
#    plt.figure()
#    plt.plot(np.transpose(b[0,:]), label='Sampled Arithmetic Average',linestyle=':')
#    plt.plot(np.transpose(b[50,:]), label='Sampled Arithmetic Average',linestyle=':')
#    plt.plot(np.transpose(b[100,:]), label='Sampled Arithmetic Average',linestyle=':')
#    plt.plot(np.transpose(b[150,:]), label='Sampled Arithmetic Average',linestyle=':')
#    plt.plot(np.transpose(b[200,:]), label='Sampled Arithmetic Average',linestyle=':')
#    plt.legend(loc='best',prop={'size':12})
#    plt.xlabel('Time Steps (dt)', fontsize=18)
#    plt.ylabel('S ($)', fontsize=16)
#    plt.ylim([0,0.1])
#    plt.show()
#    
#    
    
    
    
#    print(FRA_0)
#    a=FRA_0
    
    
    
    
    
    
    
    
    
    
    
    
    
    
#    print(M(0),M(0.5),M(1),M(1.5))
#    c=0
#    M_1=np.zeros(52)
#    V_1=np.zeros(52)
#    V_2=np.zeros(52)
#    V_3=np.zeros(52)
#
#    for i in [x * 0.5 for x in range(0, 51)]:
#        print(i)
#        M_1[c]=M(i)
#        V_1[c]=Vol_1(i)
#        V_2[c]=Vol_2(i)
#        V_3[c]=Vol_3(i)
#        c +=1
#    print('resultado')
#    print(M_1)
#    res=M_1*100
#    V1=V_1*100
#    V2=V_2*100
#    V3=V_3*100
#    
