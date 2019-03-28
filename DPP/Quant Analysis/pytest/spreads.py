# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 10:41:07 2017

@author: ngoldbergerr
"""

import pandas as pd
import numpy as np
from  matplotlib import pyplot
import blpapiwrapper as blpapi
import seaborn as sns

instruments_data = pd.read_excel('L:\\Rates & FX\\Quant Analysis\\pytest\\instruments.xlsx')
instruments = instruments_data['CUSIP'].dropna()
curvaPesos = pd.DataFrame(instruments_data['Gob CERO Pesos'])
curvaPesos.index = instruments_data['Plazo']
curvaUF = pd.DataFrame(instruments_data['Gob CERO UF'])
curvaUF.index = instruments_data['Plazo']

bbgData = blpapi.BLPTS(instruments,['MTY_YEARS','DUR_BID','BID_YIELD','TRADE_CRNCY','RTG_FITCH_NATIONAL_LT','NAME'])
bbgData.get()
table = bbgData.output
bbgData.closeSession()
table =pd.DataFrame(data = [table['NAME'],pd.to_numeric(table['MTY_YEARS']), pd.to_numeric(table['DUR_BID']), 
                            pd.to_numeric(table['BID_YIELD']), table['TRADE_CRNCY'], table['RTG_FITCH_NATIONAL_LT']]).transpose()
gov_yield = []
i = 0
for maturity in table['MTY_YEARS']:
    if table['TRADE_CRNCY'][i] == 'CLP':
        gov_yield.append(np.interp(maturity, curvaPesos.index, curvaPesos['Gob CERO Pesos']))
    elif table['TRADE_CRNCY'][i] == 'CLF':
        gov_yield.append(np.interp(maturity, curvaUF.index, curvaUF['Gob CERO UF']))
    i += 1

table['Govt Equivalent'] = gov_yield
table['Spread'] = table['BID_YIELD'] - table['Govt Equivalent']

# Filtros: Yields fuera de mercado
table = table[table['BID_YIELD'] < 20]

# Diccionario de ratings
ratingDict = {'AA(cl)': 'AA', 'AAA(cl)': 'AAA', 'AA-(cl)': 'AA-', 
              'A+(cl)': 'A+', 'AA+(cl)': 'AA+', 'AA-(cl) *+': 'AA-', 
              'A(cl)': 'A', 'WD': 'WD', 'NR':'NR'}

# Filtro para armar base de datos limpia
spreadPesos = table['Spread'][(table['TRADE_CRNCY']=='CLP') & (table['Spread'] < 2)]
spreadUF = table['Spread'][(table['TRADE_CRNCY']=='CLF') & (table['Spread'] < 2)]
madurezPesos = table['MTY_YEARS'][(table['TRADE_CRNCY']=='CLP') & (table['Spread'] < 2)]
madurezUF = table['MTY_YEARS'][(table['TRADE_CRNCY']=='CLF') & (table['Spread'] < 2)]
ratingUF = table['RTG_FITCH_NATIONAL_LT'][(table['TRADE_CRNCY']=='CLF') & (table['Spread'] < 2)]
ratingUF = [ratingDict[ratingUF[x]] for x in range(0,len(ratingUF))]
dfUF = pd.DataFrame(data = [madurezUF, spreadUF, ratingUF]).transpose()

fg = sns.FacetGrid(data = dfUF, hue='RTG_FITCH_NATIONAL_LT', size=5, aspect=2)
fg.map(pyplot.scatter,'MTY_YEARS','Spread').add_legend()

