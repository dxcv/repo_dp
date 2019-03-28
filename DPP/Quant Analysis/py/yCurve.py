# -*- coding: utf-8 -*-
"""
Created on Mon Dec 26 13:43:52 2016

@author: ngoldbergerr
"""


from scipy.optimize import leastsq
from statsmodels.tsa.vector_ar.var_model import VAR
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
from datetime import datetime as dtime

class yieldCurve(object):
    
    def __init__(self):
        self.parameters = []

    def nelsonSiegelCurve(self, tenors, parameters = None):
        #A partir de los tenores ingresados entrega los puntos de la curva de tasas para los parámetros ingresados o lo guardados
        """
        Based on the provided tenors and parameters, this method calculates the
        rates for each point of the curve. The input can be an array (of 
        tenors) and a list or another array (of parameters). The output is an 
        array that contains the rates for each of the tenors.
        input: array, list or array
        output: array
        """
        if parameters is None:
            parameters = self._parameters

        if parameters is None:
            print("""There are no parameters calibrated for the curve. Run calibrateParameters first.""")
            return False
              
        b0, b1, b2 = parameters[1:4]
        tau = float(parameters[0])
        
        yc = b0 + b1*(1 - np.exp(-tenors/tau))/(tenors/tau) + b2*((1 - np.exp(-tenors/tau))/(tenors/tau) - np.exp(-tenors/tau))
        
        return yc

    def nelsonSiegelCurveResiduals(self, p, tenors, yields, tau):
        """
        The residuals method calculates the error between the actual yields and
        what the model computes with the parameters obtained from the least
        square optimization. the inputs are an array of parameters, an array
        of tenors, an array of yields and the parameter tau (integer).
        inputs: array, array, array, int
        output: array
        """
        
        b0, b1, b2 = p
        err = yields - self.nelsonSiegelCurve(tenors, [tau, b0, b1, b2])
        err = err.astype(float)
        return err

    def calibrateCurveParametersHistorical(self, tenors, yields, tau = 1):
        """
        This method calculates the historical parameters for the provided
        tenors and yields. The inputs are an array of tenors, an array of
        yields, and tau (an integer).
        inputs: array, array, float
        output: DataFrame
        """
        yieldCurve = yields.values.astype(float)
        param= []
        x0 = np.array([0.1, 0.1, 0.1])
        
        for y in yieldCurve:
            x0 = leastsq(self.nelsonSiegelCurveResiduals, x0, args = (tenors, y, tau))
            x0 = x0[0]
            param.append([tau] + x0.tolist())
            
        self._tenorsHistorical = tenors
        self._yieldsHistorical = yields
        self._parametersHistorical = param
        
        return param


    def parametersVAR(self, tenors, yields, lag = 1, steps = 1, alpha = 0.01):
        params = pd.DataFrame(data=self.calibrateCurveParametersHistorical(tenors, yields),columns=['tau','b0','b1','b2'], index = yields.index)
        self._varModel = VAR(params[['b0','b1','b2']]).fit(lag) 
        self._varModel.summary()
        fparam = self._varModel.forecast_interval(params.tail(1)[['b0','b1','b2']].values, steps, alpha = alpha)
        return fparam, params.tail(1)[['b0','b1','b2']].values


    def plotForecastedCurve(self, tenors, yields, steps = 1, alpha = 0.05, tau = 1, style = 'fivethirtyeight', error = True):
        #Función que grafica forecast de curva, junto con error
        forecast, initialParameters = self.parametersVAR(tenors, yields, steps = steps, alpha = alpha)
        
        baseParameter = initialParameters.tolist()
        fcParameter = forecast[0].tolist()
        topParameter = forecast[1].tolist()
        bottomParameter = forecast[2].tolist()
        
        shock_level = -0.25*1
        shock_slope = 0
        shock_curvature = 0
        
        with plt.style.context(style, after_reset = True):
            plt.plot(tenors,yields.tail(1).values[0],'g.')
            plt.plot(tenors,self.nelsonSiegelCurve(tenors, [tau, baseParameter[0][0] + shock_level, baseParameter[0][1], baseParameter[0][2]]), linewidth = 1.0)
            plt.plot(tenors,self.nelsonSiegelCurve(tenors, [tau, fcParameter[0][0] + shock_level, fcParameter[0][1], fcParameter[0][2]]), 'b.')
            if error:
                plt.plot(tenors,self.nelsonSiegelCurve(tenors, [tau, topParameter[0][0] + shock_level, topParameter[0][1], topParameter[0][2]]), 'b--', linewidth = 1.0)
                plt.plot(tenors,self.nelsonSiegelCurve(tenors, [tau, bottomParameter[0][0] + shock_level, bottomParameter[0][1], bottomParameter[0][2]]), 'b--', linewidth = 1.0)
#                plt.text(0.2, 0.8, """$\\alpha$ = %s"""%alpha, transform =  plt.gca().transAxes)
                
            plt.ylabel('%')
#            plt.title('%s Months Projection for CLP calibrated curve'%(str(steps)))
        plt.show()


if __name__ == '__main__':
    # Load Data    
    data = pd.read_excel('L:\Rates & FX\Quant Analysis\pytest\chileYieldCurve.xlsx')
    print(data)
    yields = data[1:]
    tenors = yields.columns
    print(tenors)
    # Calibrate Curva and Forecast
    yc = yieldCurve()
#    params = yc.calibrateCurveParametersHistorical(tenors, yields)
#    fp = yc.parametersVAR(tenors, yields)
#    yc.plotForecastedCurve(tenors, yields)
    alpha = 0.05
    steps = 1
    tau = 1
    
    forecast, initialParameters = yc.parametersVAR(tenors, yields, steps = steps, alpha = alpha)
    
    baseParameter = initialParameters.tolist()
    fcParameter = forecast[0].tolist()
    topParameter = forecast[1].tolist()
    bottomParameter = forecast[2].tolist()
    
    tenors = np.array([1,2,3,4,5,6,7,8,9,10,15,20,25,30])
    
    forecastedCurve = yc.nelsonSiegelCurve(tenors, [tau, fcParameter[steps-1][0], fcParameter[steps-1][1], fcParameter[steps-1][2]])
    plt.plot(tenors,forecastedCurve)
    plt.show()
    print(forecastedCurve)