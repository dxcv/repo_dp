# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 10:03:50 2016

@author: ngoldbergerr
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime
from tia.bbg import v3api
from matplotlib import rc
import calendar
rc('mathtext', default='regular')
import matplotlib


class outlook(object):

    def __init__(self):
        self.x = 1

    def getLocalCurveInstrumentsFromBBG(self, country = 'CL'):
        countryDict = {'CL': 'YCGT0351 Index', 'CLi': 'YCGT0362 Index'}
        bbg_tickers = [countryDict[country]]
        
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        try:
            response = LocalTerminal.get_reference_data(bbg_tickers, ['curve_tenor_rates'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False

        curve_instruments = pd.DataFrame(response.as_frame()['curve_tenor_rates'].values[0])
        
        return curve_instruments


    def getBEI(self, country='Chile'):
        countryDict = {'Chile': ['CL', 'CLi']}
        nominal = self.getLocalCurveInstrumentsFromBBG(countryDict['Chile'][0])
        real = self.getLocalCurveInstrumentsFromBBG(countryDict['Chile'][1])
        BEI = nominal['Mid Yield']-real['Mid Yield']
        return BEI
        
        
    def getInflationExpectations(self):
        tickers = ['CFNP1 Curncy', 'CFNP2 Curncy', 'CFNP3 Curncy',
                   'CFNP4 Curncy', 'CFNP5 Curncy', 'CFNP6 Curncy', 
                   'CFNP7 Curncy', 'CFNP8 Curncy', 'CFNP9 Curncy', 
                   'CFNP10 Curncy', 'CFNP11 Curncy', 'CFNP12 Curncy', 
                   'CFNP13 Curncy', 'CFNP14 Curncy', 'CFNP15 Curncy', 
                   'CFNP16 Curncy', 'CFNP17 Curncy']
                       
        # Descarga de datos para los forwards de CLF
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        try:
            response = LocalTerminal.get_reference_data(tickers, ['SETTLE_DT','PX_LAST'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False
        
        inflation_expectations = response.as_frame()
    
        # Descarga y agrega el dato del ultimo valor de CLF al DataFrame
        response = LocalTerminal.get_reference_data('CHUF Index', ['LAST_UPDATE_DT','PX_LAST'], ignore_security_error = 1, ignore_field_error = 1)
        uf = response.as_frame()        
        uf.columns = ['SETTLE_DT','PX_LAST']
        inflation_expectations = inflation_expectations.append(uf).sort_values('SETTLE_DT')

        # Agrega la lista de 9 de mes para cada forward
        inflation_expectations['ACTUAL_DAYS'] = 1
        inflation_expectations['Forecast CPI'] = 0
        original_index = inflation_expectations.index
        inflation_expectations.index = range(0,len(inflation_expectations))
        for x in range(1,len(inflation_expectations)):
            date_nine = inflation_expectations['SETTLE_DT'].loc[x-1].to_datetime()+datetime.timedelta(days=-(inflation_expectations['SETTLE_DT'].loc[x-1].day-9))
#            number_of_days_between = int((inflation_expectations['NINETH_DAY'][1]-inflation_expectations['SETTLE_DT'][0]).days)
            number_of_days_between = int((inflation_expectations['SETTLE_DT'].loc[x]-date_nine).days)
            days_in_month = calendar.monthrange(inflation_expectations['SETTLE_DT'].loc[x-1].to_datetime().year, inflation_expectations['SETTLE_DT'].loc[x-1].to_datetime().month)[1]
            inflation_expectations['ACTUAL_DAYS'].loc[x] = float(days_in_month)/number_of_days_between
            inflation_expectations['Forecast CPI'].loc[x]  = ((float(inflation_expectations['PX_LAST'].loc[x])/inflation_expectations['PX_LAST'].loc[x-1])**inflation_expectations['ACTUAL_DAYS'].loc[x]-1)*100
            
        inflation_expectations.index = original_index
        return inflation_expectations
        
        
    def getHistoricalInflation(self, dateInitial, dateFinal):
        LocalTerminal = v3api.Terminal('localhost', 8194)
        try:
            response = LocalTerminal.get_historical(['CNPINSMO Index'], ['PX_LAST'], ignore_security_error = 1, ignore_field_error = 1, start = dateInitial, end = dateFinal)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False
            
        inflation_historical = response.as_frame()['CNPINSMO Index']
        
        return inflation_historical
        
        
    def getInflation(self,init='2015-02-03',end='2016-10-11'):
        historical = self.getHistoricalInflation(init,end)
        historical.columns = ['CPI']
        
        expected = self.getInflationExpectations()
        date_list = [historical.index[-1].to_datetime()+datetime.timedelta(days=30*i) for i in range(1,len(expected))]
        future_inf = pd.DataFrame(data = np.round(expected['Forecast CPI'][1:].values,1), columns = ['CPI'])
        future_inf.index = date_list
        
        cpi_mom = historical.append(future_inf)
        dates_index = cpi_mom.index[11:]
        cpi_mom.index = range(0,len(cpi_mom))
        cpi_yoy = pd.DataFrame(columns = ['CPI'])
        for i in range(11,len(cpi_mom)):
            cpi_yoy.loc[i-11] = np.round(((1+cpi_mom[i-11:i+1]/100).prod()-1)*100,2)
            
        cpi_yoy.index = dates_index
        return cpi_yoy
        

    def getInflationYoY(self,init='2015-02-03',end='2016-10-11'):
        LocalTerminal = v3api.Terminal('localhost', 8194)
        try:
            response = LocalTerminal.get_historical(['CNPINSYO Index'], ['PX_LAST'], ignore_security_error = 1, ignore_field_error = 1, start = init, end = end)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return False
            
        inflation_historical_yoy = response.as_frame()['GTCOP10Y Govt']
        
        return inflation_historical_yoy    
        
        
    def graphExpectedInflation(self):
        matplotlib.style.use('ggplot')
        ie = self.getInflationExpectations()
        ie.index = range(0,len(ie))
        ie['Period'] = [calendar.month_name[(ie['SETTLE_DT'].loc[x].to_datetime()-datetime.timedelta(days=60)).month][0:3]+' '+str((ie['SETTLE_DT'].loc[x].to_datetime()-datetime.timedelta(days=60)).year) for x in range(0,len(ie))]
        fig = plt.figure();
        ie.index = ie['Period']
        ax = ie['Forecast CPI'][1:].plot(kind='bar', color = ['DarkBlue'])
        plt.xlabel('',fontsize = 18)
        plt.ylabel('IPC Implicito (%)',fontsize = 18)
        plt.title('IPC (MoM) Implicita en Forwards UF',fontsize = 20)
        plt.yticks(fontsize = 16)
        plt.xticks(fontsize = 16)
        plt.tight_layout()
        fig.set_size_inches(14.5, 9.5)
        for p in ax.patches:
            ax.annotate(str(round(p.get_height(),2)), (p.get_x() * 1.001, p.get_height() * 1.006), size=12)
        return

#    def graphInflation(self):
#        matplotlib.style.use('bmh')
#        inf = self.getInflation(init='2015-02-03',end='2016-10-11')
#        before_color = (inf.index <= datetime.datetime.today()).sum()
#        after_color = len(inf)-before_color
#        colors = ['DarkBlue']*before_color + ['Gray']*after_color
#        inf['Period'] = [calendar.month_name[(inf.index[x].to_datetime()).month][0:3]+' '+str((inf.index[x].to_datetime()).year) for x in range(0,len(inf))]
#        inf.index = inf['Period']
#        fig = plt.figure();
#        ax = inf['CPI'].plot(kind='bar', color = colors)
#        plt.xlabel('',fontsize = 18)
#        plt.ylabel('IPC (%)',fontsize = 18)
#        plt.title('IPC Historico y Proyeccion Forwards UF',fontsize = 20)
#        plt.yticks(fontsize = 16)
#        plt.xticks(fontsize = 14)
#        plt.tight_layout()
#        fig.set_size_inches(14.5, 9.5)
#        for p in ax.patches:
#            ax.annotate(str(round(p.get_height(),1)), (p.get_x() * 1.001, p.get_height() * 1.006), size=12)

#        bmap = brewer2mpl.get_map('Set1','qualitative',2,reverse=True)
#        colors = bmap.mpl_colors
#        inf['CPI'].plot(color=colors,kind='bar')
            
        return

###############################################################################
###############################################################################

    def graphInflation(self):
        matplotlib.style.use('bmh')
        inf = self.getInflationYoY(init='2015-02-03',end='2016-10-11')
        before_color = (inf.index <= datetime.datetime.today()).sum()
        after_color = len(inf)-before_color
        colors = ['DarkBlue']*before_color + ['Gray']*after_color
        inf['Period'] = [calendar.month_name[(inf.index[x].to_datetime()).month][0:3]+' '+str((inf.index[x].to_datetime()).year) for x in range(0,len(inf))]
        inf.index = inf['Period']
        inf.columns = ['CPI','Period']
        fig = plt.figure();
        ax = inf['CPI'].plot(kind='bar', color = colors)
        plt.xlabel('',fontsize = 18)
        plt.ylabel('IPC (%)',fontsize = 18)
        plt.title('IPC Historico y Proyeccion Forwards UF',fontsize = 20)
        plt.yticks(fontsize = 16)
        plt.xticks(fontsize = 14)
        plt.tight_layout()
        fig.set_size_inches(14.5, 9.5)
        for p in ax.patches:
            ax.annotate(str(round(p.get_height(),1)), (p.get_x() * 1.001, p.get_height() * 1.006), size=12)
        return

###############################################################################
###############################################################################

if __name__ == '__main__':

    o = outlook()
#    bei = o.getBEI()
#    ie = o.getInflationExpectations()
#    cpi = o.getInflation()
    o.graphExpectedInflation()
    o.graphInflation()