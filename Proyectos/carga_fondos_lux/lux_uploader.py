"""
Created on Thu Jun 12 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
from tia.bbg import v3api
import pandas as pd


def fetch_bloomberg_series(tickers, start_date, end_date):
    '''
    Dada una lista de tickers, flds, una fecha de inicio, otra de fin y una moneda, descarga todos los indices de la lista entre ambas fechas en esa moneda con todos sus flds.
    '''
    LocalTerminal = v3api.Terminal('localhost', 8194)       
    response = LocalTerminal.get_historical(tickers,
                                            flds="PX_LAST",
                                            currency="USD",
                                            ignore_security_error=1,
                                            ignore_field_error=1,
                                            start=start_date,
                                            end=end_date,
                                            max_data_points=10000000,
                                            non_trading_day_fill_method="PREVIOUS_VALUE",
                                            non_trading_day_fill_option="ALL_CALENDAR_DAYS")
    # Ojo esto es para los indices que tienen menos historia de la que se pide, por convencion los mantenemos flat.
    bloombergData = response.as_frame().fillna(method = "bfill")
    # Esto es para filtrar los fines de semana, por convencion solo trabajaremos con weekdays.
    bloombergData = bloombergData[bloombergData.index.dayofweek < 5]
    return bloombergData


def process_tuples(lux_series):
    '''
    Procesa los datos que entrega la api para que queden en el formato a subir a la bdd.
    '''
    lux_tuples = pd.DataFrame(columns=["Fecha", "Ticker", "Valor_Cuota"])
    for ticker in tickers:
        serie = lux_series[ticker]
        serie["Ticker"] = ticker
        serie.reset_index(inplace=True)
        serie.rename(columns={"PX_LAST": "Valor_Cuota", "date": "Fecha"}, inplace=True)
        serie = serie[["Fecha", "Ticker", "Valor_Cuota"]]
        lux_tuples = pd.concat([lux_tuples, serie])
    lux_tuples = fs.format_tuples(lux_tuples)
    return lux_tuples


def fetch_tickers():
    '''
    Obtiene de la base de datos los tickers.
    '''
    query="SELECT ticker FROM FondosLux WHERE active = 1"
    tickers = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query)
    tickers = tickers["ticker"]
    return tickers

    return series


def delete_old_data(start_date):
    '''
    Borra los indices de los ultimos 10 dias en la base de datos.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    query = "DELETE FROM zhis_series_lux where fecha >= '" + start_date + "'"
    fs.run_sql(conn, query)
    fs.disconnect_database(conn)


def upload_tuples(lux_tuples):
    '''
    Sube las tuplas a la base de datos.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_Series_Lux VALUES (%s,%d,%d)", lux_tuples)
    conn.commit()
    fs.disconnect_database(conn)


# Fijamos las fechas en que trabajaremos en formato bloomberg
start_date = fs.get_ndays_from_today(21)
end_date = fs.get_ndays_from_today(1)
start_date_formatted = fs.convert_date_all_together(fs.convert_string_to_date(start_date))
end_date_formatted = fs.convert_date_all_together(fs.convert_string_to_date(end_date))

# Descargamos los tickers de los fondos lux
print("fetching tickers...")
tickers = fetch_tickers()

# Descargamos las series de bloomberg
print("fetching indexes...")
lux_series = fetch_bloomberg_series(tickers, start_date, end_date)

# Pasamos datos a tuplas
print("procesing tuples...")
lux_tuples = process_tuples(lux_series)

# Se borran los datos antiguos de la base de datos
print("deleting tuples...")
delete_old_data(start_date)

# Subimos las nuevas tuplas
print("uploading tuples...")
upload_tuples(lux_tuples)

