# -*- coding: utf-8 -*-
"""
Created on January 14, 2016 by Mauro Villalon. Documentation written by Natan Goldberger.
"""

from scipy.optimize import leastsq
#from statsmodels.tsa.ar_model import AR
from statsmodels.tsa.vector_ar.var_model import VAR
#from statsmodels.tsa.stattools import acf
#from statsmodels.tsa.stattools import OLS
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
from datetime import datetime as dtime

class rates(object):
    """
    The rates class calibrates the curve parameters for the Nelson & Siegel and the Diebold & Li models. 
    It's behavior is similar to the one observed on a wrapper function. The objective of this class is to provide
    curve fitting and forecasting services to other objects.
    """
    def __init__(self, parameters = pd.DataFrame()):
  
#        self._nsCurve = nelsonSiegel(parameters)
        self._dlCurve = dieboldLi()
        
    def calibrateCurveParametersNS(self, tenors, yields, tau = 1):
        """ 
        Calibrates curve parameters under the Nelson & Siegel Model
        """ 
        self._dlCurve.calibrateParameters(tenors, yields, tau)
    
#    def calibrateCurveParametersDL(self, currency = 'USD', tau = 1, lag = 1):
#        """ 
#        Calibrates curve parameters under the Diebold & Li Model 
#        """           
#        self._dlCurve.calibrateDieboldLi(currency = currency, tau = tau, lag = lag)

    def calibrateCurveParametersDL(self, yields, tenor, tau = 1, lag = 1):
        """ 
        Calibrates curve parameters under the Diebold & Li Model 
        """           
        parameters = self._dlCurve.calibrateDieboldLi(yields, tenor, tau = tau, lag = lag)
        return parameters
    
    def yieldCurve(self, tenors, yields):
        params = self.calibrateCurveParametersDL(yields,tenors)
        return self._dlCurve.nelsonSiegelCurve(tenors,params[-1])
        
    def shiftYieldCurve(self, parallel = 0, slope = 0, curvature = 0, tau = 0):
        #Función que genera una nueva yieldCurve en base a los shifts ingresados
      
        shiftedRates = rates()
        shiftedRates._dlCurve = self._dlCurve.factorShift(parallel = parallel, slope = slope, curvature = curvature, tau = tau)
        
        return shiftedRates
        

