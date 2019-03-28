import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import time
import scipy.optimize as sop
from scipy import stats as scistats
import matplotlib.ticker as mtick

def Vol_1(Tau): 
    fact1 = 0.0064306548 #first vol factor simplified to flat
    return fact1

def Vol_2(Tau):
    fact2 = -0.0035565431 + Tau * (-0.0005683999) + (Tau ** 2) * 0.0001181915 + (Tau ** 3) * (-0.0000035939)
    return fact2

def Vol_3(Tau):
    fact3 = -0.0047506715 + Tau * 0.0017541783 + (Tau ** 2) * (-0.0001415249) + (Tau ** 3) * (0.0000031274)
    return fact3

#This funciton M calculates the HJM drift for simulating the SDE
#It carries out integration for all principal factors. It uses the fact that volatility is function of time in HJM model
   
def M(Tau):
    if Tau == 0:
        Ml = 0
    else:
        dTau = 0.01 #initial step
        N = int(Tau / dTau)
        dTau = Tau / N #step for Tau
            
        #using trapezium rule to compute M1
        M1 = 0.5 * Vol_1(0)

        for i in range(1,N,1):
            M1 = M1 + Vol_1(i * dTau) #not adjusted by *0.5 because of repeating terms x1...xn-1 - see trapezoidal rule
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

#Function that simulates the FRA matrix for the HJM model that evolves the forward curve using the same-form SDE.
def SimFRA(FRA_t0,dt,dten,max_tenor,years_sim,Mint,Vol_1int,Vol_2int,Vol_3int):  
    N=int(years_sim/dt) 
    rand = np.random.standard_normal((N+1, 3)) # 3 indepent sources of randomness for the SDE simulation
  
    # We define our FRA matrix
    FRA=np.zeros([N+1,len(FRA_t0)])

    # We simulate the SDEs
    FRA[0,:]=FRA_t0
    for i in range(1, N+1):
        for j in range(0,len(FRA_t0)):
            if j==len(FRA_t0)-1:
                FRA[i,j]=FRA[i-1,j]+Mint[j]*dt+(Vol_1int[j]*rand[i,0]+Vol_2int[j]*rand[i,1]+Vol_3int[j]*rand[i,2])*math.sqrt(dt)+((FRA[i-1,j]-FRA[i-1,j-1])/((j/2-(j-1)/2)))*dt # in last tenor we use backward derivative
            else:
                FRA[i,j]=FRA[i-1,j]+Mint[j]*dt+(Vol_1int[j]*rand[i,0]+Vol_2int[j]*rand[i,1]+Vol_3int[j]*rand[i,2])*math.sqrt(dt)+((FRA[i-1,j+1]-FRA[i-1,j])/(((j+1)/2-j/2)))*dt
    
    return FRA, rand, Mint,Vol_1int,Vol_2int,Vol_3int

#Function that calculates the expected exposure
def ExpExposure(FRA_t0,dt,dten,max_tenor,years,Mint,Vol_1int,Vol_2int,Vol_3int,SwapMat,SwapFreq,FixLeg,SwapDt,Notional,sims,OIS_spread):
    SwapFwd=np.zeros([SwapMat*SwapFreq,SwapMat*SwapFreq])
    Exposure=np.zeros([sims,SwapMat*SwapFreq+1]) 
    for n in range (0,sims):
        print('Simulation: ',n, '/', sims)
        #We build the floating leg with the HJM output
        [FRA_matrix,rand,Mint,Vol1,Vol2,Vol3]=SimFRA(FRA_t0,dt,dten,max_tenor,years,Mint,Vol_1int,Vol_2int,Vol_3int)
        OIS_Matrix=FRA_matrix-OIS_spread/10000
        for i in range(0,SwapMat*SwapFreq): #We observe which is the 6m Libor each fixing time in the future (50 steps of 0.01 are 6 months)
            for j in range(0,SwapMat*SwapFreq-i): #We iterate in each tenor for each forward curve. As we go into the future, we have less tenors, that's why we iterate in "SwapMat*SwapFreq-i"
                SwapFwd[i,j]=FRA_matrix[50*i,j+1]
                Exposure[n,i]=Exposure[n,i]+(FRA_matrix[50*i,j+1]-FixLeg)*SwapDt*np.exp(-sum(OIS_Matrix[i,1:j+2])*SwapDt)*Notional
        Exposure[n,SwapMat*SwapFreq]=0
    
    # We define the different exposures
    ExposureMax=np.maximum(Exposure, 0)
    ExposureMaxMean=np.mean(ExposureMax, axis=0)
    ExposureMaxMedian=np.median(ExposureMax, axis=0)
    ExposureMaxPercentile975=np.percentile(ExposureMax, 97.5, axis=0) 
    return Exposure,ExposureMax,ExposureMaxMean,FRA_matrix,ExposureMaxMedian,ExposureMaxPercentile975

