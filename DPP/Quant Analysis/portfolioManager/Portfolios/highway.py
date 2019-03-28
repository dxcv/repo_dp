# -*- coding: utf-8 -*-
# coding: latin1
"""
Created on Thu Jul 07 09:10:22 2016

author: goldbena
"""

import numpy as np
import pandas as pd
import sqlite3
import math
from dbfunctions import *
from decimal import *
from tia.bbg import LocalTerminal
#import matplotlib.pyplot as plt
from risk import riskFactors

def banner(msg):
        print ('*' * 50)
        print (msg)
        print ('*' * 50)

banner('Opening connection to database')


class portClas(object):
    
    def __init__(self):
        self.path = getSelfPath()

### Get information from Database
        
    def getPortFromDB(self, date=getNDaysFromToday(1)):
        server = 'PUYEHUE'
        database = 'MesaInversiones'
        query_portfolios = extractTextFile(self.path+"querys\\full_carteras_new.sql").replace("AUTODATE", date)
        conn = connectDatabase(server, database)
        cursor = queryDatabase(conn, query_portfolios)
        table = getTableSQL(cursor)
        field_names = getTableFields(cursor)
        banner('Creating Portfolio Matrix')
        self.matrix = pd.DataFrame(table,columns=field_names)
        self.matrix['instrument_type_cur'] = self.matrix['instrument_type'] +' '+ self.matrix['currency']
        self.matrix = self.matrix[self.matrix['market_value'] != 0]
        disconnectDatabase(conn)
        banner('Connection to database closed')
        return self.matrix
        
    def getBenchmarkFromDB(self, date=getNDaysFromToday(1)):
        server = 'PUYEHUE'
        database = 'MesaInversiones'
        query_portfolios = extractTextFile(self.path+"querys\\full_benchmarks.sql").replace("AUTODATE", date)
        conn = connectDatabase(server, database)
        cursor = queryDatabase(conn, query_portfolios)
        table = getTableSQL(cursor)
        field_names = getTableFields(cursor)
        banner('Creating Benchmark Matrix')
        self.benchmark = pd.DataFrame(table,columns=field_names)
        disconnectDatabase(conn)
        banner('Connection to database closed')
        self.benchmark['instrument_type_cur'] = 'Bono Corporativo UF'
        return self.benchmark

    def getFXfromBloomberg(self):
        self.USDCLP = LocalTerminal.get_historical(['CLFXDOOB Index'], ['PX_LAST'], start=dt.datetime.now() - dt.timedelta(days=1)).as_frame()['CLFXDOOB Index']['PX_LAST'][0]
        self.MXNCLP = LocalTerminal.get_historical(['MXNCLP Curncy'], ['PX_LAST'], start=dt.datetime.now() - dt.timedelta(days=1)).as_frame()['MXNCLP Curncy']['PX_LAST'][0]
        self.COPCLP = LocalTerminal.get_historical(['COPCLP Curncy'], ['PX_LAST'], start=dt.datetime.now() - dt.timedelta(days=1)).as_frame()['COPCLP Curncy']['PX_LAST'][0]
        self.PENCLP = LocalTerminal.get_historical(['PENCLP Curncy'], ['PX_LAST'], start=dt.datetime.now() - dt.timedelta(days=1)).as_frame()['PENCLP Curncy']['PX_LAST'][0]
        self.BRLCLP = LocalTerminal.get_historical(['BRLCLP Curncy'], ['PX_LAST'], start=dt.datetime.now() - dt.timedelta(days=1)).as_frame()['BRLCLP Curncy']['PX_LAST'][0]
        self.CLFCLP = LocalTerminal.get_historical(['CLF Curncy'], ['PX_LAST'], start=dt.datetime.now() - dt.timedelta(days=1)).as_frame()['CLF Curncy']['PX_LAST'][0]
        self.EURCLP = LocalTerminal.get_historical(['EURCLP Curncy'], ['PX_LAST'], start=dt.datetime.now() - dt.timedelta(days=1)).as_frame()['EURCLP Curncy']['PX_LAST'][0]
        
    def getCashFromDB(self, date=getNDaysFromToday(1)):
        self.getFXfromBloomberg()  
        pd.options.display.float_format = '{:,.0f}'.format
        server = 'BCS11384'
        database = 'BDPFM2'
        username = 'usuario1'
        password = 'usuario1'
        # Cash from Investment Funds
        query_cash = extractTextFile(self.path+"querys\\cash_fi.sql").replace("AUTODATE", date)
        conn = connectDatabaseUser(server, database, username, password)
        cursor = queryDatabase(conn, query_cash)
        table = getTableSQL(cursor)
        field_names = getTableFields(cursor)
        banner('Creating Cash Positions Matrix for Investment Funds')
        cash_fi = pd.DataFrame(table,columns=field_names)
        disconnectDatabase(conn)
        banner('Connection to database closed')
        # Cash from Mutual Funds
        query_cash = extractTextFile(self.path+"querys\\cash_fm.sql").replace("AUTODATE", date)
        conn = connectDatabaseUser(server, database, username, password)
        cursor = queryDatabase(conn, query_cash)
        table = getTableSQL(cursor)
        field_names = getTableFields(cursor)
        banner('Creating Cash Positions Matrix for Mutual Funds')
        cash_fm = pd.DataFrame(table,columns=field_names)
        # Multiplico por -1 las cuentas de pasivo para FM
        for i in cash_fm.loc[cash_fm['Account'].isin(['201001001002', '201001001003', '201001001006','201001001001'])].index:
            cash_fm.loc[i,'Balance'] = -cash_fm.loc[i,'Balance']
        # Multiplico por -1 las cuentas de pasivo para FI
        for i in cash_fi.loc[cash_fi['Account'].isin(['201001001002', '201001001003', '201001001006','201001001001'])].index:
            cash_fi.loc[i,'Balance'] = -cash_fi.loc[i,'Balance']            
            
        disconnectDatabase(conn)
        banner('Connection to database closed')
        
        # Construccion de los saldos en cuenta corriente
        USDfi = ['101001001003', '101001002001', '101001002002', '101001002004']
        EURfi = ['101001002003', '201001001001']
        CLPfi = ['101001001001', '101001001002', '101001001004', '101001001005','101001001008','101003001001','101003001003','201001001002','201001001003','201001001006']
        currencies = ['CLP','USD','EUR'] #Estas son las monedas en las que hay caja, hay que arreglarlo apra que tome las monedas automaticamente ***
        cash_fi_ccy = pd.DataFrame(index =cash_fi.Name.unique(), columns = ['CLP','USD','EUR'])
        cash_fi_ccy['CLP'] = cash_fi.loc[cash_fi['Account'].isin(CLPfi)].groupby(by='Name')['Balance'].sum()
        cash_fi_ccy['USD'] = cash_fi.loc[cash_fi['Account'].isin(USDfi)].groupby(by='Name')['Balance'].sum()
        cash_fi_ccy['EUR'] = cash_fi.loc[cash_fi['Account'].isin(EURfi)].groupby(by='Name')['Balance'].sum()
        z = 0

        fi = pd.DataFrame(index=cash_fi_ccy.index, columns=currencies)
        for y in currencies: #Esto es para transformar los Decimals en Floats
            try:
                fi[y] = [np.round(float(cash_fi_ccy.values[x][z]),4) for x in range(0,len(cash_fi_ccy))]
                z += 1
            except:
                print('No '+y+' cash information for investment funds')
                