class nelsonSiegel(object):
    #Clase especializada en calcular una curva basado en los parámetros de N&S, o calibrar sus parámetros en base a los datos
    """
    The nelsonSiegel class generates a curve based on the N&S parameters. This 
    class is also capable of calibrating the parameters based on the input data.
    """
    def __init__(self, parameters = None):
        """
        The input is an array of parameters.
        """
        self._parameters = parameters
        #Los siguientes son los yields y tenores usados para estimar los parámetros de Nelson y Siegel
        self._tenors = None
        self._yields = None

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
        
    def parameters(self):
        """
        This method gives as an output the parameters expressed as a DataFrame.
        """
        return pd.DataFrame([self._parameters], columns = ['tau','b0','b1','b2'])
        
    def nelsonSiegelForwardCurve(self, tenors, parameters = None):
        
        """
        The forward curves are computed for each of the tenors, based on the 
        parameters. If no parameters are introduced the calibrated parameters 
        will be used. The inputs are an array of tenors and an array of 
        parameters (optional). The output is a DataFrame that contains the 
        rates for each of those tenors.
        """
        
        if not parameters:
            parameters = self._parameters
        if not parameters:
           return False
        
        b0, b1, b2 = parameters[1:4]
        tau = float(parameters[0])
        
        yc = b0 + b1*np.exp(-tenors/tau) + b2*(-tenors/tau)*np.exp(-tenors/tau)  
        
        return pd.DataFrame(yc)
    
    def slope(self, tenors, parameters = None):
        """
        This method calculates the slope component for each tenor provided and 
        the respective parameters (optional). The inputs are an array of tenors
        and an array of parameters. The output is a DataFrame that contains the
        slopes for each tenor.
        inputs: array, array
        output: DataFrame
        """
        
        if not parameters:
            parameters = self._parameters
        if not parameters:
           return False
           
        b1 = parameters[2]
        tau = float(parameters[0])
        yc = b1*np.exp(-tenors/tau)
        
        return pd.DataFrame(yc)
        
    def curvature(self, tenors, parameters = None):
        """
        This method calculates the curvature component for each tenor provided 
        and the respective parameters (optional). The inputs are an array of 
        tenors and an array of parameters. The output is a DataFrame that 
        contains the slopes for each tenor.
        inputs: array, array
        output: DataFrame
        """
        if not parameters:
            parameters = self._parameters
        if not parameters:
           return False
           
        b2 = parameters[3]
        tau = float(parameters[0])
        yc = b2*(-tenors/tau)*np.exp(-tenors/tau)
        
        return pd.DataFrame(yc)
           
    def calibrateParameters(self, tenors, yields, tau = 1):
        
        """
        This is the method in charge of getting the parameters based on the
        provided tenors and yields. The inputs are an array of tenors, an
        array of yields and an integer that represents the value of tau.
        inputs: array, array, int
        output: array
        """
        x0 = np.array([0.1, 0.1, 0.1])
        param = leastsq(self.nelsonSiegelCurveResiduals, x0, args = (tenors, yields, tau))
        self._tenors = tenors
        self._yields = yields
        self._parameters = [tau] + param[0].tolist()
        
        return np.array(self._parameters)
    
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
        
    def plot(self, tenor = np.array([]), style = 'fivethirtyeight'):
        """
        The plot method generates a graph for the yield curve with the 
        appropriate desgin. The input is an array with the tenors. The output
        is a line plot that represents the yield curve.
        inputs: array
        output: graph
        """
        with plt.style.context((style)):
            plt.plot(tenor,self.nelsonSiegelCurve(tenor, self._parameters))
            plt.scatter(self._tenors, self._yields)
            plt.title('N&S Calibrated Curve')
        plt.show()
    
    def factorShift(self, parallel = 0, slope = 0, curvature = 0, tau = 0):
        #Función que desplaza la curva para cada factor especificado
        """
        The shift method was constructed to stress any of the factors that
        determine the shape of the curve: level, slope or curvature. To do
        that, the function generates a new set of parameters and recalculates
        the curve based on those values. The input is an integer that
        represents a parallel shift in the curve, an integer that represents
        a change in the slope of the curve, an integer that represents the
        change in the curvature of the curve, and/or the change in the value of
        the parameter tau.
        
        """
        shift = [tau, parallel, slope, curvature]
        parameters = [a + b for a,b in zip(self._parameters, shift)]

        return nelsonSiegel(parameters = parameters)
        
        
class dieboldLi(nelsonSiegel):
    """
    The dieboldLi class generates a curve based on the D&L parameters. This 
    class is also capable of calibrating the parameters based on the input data.
    This class inherits the features of the nelsonSiegel class.
    """
    def __init__(self, parameters = None):
        super(dieboldLi, self).__init__(parameters = parameters)
        self._parametersHistorical = None
        self._tenorsHistorical = None
        self._yieldsHistorical = None
        
    def parametersHistorical(self):
        """
        This method shows the historical values of the parameters: tau, level,
        slope and curvature.
        """        
        return pd.DataFrame(self._parametersHistorical, columns = ('tau','b0','b1','b2'), index = pd.to_datetime(self._dates))
        
    def calibrateParametersHistorical(self, tenors, yields, tau = 1):
        """
        This method calculates the historical parameters for the provided
        tenors and yields. The inputs are an array of tenors, an array of
        yields, and tau (an integer).
        inputs: array, array, float
        output: DataFrame
        """
        
        yieldCurve = yields.values
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

        
    def parametersAR(self, lag = 1):
