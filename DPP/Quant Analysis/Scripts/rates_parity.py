# -*- coding: utf-8 -*-
"""
Created on Mon May 16 16:31:04 2016

"""

import sys
sys.path.insert(0,"""L:\Rates & FX\Quant Analysis\portfolioManager""")
sys.path.insert(0,"""C:\Python27\Lib\site-packages""")

from securities import security
from yieldCurve import nelsonSiegel, lineal_curve
import pandas as pd
import datetime as dt
from tia.bbg import v3api
import itertools

import seaborn as sns
#import pygal
#from bokeh.plotting import figure, output_file, show
#import ggplot

def get_forward_return(currencies, days_to_maturity):
    
    sec = security()
    maturity_date = sec._date + dt.timedelta(days = days_to_maturity)
    forward_curve = sec.getFXInformation(currencies)
    forward_curve.loc[:,'MATURITY'] = maturity_date
    
    forward = sec.priceForwardRate(forward_curve)
    forward['TOTAL_RETURN_LONG'] = (forward['PRICE_ASK'] - 100)/100
    forward['TOTAL_RETURN_SHORT'] = (100 - forward['PRICE_BID'])/100
    
    return forward


def get_swap_curves(currencies):
    
#    bbg_tickers = ['YCSW0045 Index','YCSW0023 Index','YCSW0013 Index','YCSW0001 Index','YCSW0234 Index', 'YCSW0015 Index', 'YCSW0004 Index', 'YCSW0020 Index']
#    bbg_currencies = ['EUR', 'USD', 'JPY', 'AUD','CHF','NZD','CAD', 'SEK']
#    bbg_tickers = ['YCSW0193 Index','YCSW0329 Index','YCMM0119 Index','YCSW0083 Index','YCSW0023 Index', 'YCSW0013 Index', 'YCSW0045 Index', 'YCSW0001 Index']
#    bbg_currencies = ['CLP','COP','BRL','MXN','USD','JPY','EUR','AUD']
    bbg_tickers = ['YCSW0193 Index','YCSW0023 Index']
    bbg_currencies = ['CLP','USD']
    BBG_queries_total = pd.Series(bbg_tickers, index = bbg_currencies)
    
    BBG_queries = BBG_queries_total[currencies]
    
    LocalTerminal = v3api.Terminal('localhost', 8194)   
    try:
        response = LocalTerminal.get_reference_data(BBG_queries.values, ['curve_tenor_rates','crncy'], ignore_security_error = 1, ignore_field_error = 1)
    except:
        print("Unexpected error:", sys.exc_info()[0])   
        return False
#            print response.as_map()
#                    print response.as_frame()
    data_retrieved = response.as_frame()
    newData = data_retrieved['curve_tenor_rates'].apply(lambda x: x.apply(generate_tenor, axis = 1))
    newData = pd.concat([newData, data_retrieved['crncy']], axis = 1)
    
    newData[['LINEAL_BID','LINEAL_ASK','LINEAL_MID']] = newData['curve_tenor_rates'].apply(generate_lineal_yc)
    
    return newData


def generate_tenor(row):
    tenor_code = row['Tenor']
    base_str = tenor_code[-1]
    base = None
    if base_str == 'D':
        base = 365
    if base_str == 'W':
        base = 52
    elif base_str == 'M':
        base = 12
    elif base_str == 'Y':
        base = 1
    
    if base is None:
        pass
    new_row = row
    new_row['Tenor_in_Years'] = float(tenor_code[:-1])/base
    return new_row


def get_yields(curves, days_to_maturity):
    
    return curves.set_index('crncy')[['LINEAL_BID', 'LINEAL_ASK', 'LINEAL_MID']].applymap(lambda x: x.interpolate([days_to_maturity]).values[0])


def generate_lineal_yc(curve_in):
    curve = curve_in.set_index('Tenor_in_Years')
    curve_ask = curve['Ask Yield']
    curve_bid = curve['Bid Yield']
    curve_mid = curve['Mid Yield']
    lineal_yc_ask = lineal_curve(curve_ask)
    lineal_yc_bid = lineal_curve(curve_bid)
    lineal_yc_mid = lineal_curve(curve_mid)
    
    return pd.Series([lineal_yc_ask, lineal_yc_bid, lineal_yc_mid], index = ['BID', 'ASK', 'MID'])    


def generate_excess_return(forwards, yields, currency_short, currency_long, dtm):
    
    yield_pick_up = yields['LINEAL_ASK'][currency_long] - yields['LINEAL_BID'][currency_short]
    forward_return = forward['TOTAL_RETURN_LONG'][currency_long] + forward['TOTAL_RETURN_SHORT'][currency_short]
    return forward_return + yield_pick_up/100*dtm/365
    
    
    

#currencies = ['EUR', 'USD', 'JPY', 'AUD','CHF','NZD','CAD', 'SEK']
currencies = ['CLP','COP','BRL','MXN','USD','JPY','EUR','AUD']
days_to_maturity = [2., 10., 15., 30., 45. ,60., 90.]

curves = get_swap_curves(currencies)

rate_parity_returns = pd.DataFrame(columns = ['CURRENCY_SHORT', 'CURRENCY_LONG', 'DAYS', 'RETURNS'])
yields_mid = pd.DataFrame()

for dtm in days_to_maturity:
    forward = get_forward_return(currencies, dtm).set_index('CURRENCY')
    yields = get_yields(curves, dtm/365)
    yields_mid = pd.concat([yields_mid, pd.DataFrame([yields['LINEAL_MID'].values], columns = yields.index, index = [dtm])])
    currency_combinations = itertools.product(currencies,currencies)
    for currency_short, currency_long in currency_combinations:
        returns = generate_excess_return(forward, yields, currency_short, currency_long, dtm)
        rate_parity_returns = rate_parity_returns.append(pd.DataFrame([(currency_short, currency_long, dtm, returns*10000)], columns = rate_parity_returns.columns))


rate_parity_returns['RETURNS_ANNUALIZED'] = rate_parity_returns['RETURNS']/rate_parity_returns['DAYS']*365
rate_parity_returns.sort_values(by = 'RETURNS_ANNUALIZED', ascending=False).to_csv('risk_parity_total_return.csv')
yields_mid.to_csv('yield_curve_mid.csv')
#sns.swarmplot(x="CURRENCY_SHORT", y="RETURNS", hue="CURRENCY_LONG", data = rate_parity_returns[rate_parity_returns['CURRENCY_LONG'].isin(['USD', 'EUR', 'JPY', 'CHF','AUD', 'SEK'])])
#sns.swarmplot(x="CURRENCY_SHORT", y="RETURNS", hue="CURRENCY_LONG", data = rate_parity_returns[rate_parity_returns['CURRENCY_LONG'].isin(['USD', 'EUR', 'JPY', 'AUD','CLP', 'MXN'])])
#sns.swarmplot(x="CURRENCY_SHORT", y="RETURNS", hue="CURRENCY_LONG", data = rate_parity_returns[rate_parity_returns['CURRENCY_LONG'].isin(['CLP','COP','BRL','MXN','USD','JPY','EUR','AUD'])])

#display_charts(rate_parity_returns, title="RETURNS")