#        fi['USD'] = fi['USD']#/self.USDCLP
#        fi['EUR'] = fi['EUR']#/self.EURCLP
        fi = fi.fillna(0)
        
        
        USDfm = ['101001001003', '101001001004', '101001002001', '101001002003', '101001002002', '101001002004','101001002006']
        CLPfm = ['101001001001', '101001001002', '101001001004','101001001005','101001001008','101003001001','101003001003','201001001002','201001001003']
        EURfm = ['101001002013', '201001001001']
        
        cash_fm_ccy = pd.DataFrame(index =cash_fm.Name.unique(), columns = ['CLP','USD','EUR'])
        cash_fm_ccy['CLP'] = cash_fm.loc[cash_fm['Account'].isin(CLPfm)].groupby(by='Name')['Balance'].sum()
        cash_fm_ccy['USD'] = cash_fm.loc[cash_fm['Account'].isin(USDfm)].groupby(by='Name')['Balance'].sum()
        cash_fm_ccy['EUR'] = cash_fm.loc[cash_fm['Account'].isin(EURfm)].groupby(by='Name')['Balance'].sum()
        z = 0

        fm = pd.DataFrame(index =cash_fm_ccy.index, columns=currencies)
        for y in currencies: #Esto es para transformar los Decimals en Floats
            try:
                fm[y] = [np.round(float(cash_fm_ccy.values[x][z]),4) for x in range(0,len(cash_fm_ccy))]
                z += 1
            except:
                print('No '+y+' cash information for mutual funds')
                
#        fm['USD'] = fm['USD']/self.USDCLP        
        fm['USD']['M_MARKET'] = fm['USD']['M_MARKET']*self.USDCLP
        fm = fm.loc[fm.index != 'DSMULTI']
        fm = fm.fillna(0)
        
        # Ajuste de saldos por vencimientos
#        matured= self.matrix[(matrix['name']==portName) & (matrix['maturity_date']==str(dt.datetime.today())[0:10])]
        matured = self.matrix[(self.matrix['maturity_date']==str(dt.datetime.today())[0:10])]
        inflow = pd.DataFrame(index=np.append(fm.index.values, fi.index.values), columns=fm.columns)
        for ccy in matured['currency'].unique():
            if ccy == '$':
                ccy = 'CLP'
                inflow[ccy]=matured[matured['currency']=='$'].groupby(by='name')['market_value'].sum()
#            if ccy == 'UF': # Aqui lo correcto sería sumar el vencimiento en UF pasado a CLP al saldo en CLP
#                inflow[ccy]=matured[matured['currency']=='UF'].groupby(by='name')['market_value'].sum()

        inflow = inflow.fillna(0)
        for y in currencies: #Esto es para transformar los Decimals en Floats
            inflow[y] = [np.round(float(inflow[y][q]),4) for q in range(0,len(inflow))]
        
        return fi.append(fm).add(inflow, fill_value=0)

    def getForwardsFromDB(self, date=getNDaysFromToday(1)):
        server = 'PUYEHUE'
        database = 'MesaInversiones'
        query_portfolios = extractTextFile(self.path+"querys\\forwards.sql").replace("AUTODATE", date)
        conn = connectDatabase(server, database)
        cursor = queryDatabase(conn, query_portfolios)
        table = getTableSQL(cursor)
        field_names = getTableFields(cursor)
        banner('Creating Forwards Matrix')
        self.fwd = pd.DataFrame(table,columns=field_names)
        disconnectDatabase(conn)
        banner('Connection to database closed')
        return self.fwd

