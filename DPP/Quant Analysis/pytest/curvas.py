"""
Created on Mon Feb 08 11:15:33 2016

@author: ngoldberger
"""
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
from datetime import datetime as dtime
from scipy.optimize import leastsq
from statsmodels.tsa.vector_ar.var_model import VAR

import plotly.plotly as py
import plotly.graph_objs as go

class nelsonSiegel(object):

### Nelson & Siegel

    def __init__(self, parameters = None):
        
        self._parameters = parameters
        # Los siguientes son los yields y tenores usados para estimar los 
        # parámetros de Nelson y Siegel
        self._tenors = None
        self._yields = None

    ### Core Functions

    def plotNSCurve(self, tenor = np.array([]), style = 'ggplot'):
        """
        The plot method generates a graph for the yield curve with the 
        appropriate desgin. The input is an array with the tenors. The output
        is a line plot that represents the yield curve.
        inputs: array
        output: graph
        """
        
        trace1 = go.Scatter(
        x = tenor,
        y = self.nelsonSiegelCurve(tenor, self._parameters),
        mode = 'lines',
        name = 'Curva Ajustada (NS)'
        )
        
        trace2 = go.Scatter(
        x = self._tenors,
        y = self._yields,
        mode = 'markers',
        name = 'Yields'
        )

        data = [trace1,trace2]
        
        layout = go.Layout(
            title='Yield Curve (Nelson & Siegel Model)',
            xaxis=dict(
                title='Tenor',
                titlefont=dict(
                    family='Courier New, monospace',
                    size=18,
                    color='#7f7f7f'
                )
            ),
            yaxis=dict(
                title='Yield (%)',
                titlefont=dict(
                    family='Courier New, monospace',
                    size=18,
                    color='#7f7f7f'
                )
            )
        )
        
        fig = go.Figure(data = data, layout = layout)
        py.plot(fig, filename = 'Yield Curve')
    ### Support functions

    def calibrateParameters(self, tenors, yields, tau = 1):
        
        """
        This is the method in charge of getting the parameters based on the
        provided tenors and yields. The inputs are an array of tenors, an
        array of yields and an integer that represents the value of tau.
        inputs: array, array, int
        output: array
        """
        x0 = np.array([0.1, 0.1, 0.1])
        param = leastsq(self.nelsonSiegelCurveResiduals, x0, args = (tenors, \
        yields, tau))
        
        self._tenors = tenors
        self._yields = yields
        self._parameters = [tau] + param[0].tolist()
        
        return np.array(self._parameters)

    def nelsonSiegelCurve(self, tenors, parameters = None):
        # A partir de los tenores ingresados entrega los puntos de la curva de 
        # tasas para los parámetros ingresados o lo guardados
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
            print("""There are no parameters calibrated for the curve. Run
            calibrateParameters first.""")
            return False
              
        b0, b1, b2 = parameters[1:4]
        tau = float(parameters[0])
        
        yc = b0 + b1*(1 - np.exp(-tenors/tau))/(tenors/tau) + b2*((1 -  
             np.exp(-tenors/tau))/(tenors/tau) - np.exp(-tenors/tau))
        
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
        
        return err

    def getHistoricalYields(self, currency):
        """
        inputs: str
        output: DataFrame
        """
        path = 'G:/DAT/GII/MES_INT/INVINTER/Matlab Programas/packagePY/DB/riskFactors.db'
        
        with sqlite3.connect(path) as con:
            cur = con.cursor()
            
            cur.execute("""CREATE TEMP TABLE TEMPDATA AS 
            SELECT DATE, IDENTIFIER, DATA FROM rfData
            WHERE IDENTIFIER IN 
            (SELECT IDENTIFIER FROM rfClasification WHERE CURRENCY = ? AND 
            NAME IN (SELECT NAME FROM rfNameExposures WHERE TYPE = 'Curve')
            )""", (currency,))
            
            cur.execute("""SELECT a.DATE, c.TENOR, a.DATA FROM
            TEMPDATA a,
            rfClasification b,
            rfNameExposures c
            WHERE a.IDENTIFIER = b.IDENTIFIER AND b.NAME = c.NAME
            ORDER BY a.DATE, c.TENOR""")
            
            dataTmp = cur.fetchall()
        
        yieldCurveRaw = pd.DataFrame(dataTmp, columns = ['date', 'tenor', 
                                                         'yield'])
        yieldCurve = yieldCurveRaw.pivot(index = 'date', columns = 'tenor', 
                                         values = 'yield')

        return yieldCurve
        
    ### Functions to call variables
    @property
    def parameters(self):
        """
        This method gives as an output the parameters expressed as a DataFrame.
        """
        return pd.DataFrame([self._parameters], columns = \
                            ['tau','b0','b1','b2'])


class dieboldLi(nelsonSiegel):
    
### Diebold & Li

    def __init__(self, parameters = None):
        super(dieboldLi, self).__init__(parameters = parameters)
        self._parametersHistorical = None
        self._tenorsHistorical = None
        self._yieldsHistorical = None    

    ### Core Functions
    '''
    This functions plots the forecasted yield curve and its respective confidence 
    interval. To do this it requires the calibrated parameters, and the
    Nelson&Siegel curve fitting function.
    '''
    def plotForecastedCurve(self, tenor, initialParameters = None, steps = 1, alpha = 0.05, style = 'dark_background', error = True):
        #Función que grafica forecast de curva, junto con error
        initialParameters = self.parametersHistorical().iloc[-1]
        forecast, initialParameters = self.forecastDLParameters(initialParameters = initialParameters, steps = steps, alpha = alpha)
        
        baseParameter = initialParameters
        fcParameter = [baseParameter[0]] + forecast[0][-1].tolist()
        topParameter = [baseParameter[0]] + forecast[1][-1].tolist()
        bottomParameter = [baseParameter[0]] + forecast[2][-1].tolist()