#        OLS(self.parametersHistorical()['b0'], self.parametersHistorical()['b0'][])
#        self._arModel = (AR(self.parametersHistorical()['b0']).fit(lag), AR(self.parametersHistorical()['b1']).fit(lag), AR(self.parametersHistorical()['b2']).fit(lag))
        self._varModel = VAR(self.parametersHistorical()[['b0', 'b1', 'b2']]).fit(lag)
        self._varModel.summary()
        return True

    def calibrateDieboldLi(self, yields, tenor, tau = 1, lag = 1):
        
        yieldCurve = yields
        tenors = tenor
        par = self.calibrateParametersHistorical(np.array(tenors), yieldCurve, tau = tau)
        self._dates = yields.index
        self.parametersAR(lag = lag)
        return par
        
    def setNSParameters(self, position = -1):
        
        self._parameters = self._parametersHistorical[position]
        self._tenors = self._tenorsHistorical[position]
        self._yields = self._yieldsHistorical[position]
        
    def forecastDLParameters(self, initialParameters = None, steps = 1, alpha = 0.05):
        #Función que proyecta parámetros Diebold Li a futuro
        """
        inputs : array, int
        output: array
        """
        assert not isinstance(self._varModel, VAR), "Theres no model yet. Run calibrateDieboldLi first"
        
        if initialParameters is None:
            initialParameters = self._parameters
            
        parameters = np.array([initialParameters[1:4]])
        
        return self._varModel.forecast_interval(parameters, steps, alpha = alpha), initialParameters
     
    def plotForecastedCurve(self, tenor, initialParameters = None, steps = 1, alpha = 0.05, style = 'fivethirtyeight', error = True):
        #Función que grafica forecast de curva, junto con error
        forecast, initialParameters = self.forecastDLParameters(initialParameters = initialParameters, steps = steps, alpha = alpha)
        
        baseParameter = initialParameters
        fcParameter = [baseParameter[0]] + forecast[0][-1].tolist()
        topParameter = [baseParameter[0]] + forecast[1][-1].tolist()
        bottomParameter = [baseParameter[0]] + forecast[2][-1].tolist()
        
        with plt.style.context(style, after_reset = True):
            plt.plot(tenor,self.nelsonSiegelCurve(tenor, baseParameter), linewidth = 2.0)
            plt.plot(tenor,self.nelsonSiegelCurve(tenor, fcParameter), 'w.')
            if error:
                plt.plot(tenor,self.nelsonSiegelCurve(tenor, topParameter), 'w--')
                plt.plot(tenor,self.nelsonSiegelCurve(tenor, bottomParameter), 'w--')
                plt.text(0.2, 0.7, """$\\alpha$ = %s"""%alpha, transform =  plt.gca().transAxes)   
                
            plt.ylabel('%')
            plt.title('%s Months Projection for %s calibrated curve'%(str(steps),self._currency))
                 
        plt.show()
        
if __name__ == '__main__':
#    ns = nelsonSiegel(np.array([1, 0.2, -0.8, 0.01]))
#    yc = ns.nelsonSiegelCurve(np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
#    plt.plot(yc)
#    tau = 1
#    param = ns.calibrateParameters(np.array([1,3,5,10,30]), np.array([0.5, 0.75, 1, 2.1, 2.5]), tau = tau)
#    tenor = np.array(range(1,30))
#    ns.plot(tenor)
#    ns2 = ns.factorShift(parallel = 0.1)
#    ns2.plot(tenor)
#    
#    ns3 = ns2.factorShift(slope = 0.1)
#    ns3.plot(tenor)
#    
#    dl = dieboldLi()
##    tenor, yields = dl.getHistoricalYields('USD')
##    dl.calibrateDieboldLi('EUR', tau = tau, lag = 1)
#    dl.setNSParameters()
##    dl.plot(tenor)
#    #Efecto de respuesta impulso a 2 años frente a un movimiento en los factores:
##    dl._varModel.irf(24).plot()
#    
##    forecast = dl.forecastDLParameters(steps = 1)
##    
#    dl.plotForecastedCurve(tenor, steps = 6, alpha = 0.5, error = True, style =['fivethirtyeight'] )
##
  # Curva Chile (CLP)
  # Cargar datos y construir series de tiempo de yields de la curva  
    data = pd.read_excel('L:\Rates & FX\Quant Analysis\pytest\chileYieldCurve.xlsx')
    yields = data[1:]
    yields.columns = data.columns
    tenor = yields.columns
  # Calibracion de parametros
    dl = dieboldLi()
    params = dl.calibrateParametersHistorical(np.array(yields.columns), yields.fillna(method='backfill').as_matrix())
#    r = rates()
#    parameters = r.calibrateCurveParametersDL(yields,yields.columns)
#    yc = r.yieldCurve(yields.columns,yields)
#    dl.plotForecastedCurve(yields.columns,parameters)
    dl.calibrateDieboldLi(yields,tenor)
    dl.plot(tenor)
    dl._varModel.irf(24).plot()
    forecast = dl.forecastDLParameters(steps = 1)
    dl.plotForecastedCurve(tenor, steps = 6, alpha = 0.5, error = True, style =['fivethirtyeight'])