### Build positions summary

    def buildPortPic(self, portName, date = getNDaysFromToday(1)):
#        port = portClas()
#        matrix = port.getPortFromDB()
#        self.matrix = port.getPortFromDB()
        port = portClas()
        self.matrix = port.getPortFromDB(date)
        fecha = self.matrix['date'][0]
        portfolio = self.matrix.loc[self.matrix['name'] == portName]
        return fecha, portfolio
        
    def getPositionsMatrix(self,portName, date = getNDaysFromToday(1)):
        date, portfolio = self.buildPortPic(portName, date)

        # Agregamos posiciones que estan invertidas en otros portafolios

        if 'CFI9251IM' in set(portfolio['instrument_code']):
            fecha, quota = self.buildPortPic('DEUDA CORP')
            amt_in_quota = portfolio.loc[portfolio['instrument_code'] == 'CFI9251IM']['market_value']
            quota['market_value'] = quota['pct_fund']*np.asarray(amt_in_quota)
            pct_in_quota = portfolio.loc[portfolio['instrument_code'] == 'CFI9251IM']['pct_fund']
            quota['pct_fund'] = quota['pct_fund']*np.asarray(pct_in_quota)
            portfolio = portfolio[portfolio.instrument_code != 'CFI9251IM']
            portfolio = portfolio.append(quota)

        if 'CFM9310IM' in set(portfolio['instrument_code']):
            fecha, quota = self.buildPortPic('MACRO 1.5')
            amt_in_quota = portfolio.loc[portfolio['instrument_code'] == 'CFM9310IM']['market_value']
            quota['market_value'] = quota['pct_fund']*np.asarray(amt_in_quota)
            pct_in_quota = portfolio.loc[portfolio['instrument_code'] == 'CFM9310IM']['pct_fund']
            quota['pct_fund'] = quota['pct_fund']*np.asarray(pct_in_quota)
            portfolio = portfolio[portfolio.instrument_code != 'CFM9310IM']
            portfolio = portfolio.append(quota)

        if 'CFI7275IM' in set(portfolio['instrument_code']):
            fecha, quota = self.buildPortPic('IMT E-PLUS')
            amt_in_quota = portfolio.loc[portfolio['instrument_code'] == 'CFI7275IM']['market_value']
            quota['market_value'] = quota['pct_fund']*np.asarray(amt_in_quota)
            pct_in_quota = portfolio.loc[portfolio['instrument_code'] == 'CFI7275IM']['pct_fund']
            quota['pct_fund'] = quota['pct_fund']*np.asarray(pct_in_quota)
            portfolio = portfolio[portfolio.instrument_code != 'CFI7275IM']
            portfolio = portfolio.append(quota)
            
        if 'CFI9251IM' in set(portfolio['instrument_code']):
            fecha, quota = self.buildPortPic('DEUDA CORP')
            amt_in_quota = portfolio.loc[portfolio['instrument_code'] == 'CFI9251IM']['market_value']
            quota['market_value'] = quota['pct_fund']*np.asarray(amt_in_quota)
            pct_in_quota = portfolio.loc[portfolio['instrument_code'] == 'CFI9251IM']['pct_fund']
            quota['pct_fund'] = quota['pct_fund']*np.asarray(pct_in_quota)
            portfolio = portfolio[portfolio.instrument_code != 'CFI9251IM']
            portfolio = portfolio.append(quota)

        # Ajustamos CTDy agregamos CTY
        del portfolio['ctd'] # Ajuste de Contribution to Duration:
        portfolio['ctd'] = portfolio['pct_fund']*portfolio['duration']
        portfolio['cty'] = portfolio['pct_fund']*portfolio['yield_db']
        
        # Agregamos Saldos en Efectivo
        efectivo = self.getCashFromDB()
        cash_clp = pd.DataFrame(data = [portName,'CASH',efectivo['CLP'][portName],Decimal(0.0),'Efectivo en CLP',Decimal(0.0)], 
                            index = ['name','instrument_code', 'market_value', 'ctd','instrument_type_cur','cty']).transpose()
