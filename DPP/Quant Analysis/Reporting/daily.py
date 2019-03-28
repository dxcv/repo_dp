# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 10:21:18 2016

@author: ngoldbergerr
"""

import sys
sys.path.append("L:\Rates & FX\Quant Analysis\portfolioManager\Monitors")
sys.path.append("L:\Rates & FX\Quant Analysis\portfolioManager\RatesAnalysis")
from synthetic import forwardSwap

import tia.rlab as rlab
from tia.bbg import LocalTerminal
import matplotlib.pyplot as plt
import datetime
from tia.rlab.table import PercentFormatter, FloatFormatter
import pandas as pd
import statsmodels.api as sm
import matplotlib.dates as mdates
import numpy as np
from tia.bbg import v3api
import datetime as dt
from fragility import fragility
import xlrd
import os.path
from scipy.optimize import fmin
import outlook
from dateutil.relativedelta import relativedelta
import seaborn as sns


### SUPPORT FUNCTIONS AND CLASSES
class turbulence(object):

    def __init__(self, idx = ['eurusd curncy', 'audusd curncy','cadusd curncy','jpyusd curncy','brlusd curncy']):
        self.idx = idx
        
    def downloadData(self,tw):
        self.tw = tw
        self.d = pd.datetools.BDay(-self.tw).apply(pd.datetime.now())
        self.m = pd.datetools.BMonthBegin(-2).apply(pd.datetime.now())
        self.response = LocalTerminal.get_historical(self.idx, ['px_last'], start=self.d)
    
    def getReturns(self,prices, freq = 1):
        x = {}
        x['price'] = prices
        x['returns'] = (np.log(x['price']) - np.log(x['price'].shift(freq))).fillna(0).values
        x['pct_chg'] = (x['price'].pct_change()).fillna(0).values
        return x
    
    def mahalanobis(self, x):
        mu = np.average(x['returns'],0)
        Sigma = np.cov(np.transpose(x['returns'])) 
        sigmainv = np.linalg.inv(Sigma)
        turbulenceData = (np.dot((x['returns'][-1]-mu),(np.dot(sigmainv,(x['returns'][-1]-mu)))))**0.5
        return turbulenceData

    def graph(self,data):
        t = [pd.datetools.BDay(-i).apply(pd.datetime.now()) for i in range(len(data))]
        t.reverse()
        fig, ax1 = plt.subplots(1,1,figsize=(14,7))
#        ax1.plot(t,data,'b-')
        ax1.bar(t,data)
        ax1.set_ylabel('Turbulence', fontsize = 14)
        ax1.set_title('Turbulence Level', fontsize = 16)
        ax1.xaxis.set_tick_params(labelsize=12)
        ax1.yaxis.set_tick_params(labelsize=12)
        fig.autofmt_xdate(rotation=0, ha= 'center')
        plt.show()

    def computeTurbulenceAndPlot(self,freq):
        df = self.response.as_frame()
        self.turbulenceRollingData = self.getRollingTurbulenceData(df, freq)
        self.graph(self.turbulenceRollingData)
        
    def getRollingTurbulenceData(self, df, freq, rollingWindow = 251):
        data = []        
        for i in range(0,len(df)-rollingWindow):
            try:
                data.append(self.getTurbulenceData(df[0+i:rollingWindow+i],freq))
            except:
                print('Error computing turbulence data.')
                pass
        return data
        
    def getTurbulenceData(self,df,freq):
        x = self.getReturns(df,freq)
        turbulenceData = self.mahalanobis(x)
        return turbulenceData

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
        countryDict = {'CL': 'YCGT0351 Index'}
        bbg_tickers = [countryDict['CL']]
        
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        try:
            response = LocalTerminal.get_reference_data(bbg_tickers, ['curve_tenor_rates'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False

        curve_instruments = pd.DataFrame(response.as_frame()['curve_tenor_rates'].values[0])
        
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
            response = LocalTerminal.get_reference_data(instruments, ['YLD_YTM_MID', 'DUR_ADJ_MID', 'VOLATILITY_260D', 'DAYS_TO_MTY','SECURITY_NAME'], ignore_security_error = 1, ignore_field_error = 1)
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
        
        fig.set_size_inches(15, 12)
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
        summary['Capital G/L'] = YTM['DUR_ADJ_MID']*(summary['Spot'] - summary['Estimacion'])/100
        summary['Total Period Return'] = (summary['Carry']/100 + summary['Capital G/L'])
        summary['Volatility'] = YTM['VOLATILITY_260D']
        summary['Return/Volatility'] = summary['Total Period Return']/summary['Volatility']*100
        summary.index = YTM['SECURITY_NAME']
        summary.index.names = ['Instrumento']
        return summary


def loadBBGDataHistoricalPrices(identifiers,dateInitial,dateFinal):
    flds = ['PX_LAST']
    #Descarga información sobre los indices desde Bloomberg
    LocalTerminal = v3api.Terminal('localhost', 8194)
    try:
        response = LocalTerminal.get_historical(identifiers, flds, ignore_security_error=1, ignore_field_error=1, start = dateInitial, end = dateFinal)
    except:
        print("Unexpected error:", sys.exc_info()[0])

    priceData = response.as_frame().interpolate()
    newPrice = priceData.stack()
    newPrice.index = priceData.index
    return newPrice

# - Generate a pdf path
# - define a cover page
# - Create a Pdf Builder
# - Define the templates and register with the builder
#
#        TEMPLATE_1                         TEMPLATE_2         
#  |-------------------------|        |-------------------------|
#  |        HEADER           |        |        HEADER           | 
#  |-------------------------|        |-------------------------|
#  |            |            |        |            |            |
#  |            |            |        |            |    TBL_2   |
#  |            |            |        |            |            |
#  |   IMG_1    |    IMG_2   |        |            |            |
#  |            |            |        |   TBL_1    |------------|
#  |            |            |        |            |            |
#  |            |            |        |            |    TBL_3   |
#  |            |            |        |            |            |
#  |-------------------------|        |-------------------------|
#
#        TEMPLATE_3                         TEMPLATE_4
#  |-------------------------|        |-------------------------|
#  |        HEADER           |        |        HEADER           | 
#  |-------------------------|        |-------------------------|
#  |            |            |        |            |            |
#  |   TBL_1    |            |        |   TBL_1    |    TBL_3   |
#  |            |            |        |            |            |
#  |------------|   TBL_3    |        |------------|------------|
#  |            |            |        |            |            |
#  |   TBL_2    |            |        |   TBL_2    |    TBL_4   |
#  |            |            |        |            |            |
#  |-------------------------|        |-------------------------|
#
# Define the name of the document and the Templates
now = datetime.datetime.now().strftime("%m%d%Y")
pdfpath = 'Reporte Diario ' + now + '.pdf'
x = 'Reporte del ' + now
pdf = rlab.PdfBuilder(pdfpath, showBoundary=0)
pdf = rlab.PdfBuilder(pdfpath, coverpage=None, showBoundary=0)

# Define TEMPLATE_1
template = rlab.GridTemplate('TEMPLATE_1', nrows=100, ncols=100)
# uses numpy style slicing to define the dimensions
template.define_frames({
    'HEADER': template[:10, :],
    'IMG_1': template[15:, 3:48],
    'IMG_2': template[15:, 52:97]
})
template.register(pdf)

# Define TEMPLATE_2
template = rlab.GridTemplate('TEMPLATE_2', nrows=100, ncols=100)
template.define_frames({
    'HEADER': template[:10, :],
    'TBL_1': template[10:, :50],
    'TBL_2': template[10:55, 50:],
    'TBL_3': template[55:, 50:]
})
template.register(pdf)

# Define TEMPLATE_3
template = rlab.GridTemplate('TEMPLATE_3', nrows=100, ncols=100)
template.define_frames({
    'HEADER': template[:10, :],
    'TBL_1': template[8:60, :50],
    'TBL_2': template[60:95, :50],
    'TBL_3': template[8:, 50:]
})
template.register(pdf)

# Define TEMPLATE_4
template = rlab.GridTemplate('TEMPLATE_4', nrows=100, ncols=100)
template.define_frames({
    'HEADER': template[:8, :],
    'TBL_1': template[7:52, 0:50],
    'TBL_2': template[51:100, 0:50],
    'TBL_3': template[7:52, 50:100],
    'TBL_4': template[51:100, 50:100]
})
template.register(pdf)

# Define TEMPLATE_5
template = rlab.GridTemplate('TEMPLATE_5', nrows=100, ncols=100)
template.define_frames({
    'HEADER': template[:8, :],
    'TBL_1': template[7:38, 0:33],
    'TBL_2': template[7:38, 33:66],
    'TBL_3': template[7:38, 66:100],
    'TBL_4': template[37:68, 0:33],
    'TBL_5': template[37:68, 33:66],
    'TBL_6': template[37:68, 66:100],
    'TBL_7': template[68:100, 0:33],
    'TBL_8': template[68:100, 33:66],
    'TBL_9': template[68:100, 66:100],
})
template.register(pdf)

# Define a style and method for building a header
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, TA_CENTER

# Add a stylesheet to the pdf
tb = ParagraphStyle('TitleBar', parent=pdf.stylesheet['Normal'], fontName='Helvetica-Bold', fontSize=14, 
                    leading=14, alignment=TA_CENTER)

'TitleBar' not in pdf.stylesheet and pdf.stylesheet.add(tb)


def title_bar(pdf, title):
    # Build a title bar for top of page
#    w, t, c = '100%', 2, HexColor('#404040')
    w, t, c = '100%', 1.5, HexColor('#597b7c')
    title = '<b>{0}</b>'.format(title)    
    return [HRFlowable(width=w, thickness=t, color=c, spaceAfter=5, vAlign='MIDDLE', lineCap='square'),
            pdf.new_paragraph(title, 'TitleBar'),
            HRFlowable(width=w, thickness=t, color=c, spaceBefore=5, vAlign='MIDDLE', lineCap='square')]
            

# Define method to convert a dataframe to a formatted pdf table object
def port_to_pdf_table(frame):
    table =  pdf.table_formatter(frame, inc_header=1, inc_index=1)
    # use the default style to add a bit of color
    table.apply_basic_style(cmap=rlab.Style.Cyan)
    # apply a percent formatter to the return column
    table.cells.match_column_labels('Capital G/L').apply_number_format(PercentFormatter)
    table.cells.match_column_labels('Spot').apply_number_format(FloatFormatter)
    table.cells.match_column_labels('Estimacion').apply_number_format(FloatFormatter)
    table.cells.match_column_labels('Carry').apply_number_format(FloatFormatter)
    table.cells.match_column_labels('Volatility').apply_number_format(FloatFormatter)
    table.cells.match_column_labels('Return/Volatility').apply_number_format(FloatFormatter)
    table.cells.match_column_labels('Total Period Return').apply_number_format(PercentFormatter)
    return table.build(vAlign='MIDDLE', hAlign = 'LEFT')


### PAGE ONE: Plots
# Plot time series USD rates
def plotTimeSeriesUSDrates(timeSeries):
    months = mdates.MonthLocator()  # every month
    f, axarr = plt.subplots(2, sharex=True)
    plt.style.use('bmh')
    f.set_size_inches(15, 12)
    axarr[0].plot(timeSeries.index, timeSeries.loc[:,'1M':'6M'])
    axarr[0].set_xlim(0,310)
    axarr[0].set_title('USD On-Shore Synthetic Rate', fontsize = 40)
    axarr[0].legend(['1M','2M','3M','6M'],loc=4)
    axarr[1].plot(timeSeries.index, timeSeries.loc[:,'1Y':'5Y'])
    axarr[1].legend(['1Y','2Y','3Y','4Y','5Y'],loc=4)
    axarr[1].set_xlabel('Date', fontsize = 25)
    axarr[0].set_ylabel('Rate (%)', fontsize = 25)
    axarr[1].set_ylabel('Rate (%)', fontsize = 25)
    axarr[1].xaxis.set_minor_locator(months)
    axarr[1].tick_params(axis='x',labelsize=25)

    datemin = datetime.date(timeSeries.index.min().year, timeSeries.index.min().month, timeSeries.index.min().day)
    datemax = datetime.date(timeSeries.index.max().year, timeSeries.index.min().month+2, timeSeries.index.min().day)
    axarr[1].set_xlim(datemin, datemax)
    f.tight_layout()
    f.autofmt_xdate(rotation=45, ha= 'center')
    return True
    
# Support function to download data from Bloomberg, order columns in DataFrames
def getDataFromBloomberg(tickers,fields):
    LocalTerminal = v3api.Terminal('localhost', 8194)  
    response = LocalTerminal.get_reference_data(tickers, fields, ignore_security_error = 1, ignore_field_error = 1)
    return response.as_frame()

def set_column_sequence(dataframe, seq, front=True):
    '''Takes a dataframe and a subsequence of its columns,
       returns dataframe with seq as first columns if "front" is True,
       and seq as last columns if "front" is False.
    '''
    cols = seq[:] # copy so we don't mutate seq
    for x in dataframe.columns:
        if x not in cols:
            if front: #we want "seq" to be in the front
                #so append current column to the end of the list
                cols.append(x)
            else:
                #we want "seq" to be last, so insert this
                #column in the front of the new column list
                #"cols" we are building:
                cols.insert(0, x)
    return dataframe[cols]

# Plot the Historical Deposit Curve
def buildHistoricalDepoCurve():
    tickers = ['CLTN30DN Index','CLTN90DN Index','CLTN180N Index','CLTN360N Index']
    fields = ['SHORT_NAME','PX_LAST','CHG_NET_1M','CHG_NET_YTD']
    bloombergData = getDataFromBloomberg(tickers,fields)
    table = pd.DataFrame(bloombergData)
    table.index = [180,30,360,90]
    del table['SHORT_NAME']
    table = table/12
    table['CHG_NET_1M'] = table['PX_LAST']-table['CHG_NET_1M']
    table['CHG_NET_YTD'] = table['PX_LAST']-table['CHG_NET_YTD']
    table.columns = ['Last Price','One Month','Beginning of Year']
    curve = pd.DataFrame(table, index = [30,60,90,120,150,180,210,240,270,300,330,360], columns = table.columns)
    curve = curve.interpolate(method='linear')
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.style.use('bmh') # fivethirtyeight, dark_background, bmh, grayscale
    
    ax.plot(curve.index, curve['Last Price'], '--', markersize=4)
    ax.plot(curve.index, curve['One Month'], '--', markersize=4)
    ax.plot(curve.index, curve['Beginning of Year'], '--', markersize=4)
    plt.legend(['Last Price','One Month','Beginning of Year'], fontsize=25, loc=4)     

    ax.plot(table.index, table['Last Price'], 'o', markersize=7, markerfacecolor = 'c')
    A = table.index            
    B = table['Last Price'].values

    for x, y in zip(A,B):
        ax.annotate('%s' % round(y,3), xy=(x-10,y+0.003), textcoords='data')
    
    ax.plot(table.index, table['One Month'], 'o', markersize=7, markerfacecolor = 'r')
    A = table.index            
    B = table['One Month'].values

    for x, y in zip(A,B):
        ax.annotate('%s' % round(y,3), xy=(x-10,y+0.003), textcoords='data')
        
    ax.plot(table.index, table['Beginning of Year'], 'o', markersize=7, markerfacecolor = 'purple')
    A = table.index            
    B = table['Beginning of Year'].values

    for x, y in zip(A,B):
        ax.annotate('%s' % round(y,3), xy=(x-10,y+0.003), textcoords='data')

    fig.set_size_inches(15, 12)
    plt.subplots_adjust(top=0.85)
    plt.xlabel('Tenor (dias)', fontsize=25)
    plt.xticks(fontsize=25)
    plt.ylabel('Tasa (%)', fontsize=25)
    plt.yticks(fontsize=25)
    plt.title('Evolucion Curva de Depositos', fontsize=40, y=1.05)
    plt.xticks(np.arange(min(table.index), max(table.index)+1, 30.0))
    fig.tight_layout()
    return curve.sort_index(ascending=True)


def getHistDataFromBloomberg(tickers, init = dt.datetime.today()-dt.timedelta(weeks=104), end = dt.datetime.today()-dt.timedelta(days=1)):
    
    LocalTerminal = v3api.Terminal('localhost', 8194)        
    try:
        response = LocalTerminal.get_historical(tickers, ['PX_LAST'], ignore_security_error=1, ignore_field_error=1, start = init, end = end)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return False

    bloombergData = response.as_frame()
    
    return bloombergData
            
# Plot Depo Time Series
def buildCLPDepoTimeSeries():
    tickers = ['CLTN30DN Index','CLTN180N Index','CLTN360N Index']
    ratesCLP = getHistDataFromBloomberg(tickers)
    ratesCLP.columns = ['Depositos CLP 360D','Depositos CLP 30D','Depositos CLP 180D']
    ratesCLP = set_column_sequence(ratesCLP,['Depositos CLP 30D','Depositos CLP 180D','Depositos CLP 360D'])
    fig = plt.figure(figsize=(15,12))
    ax = fig.add_subplot(111)
    plt.style.use('bmh')
    ax.plot(ratesCLP.index, ratesCLP, linewidth=1.0)
    plt.xlabel('Fecha', fontsize=25)
    plt.xticks(fontsize=25)
    plt.ylabel('Tasa (%)', fontsize=25)
    plt.yticks(fontsize=10)
    plt.title('Evolucion Tasas de Depositos CLP', fontsize=40, y=1.05)
    plt.legend(['30D','180D','360D'], fontsize=25, loc=1)    
    fig.tight_layout()
    fig.autofmt_xdate(rotation=45, ha= 'center')
    return ratesCLP

def buildCLFDepoTimeSeries():
    tickers = ['PCRR180D Index','PCRR360D Index']
    ratesCLF = getHistDataFromBloomberg(tickers)
    ratesCLF.columns = ['Depositos UF 360D','Depositos UF 180D']
    fig = plt.figure(figsize=(15,12))
    ax = fig.add_subplot(111)
    plt.style.use('bmh')
    ax.plot(ratesCLF.index, ratesCLF, linewidth=1.0)
    plt.xlabel('Fecha', fontsize=25)
    plt.xticks(fontsize=25)
    plt.ylabel('Tasa (%)', fontsize=15)
    plt.yticks(fontsize=10)
    plt.title('Evolucion Tasas de Depositos UF', fontsize=40, y=1.05)
    plt.legend(['180D','360D'], fontsize=25, loc=1)
    fig.tight_layout()
    fig.autofmt_xdate(rotation=45, ha= 'center')
    return ratesCLF

def computeTurbulenceAndPlot(freq, turbo):
    df = turbo.response.as_frame()
    turbo.turbulenceRollingData = turbo.getRollingTurbulenceData(df, freq)
    data = turbo.turbulenceRollingData
    t = [pd.datetools.BDay(-i).apply(pd.datetime.now()) for i in range(len(data))]
    t.reverse()
    fig, ax1 = plt.subplots(1,1,figsize=(15,12))
    ax1.plot(t,data)
#    ax1.bar(t,data)
    ax1.set_ylabel('Turbulence', fontsize = 25)
    ax1.set_title('Turbulence Level', fontsize = 25)
    ax1.set_xlabel('Fechas', fontsize = 25)
    ax1.xaxis.set_tick_params(labelsize=25)
    ax1.yaxis.set_tick_params(labelsize=25)
    fig.autofmt_xdate(rotation=45, ha= 'center')
    fig.tight_layout()

def graphFragility(data):
    t = [pd.datetools.BDay(-i).apply(pd.datetime.now()) for i in range(len(data))]
    t.reverse()
    fig, ax1 = plt.subplots(1,1,figsize=(15,12))
    ax1.plot(t,data)   
    ax1.set_xlabel('Fechas', fontsize = 25)
    ax1.set_ylabel('Ratio de Absorcion', fontsize = 25)
    ax1.set_title('Fragilidad Mercado FX', fontsize = 40)
    ax1.xaxis.set_tick_params(labelsize=25)
    ax1.yaxis.set_tick_params(labelsize=10)
    fig.autofmt_xdate(rotation=45, ha= 'center')
    fig.tight_layout()

def getTPMforecast():
    # Toma las proyecciones de TPM de las tablas input del usuario
    wb = xlrd.open_workbook(os.path.join(r.XLpath,'rates.xlsx'))
    sh = wb.sheet_by_index(0)
    dTPM= r.get_cell_range(sh,0,5,0,26)
    d = r.get_cell_range(sh,1,5,1,26)
    b = r.get_cell_range(sh,4,5,4,26)
    h = r.get_cell_range(sh,7,5,7,26)
    av = r.get_cell_range(sh,10,5,10,26)
    datesTPM = [xlrd.xldate.xldate_as_datetime(x[0].value, wb.datemode) for x in dTPM]
    dove_tpm = [x[0].value for x in d]
    base_tpm = [x[0].value for x in b]
    hawk_tpm = [x[0].value for x in h]
    avg_tpm = [x[0].value for x in av]
    out = pd.DataFrame([dove_tpm, base_tpm, hawk_tpm, avg_tpm], index=['Dove','Base','Hawk','Average'], columns=datesTPM).transpose()
    fig, ax1 = plt.subplots(1,1,figsize=(15,12))
    ax1.plot(out.index,out)   
    ax1.set_xlabel('Fechas', fontsize = 25)
    ax1.set_ylabel('TPM (%)', fontsize = 25)
    ax1.set_ylim(2.5,5.5)
    ax1.set_title('TPM Esperada por Escenario', fontsize = 40)
    ax1.xaxis.set_tick_params(labelsize=25)
    ax1.yaxis.set_tick_params(labelsize=25)
    fig.autofmt_xdate(rotation=0, ha= 'center')
    fig.tight_layout()
    return out

## Plot Results
def plotYieldCurves(curves, nominal=True):
    if nominal:
        instruments = r.getLocalCurveInstrumentsFromUser()
        cur = '(CLP)'
    else:
        instruments = r.getLocalCLFCurveInstrumentsFromUser()
        cur = '(UF)'          
        
    try:
        maturity = [float(x[0:4].replace(',','.').replace('Y','')) for x in instruments['Tenor']]
    except:
        False      

    YTM = r.getPriceFromBBG(instruments['Tenor Ticker']).sort('DAYS_TO_MTY')

    fig, ax = plt.subplots(1,1)
    plt.style.use('bmh') # fivethirtyeight, dark_background, bmh, grayscale
    
    def plotCurves(ax, scenario):        
        tasa = [float(x) for x in curves[scenario].values]
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
    plt.title('Curva de Rendimientos por Escenario %s' % cur, fontsize=25, y=1.05)
    plt.legend(['Dove','Base','Hawk', 'Average','YTM Mid'], fontsize=15, loc=4)
    fig.tight_layout()
        
# Define a matplotlib helper to store images by key
from tia.util.mplot import FigureHelper
figures = FigureHelper()

### PAGE ONE: Structure

def add_graph_to_report_pageOne(trend, fragility, y, portframe):
    # build the images
    plotTimeSeriesUSDrates(trend)
    img1 = 'synthetic'
    figures.savefig(key=img1)

    buildHistoricalDepoCurve()
    img2 = 'deposCurve'
    figures.savefig(key=img2)

    buildCLPDepoTimeSeries()
    img3 = 'depoTimeSeriesCLP'
    figures.savefig(key=img3)

    buildCLFDepoTimeSeries()
    img4 = 'depoTimeSeriesUF'
    figures.savefig(key=img4)

    graphFragility(fragility)
    img5 = 'fragility'
    figures.savefig(key=img5)

    idx= ['BUSG Index','BUHY Index','BUSC Index','BNDX Index','CRY Index',
          'SPX Index','BGER Index','BERC Index','BEUH Index','DAX Index',
          'BJPN Index','BJPY Index','NKY Index','BRIT Index','BGBP Index',
          'BGBH Index','UKX Index','BAUS Index','BAUD Index','AS51 Index',
          'BEMS Index','BIEM Index','BEAC Index','VEIEX US Equity']
    turbo = turbulence(idx)
    turbo.downloadData(1500)
    computeTurbulenceAndPlot(1,turbo)
    img6 = 'turbulence'
    figures.savefig(key=img6)

    getTPMforecast()
    img7 = 'depoTimeSeriesCLP2'
    figures.savefig(key=img7)

    plotYieldCurves(y,nominal=True)
    img8 = 'depoTimeSeriesUF2'
    figures.savefig(key=img8)

    tbl1 = port_to_pdf_table(portFrame)

    
    pdf.build_page('TEMPLATE_5', {
        'HEADER': title_bar(pdf, 'Monitor Macro, Tasas y Monedas {0}'.format('')),
        'TBL_1': tbl1,
        'TBL_2': rlab.DynamicPdfImage(figures[img8]),
        'TBL_3': rlab.DynamicPdfImage(figures[img7]),
        'TBL_4': rlab.DynamicPdfImage(figures[img2]),
        'TBL_5': rlab.DynamicPdfImage(figures[img3]),
        'TBL_6': rlab.DynamicPdfImage(figures[img4]),
        'TBL_7': rlab.DynamicPdfImage(figures[img1]),
        'TBL_8': rlab.DynamicPdfImage(figures[img6]),
        'TBL_9': rlab.DynamicPdfImage(figures[img5])
    })

### PAGE TWO: Heat Map

#def add_graph_to_report_pageTwo(correlationMatrix):
#    # build the images
#    plot = sns.clustermap(correlationMatrix)
#    plot.savefig('correlation.png')
#
#    
#    pdf.build_page('TEMPLATE_1', {
#        'HEADER': title_bar(pdf, 'Monitor Macro, Tasas y Monedas {0}'.format('')),
#        'TBL_1': rlab.DynamicPdfImage(figures[img1]),
#        'TBL_2': rlab.DynamicPdfImage(figures[img1])
#    })


###############################################################################
################################ MAIN #########################################
###############################################################################

fs = forwardSwap()
histUSDonshore = fs.historicalUSDimplicitRate() # Tasa USD on-shore implicita a distintos plazos
cycle, trend = sm.tsa.filters.hpfilter(histUSDonshore, 2)
idx = ['BUSG Index','BUHY Index','BUSC Index','BNDX Index','CRY Index',
          'SPX Index','BGER Index','BERC Index','BEUH Index','DAX Index',
          'BJPN Index','BJPY Index','NKY Index','BRIT Index','BGBP Index',
          'BGBH Index','UKX Index','BAUS Index','BAUD Index','AS51 Index',
          'BEMS Index','BIEM Index','BEAC Index','VEIEX US Equity']
frag = fragility(idx)
frag.downloadData(1000)
df = frag.getReturns(frag.response.as_frame(),freq=1)
fragility = frag.getRollingFragilityData(df,1)
r = rates()
y = r.buildForecastedCurves(nominal=True)
portFrame = r.valuationSummary(y,2) # Actualizar numero de meses que quedan en el año
add_graph_to_report_pageOne(trend, fragility, y, portFrame)
#fx = ['EURUSD curncy', 'GBPUSD curncy', 'DKKUSD curncy', 'SEKUSD curncy', 'NOKUSD curncy', 'PLNUSD curncy', 'CZKUSD curncy',
#      'CADUSD curncy', 'AUDUSD curncy', 'NZDUSD curncy', 'JPYUSD curncy', 'CNYUSD curncy', 'MYRUSD curncy', 'KRWUSD curncy', 
#      'SGDUSD curncy', 'THBUSD curncy', 'BRLUSD curncy', 'MXNUSD curncy', 'CLPUSD curncy', 'PENUSD curncy', 'COPUSD curncy', 
#      'ZARUSD curncy', 'TRYUSD curncy','BUSG Index', 'BGER Index', 'BJPN Index', 'BRIT Index','BAUS Index', 'BEMS Index', 'BUSC Index', 
#      'BERC Index', 'BJPY Index', 'BGBP Index', 'BAUD Index', 'BIEM Index', 'BUHY Index', 'BEUH Index','BGBH Index','BEAC Index', 
#      'CLA Comdty', 'HGA Comdty','XAU Curncy','SPX Index', 'DAX Index', 'NKY Index', 'UKX Index', 'AS51 Index','IBOV Index','IPSA Index',
#      'MEXBOL Index','IOEA Comdty','SHSZ300 Index']
#fxprices = loadBBGDataHistoricalPrices(fx, dateInitial = dt.datetime.now() - dt.timedelta(days = 90), dateFinal = dt.datetime.now())
#fxprices = set_column_sequence(fxprices, fx)
#fxprices.columns = ['EUR','GBP','DKK','SEK','NOK','PLN','CZK',
#                    'CAD','AUD','NZD','JPY','CNY', 'MYR','KRW',
#                    'SGD','THB','BRL','MXN','CLP','PEN','COP',
#                    'ZAR','TRY','US Gov','GE Gov','JN Gov', 'UK Gov',
#                    'AU Gov','EM Gov','US IG','EU IG','JN IG',
#                    'UK IG','AU IG','EM IG','US HY','EU HY',
#                    'UK HY','EM HY','WTI','Copper','Gold','SPX',
#                    'DAX','NKY','UKX','ASX','IBOV','IPSA','MEXBOL','Iron Ore',
#                    'CSI300']
#fxreturns = fxprices.pct_change()
#correl = fxreturns.corr()
add_graph_to_report_pageOne(trend, fragility, y, portFrame)
#add_graph_to_report_pageTwo(correl)

pdf.save()