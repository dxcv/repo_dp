"""
Created on Fri Dec 15 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import numpy as np
import pandas as pd

def fetch_currencies(date):
    '''
    Descarga las monedas.
    '''
    currencies_ids = ["CLP", "BRL", "COP", "MXN", "UYU", "PEN", "ARS"]
    currencies = {}
    for currency in currencies_ids:
      currencies[currency] = fetch_currency(currency, date)
    # Como el fondo se ve en dolares, usd es 1.0 por definicion
    currencies["USD"] = 1.0
    return currencies


def fetch_currency(currency, date):
    '''
    Descarga la cartera de un portfolio.
    '''
    query = "select valor from {} where fecha = '{}'"
    query = query.format(currency, date)
    price = fs.get_val_sql_user(server="Puyehue",
                                database="MesaInversiones",
                                username="usrConsultaComercial",
                                password="Comercial1w",
                                query=query)
    return price



def fetch_portfolio(portfolio_type, date, crncy_mapping):
    '''
    Descarga la cartera de un portfolio.
    '''
    query = "select * from {} where fecha = '{}'"    
    if portfolio_type == "fund":
      query = query.format("zhis_lcd_portfolio", date)
    elif portfolio_type == "benchmark":
      query = query.format("zhis_gbi_portfolio", date)
    elif portfolio_type == "fx_forward":
      query = "select * from zhis_lcd_portfolio_fx_fwd where fecha_op <= '{0}' and fecha_vcto >= '{0}'".format(date) 
    portfolio = fs.get_frame_sql_user(server="Puyehue",
                                      database="MesaInversiones",
                                      username="usrConsultaComercial",
                                      password="Comercial1w",
                                      query=query)
    if portfolio_type != "fx_forward":
      portfolio.set_index(["codigo_ins"], inplace=True)
    else:
      portfolio["moneda_compra"] = portfolio["moneda_compra"].replace(crncy_mapping)
      portfolio["moneda_venta"] = portfolio["moneda_venta"].replace(crncy_mapping)
      portfolio["days_to_maturity"] = (pd.to_datetime(portfolio["fecha_vcto"] ) - fs.convert_string_to_date(date)).astype('timedelta64[D]')

    return portfolio


def merge_derivatives(fund_portfolio, fx_fwd_portfolio, fund_date, crncy_mapping, currencies, fx_index_mapping):
    '''
    Consolida los derivados e instrumentos directos en un portfolio.
    '''    

    # Crearemos dos portafolios uno de posicion larga y otro corta
    portfolio_long = fx_fwd_portfolio
    portfolio_short = fx_fwd_portfolio
    portfolio_long = portfolio_long.reset_index()
    portfolio_short = portfolio_short.reset_index()
    
    portfolio_long["fecha"] = fund_date
    portfolio_short["fecha"] = fund_date

    portfolio_long["moneda"] = portfolio_long["moneda_compra"]
    portfolio_short["moneda"] = portfolio_short["moneda_venta"]

    portfolio_long["nombre_instrumento"] = "Forward Long " + portfolio_long["moneda"]
    portfolio_short["nombre_instrumento"] = "Forward Short " + portfolio_short["moneda"]

    portfolio_long["pais_emisor"] = portfolio_long["moneda"]
    portfolio_long["pais_emisor"] = portfolio_long["pais_emisor"].replace(country_mapping)
    portfolio_short["pais_emisor"] = portfolio_short["moneda"]
    portfolio_short["pais_emisor"] = portfolio_short["pais_emisor"].replace(country_mapping)

    portfolio_long["maturity_date"] = portfolio_long["fecha_vcto"]
    portfolio_short["maturity_date"] = portfolio_short["fecha_vcto"]

    portfolio_long["tipo_instrumento"] = "FX Forward"
    portfolio_short["tipo_instrumento"] = "FX Forward"

    portfolio_long["rating_nacional"] = "AAA"
    portfolio_short["rating_nacional"] = "AAA"
    portfolio_long["rating_internacional"] = "A+"
    portfolio_short["rating_internacional"] = "A+"

    portfolio_long["duration"] = 0.0
    portfolio_short["duration"] = 0.0

    portfolio_long["nombre_instrumento"] = "Forward " + portfolio_long["moneda"]
    portfolio_short["nombre_instrumento"] = "Forward" + portfolio_short["moneda"]

    portfolio_long["corte_minimo"] = 0.0
    portfolio_short["corte_minimo"] = 0.0


    # Ahora veremos los nominales y montos para los forwards
    portfolio_long["nominal"] = None
    portfolio_long["monto"] = None
    portfolio_long["rate_index_id"] = None
    portfolio_long["fx_index_id"] = None
    crncy_mapping_invert = fs.dictinvert(crncy_mapping)
    for i, instrument in portfolio_long.iterrows():
      currency = instrument["moneda"]
      nominal = instrument["nominal_compra"]
      fx = currencies[crncy_mapping_invert[currency]]
      amount = nominal / fx
      rate_index_id = 0
      fx_index_id = fx_index_mapping[currency]

      portfolio_long.loc[i, "nominal"] = nominal
      portfolio_long.loc[i, "monto"] = amount
      portfolio_long.loc[i, "rate_index_id"] = rate_index_id
      portfolio_long.loc[i, "fx_index_id"] = fx_index_id

    portfolio_short["nominal"] = None
    portfolio_short["monto"] = None
    portfolio_short["rate_index_id"] = None
    portfolio_short["fx_index_id"] = None
    crncy_mapping_invert = fs.dictinvert(crncy_mapping)
    for i, instrument in portfolio_short.iterrows():
      currency = instrument["moneda"]
      nominal = instrument["nominal_venta"]
      fx = currencies[crncy_mapping_invert[currency]]
      amount = nominal / fx
      rate_index_id = 0
      fx_index_id = fx_index_mapping[currency]
      portfolio_short.loc[i, "nominal"] = nominal
      portfolio_short.loc[i, "monto"] = amount
      portfolio_short.loc[i, "rate_index_id"] = rate_index_id
      portfolio_short.loc[i, "fx_index_id"] = fx_index_id

    portfolio_long.set_index(["codigo_ins"], inplace=True)
    portfolio_short.set_index(["codigo_ins"], inplace=True)
    
    portfolio_long = portfolio_long[fund_portfolio.columns]
    portfolio_short = portfolio_short[fund_portfolio.columns]

    fund_portfolio = pd.concat([fund_portfolio, portfolio_long, portfolio_short], axis=0)


    fund_portfolio["weight"] = fund_portfolio["monto"] / fund_portfolio["monto"].sum()


    return fund_portfolio

def compute_active_portfolio(fund_portfolio, benchmark_portfolio):
    '''
    Construye el portafolio activo del fondo contra el benchmark.
    '''
    # Hacemos el outer-join entre los portafolios
    active_portfolio = pd.merge(fund_portfolio, benchmark_portfolio, how="outer", left_index=True, right_index=True, suffixes=("_f", "_b"))
    
    # Vemos las columnas de ditintos tipos para rellenar nulos
    active_portfolio["weight_f"] = active_portfolio["weight_f"].fillna(0.0)
    active_portfolio["weight_b"] = active_portfolio["weight_b"].fillna(0.0)

    # Calculamos el active weight
    active_portfolio["weight_a"]  = active_portfolio["weight_f"] -  active_portfolio["weight_b"]


    # Borramos columnas duplicadas por portfolio
    print(active_portfolio.columns)
    drop_columns = ["fecha_f", "fecha_b", "codigo_emi_f", "codigo_emi_b",
                    "nombre_instrumento_f", "nombre_instrumento_b", "pais_emisor_f",
                    "pais_emisor_b", "moneda_f", "moneda_b", "tipo_instrumento_f",
                    "tipo_instrumento_b", "rating_nacional_f", "rating_nacional_b",
                    "rating_internacional_f", "rating_internacional_b", "maturity_date_f",
                    "maturity_date_b", "days_to_maturity_f", "days_to_maturity_b",
                    "nombre_emisor_f", "nombre_emisor_b", "corte_minimo_f", "corte_minimo_b",
                    "estrategia_f", "estrategia_b"]
    active_portfolio["fecha"] = None
    active_portfolio["codigo_emi"] = None
    active_portfolio["nombre_instrumento"] = None
    active_portfolio["pais_emisor"] = None
    active_portfolio["moneda"] = None
    active_portfolio["tipo_instrumento"] = None
    active_portfolio["rating_nacional"] = None
    active_portfolio["rating_internacional"] = None
    active_portfolio["maturity_date"] = None
    active_portfolio["days_to_maturity"] = None
    active_portfolio["nombre_emisor"] = None
    active_portfolio["corte_minimo"] = None
    active_portfolio["estrategia"] = None
    
    for codigo_ins, instrument in active_portfolio.iterrows():
      
      # identificamos un papel que no esta en la interseccion por la fecha
      if pd.isnull(instrument["fecha_f"]):
        fecha = pd.Timestamp(instrument["fecha_b"])
        codigo_emi = instrument["codigo_emi_b"]
        nombre_instrumento = instrument["nombre_instrumento_b"]
        pais_emisor = instrument["pais_emisor_b"]
        moneda = instrument["moneda_b"]
        tipo_instrumento = instrument["tipo_instrumento_b"]
        rating_nacional = instrument["rating_nacional_b"]
        rating_internacional = instrument["rating_internacional_b"]
        maturity_date = pd.Timestamp(instrument["maturity_date_b"])
        days_to_maturity = instrument["days_to_maturity_b"]
        nombre_emisor = instrument["nombre_emisor_b"]
        corte_minimo = instrument["corte_minimo_b"]
        estrategia = instrument["estrategia_b"]
      else:
        fecha = pd.Timestamp(instrument["fecha_f"])
        codigo_emi = instrument["codigo_emi_f"]
        nombre_instrumento = instrument["nombre_instrumento_f"]
        pais_emisor = instrument["pais_emisor_f"]
        moneda = instrument["moneda_f"]
        tipo_instrumento = instrument["tipo_instrumento_f"]
        rating_nacional = instrument["rating_nacional_f"]
        rating_internacional = instrument["rating_internacional_f"]
        maturity_date = pd.Timestamp(instrument["maturity_date_f"])
        days_to_maturity = instrument["days_to_maturity_f"]
        nombre_emisor = instrument["nombre_emisor_f"]
        corte_minimo = instrument["corte_minimo_f"]
        estrategia = instrument["estrategia_f"]


      active_portfolio.loc[codigo_ins, "fecha"] = fecha
      active_portfolio.loc[codigo_ins, "codigo_emi"] = codigo_emi
      active_portfolio.loc[codigo_ins, "nombre_instrumento"] = nombre_instrumento
      active_portfolio.loc[codigo_ins, "pais_emisor"] = pais_emisor
      active_portfolio.loc[codigo_ins, "moneda"] = moneda
      active_portfolio.loc[codigo_ins, "tipo_instrumento"] = tipo_instrumento
      active_portfolio.loc[codigo_ins, "rating_nacional"] = rating_nacional
      active_portfolio.loc[codigo_ins, "rating_internacional"] = rating_internacional
      active_portfolio.loc[codigo_ins, "maturity_date"] = maturity_date
      active_portfolio.loc[codigo_ins, "days_to_maturity"] = days_to_maturity
      active_portfolio.loc[codigo_ins, "nombre_emisor"] = nombre_emisor
      active_portfolio.loc[codigo_ins, "corte_minimo"] = corte_minimo
      active_portfolio.loc[codigo_ins, "estrategia"] = estrategia
    
    # print(active_portfolio)
    

    return active_portfolio


crncy_mapping = {"CLP": "$",
                 "BRL": "BRL",
                 "COP": "COP",
                 "MXN": "MX",
                 "UYU": "UYU",
                 "PEN": "PEN",
                 "ARS": "ARS",
                 "USD": "US$"}

country_mapping = {"$": "CL",
                   "BRL": "BR",
                   "COP": "CO",
                   "MX": "MX",
                   "UYU": "UY",
                   "PEN": "PE",
                   "ARS": "AR",
                   "US$": "US"}

fx_index_mapping = {"$": 166,
                    "BRL": 594,
                    "COP":  596,
                    "MX": 598,
                    "UYU": 597,
                    "PEN": 595,
                    "ARS": 593,
                    "US$": 0}

if __name__ == "__main__":
    # Obtenemos las fechas de los portfolios
    spot_date = fs.get_ndays_from_today(0)
    fund_date = fs.get_prev_weekday(spot_date)
    benchmark_date = fs.get_prev_weekday(fund_date)

    # Obtenemos las monedas
    currencies = fetch_currencies(spot_date)

    # Descargamos el portfolio del fondo
    fund_portfolio = fetch_portfolio("fund", fund_date, crncy_mapping)

    # Decargamos el protfolio del benchmark
    benchmark_portfolio = fetch_portfolio("benchmark", benchmark_date, crncy_mapping)

    # Descargamos los forwards de moneda del fondo
    fx_fwd_portfolio = fetch_portfolio("fx_forward", spot_date, crncy_mapping)

    # Le concatenamos los forwards al portfolio del fondo
    fund_portfolio = merge_derivatives(fund_portfolio, fx_fwd_portfolio, fund_date, crncy_mapping, currencies, fx_index_mapping)

    # Construimos el portafolio activo
    active_portfolio = compute_active_portfolio(fund_portfolio, benchmark_portfolio)