#        cash_uf = pd.DataFrame(data = [portName,'CASH',efectivo['UF'][portName],'0.0','Efectivo en CLP','0'], 
#                            index = ['name','instrument_code', 'market_value', 'ctd','instrument_type_cur','cty']).transpose()
        cash_clp['market_value'] = cash_clp['market_value'] #+cash_uf['market_value']
        portfolio = portfolio.append(cash_clp)

        cash_usd = pd.DataFrame(data = [portName,'CASH',efectivo['USD'][portName],Decimal(0.0),'Efectivo en USD',Decimal(0.0)], 
                            index = ['name','instrument_code', 'market_value', 'ctd','instrument_type_cur','cty']).transpose()        
        portfolio = portfolio.append(cash_usd)

        cash_eur = pd.DataFrame(data = [portName,'CASH',efectivo['EUR'][portName],Decimal(0.0),'Efectivo en EUR',Decimal(0.0)], 
                            index = ['name','instrument_code', 'market_value', 'ctd','instrument_type_cur','cty']).transpose()        
        portfolio = portfolio.append(cash_eur)
        
        # Agregamos posiciones forward
        fxfwd = self.getForwardsFromDB()

        forwards_long = fxfwd[['Codigo_Fdo', 'Fecha_Vcto', 'Codigo_Emi', 'Moneda_Compra', 'Nominal_Compra']]
        forwards_long.columns = ['name', 'maturity_date','issuer_name','currency','nominal']
        forwards_long = forwards_long.loc[forwards_long['name']==portName]
        
        forwards_short = fxfwd[['Codigo_Fdo', 'Fecha_Vcto', 'Codigo_Emi', 'Moneda_Venta', 'Nominal_Venta']]
        forwards_short.columns = ['name', 'maturity_date','issuer_name','currency','nominal']
        forwards_short = forwards_short.loc[forwards_short['name']==portName]
        forwards_short.loc[:,'nominal'] = forwards_short['nominal']*-1
        
        forwards = pd.DataFrame(columns = ['currency','market_value','instrument_code','instrument_type_cur','name'])
        
#        forwards['currency'] = forwards_long.append(forwards_short).groupby(by='currency')['nominal'].sum().index
#        forwards['market_value'] = forwards_long.append(forwards_short).groupby(by='currency')['nominal'].sum().values
#        forwards = forwards.loc[forwards['market_value'] !=0]
        
        forwards['currency'] = np.concatenate((forwards_long['currency'].values,forwards_short['currency'].values),axis=0)
        forwards['market_value'] = np.concatenate((forwards_long['nominal'].values,forwards_short['nominal'].values),axis=0)
        forwards['instrument_code'] = 'FX Forwards'
        forwards['name'] = portName
        for i in range(0,len(forwards)):
            if forwards['market_value'].iloc[i]<0:
                forwards['instrument_type_cur'].iloc[i] = "FX Forward Short " + forwards['currency'].iloc[i]
            else:
                forwards['instrument_type_cur'].iloc[i] = "FX Forward Long " + forwards['currency'].iloc[i]

#        for ccy in forwards['currency']:
#            if ccy == 'USD':
#                forwards['market_value'][forwards.currency == ccy] = forwards.loc[forwards['currency']==ccy]['market_value']*self.USDCLP
#            if ccy == 'MXN':
#                forwards['market_value'][forwards.currency == ccy] = forwards.loc[forwards['currency']==ccy]['market_value']*self.MXNCLP
#            if ccy == 'COP':        
#                forwards['market_value'][forwards.currency == ccy] = forwards.loc[forwards['currency']==ccy]['market_value']*self.COPCLP
#            if ccy == 'PEN':        
#                forwards['market_value'][forwards.currency == ccy] = forwards.loc[forwards['currency']==ccy]['market_value']*self.PENCLP

        for i in range(0,len(forwards)):
            if forwards['currency'].iloc[i] == 'USD':
                forwards['market_value'].iloc[i] = forwards['market_value'].iloc[i]*self.USDCLP
            if forwards['currency'].iloc[i] ==  'MXN':
                forwards['market_value'].iloc[i] = forwards['market_value'].iloc[i]*self.MXNCLP
            if forwards['currency'].iloc[i] == 'COP':        
                forwards['market_value'].iloc[i] = forwards['market_value'].iloc[i]*self.COPCLP
            if forwards['currency'].iloc[i] == 'PEN':        
                forwards['market_value'].iloc[i] = forwards['market_value'].iloc[i]*self.PENCLP
            if forwards['currency'].iloc[i] == 'EUR':        
                forwards['market_value'].iloc[i] = forwards['market_value'].iloc[i]*self.EURCLP

        portfolio = portfolio.append(forwards)

        # Ajuste de posiciones en monedas extranjeras
        exposures = portfolio.loc[portfolio.currency.isin(['BRL','US$','MXN','COP','EU','PEN'])]
        exposures['market_value'] = [float(x) for x in exposures['market_value']]
        exposures['instrument_code'] = 'Numeraire'
        exposures['ctd'] = 0
        exposures['cty'] = 0
#        exposures['currency'].loc[exposures['currency'] == 'US$'] = exposures['currency'].replace('US$','USD')
#        exposures['currency'].loc[exposures['currency'] == 'EU'] = exposures['currency'].replace('EU','EUR')
        exposures['currency'] = exposures['currency'].replace('US$','USD')
        exposures['currency'] = exposures['currency'].replace('EU','EUR')
        exposures['date'] = ['']*len(exposures)
        exposures['duration'] = 0
        exposures['sector'] = ['']*len(exposures)
        exposures['instrument_name'] = ['FX Exposure']*len(exposures)
        exposures['instrument_type'] = ['']*len(exposures)
        exposures['instrument_type_cur'] = 'FX Exposure ' + exposures['currency']
        exposures['issuer_code'] = ['']*len(exposures)
        exposures['issuer_name'] = ['']*len(exposures)
        exposures['maturity_date'] = ['']*len(exposures)
        exposures['nominal_amount'] = ['']*len(exposures)
        exposures['pct_fund'] = ['']*len(exposures)
        exposures['price'] = ['']*len(exposures)
        exposures['risk'] = ['']*len(exposures)
        exposures['yield_db'] = 0
        portfolio = portfolio.append(exposures)


        # Ajuste de pesos de instrumentos individuales
        attributes = ['market_value']
        out = pd.DataFrame(portfolio[attributes]).round(2)
        dat = pd.DataFrame(columns = attributes)
        z = 0        
        for y in attributes: #Esto es para transformar los Decimals en Floats
            dat[y] = [np.round(float(out.values[x][z]),4) for x in range(0,len(out))]
            z += 1
        dat.index = out.index
        
        dat['instrument_type_cur'] = portfolio['instrument_type_cur']