#Function that calculates the CVA given the expected exposure
def FCVA(FRA_t0,ExposureMaxMean,ExposureMaxMedian,ExposureMaxPercentile975,SwapMat,SwapFreq,SwapDt,lda,RR,OIS_spread):
    CVA=np.zeros([SwapMat*SwapFreq,3])
    SurvProb=np.zeros(SwapMat*SwapFreq+1)
    OIS=FRA_t0-OIS_spread/10000
    
    #Now computing CVA
    SurvProb[0]=1
    for m in range (0,SwapMat*SwapFreq):
        #We calculate the integral using the "center" of riemann sum rectangle
        Df=np.exp(0.5*math.log(np.exp(-sum(OIS[1:m+1])*SwapDt))+0.5*math.log(np.exp(-sum(OIS[1:m+2])*SwapDt))) #We interpolate on ln of the discount factors
        SurvProb[m+1]=np.exp(-np.sum(lda[0:m+1])*SwapDt)
        dPD=SurvProb[m]-SurvProb[m+1]
        CVA[m,0]=(ExposureMaxMean[m]+ExposureMaxMean[m+1])/2*Df*dPD*(1-RR)
        CVA[m,1]=(ExposureMaxMedian[m]+ExposureMaxMedian[m+1])/2*Df*dPD*(1-RR)
        CVA[m,2]=(ExposureMaxPercentile975[m]+ExposureMaxPercentile975[m+1])/2*Df*dPD*(1-RR)
    return CVA,SurvProb
    
