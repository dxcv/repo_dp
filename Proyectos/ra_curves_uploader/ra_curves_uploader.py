"""
Created on Fri Sep 08 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np
# Para desabilitar warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=FutureWarning)
pd.options.mode.chained_assignment = None 


def get_tuples(end_date, days):
    '''
    Descarga las tuplas de las curvas.
    '''
    tuples = []
    date = end_date
    for i in range(days):
            try:
                tuples += get_daily_tuples_ftp(date)
            except:
                pass
            date = fs.get_prev_weekday(date)
    return tuples

def get_daily_tuples_ftp(date):
    '''
    Descarga el excel con las cuatro curvas para un dia en especifico.
    '''
    # Primero definimos la informacion necesaria para conectarnos al servidor ftp
    year, month, day = date.split("-") 
    server = "sftp.riskamerica.com"
    user = "AGF_Credicorp"
    curves_path = "./out/curvas/CurvasRA_" + year + month + day + ".xls"
    port = 22
    password = "dX{\"4YjA"
    output_path = ".\\output\\"+ date + ".xls"
    
    # Descargamos por ftp las curvas
    fs.download_data_sftp(host=server,
                          username=user,
                          password=password,
                          origin=curves_path,
                          destination=output_path,
                          port=port)
    
    # Abrimos el documento excel y leemos lo que hay dentro de el (las filas
    # vienen por linea y separadas las columnas por ;)
    wb = fs.open_workbook(output_path, True, True)
    curves = fs.get_frame_xl(wb, "Curvas", 1, 1, [0, 1])
    fs.close_excel(wb=wb)
    curves = curves.reset_index()
    curves["Date"] = date
    curves = curves[["Date", "Curva", "Dias", "Valor"]]
    curves = fs.format_tuples(curves)
    return curves


def upload_data(tuples):
    '''
    Inserta las tuplas con todos los factores acumulados a la base de datos.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_RA_Curves VALUES (%s,%s,%d,%d)", tuples)
    conn.commit()


def delete_old_data(start_date, end_date):
    '''
    Borra los factores acumulados de la base de datos.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    statement = "DELETE FROM ZHIS_RA_Curves WHERE Date>='" + start_date + "' AND Date <='" + end_date + "'"
    fs.run_sql(conn, statement)
    fs.disconnect_database(conn)


# Cerramos todos las instancias de excel
fs.kill_excel()

# Fijamos la cantidad de dias que descargaremos de data
print("Starting...")
days = 3
end_date = fs.get_ndays_from_today(0)
start_date = fs.get_nweekdays_from_date(days-1, end_date)

# Descargamos las tuplas
print("Downloading tuples...")
tuples = get_tuples(end_date, days)

# Borramos datos antig}
print("Deleting old tuples...")
delete_old_data(start_date, end_date)

# Subimos los nuevos
print("Uploading new tuples...")
upload_data(tuples)