#        portfolio['w'] = [x/dat['market_value'].sum() for x in dat['market_value']]
        portfolio['w'] = [x/(dat['market_value'].sum()-float(exposures['market_value'].sum())) for x in dat['market_value']]
        portfolio = portfolio[portfolio['w'] != 0.0]
        portfolio = portfolio[portfolio['issuer_code'] != 'DOLAR']
        return portfolio

### Add trades to portfolio
    def generateTrade(self,instrument_code,issuer_name,instrument_type_cur,currency,duration,portfolio_name,nominal,price):
        fx = {'USD': self.USDCLP,'MXN': self.MXNCLP, 'BRL': self.BRLCLP, 'UF': self.CLFCLP, 'PEN': self.PENCLP}
        self.trades = pd.DataFrame(data = [instrument_code,issuer_name,instrument_type_cur,currency,duration,portfolio_name,nominal,price,nominal*float(price)/100*fx[currency]], 
                                           index = ['instrument_code','issuer_name','instrument_type_cur','currency','duration','name','nominal','price','market_value']).transpose()
        self.trades = self.trades.append(pd.DataFrame(data = ['CASH','Efectivo en '+currency,currency,0,portfolio_name,-nominal*float(price)/100,1,-nominal*float(price)/100*fx[currency]],
                                                              index = ['instrument_code','instrument_type_cur','currency','duration','name','nominal','price','market_value']).transpose())
        return self.trades
        
    def insertTradeToPortfolio(self,p):
        psim = p.append(self.trades)
        psim['market_value'] = [float(psim['market_value'].iloc[i]) for i in range(0,len(psim))]
        psim['w'] = [x/psim['market_value'].sum() for x in psim['market_value']]
        return psim
### Build risk summary

#    def getTrackingError(self, portfolio, benchmark='None'):
#        rf = riskFactors()
#        rf.allocateInstrumentToIndex(portfolio)
#        weights = portfolio.groupby(by='link').sum()
#        Sigma = rf.getCovarianceMatrix()
#        w_p = weights.reindex(index=Sigma.index).fillna(0)
#        te = np.sqrt(w_p.transpose().dot(Sigma.dot(w_p)))
#
#        # Marginal Contribution to Risk & Contribution to Risk
#        MCR = Sigma.dot(w_p)/te.values[0]
#        CTR = w_p.multiply(MCR)
#        PCTR = CTR/te.values[0]
#        
#        portfolio.index = portfolio['link']
#        portfolio['MCR'] = 0
#        portfolio['CTR'] = 0
#        portfolio['PCTR'] = 0
#        for i in portfolio.index:
#            portfolio['MCR'].loc[i] = MCR['w'].loc[i]*np.sqrt(252)*100
#            portfolio['CTR'].loc[i] = CTR['w'].loc[i]*(portfolio['w'].loc[i]/portfolio.groupby(by='link')['w'].sum().loc[i])*np.sqrt(252)*100
#            portfolio['PCTR'].loc[i] = PCTR['w'].loc[i]*(portfolio['w'].loc[i]/portfolio.groupby(by='link')['w'].sum().loc[i])*100
#            
#        return portfolio

    def getTrackingError(self, portfolio, benchmark='None'):
        rf = riskFactors()
        rf.allocateInstrumentToIndex(portfolio)
        weights = portfolio.groupby(by='link').sum()
        Sigma = rf.getCovarianceMatrix()
        w_p = weights.reindex(index=Sigma.index).fillna(0)
        try:
            del w_p['market_value']
        except:
            banner('Portfolio Market Value as decimal')
            
        if isinstance(benchmark, pd.DataFrame):
            rf.allocateInstrumentToIndex(benchmark)
            weights_b = benchmark.groupby(by='link').sum()/100
            w_b = weights_b.reindex(index=Sigma.index).fillna(0)
            del w_b['duration']
            del w_b['maturity_years']
            del w_b['yield']
            w_b.columns = ['w']
            w_a = (w_p-w_b)
        else:
            w_a = w_p
            
        te = np.sqrt(w_a.transpose().dot(Sigma.dot(w_a)))

        # Marginal Contribution to Risk & Contribution to Risk
        MCR = Sigma.dot(w_a)/te.values[0]
        CTR = w_a.multiply(MCR)
        PCTR = CTR/te.values[0]
        
        portfolio = portfolio[portfolio['link'] != ' UFCLP Curncy']
        portfolio = portfolio[portfolio['instrument_type_cur'] != 'FX Forward Long CLP']
        portfolio = portfolio[portfolio['instrument_type_cur'] != 'FX Forward Short CLP']
        portfolio.index = portfolio['link']
        portfolio['MCR'] = 0
        portfolio['CTR'] = 0
        portfolio['PCTR'] = 0
            
        for i in portfolio.index:
            portfolio['MCR'].loc[i] = MCR['w'].loc[i]*np.sqrt(252)*100
            portfolio['CTR'].loc[i] = CTR['w'].loc[i]*(portfolio['w'].loc[i]/portfolio.groupby(by='link')['w'].sum().loc[i])*np.sqrt(252)*100
            portfolio['PCTR'].loc[i] = PCTR['w'].loc[i]*(portfolio['w'].loc[i]/portfolio.groupby(by='link')['w'].sum().loc[i])*100

        if portfolio['PCTR'].sum() < 100:
            difference = pd.DataFrame(index = ['Other Active Positions'], columns = portfolio.columns)
            difference['CTR'].loc['Other Active Positions'] = float(CTR.sum().values*np.sqrt(252)*100 - portfolio['CTR'].sum())
            difference['PCTR'].loc['Other Active Positions'] = float(PCTR.sum().values*100 - portfolio['PCTR'].sum())
            difference['instrument_type_cur'].loc['Other Active Positions'] = 'Other Active Positions'
            difference['duration'].loc['Other Active Positions'] = 0
            difference['market_value'].loc['Other Active Positions'] = 0
            difference['ctd'].loc['Other Active Positions'] = 0
            difference['cty'].loc['Other Active Positions'] = 0
            difference['link'] = 'CLPCLP Curncy'
            portfolio = portfolio.append(difference)
        
        return portfolio