if __name__=="__main__":
    
    # We set up our initial variable on t=0 for the FRA matrix. Is the last observed forward curve (from last row in HJM PCA file/BOE data).
    
    FRA_t0=np.array([0.046138361,0.045251174,0.042915805,0.04283311,0.043497719,0.044053792,0.044439518,0.044708496,0.04490347,0.045056615,0.045184474,0.045294052,0.045386152,0.045458337,0.045507803,0.045534188,0.045541867,0.045534237,0.045513128,0.045477583,0.04542292,0.045344477,0.04523777,0.045097856,0.044925591,0.04472353,0.044494505,0.044242804,0.043973184,0.043690404,0.043399223,0.043104398,0.042810688,0.042522852,0.042244909,0.041978295,0.041723875,0.041482518,0.04125509,0.041042459,0.040845492,0.040665047,0.040501255,0.040353009,0.040219084	,0.040098253,0.039989288,0.039890964,0.039802053,0.039721437,0.03964844])
    
    # We define initial parameters
    
    dt=0.01
    dten=0.5
    max_tenor=25
    years=5
    SwapMat=5
    SwapDt=0.5
    SwapFreq=int(1/SwapDt)
    FixLeg=0.045
    Notional=1
    sims=500
    lda=np.ones(SwapMat*SwapFreq)*0.03 # Term structure of lamdas at 3%
    RR=0.4
    OIS_spread=80
    
    Mint=np.zeros(len(FRA_t0))
    Vol_1int=np.zeros(len(FRA_t0))
    Vol_2int=np.zeros(len(FRA_t0))
    Vol_3int=np.zeros(len(FRA_t0))
    t=0
    
    # We predefine our vol functions for HJM model for faster calculation
    for h in np.arange(0,max_tenor+dten/2,dten):
        Mint[t]=M(h)
        Vol_1int[t]=Vol_1(h)
        Vol_2int[t]=Vol_2(h)
        Vol_3int[t]=Vol_3(h)
        t+=1
   
    # We calculate expected exposure and CVA for the number of simulations defined in "sims"
    [Exposure,ExposureMax,ExposureMaxMean,FRA_matrix,ExposureMaxMedian,ExposureMaxPercentile975]=ExpExposure(FRA_t0,dt,dten,max_tenor,years,Mint,Vol_1int,Vol_2int,Vol_3int,SwapMat,SwapFreq,FixLeg,SwapDt,Notional,sims,OIS_spread)   
    [CVA,SurvProb]=FCVA(FRA_t0,ExposureMaxMean,ExposureMaxMedian,ExposureMaxPercentile975,SwapMat,SwapFreq,SwapDt,lda,RR,OIS_spread)
    
    x=[0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]        
    plt.figure()
    plt.plot(x,Exposure.transpose(), label='Exposure')
    plt.xlabel('Years', fontsize=16)
    plt.ylabel('Expected Future Value', fontsize=16)
    plt.show()
    
    plt.figure()
    plt.plot(x,ExposureMax.transpose(), label='Exposure')
    plt.xlabel('Years', fontsize=16)
    plt.ylabel('Expected Exposure', fontsize=16)
    plt.show()
    
    plt.figure()
    plt.plot(x,ExposureMaxMean, label='Mean Expected Exposure')
    plt.plot(x,ExposureMaxMedian, label='Median Expected Exposure')
    plt.plot(x,ExposureMaxPercentile975, label='97.5th Percentile Expected Exposure')
    plt.legend(loc='best',prop={'size':12})
    plt.xlabel('Years', fontsize=16)
    plt.ylabel('Expected Exposure', fontsize=16)
    plt.show()
    
    plt.figure()
    plt.plot(CVA, label='CVA')
    plt.xlabel('Years', fontsize=16)
    plt.ylabel('Exposure', fontsize=16)
    plt.show()
    
    #Now, we test the CVA in several different situations
    