#        
#        with plt.style.context(style, after_reset = True):
#            plt.plot(tenor,self.nelsonSiegelCurve(tenor, baseParameter), linewidth = 1.0)
#            plt.plot(tenor,self.nelsonSiegelCurve(tenor, fcParameter), 'w.')
#            if error:
#                plt.plot(tenor,self.nelsonSiegelCurve(tenor, topParameter), 'w--')
#                plt.plot(tenor,self.nelsonSiegelCurve(tenor, bottomParameter), 'w--')
#                plt.text(0.2, 0.7, """$\\alpha$ = %s"""%alpha, transform =  plt.gca().transAxes)   
#                
#            plt.ylabel('%')
#            plt.title('%s Months Projection for %s calibrated curve'%(str(steps),self._currency))
#                 
#        plt.show()


#        x = [2, 3, 5, 7, 10, 30]
        x = tenor
        x_rev = x[::-1]
        
        # Line 1
        y1 = self.nelsonSiegelCurve(tenor, fcParameter)
        y1_upper = self.nelsonSiegelCurve(tenor, bottomParameter)
        y1_lower = self.nelsonSiegelCurve(tenor, topParameter)
        y1_lower = y1_lower[::-1]
        
        
        trace1 = go.Scatter(
            x=x+x_rev,
            y=y1_upper+y1_lower,
            fill='tozerox',
            fillcolor='rgba(0,100,80,0.2)',
            line=go.Line(color='transparent'),
            showlegend=False,
            name='Fair',
        )

        trace4 = go.Scatter(
            x=x,
            y=y1,
            line=go.Line(color='rgb(0,100,80)'),
            mode='lines',
            name='Fair',
        )

        data = go.Data([trace1, trace4])
        
        layout = go.Layout(
            paper_bgcolor='rgb(255,255,255)',
            plot_bgcolor='rgb(229,229,229)',
            xaxis=go.XAxis(
                gridcolor='rgb(255,255,255)',
                range=[1,37],
                showgrid=True,
                showline=False,
                showticklabels=True,
                tickcolor='rgb(127,127,127)',
                ticks='outside',
                zeroline=False
            ),
            yaxis=go.YAxis(
                gridcolor='rgb(255,255,255)',
                showgrid=True,
                showline=False,
                showticklabels=True,
                tickcolor='rgb(127,127,127)',
                ticks='outside',
                zeroline=False
            ),
        )
        
        fig = go.Figure(data = data, layout = layout)
        py.plot(fig, filename = 'Yield Curve')

    ### Support functions

    ### Support Functions
    def calibrateParametersHistorical(self, tenors, yields, tau = 1):
        """
        This method calculates the historical parameters for the provided
        tenors and yields. The inputs are an array of tenors, an array of
        yields, and tau (an integer).
        inputs: array, array, float
        output: DataFrame
        """
        
        yieldCurve = zip(tenors, yields)
        param= []
        x0 = np.array([0.1, 0.1, 0.1])
        
        for t,y in yieldCurve:
            
            x0 = leastsq(self.nelsonSiegelCurveResiduals, x0, args = (t, y, tau))
            x0 = x0[0]
            param.append([tau] + x0.tolist())
            
        self._tenorsHistorical = tenors
        self._yieldsHistorical = yields
        self._parametersHistorical = param
        
        return param    

    def parametersVAR(self, lag = 1):
        self._varModel = VAR(self.parametersHistorical()[['b0', 'b1', 'b2']]).fit(lag)
        self._varModel.summary()
        return True
    
    def calibrateDieboldLi(self, currency = 'USD', tau = 1, lag = 1):
        
        yieldCurve = self.getHistoricalYields(currency)
        tenors = [yieldCurve.columns.tolist()] * len(yieldCurve)
        yields = yieldCurve.values.tolist()
        self.calibrateParametersHistorical(np.array(tenors), np.array(yields), tau = tau)
        self._dates = [dtime.strptime(datestr,"%Y-%m-%d").date() for datestr in yieldCurve.index]
        self.parametersVAR(lag = lag)
        self._currency = currency

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
    
    ### Functions to call variables
    def parametersHistorical(self):
        """
        This method shows the historical values of the parameters: tau, level,
        slope and curvature.
        """        
        return pd.DataFrame(self._parametersHistorical, columns = ('tau','b0',
                            'b1','b2'), index = pd.to_datetime(self._dates))


### Sample

if __name__ == '__main__':
#    ns = nelsonSiegel()
#    yields = ns.getHistoricalYields('USD').iloc[-1]
#    ns.calibrateParameters(yields.index, yields, tau = 10)
#    ns.plotNSCurve(np.array(range(1,30)))
    
    dl = dieboldLi()
    yields = dl.getHistoricalYields('USD')
#    dl.calibrateParametersHistorical(yields.index,yields,tau = 10)
    dl.calibrateDieboldLi('USD',tau = 10, lag = 1)
    dl.forecastDLParameters(dl.parametersHistorical().iloc[-1])
    dl.plotForecastedCurve(yields.columns, steps = 6, alpha = 0.05, error = True)
    
    