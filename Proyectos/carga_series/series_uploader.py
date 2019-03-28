"""
Created on Thu Jul 14 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs


def get_series(start_date, end_date):
    '''
    Retorna el vector de ajuste acumulado dado un fondo y serie.
    '''
    print("Descargando datos de Lagunillas")
    query_fondos_series = fs.read_file(".\\querys_series_uploader\\series.sql")
    query_fondos_series = query_fondos_series.replace("AUTODATE1", start_date)
    query_fondos_series = query_fondos_series.replace("AUTODATE2", end_date)
    series_fondos_mutuos = fs.get_frame_sql_user(server="Lagunillas",
                                                 database="PFMIMT1",
                                                 username="usuario1",
                                                 password="usuario1",
                                                 query=query_fondos_series)
    series_fondos_inversion = fs.get_frame_sql_user(server="Lagunillas",
                                                    database="PFMIMT2",
                                                    username="usuario1",
                                                    password="usuario1",
                                                    query=query_fondos_series)
    series_carteras_administradas = fs.get_frame_sql_user(server="Lagunillas",
                                                          database="PFMIMT3",
                                                          username="usuario1",
                                                          password="usuario1",
                                                          query=query_fondos_series)
    series_fondos_mutuos = fs.format_tuples(series_fondos_mutuos)
    series_fondos_inversion = fs.format_tuples(series_fondos_inversion)
    series_carteras_administradas = fs.format_tuples(series_carteras_administradas)
    tuple_list = series_fondos_mutuos + series_fondos_inversion + series_carteras_administradas
    return tuple_list



def upload_data(tuple_list):
    '''
    Inserta las tuplas con todos los factores acumulados a la base de datos.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_Series_Main VALUES (%s,%s,%s,%d,%d)", tuple_list)
    conn.commit()


def delete_old_data(dia_inic):
    '''
    Borra los factores acumulados de la base de datos.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    statement = fs.read_file(".\\querys_series_uploader\\delete_series.sql")
    statement = statement.replace("AUTODATE", dia_inic)
    fs.run_sql(conn, statement)
    fs.disconnect_database(conn)


# Obtenemos los datos iniciales
spot_date = fs.get_ndays_from_today(0)
end_date = fs.get_ndays_from_date(1, spot_date)
start_date = fs.get_ndays_from_date(15, spot_date)

# Descargamos todas las tuplas de lagunillas
print("Fetching navs and total assets...")
tuple_list = get_series(start_date, end_date)

# Borramos los factores historicos
print("Deleting old data...")
delete_old_data(start_date)

# Insertamos los factores a la fecha
print("Uploading new data...")
upload_data(tuple_list)