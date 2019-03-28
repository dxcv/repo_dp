"""
Created on Thu Oct 18 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
from libreria_fdo import *
from tia.bbg import v3api




'''FUNCIONES BLOOMBERG'''

def get_hist_data_bbl(tickers, currency , fields, init , end , max_data_points=10000000, non_trading_day_fill_method="PREVIOUS_VALUE", non_trading_day_fill_option="ALL_CALENDAR_DAYS"):
    '''
	Dada una lista de tickers, flds, una fecha de inicio, otra de fin y una moneda, descarga todos los indices de la lista entre ambas fechas en esa moneda con todos sus flds.
    '''
    LocalTerminal = v3api.Terminal('localhost', 8194)
    response = LocalTerminal.get_historical(tickers, fields, currency = currency, ignore_security_error = 1, ignore_field_error = 1, start = init, end = end, max_data_points = max_data_points, non_trading_day_fill_method = non_trading_day_fill_method, non_trading_day_fill_option = non_trading_day_fill_option)
    bloombergData = response.as_frame().fillna(method = "bfill") #Ojo esto es para los indices que tienen menos historia de la que se pide, por convencion los mantenemos flat.
    bloombergData = bloombergData[bloombergData.index.dayofweek < 5] #Esto es para filtrar los fines de semana, por convencion solo trabajaremos con weekdays.
    return bloombergData

'''FUNCIONES UPLOADER'''

def get_indices():
    '''
    Descarga la lista de indices a actualizar desde Puyehue.
    '''
    print("Downloading indexes list...")
    query = "SELECT Index_Id, Ticker, Moneda FROM Indices_Estatica"
    indices = get_frame_sql_user(server="Puyehue",
                                 database="MesaInversiones",
                                 username="usrConsultaComercial",
                                 password="Comercial1w",
                                 query=query)
    return indices


def get_dataset(indices, dia_inic, dia_fin):
    '''
    Descarga la informacion historica de los indices desde Bloomberg en un dataframe.
    '''
    print("Downloading historical data...")
    currencies = ["CLP",  "BRL", "COP", "MXN", "UYU", "PEN", "ARS", "USD"]
    mapping = {"CLP": "$",
               "BRL": "BRL",
               "COP": "COP",
               "MXN": "MX",
               "UYU": "UYU",
               "PEN": "PEN",
               "ARS": "ARS",
               "USD": "US$"}
    currencies_bcs = [mapping[x] for x in currencies]
    dataset = []
    for currency in currencies:
        dataset_i = get_hist_data_bbl(tickers = indices[indices["Moneda"] == mapping[currency]]["Ticker"], currency = currency, fields = ["px_last"], init = dia_inic, end = dia_fin)
        dataset.append(dataset_i)   
    dataset = pd.concat(dataset, axis = 1, keys=currencies_bcs )
    return dataset


def process_tuples(indices, dataset):
    '''
    Procesa el dataset para generar una lista de tuplas con los index_id que seran subidos a Puyehue.
    '''
    print("Procesing tuples...")
    indices = indices.reset_index().set_index(["Ticker", "Moneda"])
    tuplas = []
    for ticker_crncy in indices.index.values:
    	ticker = ticker_crncy[0]
    	moneda = ticker_crncy[1]
    	index_id = indices.loc[ticker, moneda]["Index_Id"]
    	serie = dataset[moneda, ticker].reset_index()
    	serie["Index_Id"] = index_id
    	serie = serie[["date", "Index_Id","px_last"]]
    	serie_tuplas = format_tuples(df = serie)
    	tuplas += serie_tuplas
    return tuplas


def delete_old_data(dia_inic):
    '''
    Borra los indices de los ultimos 10 dias en la base de datos.
    '''
    print("Deleting historical data...")
    conn = connect_database_user(server="Puyehue",
                                database="MesaInversiones",
                                username="usrConsultaComercial",
                                password="Comercial1w")
    query = read_file(".\\querys_indexes_uploader\\delete_indexes.sql").replace("AUTODATE", dia_inic)
    run_sql(conn, query)
    disconnect_database(conn)


def upload_new_data(tuplas):
    '''
    Sube los indices de los ultimos 10 dias a la base de datos.
    '''
    print("Uploading historical data...")
    conn = connect_database_user(server="Puyehue",
                                 database="MesaInversiones",
                                 username="usrConsultaComercial",
                                 password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO Indices_Dinamica VALUES (%s,%d,%d)", tuplas)
    conn.commit()
    disconnect_database(conn)


print("Start...")
print("Descargando indices, NO CERRAR ESTA VENTANA")
#FIJAMOS LAS FECHAS ENTRE LAS QUE TRABAJAREMOS
dias_hoy = -1
dias_historia = 10
# dia_inic_str = "2017-01-01" #PARA INFO HISTORICA MASIVA
dia_inic_str = get_ndays_from_today(dias_historia)
dia_fin_str = get_ndays_from_today(dias_hoy)
dia_inic = convert_string_to_date(dia_inic_str)
dia_fin = convert_string_to_date(dia_fin_str)

#OBTENEMOS LA LISTA DE LOS INDICES QUE BAJAREMOS
indices = get_indices()

#DESCARGAMOS EL DATASET CON TODA LA INFORMACION HISTORICA DESDE BLOOMBERG
dataset = get_dataset(indices = indices, dia_inic = dia_inic, dia_fin = dia_fin)

#PROCESAMOS LOS DATOS CRUDOS EN TUPLAS PARA SUBIRLOS A PUYEHUE
tuplas = process_tuples(indices = indices, dataset = dataset)

#SE BORRA DE LA BDD LAS TUPLAS DE INDICES A PARTIR DE LA FECHA DE INICIO
delete_old_data(dia_inic = dia_inic_str)

#INSERTAMOS LAS NUEVAS TUPLAS A LA BDDD
upload_new_data(tuplas = tuplas)

print("Finished")
print("Uploaded tuples: "+ str(len(tuplas)))