### Positions and Risk summary

    def getBasicView(self, portName, benchmarkName = 'None', date = getNDaysFromToday(1)):
        pd.options.display.float_format = '{:,.4f}'.format
        port = self.getPositionsMatrix(portName, date)
        if benchmarkName != 'None':
            b = self.getBenchmarkFromDB(date)
            benchmark = b[b['name'] == benchmarkName]
            portfolio = self.getTrackingError(port, benchmark)
        else:
            portfolio = self.getTrackingError(port)
        
        attributes = ['market_value','ctd','cty','CTR','PCTR']
        out = pd.DataFrame(portfolio.groupby(['instrument_type_cur'])[attributes[0:3]].sum()).round(2)
        aux = pd.DataFrame(portfolio.groupby(['instrument_type_cur'])[attributes[3:6]].sum()).round(2)
        out = out.join(aux)
        dat = pd.DataFrame(columns = attributes)
        z = 0        
        for y in attributes: #Esto es para transformar los Decimals en Floats
            dat[y] = [np.round(float(out.values[x][z]),4) for x in range(0,len(out))]
            z += 1
        dat.index = out.index
        mv_adj = dat[dat.index.str[:11] == 'FX Exposure']['market_value'].sum()
        out['Weight'] = [x/(dat['market_value'].sum()-mv_adj)*100 for x in dat['market_value']]
        out['Market Value (MM)'] = dat['market_value']/1000000
        out['CTD'] = dat['ctd']*(1-out['Weight']['Efectivo en CLP']/100)
        out['YTM'] = (dat['cty']*100)/out['Weight']
        for y in attributes[0:3]:
            del out[y]
        pd.options.display.float_format = '{:,.4f}'.format

        out.index.name = ''
        out.loc['Total'] = out.sum()
        out['Weight'].loc['Total']= out['Weight'].loc['Total']- mv_adj/(out['Market Value (MM)'].loc['Total']*1000000)*100
        out['Market Value (MM)'].loc['Total']= out['Market Value (MM)'].loc['Total']- mv_adj/1000000
        out['YTM']['Total'] = dat['cty'].sum()
        out['Duration'] = out['CTD']/out['Weight']*100

        print (portName)       
        
        self.set_column_sequence(out,['Weight','Market Value (MM)','CTD','YTM','Duration','CTR','PCTR'])
        
        return out.fillna(0), portfolio


    def getDurationBucketView(self, portName, benchmarkName = 'None', date = getNDaysFromToday(1)):
        pd.options.display.float_format = '{:,.4f}'.format
        port = self.getPositionsMatrix(portName, date)
        if benchmarkName != 'None':
            b = self.getBenchmarkFromDB(date)
            benchmark = b[b['name'] == benchmarkName]
            portfolio = self.getTrackingError(port, benchmark)
        else:
            portfolio = self.getTrackingError(port)
        
        portfolio['bucket'] = 'x'
        for i in range(0,len(portfolio)):
            if portfolio['duration'].between(0.0,1.0)[i]:
                portfolio['bucket'].iloc[i] = '00 - 01 Y'
            if portfolio['duration'].between(1.0,3.0)[i]:
                portfolio['bucket'].iloc[i] = '01 - 03 Y'
            if portfolio['duration'].between(3.0,5.0)[i]:
                portfolio['bucket'].iloc[i] = '03 - 05 Y'
            if portfolio['duration'].between(5.0,7.0)[i]:
                portfolio['bucket'].iloc[i] = '05 - 07 Y'
            if portfolio['duration'].between(7.0,10.0)[i]:
                portfolio['bucket'].iloc[i] = '07 - 010 Y'
            if portfolio['duration'].between(10.0,15.0)[i]:
                portfolio['bucket'].iloc[i] = '10 - 15 Y'
            if portfolio['duration'].between(15.0,20.0)[i]:
                portfolio['bucket'].iloc[i] = '15 - 20 Y'
            if portfolio['duration'].between(20.0,30.0)[i]:
                portfolio['bucket'].iloc[i] = '20 - 30 Y'
            if math.isnan(portfolio['duration'].iloc[i]):
                portfolio['bucket'].iloc[i] = 'CASH'

        portfolio.ctd = portfolio.ctd.fillna(Decimal(0))
        portfolio.cty = portfolio.cty.fillna(Decimal(0))
        attributes = ['market_value','ctd','cty','CTR','PCTR']
        out = pd.DataFrame(portfolio.groupby(['bucket'])[attributes[0:3]].sum()).round(2)
        aux = pd.DataFrame(portfolio.groupby(['bucket'])[attributes[3:6]].sum()).round(2)
        out = out.join(aux)
        dat = pd.DataFrame(columns = attributes)
        z = 0        
        for y in attributes: #Esto es para transformar los Decimals en Floats
            dat[y] = [np.round(float(out.values[x][z]),4) for x in range(0,len(out))]
            z += 1
        dat.index = out.index
        mv_adj = dat[dat.index.str[:11] == 'FX Exposure']['market_value'].sum()
        out['Weight'] = [x/(dat['market_value'].sum()-mv_adj)*100 for x in dat['market_value']]
        out['Market Value (MM)'] = dat['market_value']/1000000
        out['CTD'] = dat['ctd']*(1-out['Weight']['CASH']/100)
        out['YTM'] = (dat['cty']*100)/out['Weight']
        for y in attributes[0:3]:
            del out[y]
        pd.options.display.float_format = '{:,.4f}'.format

        out.index.name = ''
        out.loc['Total'] = out.sum()
        out['Weight'].loc['Total']= out['Weight'].loc['Total']- mv_adj/(out['Market Value (MM)'].loc['Total']*1000000)*100
        out['Market Value (MM)'].loc['Total']= out['Market Value (MM)'].loc['Total']- mv_adj/1000000
        out['YTM']['Total'] = dat['cty'].sum()
        out['Duration'] = out['CTD']/out['Weight']*100

        print (portName)
        
        self.set_column_sequence(out,['Weight','Market Value (MM)','CTD','YTM','Duration','CTR','PCTR'])
        
        return out.fillna(0), portfolio