#    #1.- CVA and Expected Exposure depending on number of simulations
#    print('Calculating CVA depending on number of simulations ...')
#    sim_input=[50, 100, 200, 500, 1000, 2000, 5000, 10000]
#    CVA_sims=np.zeros([len(sim_input),3])
#    for n in range(0,len(sim_input)):
#        [Exposure,ExposureMax,ExposureMaxMean,FRA_matrix,ExposureMaxMedian,ExposureMaxPercentile975]=ExpExposure(FRA_t0,dt,dten,max_tenor,years,Mint,Vol_1int,Vol_2int,Vol_3int,SwapMat,SwapFreq,FixLeg,SwapDt,Notional,sim_input[n],OIS_spread)
#        [CVA,SurvProb]=FCVA(FRA_t0,ExposureMaxMean,ExposureMaxMedian,ExposureMaxPercentile975,SwapMat,SwapFreq,SwapDt,lda,RR,OIS_spread)
#        CVA_sims[n,:]=sum(CVA,axis=0)
#
#    #2.- CVA and Expected Exposure depending on fixed lambda
#    print('Calculating CVA depending on lambda ...')
#    lda_input=[0.01, 0.05, 0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.95,0.99]
#    CVA_lambda=np.zeros([len(lda_input),3])
#    SurvProb_lambda=np.zeros([len(lda_input),SwapMat*SwapFreq+1])
#    for n in range(0,len(lda_input)):
#        lda_sim=np.ones(SwapMat*SwapFreq)*lda_input[n]
#        [CVA,SurvProb]=FCVA(FRA_t0,ExposureMaxMean,ExposureMaxMedian,ExposureMaxPercentile975,SwapMat,SwapFreq,SwapDt,lda_sim,RR,OIS_spread)
#        CVA_lambda[n,:]=np.sum(CVA,axis=0)
#        SurvProb_lambda[n,:]=SurvProb
#    
#    #3.- CVA and expected exposure depending on RR
#    print('Calculating CVA depending on RR ...')
#    RR_input=[0.1,0.3,0.5,0.7,0.9]
#    CVA_RR=np.zeros([len(RR_input),3])
#    for n in range(0,len(RR_input)):
#        [CVA,SurvProb]=FCVA(FRA_t0,ExposureMaxMean,ExposureMaxMedian,ExposureMaxPercentile975,SwapMat,SwapFreq,SwapDt,lda,RR_input[n],OIS_spread)
#        CVA_RR[n,:]=np.sum(CVA, axis=0)
#     
#    #4.- CVA and Expected Exposure depending on hazard rate term structure    
#    print('Calculating CVA depending on Hazard Rate Term Structure ...')
#    lda_input=np.asarray([[1.07, 0.79, 0.41, 0.19, 0.16, 0.10, 0.08, 0.06,0.05,0.04],[0.08,0.12,0.17,0.26,0.37,0.52,0.68,0.82,1.03,1.5],[0.009,0.012,0.015,0.017,0.019,0.021,0.022,0.024,0.025,0.027]])
#    CVA_lambda=np.zeros([len(lda_input),3])
#    SurvProb_lambda=np.zeros([len(lda_input),SwapMat*SwapFreq+1])
#    for n in range(0,3):
#        [CVA,SurvProb]=FCVA(FRA_t0,ExposureMaxMean,ExposureMaxMedian,ExposureMaxPercentile975,SwapMat,SwapFreq,SwapDt,lda_input[n,:],RR,OIS_spread)
#        CVA_lambda[n,:]=np.sum(CVA,axis=0)
#        SurvProb_lambda[n,:]=SurvProb
#    
#    #5.- CVA and expected exposure depending on fixed rate
#    print('Calculating CVA depending on different fixed rates for IRS...')
#    FixLeg_input=[0.02,0.03,0.04,0.05,0.06,0.07]
#    CVA_FixLeg=np.zeros([len(FixLeg_input),3])
#    ExposureMaxMean_FixLeg=np.zeros([len(FixLeg_input),SwapMat*SwapFreq+1])
#    for n in range(0,len(FixLeg_input)):
#        print('Fixed rate: ',FixLeg_input[n])
#        [Exposure,ExposureMax,ExposureMaxMean,FRA_matrix,ExposureMaxMedian,ExposureMaxPercentile975]=ExpExposure(FRA_t0,dt,dten,max_tenor,years,Mint,Vol_1int,Vol_2int,Vol_3int,SwapMat,SwapFreq,FixLeg_input[n],SwapDt,Notional,sims,OIS_spread)
#        [CVA,SurvProb]=FCVA(FRA_t0,ExposureMaxMean,ExposureMaxMedian,ExposureMaxPercentile975,SwapMat,SwapFreq,SwapDt,lda,RR,OIS_spread)
#        CVA_FixLeg[n,:]=sum(CVA,axis=0)
#        ExposureMaxMean_FixLeg[n,:]=ExposureMaxMean
        
     
     #Some plotting for the tested situations above   

#    plt.figure()
#    plt.legend(iter(plt.plot(x,ExposureMaxMean_FixLeg.transpose())), FixLeg_input)
#    plt.xaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
#    plt.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
#    plt.xlabel('Years', fontsize=16)
#    plt.ylabel('Expected Exposure / Mean', fontsize=16)
#    plt.legend(loc='best',prop={'size':12})
#    plt.show()
#    
#    plt.figure()
#    plt.legend(iter(plt.plot(FixLeg_input,CVA_FixLeg, 'o')), ['CVA mean','CVA median','CVA 97.5th Percentile'])
#    plt.xlabel('Fixed Coupon', fontsize=16)
#    plt.ylabel('CVA', fontsize=16)
#    plt.legend(loc='best',prop={'size':12})
#    plt.show()
#    
#    plt.figure()
#    plt.legend(iter(plt.plot(RR_input,CVA_RR,'o')), ['CVA mean','CVA median','CVA 97.5th Percentile'])
#    plt.xlabel('RR', fontsize=16)
#    plt.ylabel('CVA', fontsize=16)
#    plt.legend(loc='best',prop={'size':12})
#    plt.show()