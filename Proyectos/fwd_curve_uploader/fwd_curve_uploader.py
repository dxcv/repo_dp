"""
Created on Wed May 17 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import numpy as np
import pandas as pd
import re
import matplotlib.pyplot as plt


def build_date_name_title(date):
    '''
    Construye el nombre una fecha en formato ICAP. 
    '''
    date = fs.convert_string_to_date(date)
    month = date.strftime("%B")
    day = str(int(date.strftime("%d"))) + "th"
    year = str(date.year)
    date_name = month + " " + day + " " + year
    return date_name


def build_date_name_file(date):
    '''
    Construye el nombre una fecha en formato ICAP. 
    '''
    date = fs.convert_string_to_date(date)
    month = date.strftime("%B")
    month = month[:3]
    day = str(int(date.strftime("%d"))) + "th"
    year = str(date.year)
    date_name = month + " " + day + " " + year
    return date_name


def build_message_name(date_name):
    '''
    Construye el titulo del correo de ICAP. 
    '''
    preamble = "RV: ICAP CHILE SWAPS Closing "
    message_name = preamble + date_name
    print('message_name '+message_name)
    return message_name


def build_attachment_name(date_name):
    '''
    Construye el nombre del archivo adjunto de ICAP. 
    '''
    attachment_name = date_name.replace(" ", "")
    attachment_name = "Closing" + attachment_name
    attachment_name = attachment_name[:-6]
    attachment_name = attachment_name.replace("Dec", "Dic")
    print("attachment_name "+attachment_name)
    if len(attachment_name) < 12:
        attachment_name = attachment_name[:-1] + "0" + attachment_name[10:]
    attachment_name = attachment_name + ".xls"
    return attachment_name


def fetch_icap_file(date):
    '''
    Descarga el archivo de icap dada una fecha. 
    '''
    date_name_title = build_date_name_title(date)
    date_name_file = build_date_name_file(date)
    message_name = build_message_name(date_name_title)
    attachment_name = build_attachment_name(date_name_file)
    message_name_regex = "^" + message_name
    attachment_regex = "^" + attachment_name
    output_path = fs.get_self_path() + "output\\" + date + ".xls"
    fs.fetch_attachment(message_name_regex, attachment_name, output_path)


def fetch_tuples(spot_date, period_lenght):
    '''
    Descarga el archivo para una serie de fechsa y traspasa los datos
    a tuplas. 
    '''
    date = spot_date
    historical_fwd_yield = []
    historical_fwd_days = []
    historical_fwd_bid = []
    historical_fwd_ask = []
    for i in range(period_lenght):
        # try :
        fetch_icap_file(date)
        fwd_yield, fwd_days, fwd_bid, fwd_ask = read_icap_file(date)
        '''
        except:
            print("Fail on " + date)
            aux_date = fs.get_prev_weekday(date)
            fwd_yield = fetch_curve(aux_date, "fwd")
            fwd_days = fetch_curve(aux_date, "days")
            fwd_bid = fetch_curve(aux_date, "bid")
            fwd_ask= fetch_curve(aux_date, "ask")
            fwd_yield = np.append([date], fwd_yield)
            fwd_days = np.append([date], fwd_days)
            fwd_bid = np.append([date], fwd_bid)
            fwd_ask = np.append([date], fwd_ask)
        '''
        # Permutamos el tenor 1 y 7 ya que agregamos
        # el 1MO despues de crear la tabla yield y esta al final
        fwd_yield = fwd_yield[[0, 2, 3, 4, 5, 6, 7, 1]]
        historical_fwd_yield.append(fwd_yield)
        historical_fwd_days.append(fwd_days)
        historical_fwd_bid.append(fwd_bid)
        historical_fwd_ask.append(fwd_ask)
        date = fs.get_prev_weekday(date)    
    # Consolidamos en un dataframe
    historical_fwd_yield = pd.DataFrame(historical_fwd_yield, columns = ["Fecha", 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 0.0833333])
    historical_fwd_days = pd.DataFrame(historical_fwd_days, columns = ["Fecha", "1M", "3M", "6M", "9M", "12M", "18M", "24M"])
    historical_fwd_bid = pd.DataFrame(historical_fwd_bid, columns = ["Fecha", "1M", "3M", "6M", "9M", "12M", "18M", "24M"])
    historical_fwd_ask = pd.DataFrame(historical_fwd_ask, columns = ["Fecha", "1M", "3M", "6M", "9M", "12M", "18M", "24M"])
    # Casteamos a tuplas todo
    historical_fwd_yield = fs.format_tuples(historical_fwd_yield)
    historical_fwd_days = fs.format_tuples(historical_fwd_days)
    historical_fwd_bid = fs.format_tuples(historical_fwd_bid)
    historical_fwd_ask = fs.format_tuples(historical_fwd_ask)
    return historical_fwd_yield, historical_fwd_days, historical_fwd_bid, historical_fwd_ask


def read_icap_file(date):
    '''
    Abre el archivo de ICAP de una fecha determinada y retorna los
    puntos forward como tasa actual 360. 
    '''
    # Leemos la info del excel de ICAP
    file_path = "output\\" + date + ".xls"
    wb = fs.open_workbook(file_path, True, False)
    sheet = "Closing"
    fx_bid = fs.get_value_xl(wb, sheet, 10, 3)
    fx_offer = fs.get_value_xl(wb, sheet, 11, 3)
    fwd_points_bid = fs.get_column_xl(wb, sheet, 81, 4)
    fwd_points_mid = fs.get_column_xl(wb, sheet, 81, 5)
    fwd_points_ask = fs.get_column_xl(wb, sheet, 81, 6)
    fwd_days = fs.get_column_xl(wb, sheet, 81, 3)
    fs.close_excel(wb)

    # Calculamos el precio mid del fx
    fx_spot = (fx_bid+fx_offer) / 2
    # Traspasamos todos los datos leidos a numpy arrays
    fwd_points_bid = np.array(fwd_points_bid)
    fwd_points_mid = np.array(fwd_points_mid)
    fwd_points_ask = np.array(fwd_points_ask)

    # Elegimos solo los tenors que nos interesan
    fwd_points_bid = fwd_points_bid[[2, 4, 7, 8, 9, 10, 11]]
    fwd_points_mid = fwd_points_mid[[2, 4, 7, 8, 9, 10, 11]]
    fwd_points_ask = fwd_points_ask[[2, 4, 7, 8, 9, 10, 11]]
    fwd_days = np.array(fwd_days)
    fwd_days = fwd_days[[2, 4, 7, 8, 9, 10, 11]]
    fwd_days = fwd_days.astype(int)
    fwd_yield = ((fwd_points_mid/fx_spot)/fwd_days) * 360
    fwd_yield = np.append([date], fwd_yield)
    fwd_days = np.append([date], fwd_days)
    fwd_bid = np.append([date], fwd_points_bid)
    fwd_ask = np.append([date], fwd_points_ask)
    return fwd_yield, fwd_days, fwd_bid, fwd_ask


def fetch_curve(date, curve_name):
    '''
    Descarga las curvas de la base de datos, en caso
    de que el upload falle. 
    '''
    path = ".\\querys\\" + curve_name + ".sql"
    query = fs.read_file(path)
    query = query.replace("autodate", date)
    curve = fs.get_frame_sql_user(server="Puyehue",
                                   database="MesaInversiones",
                                   username="usrConsultaComercial",
                                   password="Comercial1w",
                                   query=query)
    curve.set_index(["fecha"], inplace=True)
    return curve


def delete_old_data(start_date):
    '''
    Borra las carteras de los ultimos dias, dada la cantidad de dias.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    query = "DELETE FROM ZHIS_Curva_FWD WHERE Fecha >= '" + start_date + "'"
    fs.run_sql(conn, query)
    query = "DELETE FROM ZHIS_FWD_USD_Days WHERE Fecha >= '" + start_date + "'"
    fs.run_sql(conn, query)
    query = "DELETE FROM ZHIS_FWD_USD_Bid WHERE Fecha >= '" + start_date + "'"
    fs.run_sql(conn, query)
    query = "DELETE FROM ZHIS_FWD_USD_Ask WHERE Fecha >= '" + start_date + "'"
    fs.run_sql(conn, query)
    fs.disconnect_database(conn)


def upload_new_data(historical_fwd_yield, historical_fwd_days, historical_fwd_bid, historical_fwd_ask):
    '''
    Sube a la base de datos las tuplas nuevas.
    '''
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_Curva_FWD VALUES (%s, %d, %d, %d, %d, %d, %d, %d)", historical_fwd_yield)
    cursor.executemany("INSERT INTO ZHIS_FWD_USD_Days VALUES (%s, %d, %d, %d, %d, %d, %d, %d)", historical_fwd_days)
    cursor.executemany("INSERT INTO ZHIS_FWD_USD_Bid VALUES (%s, %d, %d, %d, %d, %d, %d, %d)", historical_fwd_bid)
    cursor.executemany("INSERT INTO ZHIS_FWD_USD_Ask VALUES (%s, %d, %d, %d, %d, %d, %d, %d)", historical_fwd_ask)
    conn.commit()
    fs.disconnect_database(conn)


# Cerramos posibles instancias de Excel
fs.kill_excel()

# Definimos las fechas en que trabajaremos
spot_date = fs.get_ndays_from_today(5)
period_lenght = 4
start_date = fs.get_nweekdays_from_date(period_lenght - 1, spot_date)

print("Fetching tuples...")
# Descargamos las tuplas del correo
historical_fwd_yield, historical_fwd_days, historical_fwd_bid, historical_fwd_ask = fetch_tuples(spot_date, period_lenght)


print("Deleting old tuples...")
# Borramos las tuplas antiguos
delete_old_data(start_date)

print("Inserting new tuples...")
# Insertamos las nuevas tuplas
upload_new_data(historical_fwd_yield,
                historical_fwd_days,
                historical_fwd_bid,
                historical_fwd_ask)
