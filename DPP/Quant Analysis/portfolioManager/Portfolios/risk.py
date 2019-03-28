# -*- coding: utf-8 -*-
# coding: latin1
"""
Created on Mon Jul 25 13:48:09 2016

@author: ngoldbergerr
"""

from tia.bbg import v3api
import pandas as pd
#from dataBLP import blp
import sqlite3
import numpy as np
import csv
import sys

def banner(msg):
        print '*' * 50
        print msg
        print '*' * 50
        
class riskFactors(object):
    def __init__(self,path='L:\Rates & FX\Quant Analysis\portfolioManager\Portfolios\DB\\riskFactors.db'):
        #Generar objeto de factor de riesgo, que se encarga de descargar, clasificar y guardar información de factores de riesgo histórica.
        
        self.riskFactorDataName=[]
        self.BBGdata=[]
        self.dbPath=path        
        #self.riskFactorTicker=[]

### Open Connection to Database and Upload Data        
    def openConnection(self):
        #Función que abre una conexión con el default path de la clase
        con = sqlite3.connect(self.dbPath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        con.text_factory = str
        return con
        
    def createDB(self):
        #Función que crea base de datos y tablas necesarias para trabajar con el objeto
        con=self.openConnection()
        cursor = con.cursor()
        #con=sqlite3.connect(':memory:')
        cursor.execute('DROP TABLE IF EXISTS IndexIdentifier')
        cursor.execute('DROP TABLE IF EXISTS IndexData')

        cursor.execute("CREATE TABLE IndexIdentifier \
                (ID INTEGER PRIMARY KEY NOT NULL,\
                TICKER,\
                CURRENCY TEXT NOT NULL,\
                DESCRIPTION TEXT NOT NULL, \
                UNIQUE(TICKER))")
        
        cursor.execute("CREATE TABLE IndexData \
                (ID INTEGER PRIMARY KEY NOT NULL,\
                TICKER TEXT NOT NULL,\
                DATE DATE NOT NULL,\
                DATA REAL,\
                UNIQUE(TICKER,DATE))")

        con.close()
    
    def csvTicker(self, csvName = 'indexes.csv'):
        #Genera tabla importando los datos de los tickers desde un csv y los inserta en la base de datos
        with open(csvName) as csvfile:
            reader = csv.reader(csvfile)
            dataTmp=[]            
            [dataTmp.append(tickerData) for tickerData in reader]       
        
        tickers = [x[0] for x in dataTmp] 
        return tickers
    
    def loadBBGDataCharacteristics(self,identifiers):
#        d = pd.datetime.today()
        flds = ['ID_BB_SEC_NUM_DES','CRNCY','LONG_COMP_NAME']
        #Descarga información sobre los indices desde Bloomberg
        LocalTerminal = v3api.Terminal('localhost', 8194)
        try:
            response = LocalTerminal.get_reference_data(identifiers, flds, ignore_security_error=1, ignore_field_error=1)
        except:
            print("Unexpected error:", sys.exc_info()[0])

        newData = response.as_frame()

        return newData

    def loadBBGDataHistoricalPrices(self,identifiers,dateInitial,dateFinal):
#        d = pd.datetime.today()
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

    def buildIndexIdentifierAndUploadtoDB(self, source = 'indexes.csv'):
        #Construye la tabla que contiene la información estática de los indices y la sube a la base de datos
        tickers = self.csvTicker()
        dataIndex = self.loadBBGDataCharacteristics(tickers)
        con = self.openConnection()
        dataIndex.to_sql('IndexIdentifier', con, if_exists='replace')
        return True

    def buildHistoricalPricesAndUploadtoDB(self, source = 'indexes.csv', start='2015-07-01', end='2016-07-24'):
        #Construye la tabla que contiene la información estática de los indices y la sube a la base de datos
        tickers = self.csvTicker()
        prices = self.loadBBGDataHistoricalPrices(tickers, start, end)
        prices['CLPCLP Curncy'] = 1
        con = self.openConnection()
        aux = pd.DataFrame(columns = ['TICKER','DATE','DATA'])
        aux['DATA'] = prices.stack().values
        aux['DATE'] = prices.index.repeat(len(prices.columns))
        aux['TICKER'] = np.tile(prices.columns,len(prices.index))
#        x = pd.read_excel('C:\\Users\\ngoldbergerr\\Desktop\\indicejp.xlsx') # Nuevo, el directorio debe ajusarse
        aux.to_sql('IndexData', con, flavor='sqlite', if_exists='replace')
#        x.to_sql('IndexData', con, flavor='sqlite', if_exists='append', index = False)
        return True

### Get information from the database and compute returns and covariance matrix
    def getHistoricalPrices(self):
        #Construye el DataFrame con las series historicas de precios de los indices
        con = self.openConnection()
        p = pd.read_sql('SELECT DATE,TICKER,DATA FROM IndexData',con)
        prices = p.pivot(index='DATE',columns='TICKER')
        prices.columns = [prices.columns[x][1] for x in range(0,len(prices.columns))]
        return prices
    
    def getReturnsSeries(self):
        #Construye el DataFrame con las series historicas de retornos de los indices
        prices = self.getHistoricalPrices()
#        returns = prices.pct_change().fillna(0)
        returns = prices.pct_change()
        return returns
        
    def getCovarianceMatrix(self):
        returns = self.getReturnsSeries()
#        returns = pd.ewma(returns,span)
        return returns.cov().fillna(0)

### Update Database
    
    def buildHistoricalPricesAndUpdateDB(self, source = 'indexes.csv', start='2015-07-01', end='2016-07-24'):
        #Construye la tabla que contiene la información estática de los indices y actualiza la base de datos
        tickers = self.csvTicker()
        prices = self.loadBBGDataHistoricalPrices(tickers, start, end)
        prices['CLPCLP Curncy'] = 1
        con = self.openConnection()
        aux = pd.DataFrame(columns = ['TICKER','DATE','DATA'])
        aux['DATA'] = prices.stack().values
        aux['DATE'] = prices.index.repeat(len(prices.columns))
        aux['TICKER'] = np.tile(prices.columns,len(prices.index))
        aux.to_sql('IndexData', con, flavor='sqlite', if_exists='append')
        return True

    def insertNewIndexToDB(self, index_name, start='2015-07-01', end='2016-07-24'):
        #Agrega información histórica de uno o más índices a la tabla que contiene la información estática de los indices
        tickers = index_name
        prices = self.loadBBGDataHistoricalPrices(tickers, start, end)
        con = self.openConnection()
        aux = pd.DataFrame(columns = ['TICKER','DATE','DATA'])
        aux['DATA'] = prices.stack().values
        aux['DATE'] = prices.index.repeat(len(prices.columns))
        aux['TICKER'] = np.tile(prices.columns,len(prices.index))
        aux.to_sql('IndexData', con, flavor='sqlite', if_exists='append')
        return True


### Get Portfolio Positions and Allocate to Indexes
    def allocateInstrumentToIndex(self, portfolio):
        portfolio.index = range(0,len(portfolio))
        portfolio['link']='NULL'
        for n in range(0,len(portfolio)):
            if portfolio.instrument_type_cur[n] == 'Bono de Gobierno $':
                if portfolio['duration'].between(0.0,2.5)[n]:
                    portfolio['link'].loc[n] = 'RIAMBP02 Index'
                elif portfolio['duration'].between(2.5,3.5)[n]:
                    portfolio['link'].loc[n] = 'RIAMBP03 Index'
                elif portfolio['duration'].between(3.5,4.5)[n]:
                    portfolio['link'].loc[n] = 'RIAMBP04 Index'
                elif portfolio['duration'].between(4.5,5.92)[n]:
                    portfolio['link'].loc[n] = 'RIAMBP05 Index'                    
                elif portfolio['duration'].between(5.92,7.92)[n]:
                    portfolio['link'].loc[n] = 'RIAMBP07 Index'
                elif portfolio['duration'].between(7.92,10.92)[n]:
                    portfolio['link'].loc[n] = 'RIAMBP10 Index'
                elif portfolio['duration'].between(10.92,20.0)[n]:
                    portfolio['link'].loc[n] = 'RIAMBP20 Index'
                elif portfolio['duration'].between(20.0,30.0)[n]:
                    portfolio['link'].loc[n] = 'RIAMBP30 Index'
                    
            elif portfolio.instrument_type_cur[n] == 'Bono de Gobierno UF':
                if portfolio['duration'].between(0.0,2.5)[n]:
                    portfolio['link'].loc[n] = 'RIAMBU02 Index'
                elif portfolio['duration'].between(2.5,3.5)[n]:
                    portfolio['link'].loc[n] = 'RIAMBU03 Index'
                elif portfolio['duration'].between(3.5,4.5)[n]:
                    portfolio['link'].loc[n] = 'RIAMBU04 Index'
                elif portfolio['duration'].between(4.5,5.92)[n]:
                    portfolio['link'].loc[n] = 'RIAMBU05 Index'                    
                elif portfolio['duration'].between(5.92,7.92)[n]:
                    portfolio['link'].loc[n] = 'RIAMBU07 Index'
                elif portfolio['duration'].between(7.92,10.92)[n]:
                    portfolio['link'].loc[n] = 'RIAMBU10 Index'
                elif portfolio['duration'].between(10.92,20.0)[n]:
                    portfolio['link'].loc[n] = 'RIAMBU20 Index'
                elif portfolio['duration'].between(20.0,30.0)[n]:
                    portfolio['link'].loc[n] = 'RIAMBU30 Index'

            elif portfolio.instrument_type_cur[n] == 'Bono de Gobierno PEN':
                if portfolio['duration'].between(0.0,30.0)[n]:
                    portfolio['link'].loc[n] = 'PEP01000C4G7 Govt'

            elif portfolio.instrument_type_cur[n] == 'Bono de Gobierno EU':
                if portfolio['issuer_code'][n]=='FED REP BR':
                    portfolio['link'].loc[n] = 'US105756BM14 Govt'
                if portfolio['issuer_code'][n]=='UNITED MEX':
                    portfolio['link'].loc[n] = 'XS0525982657 Govt'
                    

            elif portfolio.instrument_type_cur[n] == 'Bono de Gobierno US$':
                if portfolio['issuer_name'][n] == 'Republica Federativa do Brasil':
                    if portfolio['duration'].between(3.0,5.0)[n]:
#                        portfolio['link'].loc[n] = 'BSEZTRUU Index'
                        portfolio['link'].loc[n] = 'US105756BS83 Govt'
                    elif portfolio['duration'].between(7.0,9.0)[n]:
#                        portfolio['link'].loc[n] = 'BEMSBR Index'
                        portfolio['link'].loc[n] = 'US105756BV13 Govt'
                if portfolio['issuer_name'][n] == 'Republica de Colombia':
                    if portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'US195325BN40 Govt'
                    
            elif portfolio.instrument_type_cur[n] == 'Gobierno EM':
                if portfolio['currency'].loc[n] == 'MXN':
                    if portfolio['duration'].between(0.0,30)[n]:
                        portfolio['link'].loc[n] = 'LCEXTRUU Index'
                    
            elif portfolio.instrument_type_cur[n] == 'Bono Corporativo $':
                if portfolio['risk'][n] in ['AAA']:
                    if portfolio['duration'].between(0.0,1.0)[n]: #Link a depo1Y!
                        portfolio['link'].loc[n] = 'RIAMI11Y Index'
                    elif portfolio['duration'].between(1.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1280 Index'                        
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1283 Index'    
                    elif portfolio['duration'].between(5.0,30.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1286 Index'
                
                elif portfolio['risk'][n] in ['AA+','AA','AA-']:
                    if portfolio['duration'].between(0.0,1.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1278 Index'
                    elif portfolio['duration'].between(1.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1281 Index'                        
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1284 Index'    
                    elif portfolio['duration'].between(5.0,30.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1287 Index'                    
                
                elif portfolio['risk'][n] in ['A+','A','A-']:
                    if portfolio['duration'].between(0.0,2.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC2 Index'
                    elif portfolio['duration'].between(2.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC3 Index'                        
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC5 Index'
                    elif portfolio['duration'].between(5.0,7.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC7 Index'
                    elif portfolio['duration'].between(7.0,30.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC8 Index'
                        
                elif portfolio['risk'][n] in ['BBB+','BBB','BBB-','BB+','BB','BB-','B+','B','B-','C']:
                    if portfolio['duration'].between(0.0,2.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB2 Index'
                    elif portfolio['duration'].between(2.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB3 Index'                        
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB5 Index'
                    elif portfolio['duration'].between(5.0,7.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB7 Index'
                    elif portfolio['duration'].between(7.0,150.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB8 Index'
                        
            elif portfolio.instrument_type_cur[n] == 'Bono Corporativo UF':
                if portfolio['risk'][n] in ['AAA']:
                    if portfolio['duration'].between(0.0,1.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1259 Index'
                    elif portfolio['duration'].between(1.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1262 Index'
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1265 Index'
                    elif portfolio['duration'].between(5.0,100.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1274 Index'
                
                elif portfolio['risk'][n] in ['AA+','AA','AA-']:
                    if portfolio['duration'].between(0.0,1.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1260 Index'
                    elif portfolio['duration'].between(1.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1263 Index'                        
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1266 Index'    
                    elif portfolio['duration'].between(5.0,30.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM1275 Index'                    
                
                elif portfolio['risk'][n] in ['A+','A','A-']:
                    if portfolio['duration'].between(0.0,2.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC2 Index'
                    elif portfolio['duration'].between(2.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC3 Index'                        
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC5 Index'
                    elif portfolio['duration'].between(5.0,7.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC7 Index'
                    elif portfolio['duration'].between(7.0,30.0)[n]:
                        portfolio['link'].loc[n] = 'RIAM0AC8 Index'

                elif portfolio['risk'][n] in ['BBB+','BBB','BBB-','BB+','BB','BB-','B+','B','B-','C']:
                    if portfolio['duration'].between(0.0,2.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB2 Index'
                    elif portfolio['duration'].between(2.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB3 Index'
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB5 Index'
                    elif portfolio['duration'].between(5.0,7.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB7 Index'
                    elif portfolio['duration'].between(7.0,150.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB8 Index'
                
                elif portfolio['risk'].isnull()[n]:
                    if portfolio['instrument_name'][n] == 'Im Trust  Spread Corporativo Local':
                        portfolio['link'].loc[n] = 'RIAM0AC7 Index'
                    elif portfolio['instrument_name'][n]  == 'Im Trust Deuda Corporativa Ig': 
                        portfolio['link'].loc[n] = 'RIAM1266 Index'
                
                else:
                    if portfolio['duration'].between(0.0,2.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB2 Index'
                    elif portfolio['duration'].between(2.0,3.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB3 Index'
                    elif portfolio['duration'].between(3.0,5.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB5 Index'
                    elif portfolio['duration'].between(5.0,7.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB7 Index'
                    elif portfolio['duration'].between(7.0,150.0)[n]:
                        portfolio['link'].loc[n] = 'RIAMBBB8 Index'
                        
            elif portfolio.instrument_type_cur[n] == 'Bono Corporativo US$':
                if portfolio['risk'][n] in ['AAA','AA+','AA','AA-','A+','A','A-']:
                    portfolio['link'].loc[n] = 'USDCLP Curncy' #'BUSC Index' # Aqui iba el jbcdcl
                elif portfolio['risk'][n] in ['BBB+','BBB','BBB-','BB+','BB','BB-','B+','B','B-','C']:
                    portfolio['link'].loc[n] = 'USDCLP Curncy' #'BUHY Index'
                
            elif portfolio.instrument_type_cur[n][0:3] == 'Dep' and portfolio.instrument_type_cur[n][-1] == '$':
                if portfolio['duration'].between(0.0,float(7)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMI107 Index'
                elif portfolio['duration'].between(float(7.00001)/365,float(30)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMI130 Index'
                elif portfolio['duration'].between(float(30.00001)/365,float(60)/365)[n]:                 
                    portfolio['link'].loc[n] = 'RIAMI160 Index'
                elif portfolio['duration'].between(float(60.00001)/365,float(90)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMI190 Index'
                elif portfolio['duration'].between(float(90.00001)/365,float(120)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI120 Index'   
                elif portfolio['duration'].between(float(120.00001)/365,float(150)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMI150 Index'                       
                elif portfolio['duration'].between(float(150.00001)/365,float(180)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI180 Index'                     
                elif portfolio['duration'].between(float(180.00001)/365,float(270)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI270 Index'      
                elif portfolio['duration'].between(float(270.00001)/365,float(365)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI11Y Index'
                elif portfolio['duration'].between(1.0000001,30.0)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIIA1 Index'

            elif portfolio.instrument_type_cur[n] == 'Factura $':
                if portfolio['duration'].between(0.0,float(7)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMI107 Index'
                elif portfolio['duration'].between(float(7.01)/365,float(30)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMI130 Index'
                elif portfolio['duration'].between(float(30.01)/365,float(60)/365)[n]:                 
                    portfolio['link'].loc[n] = 'RIAMI160 Index'
                elif portfolio['duration'].between(float(60.01)/365,float(90)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI190 Index'
                elif portfolio['duration'].between(float(90.01)/365,float(120)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI120 Index'   
                elif portfolio['duration'].between(float(120.01)/365,float(150)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMI150 Index'                       
                elif portfolio['duration'].between(float(150.01)/365,float(180)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI180 Index'                     
                elif portfolio['duration'].between(float(180.01)/365,float(270)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI270 Index'      
                elif portfolio['duration'].between(float(270.01)/365,float(365)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMI11Y Index'
                elif portfolio['duration'].between(1.0001,30.0)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIIA1 Index'

            elif portfolio.instrument_type_cur[n] == 'Letra Hipotecaria UF':
                if portfolio['duration'].between(0.0,float(7)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMIU07 Index'
                elif portfolio['duration'].between(float(7)/365,float(30)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMIU30 Index'
                elif portfolio['duration'].between(float(31)/365,float(60)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU60 Index'
                elif portfolio['duration'].between(float(61)/365,float(90)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU90 Index'
                elif portfolio['duration'].between(float(91)/365,float(120)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU12 Index'   
                elif portfolio['duration'].between(float(121)/365,float(150)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU15 Index'                       
                elif portfolio['duration'].between(float(151)/365,float(180)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU18 Index'                     
                elif portfolio['duration'].between(float(181)/365,float(270)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU27 Index'      
                elif portfolio['duration'].between(float(271)/365,float(365)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU1Y Index'
                elif portfolio['duration'].between(1.0,30.0)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIT2Y Index'

            elif portfolio.instrument_type_cur[n][0:3] == 'Dep' and portfolio.instrument_type_cur[n][-2:]=='UF':
                if portfolio['duration'].between(0.0,float(7)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMIU07 Index'
                elif portfolio['duration'].between(float(7)/365,float(30)/365)[n]:
                    portfolio['link'].loc[n] = 'RIAMIU30 Index'
                elif portfolio['duration'].between(float(30)/365,float(60)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU60 Index'
                elif portfolio['duration'].between(float(60)/365,float(90)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU90 Index'
                elif portfolio['duration'].between(float(90)/365,float(120)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU12 Index'   
                elif portfolio['duration'].between(float(120)/365,float(150)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU15 Index'                
                elif portfolio['duration'].between(float(150)/365,float(180)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU18 Index'                     
                elif portfolio['duration'].between(float(180)/365,float(270)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU27 Index'      
                elif portfolio['duration'].between(float(270)/365,float(365)/365)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIU1Y Index'
                elif portfolio['duration'].between(1.0,30.0)[n]:                    
                    portfolio['link'].loc[n] = 'RIAMIT2Y Index'

            elif portfolio.instrument_type_cur[n] == 'Cuota de Fondo $':
                if portfolio['instrument_code'][n] == 'CFI7275IM':
                    portfolio['link'].loc[n] = 'CLPCLP Curncy'
                elif portfolio['instrument_code'][n] == 'CFI9251IM':
                    portfolio['link'].loc[n] = 'CLPCLP Curncy'
                elif portfolio['instrument_code'][n] == 'CFI9107IM':
                    portfolio['link'].loc[n] = 'CLPCLP Curncy'
                else:
                    portfolio['link'].loc[n] = 'CLPCLP Curncy'
      
            elif portfolio.instrument_type_cur[n] == 'Cuota de Fondo US$':
                if portfolio['instrument_code'][n] == 'CFM9365IM':
                    portfolio['link'].loc[n] = 'USDCLP Curncy'
      
            elif portfolio.instrument_type_cur[n][0:8] == 'Efectivo':
                if portfolio.instrument_type_cur[n][-3:] == 'CLP':
                    portfolio['link'].loc[n] = 'CLPCLP Curncy'
                elif portfolio.instrument_type_cur[n][-2:] == 'UF':
                    portfolio['link'].loc[n] = 'CLFCLP Curncy'
                else:
                    portfolio['link'].loc[n] = portfolio.instrument_type_cur[n][-3:]+'CLP Curncy'

            elif portfolio.instrument_type_cur[n][0:2] == 'FX':
                if portfolio.instrument_type_cur[n][-2:] == 'UF':
                    portfolio['link'].loc[n] = 'CLFCLP Curncy'
                if portfolio.instrument_type_cur[n] == ' UFCLP Curncy':
                    portfolio['link'].loc[n] = 'CLFCLP Curncy'
                if portfolio.currency[n] == '$':
                    portfolio['link'].loc[n] = 'CLPCLP Curncy'
                else:
                    portfolio['link'].loc[n] = portfolio.instrument_type_cur[n][-3:]+'CLP Curncy'


if __name__=='__main__':
    rf=riskFactors()
    rf.createDB() # Correr solo para crear nuevamente la base de datos
    identifiers = rf.csvTicker() # Extrae los identificadores del csv del archivo (path)
    rf.buildIndexIdentifierAndUploadtoDB()  # Construir la tabla con los indices e identificadores
    rf.buildHistoricalPricesAndUploadtoDB(source = 'indexes.csv', start='2016-01-31', end='2017-02-21') # Construir la tabla con los valores de los indices
#    p = rf.getHistoricalPrices() # Construir la tabla de precios de los indices
#    ret = rf.getReturnsSeries() # Construir la tabla de retornos de los indices
#    cm = rf.getCovarianceMatrix() # Construir la matriz de varianza covarianza de los indices
#    rf.allocateInstrumentToIndex()
#    rf.allocateInstrumentToIndex(portfolio)
#    rf.buildHistoricalPricesAndUpdateDB(source = 'indexes.csv', start='2016-12-31', end='2017-02-21')
#    rf.insertNewIndexToDB(['XS0525982657 Govt'],start='2016-07-21', end='2016-11-21') # Agregar Indice a la base de datos de indices

    
    
    
    
    
        