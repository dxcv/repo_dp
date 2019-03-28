"""
Created on Thu Oct 06 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
sys.path.insert(1, '../risk_library/')
import risk as rk
import pandas as pd


def export_historical_excel(serie):
    '''
    Exporta el reporte a un pdf consolidado.
    '''
    # Abrimos el workbook con el template del informe
    wb = fs.open_workbook(path=".\\Historical.xlsx", screen_updating=True, visible=True)
    # Borramos la informacion anterior
    fs.clear_sheet_xl(wb=wb, sheet="Historical")
    fs.paste_val_xl(wb=wb, sheet="Historical", row=1, column=1, value=serie)
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)



# Cerramos posibles instancias de Excel abiertas
fs.kill_excel()

#  las fechas entre las que trabajaremos
pd.set_option("display.max_columns", 3)
pd.set_option("display.max_rows", 3)

# dia_fin = "2016-09-30"
spot_date = "2017-12-29"#fs.get_ndays_from_today(0)

# Fijamos la fecha en la que empieza el dataset
# de la matriz de varianza covarianza
data_start_date = "2017-06-01"

# Fijamos la fecha para la cual se tomara
# el vector de weights de los portafolios
fund_date = fs.get_prev_weekday(spot_date)

# Fijamos la fecha para la cual se tomara
# el vector de weights de los benchmarks
benchmark_date = fs.get_prev_weekday(fund_date)

# Fijamos la fecha para la cual se tomara
# el ultimo dato para la matriz de varianza-covarianza
data_end_date = benchmark_date

# Dias a generar por defecto ytd
days = fs.get_current_weekdays_year(fs.convert_string_to_date(fund_date))

# Obtenemos la inflacion para calcular yield de bonos reajustables
inflation = rk.get_inflation(start_date=benchmark_date, end_date=fund_date)

print("Generating investment report for: ")
print("spot date: " + spot_date)
print("data start date: " + data_start_date)
print("portfolio date: " + fund_date)
print("benchmark date: " + benchmark_date)
print("inflation: " + str(inflation))

# Obtenemos el dataset con toda la informacion historica
print("Fetching historical dataset...")
dataset = rk.get_historical_dataset(data_start_date=data_start_date,
                                    data_end_date=data_end_date)
print("Dataset: ")
# Obtenemos la lista de los fondos con su informacion basica
# y obtenemos todos los portafolios activos con sus metricas de riesgo
print("Computing ex ante volatility...")
funds = rk.get_funds()

# Obtenemos la data historica
funds_hist = funds[(funds["codigo_fdo"] == "LATAM IG")]
serie = rk.get_historical_metrics(funds=funds_hist,
                                  dataset=dataset,
                                  fund_date=fund_date,
                                  benchmark_date=benchmark_date,
                                  inflation=inflation,
                                  days=days)
# Exportamos a excel
export_historical_excel(serie)