### Upload Portfolio to Database
    def uploadPortfolioAttributesToDB(self, basicView, portName, date = dt.datetime.now()):
        #Construye la tabla que contiene la información general de los portafolios y las sube a la base de datos
        aux = pd.DataFrame(data = basicView)
        aux['PortfolioName'] = portName
        aux['Date'] = date
        aux['AssetClass'] = basicView.index
        aux.columns = ['CTR','PCTR','Weight','MarketValue','CTD','YTM','Duration','PortfolioName','Date','AssetClass']
        con = self.openConnection()
        aux.to_sql('HistoricalAttributes', con, flavor='sqlite', if_exists='append', index = False)
        return True

    def uploadPortfolioPositionsToDB(self, portfolio, portName, date = dt.datetime.now()):                         
        #Construye la tabla que contiene la información de las posiciones del portafolios y las sube a la base de datos                                             
        aux = pd.DataFrame(data = portfolio)
        aux['Date'] = date
        del aux['date']
        del aux['instrument_type']
        del aux['nominal_amount']
        del aux['instrument_code']
        del aux['pct_fund']
        del aux['price']
        del aux['yield_db']
        aux.columns = ['CTD','CTY','Currency','Duration','InstrumentName','InstrumentTypeCurrency','IssuerCode','IssuerName',
                       'MarketValue','MaturityDate','PortfolioName','Risk','Sector','Weight','Link','MCR','CTR','PCTR','Date']
        aux = aux[aux.Duration.notnull()]
        aux.CTD = [float(aux.CTD.values[i]) for i in range(0,len(aux))]
        aux.CTY = [float(aux.CTY.values[i]) for i in range(0,len(aux))]
        aux.Duration = [float(aux.Duration.values[i]) for i in range(0,len(aux))]
        aux.MarketValue = [float(aux.MarketValue.values[i]) for i in range(0,len(aux))]
        
        con = self.openConnection(path = 'L:\Rates & FX\Quant Analysis\portfolioManager\Portfolios\DB\\historicalPositions.db')
        aux.to_sql('HistoricalPositions', con, flavor='sqlite', if_exists='append', index = False)
        return True

        
### Support Functions
    def set_column_sequence(self, dataframe, seq, front=True):
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

    def getAvailablePortfolios(self):
        portfolio_list = self.matrix[self.matrix['ctd'] > 0.0]
        names = portfolio_list['name'].unique()
        return names

    def getAvailableBenchmarks(self, date = getNDaysFromToday(1)):
        benchmark_list = self.getBenchmarkFromDB(date = '2016-07-26')
        names = benchmark_list['name'].unique()
        return names

    def openConnection(self, path = 'L:\Rates & FX\Quant Analysis\portfolioManager\Portfolios\DB\\historicalPort.db'):
        #Función que abre una conexión con el default path de la clase
        con = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        con.text_factory = str
        return con
        
    def createDB(self):
        #Función que crea base de datos y tablas necesarias para trabajar con el objeto
        con=self.openConnection()
        cursor = con.cursor()
        #con=sqlite3.connect(':memory:')
        cursor.execute('DROP TABLE IF EXISTS HistoricalAttributes')
        
        cursor.execute("CREATE TABLE HistoricalAttributes \
                (CTR,\
                PCTR,\
                Weight,\
                MarketValue,\
                CTD,\
                YTM,\
                Duration,\
                PortfolioName TEXT NOT NULL,\
                Date DATE NOT NULL,\
                AssetClass TEXT NOT NULL)")
        con.close()

