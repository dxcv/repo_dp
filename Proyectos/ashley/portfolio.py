"""
Created on Mon Oct 02 11:00:00 2017

@author: Ashley Mac Gregor
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np


def get_benchmark_last_date():
    '''
    Retorna la fecha más reciente del portafolio del benchmark del renta
    '''
    path = ".\\Portfolio Dash Board\\benchmark_last_date.sql"
    query = fs.read_file(path=path)
    bmk_last_date = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    date_string = bmk_last_date.strftime('%Y-%m-%d')
    return date_string

def get_benchmark(path, fec):
    '''
    Lee el query del portafolio de competidores, y lo transforma en dataframe
    '''

    portfolio_query = fs.read_file(path=path)
    portfolio_query = portfolio_query.replace("autodate", fec)
    full_portfolio = fs.get_frame_sql_user(server="Puyehue",
                                           database="MesaInversiones",
                                           username="usrConsultaComercial",
                                           password="Comercial1w",
                                           query=portfolio_query)
    return full_portfolio



def weight_benchmark_total(full_portfolio):
    '''
    Agregamos al dataframe una columna Weight, que muestra el peso del instrumento en el portafolio total (compuesto por todos los instrumentos 
    de todos los competidores)
    '''
    full_portfolio["valoriz_cierre"] = full_portfolio["valoriz_cierre"].astype(float)
    full_portfolio["Valoriz_Total_Portfolio"] = full_portfolio.groupby("fecha")["valoriz_cierre"].transform(sum)
    full_portfolio["weight"] = full_portfolio["valoriz_cierre"]/full_portfolio["Valoriz_Total_Portfolio"]
    del full_portfolio["Valoriz_Total_Portfolio"]
    return full_portfolio


# Definimos variables de input

portfolio_query_path = ".\\Portfolio Dash Board\\portfolios.sql"
bmk_last_date = get_benchmark_last_date()
full_portfolio = get_benchmark(portfolio_query_path,bmk_last_date)
weight_benchmark_total(full_portfolio)
print(weight_benchmark_total(full_portfolio).groupby("fecha")["weight"].sum())
#print(recent_date = weight_benchmark_total(full_portfolio)['Fecha'].max())

print(full_portfolio)