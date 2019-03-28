# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 12:10:42 2016

@author: ngoldbergerr
"""

import sys
sys.path.insert(0,"""F:\Quant Analysis\portfolioManager\RatesAnalysis""")
sys.path.insert(0,"""L:\Rates & FX\Quant Analysis\portfolioManager\Monitors""")
import xlrd
import pandas as pd
import numpy as np
import datetime as dt
import os.path
import sys
from scipy.optimize import fmin
from tia.bbg import v3api
#from scipy import interpolate
import matplotlib.pyplot as plt
import outlook
from dateutil.relativedelta import relativedelta

class rates(object):
    
    def __init__(self, path = 'L:\Rates & FX\Quant Analysis\portfolioManager\RatesAnalysis'):
        self.XLpath = path

### Zero Rates Table

    def createRatesTable(self):
        # Crear la tabla con la tasa cero para todas las fechas
        tpm = self.getTPMforecast()
        prob = self.getProbabilities()
        days = np.arange(1,11000)
        dates = [tpm.index[0]+dt.timedelta(days = x) for x in range(1,11000)]
        index = pd.date_range(dates[0],dates[-1])
        short_rate = tpm.reindex(index).append(tpm[-1:])
        short_rate[0:1] = 3.5
#        short_rate= short_rate.fillna(method='ffill')[:-1]
        short_rate = short_rate[:-1].apply(pd.Series.interpolate)
        factor = short_rate.divide(36000) + 1
        days = pd.DataFrame(data = [days, days, days, days], index = factor.columns, columns = factor.index).transpose()
        Z = pd.DataFrame(index = factor.index, columns = factor.columns)
        dFactor = pd.DataFrame(index = factor.index, columns = factor.columns)
        Z[0:1] = (factor[0:1]**365-1)*100
        dFactor[0:1] = 1
#        Z[0:1] = 1/factor[0:1]
        for i in Z.index[1:]:
            Z.loc[i] = 100*(((1+Z.loc[i-dt.timedelta(1)]/100)**(days.loc[i-dt.timedelta(1)]/365)*factor.loc[i])**(365/days.loc[i])-1)
#            Z.loc[i] = 1/((1+Z.loc[i-dt.timedelta(1)]/100)**(days.loc[i-dt.timedelta(1)]/365)*factor.loc[i])
#            Z.loc[i] = 1/((1+short_rate.loc[i-dt.timedelta(1)]/100)**(days.loc[i-dt.timedelta(1)]/365)) # Factores de descuento
            dFactor.loc[i] = 1/((1+Z.loc[i]/100)**(days.loc[i]/365))
        return days, dates, short_rate, factor, dFactor, prob, Z

    def getInflationforecast(self):
        # Toma las proyecciones de inflación de las tablas input del usuario
        wb = xlrd.open_workbook(os.path.join(self.XLpath,'rates.xlsx'))
        sh = wb.sheet_by_index(0)
        i = self.get_cell_range(sh,0,2,0,4)
        d = self.get_cell_range(sh,1,2,1,4)
        b = self.get_cell_range(sh,4,2,4,4)
        h = self.get_cell_range(sh,7,2,7,4)
        inflation_index = [x[0].value for x in i]
        dove_inflation = [x[0].value for x in d]
        base_inflation = [x[0].value for x in b]
        hawk_inflation = [x[0].value for x in h]
        out = pd.DataFrame([dove_inflation, base_inflation, hawk_inflation]).transpose()
        out.index = inflation_index
        out.columns = ['Dove','Base','Hawk']
        out['Average'] = out.mean(axis=1)
        return out
        
    def getTPMforecast(self):
        # Toma las proyecciones de TPM de las tablas input del usuario
        wb = xlrd.open_workbook(os.path.join(self.XLpath,'rates.xlsx'))
        sh = wb.sheet_by_index(0)
        dTPM= self.get_cell_range(sh,0,5,0,26)
        d = self.get_cell_range(sh,1,5,1,26)
        b = self.get_cell_range(sh,4,5,4,26)
        h = self.get_cell_range(sh,7,5,7,26)
        av = self.get_cell_range(sh,10,5,10,26)
        datesTPM = [xlrd.xldate.xldate_as_datetime(x[0].value, wb.datemode) for x in dTPM]
        dove_tpm = [x[0].value for x in d]
        base_tpm = [x[0].value for x in b]
        hawk_tpm = [x[0].value for x in h]
        avg_tpm = [x[0].value for x in av]
        out = pd.DataFrame([dove_tpm, base_tpm, hawk_tpm, avg_tpm], index=['Dove','Base','Hawk','Average'], columns=datesTPM).transpose()
#        out['Average'] = out.mean(axis=1)
#        out['Average'] = out*prob
        return out

    def getProbabilities(self):
        # Toma las probabilidades de los tres escenarios de las tablas input del usuario
        wb = xlrd.open_workbook(os.path.join(self.XLpath,'rates.xlsx'))
        sh = wb.sheet_by_index(0)
        ddd = self.get_cell_range(sh,0,1,0,1)[0]
        bbb = self.get_cell_range(sh,3,1,3,1)[0]
        hhh = self.get_cell_range(sh,6,1,6,1)[0]
        dove_prob = ddd[0].value
        base_prob = bbb[0].value
        hawk_prob = hhh[0].value
        out = pd.DataFrame([dove_prob, base_prob, hawk_prob], columns=['Probability'], index=['Dove','Base','Hawk']).transpose()
        out['Average'] = out.sum(axis=1)
        return out
        
    def get_cell_range(self,sheet, start_col, start_row, end_col, end_row):
        return [sheet.row_slice(row, start_colx=start_col, end_colx=end_col+1) for row in xrange(start_row, end_row+1)]
    
### Price Local Bonds
    def getLocalCurveInstrumentsFromBBG(self, country = 'CL'):
        countryDict = {'CL': 'YCFC1FN9 Index'}
        bbg_tickers = [countryDict['CL']]
        
        LocalTerminal = v3api.Terminal('localhost', 8194)      
        try:
            response = LocalTerminal.get_reference_data(bbg_tickers, ['CURVE_TENOR_RATES'], ignore_security_error = 1, ignore_field_error = 1)
            print response.as_frame()['CURVE_TENOR_RATES'].values[0]
        except: 
            print("Unexpected error:", sys.exc_info()[0])   
            return False

        curve_instruments = pd.DataFrame(response.as_frame()['CURVE_TENOR_RATES'].values[0])
        
        return curve_instruments

    def getLocalCurveInstrumentsFromExcel(self):
        wb = xlrd.open_workbook(os.path.join(self.XLpath,'rates.xlsx'))
        sh = wb.sheet_by_index(1)
        tickers = self.get_cell_range(sh,0,0,0,25)
        tenor = self.get_cell_range(sh,1,0,1,25)
        tick = [tickers[x][0] for x in range(0,len(tickers))]
        ten = [x[0].value for x in tenor]
        out = pd.DataFrame(data = [tick, ten], index=['Tenor Ticker','Tenor']).transpose()
        return out
        
    def getLocalCurveInstrumentsFromUser(self):
        ticker = ['EI964335 Corp', 'EG316074 Corp', 'EJ237864 Corp', 'EI553642 Corp', 'EJ591386 Corp', 'EH381904 Corp', 'EJ716536 Corp','JK818218 Corp',
        'EI120454 Corp', 'EK936444 Corp', 'AF217465 Corp', 'EI577823 Corp', 'JK950287 Corp', 'EJ041155 Corp','EJ111061 Corp', 'EJ591441 Corp', 
        'EK274744 Corp', 'EK877544 Corp', 'EJ041159 Corp', 'EK274762 Corp', 'EK985952 Corp', 'EJ529959 Corp']
        tenor = ['0,18Y','0,34Y','0,59Y','1,17Y','1,34Y','1,50Y','1,57Y','2,17Y','3,17Y','3,59Y','3,67Y','4,26Y','4,34Y','5,17Y','5,34Y',
                 '6,33Y','7,17Y','9,34Y','15,17Y','17,17Y','18,33Y','26,17Y']
        LocalTerminal = v3api.Terminal('localhost', 8194)   
        try:
            response = LocalTerminal.get_reference_data(ticker, ['SECURITY_NAME'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False
        name = [x for x in response.as_frame()['SECURITY_NAME']]
        out = pd.DataFrame(data = [ticker, tenor, name], index=['Tenor Ticker','Tenor', 'Name']).transpose()
        return out

    def getLocalCLFCurveInstrumentsFromUser(self):
        
        ticker = ['BCU0300318 Govt','BCU0300718 Govt' ,'BCU0300818 Govt','BCU0301018 Govt','BTU0300119 Govt','BCU0300519 Govt','BTU0300719 Govt','BTU0300120 Govt',
        'BCU0300221 Govt','BTU0150321 Govt','BTU0300122 Govt','BCU0300322 Govt','BCU0500922 Govt','BCU0300323 Govt','BTU0451023 Govt','BTU0300124 Govt','BTU0450824 Govt',
        'BTU0260925 Govt','BTU0150326 Govt','BTU0300327 Govt','BTU0300328 Govt','BCU0300528 Govt','BTU0300329 Govt','BTU0300130 Govt','BCU0300231 Govt','BTU0300132 Govt',
        'BTU0300134 Govt','BTU0200335 Govt','BTU0300338 Govt','BTU0300339 Govt','BTU0300140 Govt','BCU0300241 Govt','BTU0300142 Govt','BTU0300144 Govt']

        tenor = ['1,47Y','1,80Y','1,88Y','2,02Y','2,27Y','2,57Y','2,72Y','3,19Y','4,16Y','4,32Y','4,95Y','5,05Y','5,23Y','5,88Y','6,17Y','6,61Y','6,82Y','7,99Y',
                 '8,75Y','9,03Y','9,76Y','9,91Y','10,48Y','11,13Y','11,89Y','12,51Y','13,82Y','15,33Y','16,29Y','16,86Y','17,43Y','18,09Y','18,57Y','19,60Y']
        LocalTerminal = v3api.Terminal('localhost', 8194)   
        try:
            response = LocalTerminal.get_reference_data(ticker, ['SECURITY_NAME'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False
        name = [x for x in response.as_frame()['SECURITY_NAME']]
        out = pd.DataFrame(data = [ticker, tenor, name], index=['Tenor Ticker','Tenor', 'Name']).transpose()
        return out

    def getBondCashFlows(self, instrument):
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        try:
            response = LocalTerminal.get_reference_data(instrument, ['DES_CASH_FLOW_ADJ'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False
        cash_flows = pd.DataFrame(response.as_frame()['DES_CASH_FLOW_ADJ'].values[0])
        cash_flows['TCF'] = cash_flows['Interest']+cash_flows['Principal']
        del cash_flows['Interest']
        del cash_flows['Principal']
        
        return cash_flows
        
    def getBondPriceAndYield(self, instrument, days, dates, short_rate, factor, Z, prob, ZZ, x0=5, nominal = True):
#        if nominal:
#            days, dates, short_rate, factor, Z, prob, ZZ = r.createRatesTable()
#        else:
#            Z, days, dates = r.createInflationTable()
            
        cf = self.getBondCashFlows(instrument)
        DF = Z.loc[cf['Date']]
        price = pd.DataFrame(data = np.sum(DF.transpose().values*cf['TCF'].values, axis=1), index = DF.columns, columns = [instrument]).transpose()
        cf.index = cf['Date']
        del cf['Date']
        ndays = (days.loc[cf.index])
        yieldBond = pd.DataFrame(index = price.index ,columns = price.columns)
        
        def f(y,price,cf,ndays):
            return np.abs(price - cf.multiply(1/((1+float(y)/float(100))**(ndays['Dove']/365)),axis='index').sum()).TCF
            
        for x in price.columns:
            yieldBond[x] = fmin(f,x0,args=(price[x][instrument],cf,ndays))

        return yieldBond

    def getPriceFromBBG(self,instruments):
        LocalTerminal = v3api.Terminal('localhost', 8194)   
        try:
            response = LocalTerminal.get_reference_data(instruments, ['YLD_YTM_MID', 'DAYS_TO_MTY'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False
        return response.as_frame()

    def getPriceDurationVolatilityFromBBG(self,instruments):
        LocalTerminal = v3api.Terminal('localhost', 8194)   
        try:
            response = LocalTerminal.get_reference_data(instruments, ['YLD_YTM_MID', 'DUR_ADJ_MID', 'VOLATILITY_260D', 'DAYS_TO_MTY'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False
        return response.as_frame()
### Inflation Forecast and CLF Forecasted Values
    # Hay un detalle con la fecha en la que se publica la inflacion. Si en dos meses mas la fecha es 7 del mes, la fecha del mes actual lo tomara como que es 7
    # Eso genera una leve diferencia en el valor de la UF actual.

    def createCLFpath(self, init='2015-12-01', end=dt.datetime.today()):
        iforecast = self.getInflationforecast()
        historical = outlook.outlook().getHistoricalInflation(init, end)
        historical.columns = ['Dove']
        historical['Base'] = historical['Dove']
        historical['Hawk'] = historical['Dove']
        historical['Average'] = historical['Dove']

        expected = outlook.outlook().getInflationExpectations()
        forecasted = pd.DataFrame(data = expected['Forecast CPI'][1:])
        forecasted.columns = ['PX_LAST']
        forecasted.index = [expected['SETTLE_DT'][x+1] - relativedelta(months=2) for x in range(0,len(forecasted))]
        forecasted['year'] = [forecasted.index[i].to_datetime().year for i in range(0,len(forecasted))]
        forecast_adj = pd.DataFrame(columns = ['Dove','Base','Hawk','Average'], index = forecasted.index)

        forecast_adj['Dove'][forecasted.index.to_datetime().year == 2016] = forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016] + (iforecast['Dove'][0]-historical['Dove'].sum()-forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016].sum())/len(forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016])  # Esto se tiene que ajustar cada anio para que funcione correctamente, o mejorar el codigo  
        forecast_adj['Dove'][forecasted.index.to_datetime().year == 2017] = forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017] + (iforecast['Dove'][1]-historical['Dove'].sum()-forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017].sum())/len(forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017])        
        forecast_adj['Base'][forecasted.index.to_datetime().year == 2016] = forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016] + (iforecast['Base'][0]-historical['Base'].sum()-forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016].sum())/len(forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016])
        forecast_adj['Base'][forecasted.index.to_datetime().year == 2017] = forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017] + (iforecast['Base'][1]-historical['Base'].sum()-forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017].sum())/len(forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017])    
        forecast_adj['Hawk'][forecasted.index.to_datetime().year == 2016] = forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016] + (iforecast['Hawk'][0]-historical['Hawk'].sum()-forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016].sum())/len(forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016])  
        forecast_adj['Hawk'][forecasted.index.to_datetime().year == 2017] = forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017] + (iforecast['Hawk'][1]-historical['Hawk'].sum()-forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017].sum())/len(forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017])                    
        forecast_adj['Average'][forecasted.index.to_datetime().year == 2016] = forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016] + (iforecast['Average'][0]-historical['Average'].sum()-forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016].sum())/len(forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2016]) 
        forecast_adj['Average'][forecasted.index.to_datetime().year == 2017] = forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017] + (iforecast['Average'][1]-historical['Average'].sum()-forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017].sum())/len(forecasted['PX_LAST'][forecasted.index.to_datetime().year == 2017])                            

        inflation = historical.append(forecast_adj)

        days, dates, short_rate, factor, dF, prob, Z = self.createRatesTable()
        fechas = self.dateCount(inflation.index[-1],dates[-1],day_of_month = 9)

        inflation_long = pd.DataFrame(columns = forecast_adj.columns, index=fechas[1:])
        inflation_long['Dove'] = iforecast['Dove'][2]/12
        inflation_long['Base'] = iforecast['Base'][2]/12
        inflation_long['Hawk'] = iforecast['Hawk'][2]/12
        inflation_long['Average'] = iforecast['Average'][2]/12

        inflation = inflation.append(inflation_long)

        clf = pd.DataFrame(columns = forecast_adj.columns, index=inflation.index)
        x = 0
        for i in range(0,len(clf)):
            if clf['Dove'].index[i] < dt.datetime.today():
                x += 1
                clf['Dove'].iloc[i] = self.getUF(inflation.index[i])
                
        clf['Base'] = clf['Dove']
        clf['Hawk'] = clf['Dove']
        clf['Average'] = clf['Dove']
        
        clf['Dove'][x:] = (1+inflation['Dove'][x-2:-2]/100).cumprod()*clf['Dove'][x-1]
        clf['Base'][x:] = (1+inflation['Base'][x-2:-2]/100).cumprod()*clf['Base'][x-1]
        clf['Hawk'][x:] = (1+inflation['Hawk'][x-2:-2]/100).cumprod()*clf['Hawk'][x-1]
        clf['Average'][x:] = (1+inflation['Average'][x-2:-2]/100).cumprod()*clf['Average'][x-1]
        
        clf_long = pd.DataFrame(data = clf, index = dF.index, columns = clf.columns)
        LocalTerminal = v3api.Terminal('localhost', 8194)
        response = LocalTerminal.get_historical(['CLF Curncy'], ['PX_LAST'], ignore_security_error=1, ignore_field_error=1, start = clf_long.index[0].to_datetime()-dt.timedelta(days=1), end = clf_long.index[0].to_datetime()-dt.timedelta(days=1))
        clf_long.iloc[0] = response.as_frame().values
        for col in clf_long:
            clf_long[col] = pd.to_numeric(clf_long[col], errors='coerce')
        clf_long = clf_long.interpolate(method='linear')
        return inflation, clf_long, Z, days, dates

    def createInflationTable(self):
        inflation, clf, Z, days, dates = self.createCLFpath()
        A = (1+Z/100)
        B = (days/365)
        C = clf.iloc[0]/clf
        D = (365/days)
        ZUF = 100*(((A**B)*C)**D-1)
        dFactor = pd.DataFrame(index = ZUF.index,columns = ['Dove','Base','Hawk','Average'])
        for i in ZUF.index[1:]:
            dFactor.loc[i] = 1/((1+ZUF.loc[i]/100)**(days.loc[i]/365))
        return ZUF, dFactor, days, dates


    def getUF(self,start=dt.datetime.today()):
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        self.CLFCLP = LocalTerminal.get_historical(['CLF Curncy'], ['PX_LAST'], start - dt.timedelta(days=1)).as_frame()['CLF Curncy']['PX_LAST'][0]
        return self.CLFCLP

    def dateCount(self, start, end, day_of_month=1):
        dates = [start]
        next_date = start.replace(day=day_of_month)
        if day_of_month > start.day:
            dates.append(next_date)
        while next_date < end.replace(day=day_of_month):
            next_date += relativedelta(next_date, months=+1)
            dates.append(next_date)
        return dates

### Build Forecasted Curves
    def buildForecastedCurves(self,nominal=True):
#        instruments = self.getLocalCurveInstrumentsFromBBG()
#        instruments = self.getLocalCurveInstrumentsFromExcel()
        if nominal:
            instruments = self.getLocalCurveInstrumentsFromUser()
            days, dates, short_rate, factor, Z, prob, ZZ = r.createRatesTable()
        else:
            instruments = self.getLocalCLFCurveInstrumentsFromUser()
            days, dates, short_rate, factor, X, prob, ZZ = r.createRatesTable()
            ZUF, Z, days, dates = r.createInflationTable()
             
        y = pd.DataFrame(index = instruments['Tenor Ticker'], columns = ['Dove','Base','Hawk','Average'])
        for bond in instruments['Tenor Ticker']:
            aux = self.getBondPriceAndYield(bond, days, dates, short_rate, factor, Z, prob, ZZ, x0=5,nominal=nominal)
            y.loc[bond,:] = aux.values
            
        try:
            y.index = instruments['Name']
        except:
            y.index = instruments['Tenor Ticker']

        YTM = self.getPriceFromBBG(instruments['Tenor Ticker'])
        y['YTM'] = YTM['YLD_YTM_MID']
        y['Days to Maturity'] = YTM['DAYS_TO_MTY'] 
        return y.sort(columns = 'Days to Maturity')

### Plot Results
    def plotYieldCurves(self, curves, nominal=True):
        if nominal:
            instruments = self.getLocalCurveInstrumentsFromUser()
            cur = '(CLP)'
        else:
            instruments = self.getLocalCLFCurveInstrumentsFromUser()
            cur = '(UF)'          
            
        try:
            maturity = [float(x[0:4].replace(',','.').replace('Y','')) for x in instruments['Tenor']]
        except:
            False      

        YTM = self.getPriceFromBBG(instruments['Tenor Ticker']).sort('DAYS_TO_MTY')

        fig, ax = plt.subplots(1,1)
        plt.style.use('bmh') # fivethirtyeight, dark_background, bmh, grayscale
        
        def plotCurves(ax, scenario):        
            tasa = [float(x) for x in curves[scenario].values]
#            fit = np.polyfit(YTM['DAYS_TO_MTY'].values,y[scenario].values,20)
#            fit_fn = np.poly1d(fit)
#            if scenario == 'Hawk':
#                adj = 4
#                yinterp = interpolate.UnivariateSpline(maturity, tasa, k=adj, s = 5e8)(maturity)
#                yinterp = interpolate.interp1d(maturity, tasa, kind='slinear', assume_sorted=False)(maturity)
#            elif scenario == 'Dove':
#                adj = 3.99
#                yinterp = interpolate.UnivariateSpline(maturity, tasa, k=adj, s = 5e8)(maturity)
#                yinterp = interpolate.interp1d(maturity, tasa, kind='slinear', assume_sorted=False)(maturity)
#            else:
#                yinterp = interpolate.UnivariateSpline(maturity, tasa, s = 5e8)(maturity)
#                yinterp = interpolate.interp1d(maturity, tasa, kind='slinear', assume_sorted=False)(maturity)
#            plt.plot(maturity, tasa, 'bo', label = 'Original')
#            return ax.plot(maturity, yinterp, label = 'Interpolated')
            return ax.plot(maturity, tasa, 'o--', markersize=4)
            
        for scenario in curves.columns[0:4]:
            plotCurves(ax, scenario)
            
        ax.plot(maturity, YTM['YLD_YTM_MID'], 'yo', markersize=7, markeredgecolor='b')
        
        fig.set_size_inches(12, 8)
        plt.subplots_adjust(top=0.85)
        plt.xlabel('Tenor', fontsize=15)
        plt.xticks(fontsize=15)
        plt.ylabel('Yield (%)', fontsize=15)
        plt.yticks(fontsize=15)
        plt.title('Curva de Rendimientos por Escenario %s' % cur, fontsize=18, y=1.05)
        plt.legend(['Dove','Base','Hawk', 'Average','YTM Mid'], fontsize=15, loc=4)

        plt.show()
        
### Create Summary Valuation Table
    def valuationSummary(self, curves, monthsToEndOfYear, nominal=True):
        if nominal:
            instruments = self.getLocalCurveInstrumentsFromUser()
        else:
            instruments = self.getLocalCLFCurveInstrumentsFromUser()

        YTM = self.getPriceDurationVolatilityFromBBG(instruments['Tenor Ticker']).sort('DAYS_TO_MTY')
        tasa = [float(x) for x in curves['Average'].values]

        summary = pd.DataFrame(index = YTM.index)
        summary['Spot'] = YTM['YLD_YTM_MID']
        summary['Estimacion'] = tasa
        summary['Carry'] = YTM['YLD_YTM_MID']/(12/monthsToEndOfYear)
        summary['Curve'] = YTM['DUR_ADJ_MID']*(summary['Spot'] - summary['Estimacion'])
        summary['Total Period Return'] = (summary['Carry']/100 + summary['Curve'])
        summary['Volatility'] = YTM['VOLATILITY_260D']
        summary['Return/Volatility'] = summary['Total Period Return']/summary['Volatility']
        return summary


if __name__ == '__main__':
    r = rates() # Run this to update
    days, dates, short_rate, factor, dFactor, prob, Z = r.createRatesTable()
#    x = r.getLocalCurveInstrumentsFromBBG()
#    days, dates, short_rate, factor, dF, prob, Z = r.createRatesTable()
#    instruments = r.getLocalCurveInstrumentsFromUser() # Run this to update
#    cf = r.getBondCashFlows('EK8775448 Corp')
#    byield = r.getBondPriceAndYield('EK8775448 Corp')
#    y = r.buildForecastedCurves(nominal=True) # Run this to update
#    inflation, clf_long, Z, days, dates = r.createCLFpath()
#    y.to_pickle('testpickle.p')
#    y = pd.read_pickle('testpickle.p')
#    r.plotYieldCurves(y,nominal=True)
#    inflation, uf, Z, days = r.createCLFpath()
#    Zuf = r.createInflationTable()
#    r.getTPMforecast()[:12].plot(figsize=(13,9),ylim=(2.5,5),fontsize=12, title = 'TPM Esperada por Escenario') # Para graficar path de TPM
#    summaryTable = r.valuationSummary(y,2)

# Function getLocalCurvesFromUser has to be updated manually