if __name__ == '__main__':
    port = portClas()
    matrix = port.getPortFromDB(date = '2017-02-21')
#    cash = port.getCashFromDB() # Para probar la descarga de cajas

# Creacion de vistas de portafolio con todas las posiciones
#    p = port.getPositionsMatrix('MACRO 1.5')
#    p = port.getTrackingError(p)
#    p= port.getPositionsMatrix('MACRO CLP3')
#    p = port.getPositionsMatrix('IMT E-PLUS')
#    p = port.getPositionsMatrix('RENTA')
#    p = port.getTrackingError(p)
#    portfolio = port.getTrackingError(p)
#    p = port.getPositionsMatrix('DEUDA 360')
#    p = port.getTrackingError(p)


# Creacion de vistas basicas de posicionamiento de portafolio
#    view, portfolio = port.getBasicView('MACRO 1.5')
    view, portfolio = port.getBasicView('MACRO CLP3')
#    view, portfolio = port.getBasicView('IMT E-PLUS')
#    view, portfolio = port.getBasicView('RENTA')
#    view, portfolio = port.getBasicView('SPREADCORP')
#    view, portfolio = port.getBasicView('DEUDA 360')
    
# Descarga de la base de datos del benchmark
#    benchmark = port.getBenchmarkFromDB(date = getNDaysFromToday(18))
#    b = benchmark[benchmark['name'] == 'IMT Corp Clas A+ To AAA Dur 0y9y Liquido']
#    p = port.getPositionsMatrix('SPREADCORP')
#    p = port.getTrackingError(p, 'IMT Corp Clas BBB- To A+ Liquidez 30000UF')
#    view, portfolio = port.getBasicView('DEUDA CORP','IMT Corp Clas A+ To AAA Dur 0y9y Liquido', '2016-09-02')
#    view, portfolio  = port.getBasicView('SPREADCORP', 'IMT Corp Clas BBB- To A+ Liquidez 30000UF', '2016-09-02')
#    view, portfolio  = port.getBasicView('SPREADCORP','IMT Corp Clas BBB- To A+ Liquidez 30000UF')
#    view, portfolio  = port.getDurationBucketView('DEUDA CORP','IMT Corp Clas A+ To AAA Dur 0y9y Liquido')

# Simulacion de trades
#    trade = port.generateTrade('US195325BN40','Republica de Colombia','Bono de Gobierno US$','USD',4.302,'MACRO 1.5', 200000, 108.5)
#    trade = port.generateTrade('US195325BN40','Republica de Colombia','Bono de Gobierno US$','USD',4.302,'MACRO CLP3', 900000, 108.5)
#    simPort = port.insertTradeToPortfolio(p)
#    portfolio = port.getTrackingError(p)
#    portfolio_simulated = port.getTrackingError(simPort)

# Simulacion de trades credito
#    p = port.getPositionsMatrix('MACRO CLP3')
#    trade = port.generateTrade('PEP01000C4G7','Bono Tesoreria del Peru','Bono de Gobierno PEN','PEN',9.13,'MACRO CLP3', 1000000, 105.78)
#    trade = port.generateTrade('EK929786','Bono Tesoreria en UF','Bono de Gobierno UF','UF',8.79,'DEUDA CORP', -170000, 102.6)
#    simPort = port.insertTradeToPortfolio(p)
#    portfolio = port.getTrackingError(p)
#    portfolio_simulated = port.getTrackingError(simPort)

# Subir data historica del portafolio a la base de datos
#    port.createDB()
#    port.uploadPortfolioAttributesToDB(view,'MACRO CLP3')

# Subir data historica de las posiciones de los portafolios a las bases
#    port.uploadPortfolioPositionsToDB(portfolio,'IMT E-PLUS')

# Fondos mutuos --------------------------------------------------------------- 
# Credicorp Capital Liquidez (Run 8401)
# Credicorp Capital Money Market (Run 8945)
# Credicorp Capital Deuda 360 (Run 9056) 
# Credicorp Capital Macro CLP 1.5 (Run 9310) 
# Credicorp Capital Renta Estratégica (Run 8421) 
#
# Fondos de Inversión: 
# Credicorp Capital Spread Corporativo Local (Run 7275)
# Credicorp Capital Deuda Corporativa Investment Grade (Run 9251)
# Credicorp Capital Macro CLP 3 (Run 9107) – (Ex Trading Deuda Local)
# IMT E Plus (Run 9108)
#    
# pd.options.display.float_format = '{:,.4f}'.format



                                     
                                     
                                     
                                     
# Simulacion de trades High-Yielders
#    trade = port.generateTrade('BRSTNCLTN723','Republica Federativa de Brasil','Letra Tesouro Nacional','BRL',4.302,'MACRO 1.5', 200000, 108.5)
#    trade = port.generateTrade('US195325BN40','Republica de Colombia','Bono de Gobierno US$','USD',0.841,'MACRO CLP3', 900000, 108.5)
#    simPort = port.insertTradeToPortfolio(p)
#    portfolio = port.getTrackingError(p)
#    portfolio_simulated = port.getTrackingError(simPort)



