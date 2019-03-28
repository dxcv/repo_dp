"""
Created on Tue Mar 13 11:00:00 2018

@author: Fernando Suarez
"""
import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

def fetch_icp_serie(benchmark_start_date, end_date, alpha_target, terminal_date, fund_start_date, expected_rate):
    '''
     Baja la serie del ICP y le compone su target de alpha.
     '''
    expected_rate_daily = expected_rate / 360
    query = "select fecha, valor  from indices_dinamica where fecha >= '{}' and fecha <= '{}' and index_id = 4 order by fecha asc"
    query = query.format(benchmark_start_date, end_date)
    serie = fs.get_frame_sql_user(server="Puyehue",
                                  database="MesaInversiones",
                                  username="usrConsultaComercial",
                                  password="Comercial1w",
                                  query=query)
    serie.set_index(["fecha"], inplace=True)
    serie = serie["valor"]
    serie.name = "benchmark"
    dates = pd.date_range(benchmark_start_date, serie.index[-1])
    serie = serie.reindex(dates)
    serie = serie.fillna(method="bfill")
    serie = serie[serie.index >= fund_start_date]

    serie = serie.pct_change()
    serie.loc[serie.index[0]] = 0

    dates = pd.date_range(serie.index[0], terminal_date)
    serie = serie.reindex(dates)
    serie = serie.fillna(expected_rate_daily)

    serie = serie + 1
    serie = serie.cumprod()
    serie = serie * 100
    aux = np.arange(len(serie.index))
    aux = (aux*alpha_target/100) / 365
    aux = pd.Series(aux, index=serie.index)
    serie += aux

    return serie


def fetch_fund_serie(start_date, end_date, fund_id, fund_serie, tac, terminal_date, bill_rate):
    '''
     Baja la serie del valor cuota con comision de un fondo.
     '''
    query = "select fecha, valor_cuota  from zhis_series_main where fecha >= '{}' and fecha <= '{}' and codigo_fdo = '{}' and codigo_ser = '{}'"
    query = query.format(start_date, end_date, fund_id, fund_serie)
    serie = fs.get_frame_sql_user(server="Puyehue",
                                  database="MesaInversiones",
                                  username="usrConsultaComercial",
                                  password="Comercial1w",
                                  query=query)
    serie.set_index(["fecha"], inplace=True)
    serie = serie["valor_cuota"]
    serie.name = fund_id
    serie = serie.pct_change()
    tac_daily = tac / 365
    serie += tac_daily
    serie.loc[serie.index[0]] = 0
    serie = serie + 1
    serie = serie.cumprod()
    serie = serie * 100
    serie = compute_forecast_return(serie, terminal_date, bill_rate)

    return serie


def compute_forecast_return(serie, terminal_date, bill_rate):
     '''
     Proyecta el retorno total del fondo en base a estar fully invested en un deposito mas TAC.
     '''
     serie = serie.pct_change()
     dates = pd.date_range(serie.index[0], terminal_date)
     unknown_dates = pd.date_range(serie.index[-1], terminal_date)
     accruing_period = len(unknown_dates)
     bill_rate_daily = (((bill_rate*accruing_period/30) + 1)**(1/accruing_period)) - 1
     serie = serie.reindex(dates)
     serie = serie.fillna(bill_rate_daily)
     serie.loc[serie.index[0]] = 0.0
     serie = serie + 1
     serie = serie.cumprod()
     serie = serie * 100


     return serie
     


if __name__ == "__main__":
    
    tac_macro_15 = 0.0085
    tac_macro_30 = 0.0133
    bill_rate = 0.0026
    expected_rate = 0.025
    spot_date = fs.get_ndays_from_today(0)
    fund_date = fs.get_prev_weekday(spot_date)
    fund_start_date = "2017-12-31"
    benchmark_start_date = "2017-12-29"
    terminal_date = "2018-12-31"
    
    serie_macro_15 = fetch_fund_serie(fund_start_date, fund_date, "MACRO 1.5", "I", tac_macro_15, terminal_date, bill_rate)
    serie_macro_30 = fetch_fund_serie(fund_start_date, fund_date, "MACRO CLP3", "I", tac_macro_30, terminal_date, bill_rate)

    #fs.plot_series([serie_macro_15, serie_macro_30], title="Macro Performance", animated=False)

    benchmark_macro_15 = fetch_icp_serie(benchmark_start_date, fund_date, 150, terminal_date, fund_start_date, expected_rate)
    benchmark_macro_30 = fetch_icp_serie(benchmark_start_date, fund_date, 300, terminal_date, fund_start_date, expected_rate)

    fs.plot_series([serie_macro_15, benchmark_macro_15], title="Macro Performance", animated=False)