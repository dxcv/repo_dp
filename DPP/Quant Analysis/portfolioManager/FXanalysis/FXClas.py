# -*- coding: utf-8 -*-
"""
Created on Tue Jan 05 09:22:00 2016

author: goldbena
"""
import sys
import sqlite3
import pandas as pd
#import os
import numpy as np
from sklearn.decomposition import PCA
#from sklearn.preprocessing import scale
import matplotlib.pyplot as plt
from datetime import date as dt
#from pandas.tools.plotting import andrews_curves
#from pandas.tools.plotting import autocorrelation_plot
#plt.style.use(['dark_background'])
#print plt.style.available

#from tia.bbg import LocalTerminal
from tia.bbg import v3api

class fxData(object):
    
    def __init__(self, dbFile = 'L:\Rates & FX\Quant Analysis\portfolioManager\FXanalysis\\fxData.db'):
        self.dbPath = dbFile
        self.pca = None
    
    def openConnection(self):
        #Abre conexión con la base de datos
        con=sqlite3.connect(self.dbPath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
#        con.text_factory = str
        return con
        
    def createDB(self):
        #Genera bases de datos iniciales para trabajar con el objeto
        with self.openConnection() as con:
            
            cur = con.cursor()
            cur.execute("""DROP TABLE IF EXISTS historicalDataUSD""")
            cur.execute("""DROP TABLE IF EXISTS fxIdentifierData""")
            
            cur.execute("""CREATE TABLE historicalDataUSD
            (
            ID INTEGER PRIMARY KEY NOT NULL,
            DATE DATE NOT NULL,
            IDENTIFIER TEXT NOT NULL,
            PRICE REAL,
            UNIQUE(DATE, IDENTIFIER)
            )""")
            cur.execute("""CREATE TABLE fxIdentifierData
            (
            ID INTEGER PRIMARY KEY NOT NULL,
            IDENTIFIER TEXT NOT NULL,
            TICKER TEXT NOT NULL,
            DESCRIPTION TEXT,
            FXRISK TEXT,
            UNIQUE(IDENTIFIER, TICKER, FXRISK)
            )""")
        
    
    def insertFXTicker(self, identifiers = []):
        #Función que se encarga de incorporar identificadores a la base de datos y genera su ticker
        if not identifiers:
            return False
            
        identifierTuple = [(identifier, identifier + 'USD curncy', None, None) if identifier != 'USD' else (identifier, 'USD curncy', None, None) for identifier in identifiers]   
       
        with self.openConnection() as con:
            cur = con.cursor()
            cur.executemany("""INSERT OR IGNORE INTO fxIdentifierData (IDENTIFIER, TICKER, DESCRIPTION, FXRISK)
            VALUES (?,?,?,?)""", identifierTuple)
        
        return True
        
    def insertFXRisk(self, riskName, currencies):
        #Inserta en BD el nombre de riesgo a las monedas ingresadas
        currencyListStr = '\',\''.join(currencies)
        
        with self.openConnection() as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO fxIdentifierData (IDENTIFIER, TICKER, FXRISK)
            SELECT DISTINCT IDENTIFIER, TICKER, ? FROM fxIdentifierData 
            WHERE IDENTIFIER IN ('%s') AND IDENTIFIER NOT IN 
            (SELECT IDENTIFIER FROM fxIdentifierData where FXRISK = ?)""" %currencyListStr, (riskName, riskName))
        return True                
            
    def getDataBBGHistorical(self, start = None, end = None, window = None, period = 'DAILY', identifier = None):
        #Función que descarga información de Bloomberg        
        ticker = self.getFXTickerFromDB(identifier = identifier)
        response = None
        
        if not start:
            start = pd.datetools.BDay(-window).apply(pd.datetime.now()).date()
        
        if not end:
            end = pd.datetime.now().date()
        
        LocalTerminal = v3api.Terminal('localhost', 8194)
        try:
            response = LocalTerminal.get_historical(ticker, ['px_last'], ignore_security_error=1, ignore_field_error=1, period=period, start = start, end = end)
        except:
            print("Unexpected error:", sys.exc_info()[0])
#            print response.as_map()
#                    print response.as_frame()
        if response:    
            data = response.as_map()
            return data
            
        return False
        
    def uploadDataBBGHistoricalToDB(self, start = None, end = None, window = 1, identifier = None):
        #Carga información histórica desde Bloomberg a BD, para una ventana de tiempo en el pasado en particular
        dataBBG = self.getDataBBGHistorical(start = start, end = end, window = window, identifier = identifier)      
        dataTmp = []
        [dataTmp.extend([(date.date(),price,ticker) if ticker != 'KRWUSD curncy' else (date.date(),price/100,ticker) for date,price in data['px_last'].to_dict().iteritems()]) for ticker, data in dataBBG.iteritems()]
        
        with self.openConnection() as con:
            cur = con.cursor()
            cur.executemany("""INSERT OR IGNORE INTO historicalDataUSD (DATE, PRICE, IDENTIFIER)
            SELECT ?, ?, IDENTIFIER FROM fxIdentifierData where TICKER = ?""", dataTmp)
            
        return dataTmp
        
    def getFXTickerFromDB(self, identifier = None):
        #Entrega los tickers actualmente registrados en BD
        with self.openConnection() as con:
            cur = con.cursor()
            if identifier is None:
                cur.execute("""SELECT DISTINCT TICKER FROM fxIdentifierData""")
            if identifier:
                cur.execute("""SELECT DISTINCT TICKER FROM fxIdentifierData WHERE IDENTIFIER IN ('%s')""" %'\',\''.join(identifier))
            ticker = cur.fetchall()
        
        if ticker:
            return [str(t[0]) for t in ticker]
        return False
    
    def getFXIdentifierFromDB(self, fxRisk = None):
        #Entrega los identificadores actualmente registrados en BD
        
        with self.openConnection() as con:
            cur = con.cursor()
            if not fxRisk:
                cur.execute("""SELECT DISTINCT IDENTIFIER FROM fxIdentifierData""")
            else:
                cur.execute("""SELECT DISTINCT IDENTIFIER FROM fxIdentifierData WHERE FXRISK = ?""", (fxRisk,))
                
            ticker = cur.fetchall()
            
        if ticker:
            return [str(t[0]) for t in ticker]
        return False
        
    def getHistoricalDataUSDFromDB(self, currencies, periodicity = 'daily'):
        #Función que entrega información histórica de tipo de cambio para una divisa en particular respecto al USD
        monthlyQuery = ""
        if periodicity.upper() == 'MONTHLY':
            monthlyQuery = """AND DATE IN (SELECT max(date) AS DATE FROM historicalCurrencyBasket
            GROUP BY strftime('%m', date), strftime('%Y', date))"""
        
        currencyData = pd.DataFrame()
        with self.openConnection() as con:
            cur = con.cursor()
            for currency in currencies:
                cur.execute("""SELECT PRICE, DATE FROM historicalDataUSD
                WHERE IDENTIFIER = ? %s
                ORDER BY DATE """%monthlyQuery, (currency,))
                dataTmp = cur.fetchall()
                if dataTmp:
                    price = [p[0] for p in dataTmp]
                    date  = [p[1] for p in dataTmp]
                    df = pd.Series(price, index = date, name = currency)
                    currencyData = pd.concat([currencyData, df], axis = 1)
         
        return currencyData
            

    
    def getCrossCurrencyData(self, currency, numeraire, periodicity = 'daily'):
        #Función que entrega tipo de cambio cruzado entre dos divisas actualmente cargadas en BD
                
        currencyUSD =  self.getHistoricalDataUSDFromDB([currency], periodicity = periodicity) 
        numeraireUSD = self.getHistoricalDataUSDFromDB([numeraire], periodicity = periodicity) 
        crossCurrencyData = currencyUSD/numeraireUSD
        return crossCurrencyData
    
    def getAllCurrencyUSDReturnData(self, periodicity = 'daily', fxRisk = None):
        
        identifiers = self.getFXIdentifierFromDB(fxRisk = fxRisk) 
#        identifiers.remove('USD')
        currencyDataFrame = self.getHistoricalDataUSDFromDB(identifiers, periodicity = periodicity)
        
        return currencyDataFrame.pct_change()
    
        
    def getAllCrossCurrencyData(self, periodicity = 'daily', fxRisk = None):
        #Función que entrega todos los tipos de cambios cruzados entre todas las divisas actualmente cargados en BD
        
        identifiers = self.getFXIdentifierFromDB(fxRisk = fxRisk) 
        currencyDataFrame = self.getHistoricalDataUSDFromDB(identifiers, periodicity = periodicity)        
        
        allCrossCurrencyDataDict = {}
        
        for cur in identifiers:
            if cur not in allCrossCurrencyDataDict: allCrossCurrencyDataDict[cur] = {}            
            
            for num in identifiers:                
                if cur != num:
                   allCrossCurrencyDataDict[cur][num] = currencyDataFrame[cur]/currencyDataFrame[num]
                            
        if allCrossCurrencyDataDict:
            return allCrossCurrencyDataDict
        return False
    
    def getCrossCurrencyReturns(self, periodicity = 'daily'):
        #Función que entrega los retornos para cada tipo de cambio cruzado
        crossCurrencyDict = self.getAllCrossCurrencyData(periodicity = periodicity)
        ccReturns = {}
        for cur in crossCurrencyDict:
            if cur not in ccReturns: ccReturns[cur] = {}
            for num in crossCurrencyDict[cur]:
                data = crossCurrencyDict[cur][num]
                ccReturns[cur][num] = data.pct_change()
        if ccReturns:
            return ccReturns
        return False
        
    def averageReturnPerCurrency(self, periodicity = 'daily'):
        #Función que entrega el promedio de retornos para cada tipo de cambio respecto a todos los numerarios.
        #O con otras palabras, entrega la canasta moneda para cada currency
        crossCurrencyReturns = self.getCrossCurrencyReturns(periodicity = periodicity)
        currencyReturns = {}
        for cur in crossCurrencyReturns:
            data = pd.concat(crossCurrencyReturns[cur].values(), axis = 1, keys = crossCurrencyReturns[cur].keys())
#            [data.append(d) for d in crossCurrencyReturns[cur].values()]
            currencyReturns[cur] = data.mean(axis = 1)
        if currencyReturns:
            return currencyReturns
        return False
    
    def createCurrencyBasketDB(self):
        
        with self.openConnection() as con:
            cur = con.cursor()
            cur.execute("""DROP  TABLE IF EXISTS historicalCurrencyBasket""")
            cur.execute("""CREATE TABLE historicalCurrencyBasket
            (
            ID INTEGER PRIMARY KEY NOT NULL,
            DATE DATE NOT NULL,
            IDENTIFIER TEXT NOT NULL,
            RETURN REAL,
            UNIQUE(DATE, IDENTIFIER)
            )""")
            
            cur.execute("""DROP  TABLE IF EXISTS historicalCurrencyBasketMonthly""")
            cur.execute("""CREATE TABLE historicalCurrencyBasketMonthly
            (
            ID INTEGER PRIMARY KEY NOT NULL,
            DATE DATE NOT NULL,
            IDENTIFIER TEXT NOT NULL,
            RETURN REAL,
            UNIQUE(DATE, IDENTIFIER)
            )""")
            
            
    def updateCurrencyBasketDB(self, periodicity = 'daily'):
        
        returnPerCurrency = self.averageReturnPerCurrency(periodicity = periodicity)
        
        table = 'historicalCurrencyBasket'
        if periodicity.upper() == "MONTHLY":
            table = 'historicalCurrencyBasketMonthly'
            
        dataTmp = []
        [dataTmp.extend([(date, currency, price) for date, price in value.iteritems()]) for currency, value in returnPerCurrency.iteritems()]
        with self.openConnection() as con:
            cur = con.cursor()
            cur.executemany("""INSERT OR REPLACE INTO %s (DATE, IDENTIFIER, RETURN)
            VALUES (?,?,?)""" %table, dataTmp)
            
        return True
        
    def getCurrencyBasketFromDB(self, currencies = None, periodicity = 'daily', fxRisk = None):
        #Función que descarga una moneda canasta solicitada desde DB. En caso de no ingresar una lista de currencies, descarga toda la información disponible.
        allCurrencyBasket = pd.DataFrame()
        
        if not currencies:
            currencies = self.getFXIdentifierFromDB(fxRisk = fxRisk)
        if not currencies:
            return False
            
        table = 'historicalCurrencyBasket'
        if periodicity.upper() == "MONTHLY":
            table = 'historicalCurrencyBasketMonthly'
            
        
        with self.openConnection() as con:
            cur = con.cursor()
            for currency in currencies:
                cur.execute("""SELECT DATE, RETURN FROM %s
                WHERE IDENTIFIER = ?""" %table, (currency,))
                dataTmp = cur.fetchall()
                if dataTmp:
                    price = [p[1] for p in dataTmp]
                    date  = [p[0] for p in dataTmp]
                    currencyBasket = pd.Series(price, index = date, name = currency)
                    allCurrencyBasket = pd.concat([allCurrencyBasket, currencyBasket], axis = 1)
        
        allCurrencyBasket.index = pd.to_datetime(allCurrencyBasket.index)
        return allCurrencyBasket
        
        
    def PCAFXAnalysis(self, periodicity = 'daily', fxRisk = None, start = None, end = None):
        #Función que genera análisis de componentes principales para los currency Baskets actualmente cargados en historicalCurrencyBasket.
        #Si no se ha cargado información a base de datos, se recomiendo hacerlo usando la función updateCurrencyBasketDB
        currencyBasket = self.getCurrencyBasketFromDB(periodicity = periodicity, fxRisk = fxRisk)
        if start is None:
            start = min(currencyBasket.index)
        if end is None:
            end = max(currencyBasket.index)
        
        self.pca = PCA()
        self.pca.fit_transform(currencyBasket[start:end].fillna(0))
        components = pd.DataFrame(self.pca.components_.T, index = currencyBasket.columns)
        variance = pd.DataFrame(self.pca.explained_variance_ratio_)
        return components, variance
    
    def plotPCA(self, PCA = None, periodicity = 'daily', fxRisk = None, style = 'fivethirtyeight', start = None, end = None):
        
        if PCA is None:
            components, variance = self.PCAFXAnalysis(periodicity = periodicity, fxRisk = fxRisk, start = start, end = end)
        else:
            components, variance = PCA
        
        n = float(len(variance))
        
        title = periodicity + ' PCA '
        if fxRisk: title += fxRisk
        
        with plt.style.context((style)):
            axes = components.plot(kind = 'barh', legend = False, figsize = [15,n*2.5], subplots = True, layout = [int(np.ceil(n/3)),3], title = title, sharex=False, style = 'fivethirtyeight')#, layout = [np.floor(n**0.5), np.floor(n**0.5)+3])
            for axe, v in zip(axes.flatten(),variance.values):
                axe.set_title(str(round(v[0]*100, 2)) + '%')
#            plt.gcf().autolayout = True
                
            if n <= 3:
                top = 0.9 
            else:
                top = 0.95    
                
            plt.subplots_adjust(left=None, bottom=None, right=None, top=top, wspace=None, hspace=None)
#            plt.tight_layout()
#        andrews_curves(components, 1)
    
    def plotCurrencyBasketIndex(self, periodicity = 'daily', fxRisk = None, style = 'fivethirtyeight'):
        currencyBasket = (1+self.getCurrencyBasketFromDB(periodicity = periodicity, fivethirtyeight = fxRisk)).cumprod()
        n = float(len(currencyBasket.columns))
        
        title = 'Return Index '
        if fxRisk: title += fxRisk
        
        with plt.style.context((style)):
            axes = currencyBasket.plot( figsize = [18,n*1.1], subplots = True, layout = [int(np.ceil(n/3)),3], xticks = currencyBasket.index[::5], title =  title, sharex=False, style = 'g.--', rot = 45)
            
#            axes = currencyBasket.plot(subplots = True)
            for axe, v in zip(axes.flatten(),currencyBasket.columns):
                axe.legend([v])
#                axe.set_title(v)
                
                
            plt.gcf().autolayout = True
#            axes.tight_layout()   
            
#            plt.tight_layout()
            
    def getFactorsReturns(self, periodicity = 'daily', fxRisk = None, start = None, end = None):
        
        currencyBasket = self.getCurrencyBasketFromDB(periodicity = periodicity, fxRisk = fxRisk).fillna(0)
        components, variance = self.PCAFXAnalysis(periodicity = periodicity, fxRisk = fxRisk, start = start, end = end)
        
        return currencyBasket.dot(components), components, variance
        
    def getCorrelationVariance(self, periodicity = 'daily', fxRisk = None, numeraire = 'None'):
        
        if numeraire== 'USD':
            currencyBasket = self.getAllCurrencyUSDReturnData(periodicity = periodicity, fxRisk = fxRisk)
        else:    
            currencyBasket = self.getCurrencyBasketFromDB(periodicity = periodicity, fxRisk = fxRisk)
        
            
        self.pca = PCA()
        self.pca.fit_transform(currencyBasket.fillna(0))
        covariance = self.pca.get_covariance()
        variance = np.sqrt(np.diag(covariance))*np.eye(len(covariance))
        varianceInv = np.linalg.inv(variance)
        corr = np.dot(covariance,varianceInv)
        corr = np.dot(varianceInv,corr)
        corrDF = pd.DataFrame(corr, columns = currencyBasket.columns, index = currencyBasket.columns)
        
        varDF = pd.Series(np.sqrt(np.diag(covariance)), index = currencyBasket.columns)
        return corrDF, varDF
        
    def plotCorrelationMatrix(self, periodicity = 'daily', fxRisk = None, numeraire = 'None', style = 'gg_plot'):
        
        corr, variance = self.getCorrelationVariance(periodicity = periodicity, fxRisk = fxRisk, numeraire = numeraire)
        df = corr
        
        with plt.style.context((style)):
            plt.figure(figsize = (15,10))
            plt.pcolor(df, cmap='coolwarm', vmin = -1, vmax = 1)
            
            for (i, j), z in np.ndenumerate(corr.values):
                plt.text(j+0.5, i+0.5, '{:0.2f}'.format(z), ha='center', va='center')
                
            plt.yticks(np.arange(0.5, len(df.index), 1), df.columns)
            plt.xticks(np.arange(0.5, len(df.index), 1), df.columns, rotation = 45)
            
            ax = plt.gca()
            ax.invert_xaxis()
            ax.xaxis.tick_top()
        
            plt.yticks(np.arange(0.5, len(df.index), 1), df.columns)
            plt.xticks(np.arange(0.5, len(df.index), 1), df.columns, rotation = 45)
            plt.colorbar()
            plt.show()
            
    def risk_type(self):
        #Función que retorna los tipo de fxRisk cargados en BD
        with self.openConnection() as con:
            cur = con.cursor()
            cur.execute("""SELECT DISTINCT FXRISK FROM fxIdentifierData""")
            fxRisk = cur.fetchall()
            
        if fxRisk:
            return [str(r[0]) for r in fxRisk]
            
        return False
#        axe.invert_yaxis()
#                

#        
#class fx(object):
#    def __init__(self):
#        self.fxUSD = []        
       
#            
#    def plotCurrencyBasketAutoCorrelation(self, periodicity = 'daily', fxRisk = None):
#        currencyBasket = self.getCurrencyBasketFromDB(periodicity = periodicity, fxRisk = fxRisk)
#        n = float(len(currencyBasket.columns))
        
#        title = 'Return Index '
#        if fxRisk: title += fxRisk
        
##        with plt.style.context(('dark_background')):
#            
#        axes = autocorrelation_plot(currencyBasket.fillna(0)['EUR'])
#        axes.color = 'g'
#        axes = currencyBasket.plot( legend = False, figsize = [25,n*2], subplots = True, layout = [int(np.ceil(n/3)),3], xticks = currencyBasket.index[::5], title =  title, sharex=False, style = 'g.-')
#        axes = currencyBasket.plot(subplots = True)
#        for axe, v in zip(axes.flatten(),currencyBasket.columns):
#            axe.set_title(v)
#        plt.gcf().autolayout = True

#fx = fxData() # Para llamar a la clase
#    fx.createDB() # Creacion de la base de datos (borra todo y reinicia)
#    identifiers = ['AUD', 'BRL', 'CAD', 'CHF', 'CLP', 'CNH', 'COP', 'DKK', 'EUR', 'GBP', 'JPY', 'KRW', 'MXN', 'NOK', 'NZD', 'PLN', 'SEK', 'PEN', 'ZAR', 'TRY'] # Monedas para agregar
#    identifiers = ['PEN', 'ZAR', 'TRY'] # Otras monedas agregadas
#    fx.insertFXTicker(identifiers = identifiers) # Insertar monedas a la base de datos
#    datahistorical = fx.getDataBBGHistorical(window = 180) # Descargar data historica de una ventana de tiempo
#    fx.uploadDataBBGHistoricalToDB(start = pd.datetime(2016,12,23).date(), end = pd.datetime(2017,01,10).date()) # Actualizar data en la BD (Ultima fecha 2016,8,17)
#    fx.uploadDataBBGHistoricalToDB(window = 1080, identifier = ['USD']) # Actualizar data en la BD para solo una moneda, para un plazo determinado
#    eurHistoricalData = fx.getHistoricalDataUSDFromDB('EUR') # Descargar data historica para una moneda
#    crossCurrency = fx.getCrossCurrencyData('EUR','JPY') # Descargar data historica para un cruce de monedas determinado
#    crossCurrencyDict = fx.getAllCrossCurrencyData() # Descargar todos los crosses en base a los tickers ingresados
#    crossCurrencyReturns = fx.getCrossCurrencyReturns() # Obtener los retornos de todos los crosses
#    fx.createCurrencyBasketDB() # Creacion de las canastas de moneda
#    returnPerCurrency = fx.averageReturnPerCurrency() # Calcular series de tiempo de retornos de las monedas
#    fx.updateCurrencyBasketDB(periodicity='daily') # Actualizar datos de las monedas canastas en base diaria
#    fx.updateCurrencyBasketDB(periodicity='monthly') # Actualizar datos de las monedas canastas en base mensual
#    currencyBasket = fx.getCurrencyBasketFromDB() # Descargar los retornos de las monedas canastas
#    components, variance = fx.PCAFXAnalysis(periodicity='monthly') # Entrega las sensibilidades de componentes principales y su varianza explicada

# Plot de Principal Component Analysis:
#    fx.plotPCA(periodicity = 'monthly')
#    fx.plotPCA(periodicity = 'monthly', fxRisk = 'Reserve')
#    fx.plotPCA(periodicity = 'monthly', fxRisk = 'Commodity'), fxRisk = 'G10'
#fx.plotPCA(periodicity = 'daily', style = 'fivethirtyeight', start = pd.datetime(2016,01,01).date(), end = pd.datetime(2017,06,05).date())
#    fx.plotCurrencyBasketIndex(periodicity = 'monthly', fxRisk = 'G10') # Series de tiempo plot

# Asignacion de monedas por grupos:
#    fx.insertFXRisk('G10', ['USD','EUR','JPY','GBP','CAD','AUD','NZD','CHF','DKK','NOK','SEK'])
#    fx.insertFXRisk('Reserve', ['USD','EUR','JPY'])
#    fx.insertFXRisk('Commodity', ['NZD','CAD','AUD', 'NOK', 'CLP', 'MXN', 'BRL', 'COP','PEN'])
#    fx.insertFXRisk('Europe', ['EUR','GBP','NOK', 'CHF', 'PLN', 'SEK', 'DKK'])
#    fx.insertFXRisk('EM', ['CNH','CLP','PLN', 'KRW', 'MXN', 'BRL', 'COP','PER','ZAR','TRY'])
#    fx.insertFXRisk('DM', ['USD','EUR','JPY', 'CAD', 'AUD', 'NZD', 'NOK', 'CHF', 'SEK', 'DKK'])
#    fx.insertFXRisk('Commodity Ex-BRL', ['NZD','CAD','AUD', 'NOK', 'CLP', 'MXN', 'COP','PEN'])

#    fx.plotCorrelationMatrix(periodicity = 'monthly') # Graficar la matriz de correlaciones de las monedas canastas
#    returns = fx.getAllCurrencyUSDReturnData(periodicity = 'daily') # Descargar series de retornos de las monedas en dolares en base mensual
#    print(fx.risk_type()) # Ver los grupos de monedas disponbles
    
#    factorsIndex = fx.getFactorsReturns(periodicity = 'monthly', end = pd.datetime(2016,06,30).date()) # Generar series de retornos de los factores
#    factorsIndex = fx.getFactorsReturns(periodicity = 'daily', fxRisk='Reserve') # Generar series de retornos de los factores para un subgrupo de monedas
#    factorsIndex[0].sum(axis = 1).cumsum().plot(figsize=[15,9], fontsize = 13, title = 'Factor Risk-off (FX Only)') # Generar gráfico de retorno del factor
    
# Estrategia de monedas:
#    pd.options.display.mpl_style = 'default'
#    a = returns.ix[1000:,['AUD','CAD','COP','MXN','CLP']]
#    vol_a = a.std()*np.sqrt(252)
#    weights_a = (1/vol_a.drop('CLP'))/(1/vol_a.drop('CLP')).sum()
#    weights_a['CLP'] = -1
#    tsa = a.multiply(weights_a).sum(axis=1)
#    tsa.cumsum().plot(figsize=[12,8], fontsize = 10, title = 'AUD-CAD-COP-MXN vs CLP')
#    tsa.std()*np.sqrt(252)*100
#
#    
#    b = returns.ix[:,['AUD','BRL','ZAR','NZD','CLP']]
#    vol_b = b.std()*np.sqrt(252)
#    weights_b = (1/vol_b.drop('CLP'))/(1/vol_b.drop('CLP')).sum()
#    weights_b['CLP'] = -1
#    tsb = b.multiply(weights_b).sum(axis=1)
#    tsb.cumsum().plot(figsize=[12,8], fontsize = 13, title = 'AUD-BRL-ZAR-NZD vs CLP')
#    tsb.std()*np.sqrt(252)*100
#    
#    c = returns.ix[:,['AUD','BRL','ZAR','NZD','CLP','MXN','JPY','CHF','USD']]
#    vol_c = c.std()*np.sqrt(252)
#    weights_c = (1/vol_c.drop('CLP'))/(1/vol_c.drop('CLP')).sum()
#    weights_c['CLP'] = -1
#    tsc = c.multiply(weights_c).sum(axis=1)
#    tsc.cumsum().plot(figsize=[12,8], fontsize = 13, title = 'AUD-BRL-ZAR-NZD vs CLP')
#    tsc.std()*np.sqrt(252)*100