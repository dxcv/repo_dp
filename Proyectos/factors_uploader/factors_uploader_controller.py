"""
Created on Thu Aug 15 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd


def fetch_factors_series(start_date, end_date):
    '''
    Descarga todas las series de factores de ajuste y reparto
    desde lagunillas (SIGA 1).
    '''
    # Obtenemos los paths de las querys Y parametrizamos
    # la fecha de inicio y fin
    path_ajuste = ".\\querys_factors_uploader\\ajuste.sql"
    path_reparto = ".\\querys_factors_uploader\\reparto.sql"
    query_ajuste = fs.read_file(path_ajuste)
    query_ajuste = query_ajuste.replace("AUTODATE1", start_date)
    query_ajuste = query_ajuste.replace("AUTODATE2", end_date)
    query_reparto = fs.read_file(path_reparto)
    query_reparto = query_reparto.replace("AUTODATE1", start_date)
    query_reparto = query_reparto.replace("AUTODATE2", end_date)
    # Obtenemos las series desde la base de datos de SIGA 1
    ajuste_series = fs.get_frame_sql_user(server="Puyehue",
                                          database="MesaInversiones",
                                          username="usrConsultaComercial",
                                          password="Comercial1w",
                                          query=query_ajuste)
    reparto_series = fs.get_frame_sql_user(server="Puyehue",
                                           database="MesaInversiones",
                                           username="usrConsultaComercial",
                                           password="Comercial1w",
                                           query=query_reparto)
    # Indexamos los vectores por fecha fondo y serie
    ajuste_series.set_index(["fecha", "codigo_fdo", "codigo_ser"], inplace=True)
    reparto_series.set_index(["fecha", "codigo_fdo", "codigo_ser"], inplace=True)
    return ajuste_series, reparto_series


def compute_cumulative_series(ajuste_series, reparto_series, start_date, end_date):
    '''
    Calcula el factor de reparto y ajuste acumulado de todas la series.
    '''
    # Obtenemos todas las combinaciones existentes
    # de fondo y serie existentes en SIGA
    series = reparto_series.index.droplevel("fecha").unique()
    
    # Obtenemos una lista con todas las fechas para acumular
    days_list = fs.get_dates_between(start_date, spot_date)
    # Hacemos dos listas donde almacenamos las distintas series
    ajuste_cumulative_series = []
    reparto_cumulative_series = []
    # Por cada serie y fondo computamos sus facotres acumulados
    for serie in series:
        fund_id = serie[0]
        fund_serie = serie[1]
        # Calculamos los factores acumulados en dos dataframes distintos
        ajuste_serie = compute_cumulative_serie(ajuste_series, fund_id, fund_serie, days_list)
        reparto_serie = compute_cumulative_serie(reparto_series, fund_id, fund_serie, days_list)
        # Guardamos las distintas series
        ajuste_cumulative_series.append(ajuste_serie)
        reparto_cumulative_series.append(reparto_serie)
    # Consolidamos todo en dos dataframes
    ajuste_cumulative_series = pd.concat(ajuste_cumulative_series)
    reparto_cumulative_series = pd.concat(reparto_cumulative_series)
    return ajuste_cumulative_series, reparto_cumulative_series


def compute_cumulative_serie(factor_series, fund_id, fund_serie, days_list):
    '''
    Calcula el factor acumulado para una serie en particular.
    '''
    # Aislamos la serie que nos interesa
    factor_serie = factor_series[(factor_series.index.get_level_values("codigo_fdo") == fund_id) & (factor_series.index.get_level_values("codigo_ser") == fund_serie)] 
    # Transformamos a DateTimeIndex y botamos
    # los codigos de fondo y serie
    factor_serie.index = factor_serie.index.droplevel("codigo_fdo")
    factor_serie.index = factor_serie.index.droplevel("codigo_ser")
    factor_serie.index = pd.to_datetime(factor_serie.index)
    # Reindexamos con la lista de dias, notar que los dias en que no hay
    # dato dejamos lefactor en 1 para no alterar el valor cuota
    factor_serie = factor_serie.reindex(days_list, fill_value=1)
    # Calculamos el factor acumulado
    factor_serie = factor_serie.cumprod()
    # Rearmamos la serie con fndo y serie para que pueda ser concatenada
    factor_serie["codigo_fdo"] = fund_id
    factor_serie.set_index("codigo_fdo", append=True, inplace=True)
    factor_serie["codigo_ser"] = fund_serie
    factor_serie.set_index("codigo_ser", append=True, inplace=True)
    return factor_serie


def delete_old_data():
    '''
    Borra los factores acumulados de la base de datos.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    delete_statement = "DELETE FROM dbo.Factores WHERE 1=1"
    fs.run_sql(conn, delete_statement)
    fs.disconnect_database(conn)


def insert_new_data(ajuste_series, reparto_series):
    '''
    '''
    factor_series = pd.merge(ajuste_series,
                             reparto_series,
                             how="outer",
                             left_index=True,
                             right_index=True,
                             suffixes=("_a", "_r"))
    factor_series.reset_index(inplace=True)
    factor_series = fs.format_tuples(factor_series)
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO Factores VALUES (%s,%s,%s,%d,%d)", factor_series)
    conn.commit()


print("Starting factors uploader...")
# Obtenemos los datos iniciales
factors_start_date = "2011-01-01"
spot_date = fs.get_ndays_from_today(0)

# Descargamos las series de factores
print("Fetching factors series...")
ajuste_series, reparto_series = fetch_factors_series(factors_start_date, spot_date)

# Obtenemos el producto acumulado de los factores
print("Compounding cumulative series...")
ajuste_series, reparto_series = compute_cumulative_series(ajuste_series, reparto_series, factors_start_date, spot_date)

# Borramos los factores historicos
print("Deleting old data...")
delete_old_data()

# Subimos los nuevos factores acumulados
print("Uploading new data...")
insert_new_data(ajuste_series, reparto_series)



