"""
Created on Tue Aug 22 11:00:00 2017

@author: Ashley Mac Gregor
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np

#default='warn'
pd.options.mode.chained_assignment = None  

def read_file(path):
    '''
    Lee archivo de texto en utf8.
    '''
    f = open(path,encoding="utf8")
    file_string=f.read()
    f.close()
    return file_string


def cartera_nacional(path_nac, path_columns_nac, date):
    '''
    Lee y moldea la CARTERA NACIONAL de archivo de texto a dataframe.

    '''
    #separa el archivo de texto por fila (\n), y lo guarda como una lista de strings (los strings son los datos de las filas)
    dataset_nac = read_file(path=path_nac)
    dataset_nac = dataset_nac.split('\n')
    instrument_number_nac = len(dataset_nac)

    # se genera una lista de listas con la data
    for i in range(instrument_number_nac-1):
    	wordi = dataset_nac[i]
    	dataset_nac[i] = np.array(wordi.split(';'))

    #diccionario con los nombres de las columnas más explicativos
    dict_headers_nac = read_file(path=path_columns_nac)
    dict_headers_nac = fs.convert_json_to_dict(dict_headers_nac)

    #se reemplazan los códigos de columnas dataset[0] por los nombres del diccionario
    headers_nac = [dict_headers_nac[k.replace("\ufeff", "")] for k in dataset_nac[0]]

    #la ultima fila viene sin datos, por eso se elimina la ultima fila -1
    dataset_nac = dataset_nac[1:-1]
    dataset_nac = pd.DataFrame(dataset_nac, columns=headers_nac)

    #se agrega la columna "fecha" para reconocer de qué periodo son los datos
    dataset_nac["Fecha"] = date

    #se une el rut y codigo verif del emisor en una misma columna nueva Nombre_Emisor, y se eliminan las columnas RUT y Verif
    dataset_nac["Nombre_Emisor"] = dataset_nac["RUT_Emisor"]+"-"+dataset_nac["Digito_Verif_RUT_Emisor"]
    del dataset_nac["RUT_Emisor"]
    del dataset_nac["Digito_Verif_RUT_Emisor"]

    #inplace es otra forma de volver a definir database
    #se definen los índices para ordenar la información del dataframe
    dataset_nac.set_index(["Fecha", "Run_Fondo", "Codigo_Ins", "Nombre_Emisor"],inplace=True)
    return dataset_nac


def cartera_internacional(path_internac, path_columns_internac, date):
    '''
    Lee y moldea la CARTERA INTERNACIONAL de archivo de texto a dataframe.

    '''
    #separa el archivo de texto por fila (\n), y lo guarda como una lista de strings (los strings son los datos de las filas)
    dataset_internac = read_file(path=path_internac)
    dataset_internac = dataset_internac.split('\n')
    instrument_number_internac = len(dataset_internac)

    #se genera una lista de listas con la data
    for j in range(instrument_number_internac-1):
    	wordj = dataset_internac[j]
    	dataset_internac[j] = np.array(wordj.split(';'))

    #diccionario con los nombres de las columnas más explicativos
    dict_headers_internac = read_file(path=path_columns_internac)
    dict_headers_internac = fs.convert_json_to_dict(dict_headers_internac)

    #se reemplazan los códigos de columnas dataset[0] por los nombres del diccionario
    headers_internac = [dict_headers_internac[k.replace("\ufeff", "")] for k in dataset_internac[0]]

    #la ultima fila viene sin datos, por eso se elimina la ultima fila -1
    dataset_internac = dataset_internac[1:-1]
    dataset_internac = pd.DataFrame(dataset_internac, columns=headers_internac)

    #se agrega la columna "fecha" para reconocer de qué periodo son los datos
    dataset_internac["Fecha"] = date

    #se definen los índices para ordenar la información del dataframe
    dataset_internac.set_index(["Fecha", "Run_Fondo", "Codigo_Ins", "Nombre_Emisor"],inplace=True)
    return dataset_internac


def cartera_futuros(path_futur,vpath_columns_futur, date):
    '''
    Lee y moldea la CARTERA FUTUROS de archivo de texto a dataframe.

    '''

    #separa el archivo de texto por fila (\n), y lo guarda como una lista de strings (los strings son los datos de las filas)
    dataset_futur = read_file(path=path_futur)
    dataset_futur = dataset_futur.split('\n')
    instrument_number_futur = len(dataset_futur)

    #se genera una lista de listas con la data
    for k in range(instrument_number_futur-1):
    	wordk = dataset_futur[k]
    	dataset_futur[k] = np.array(wordk.split(';'))

    #diccionario con los nombres de las columnas más explicativos
    dict_headers_futur = read_file(path=path_columns_futur)
    dict_headers_futur = fs.convert_json_to_dict(dict_headers_futur)

    #se reemplazan los códigos de columnas dataset[0] por los nombres del diccionario
    headers_futur = [dict_headers_futur[k.replace("\ufeff", "")] for k in dataset_futur[0]]

    #la ultima fila viene sin datos, por eso se elimina la ultima fila -1
    dataset_futur = dataset_futur[1:-1]
    dataset_futur = pd.DataFrame(dataset_futur, columns=headers_futur)

    #se agrega la columna "fecha" para reconocer de qué periodo son los datos
    dataset_futur["Fecha"] = date

    #se crea a partir del dataset_futur un nuevo dataframe en el cual cada fila del dataset_futur se transforma en dos filas, l:moneda_futur 
    #de compra a largo plazo y monto valorización positivo, y c: moneda_futur de venta a corto plazo y monto negativo
    new_dataset_futur = pd.DataFrame(columns=headers_futur)

    for i, row in dataset_futur.iterrows():
        row_l = dataset_futur.loc[i]
        row_c = dataset_futur.loc[i]

        if row["Compra/Venta"] == "C":
            row_l["Moneda_Futur"] = row["Activo_Objeto"]
            row_c["Moneda_Futur"] = row["Moneda_Liquidacion"]

        else:
            row_l["Moneda_Futur"] = row["Moneda_Liquidacion"]
            row_c["Moneda_Futur"] = row["Activo_Objeto"]


        row_c["Valoriz_Cierre"] = float(row["Valoriz_Cierre"])*-1
        row_l["Valoriz_Cierre"] = float(row["Valoriz_Cierre"])

        new_dataset_futur = new_dataset_futur.append(row_c)
        new_dataset_futur = new_dataset_futur.append(row_l)
    #print(np.sum(new_dataset_futur["Valoriz_Cierre"]))

    #se crea la columna Codigo Instrumento para los futuros, y se arregla el dataframe para que calce con el nacional e internacional
    new_dataset_futur["Codigo_Ins"] = new_dataset_futur["Fec_Vcto"]+new_dataset_futur["Moneda_Liquidacion"]+new_dataset_futur["Unidad_Cotizacion"]+new_dataset_futur["Activo_Objeto"]+new_dataset_futur["Precio_Futuro"]+new_dataset_futur["Monto_Comprometido"]+new_dataset_futur["Moneda_Futur"]+new_dataset_futur["Compra/Venta"]
    new_dataset_futur["Tipo_Unidades"] = new_dataset_futur["Moneda_Futur"]
    new_dataset_futur["Moneda_Liquidacion"] = new_dataset_futur["Moneda_Futur"]

    del new_dataset_futur["Activo_Objeto"]
    del new_dataset_futur["Unidad_Cotizacion"]
    del new_dataset_futur["Compra/Venta"]
    del new_dataset_futur["Unidades_Nominales_Totales"]
    del new_dataset_futur["Precio_Futuro"]
    del new_dataset_futur["Monto_Comprometido"]
    del new_dataset_futur["Moneda_Futur"]

    new_dataset_futur["Nombre_Emisor"] = ""
    new_dataset_futur["Pais_Emisor"] = ""
    new_dataset_futur["Situacion_Inst"] = ""
    new_dataset_futur["Clasif_Riesgo"] = ""
    new_dataset_futur["Cod_Grupo_Empresarial"] = ""
    new_dataset_futur["Cant_Unidades"] = ""
    new_dataset_futur["TIR"] = ""
    new_dataset_futur["Valor_Par"] = ""
    new_dataset_futur["Valor_Relevante"] = ""
    new_dataset_futur["Cod_Valoriz"] = ""
    new_dataset_futur["Base_Tasa"] = ""
    new_dataset_futur["Tipo_Interes"] = ""
    new_dataset_futur["Porcentaje_Capital_Emisor"] = ""
    new_dataset_futur["Porcentaje_Activos_Emisor"] = ""
    new_dataset_futur["Porcentaje_Activos_Fondo"] = ""

    new_dataset_futur = new_dataset_futur[["Fecha","Run_Fondo","Codigo_Ins","Nombre_Emisor","Nombre_Fondo","Pais_Emisor","Tipo_Instrumento","Fec_Vcto",
    "Situacion_Inst","Clasif_Riesgo","Cod_Grupo_Empresarial","Cant_Unidades","Tipo_Unidades","TIR","Valor_Par","Valor_Relevante","Cod_Valoriz",
    "Base_Tasa","Tipo_Interes","Valoriz_Cierre","Moneda_Liquidacion","Pais_Transaccion","Porcentaje_Capital_Emisor","Porcentaje_Activos_Emisor","Porcentaje_Activos_Fondo"]]

    #se definen los mismos índices que para cartera nacional e internacional
    new_dataset_futur.set_index(["Fecha", "Run_Fondo", "Codigo_Ins", "Nombre_Emisor"],inplace=True)
    return new_dataset_futur


def merge_dataframes(dataset_nac, dataset_internac, new_dataset_futur):
    '''
    Unir verticalmente DATASET NACIONAL, INTERNACIONAL Y FUTUROS EN UN MISMO DATAFRAME

    '''
    frames = [dataset_nac, dataset_internac, new_dataset_futur]
    dataset = pd.concat(frames)

    #Agregamos al dataset una columna Weight, que muestra el peso del instrumento en el Fondo
    dataset = dataset.reset_index()
    dataset["Valoriz_Cierre"] = dataset["Valoriz_Cierre"].astype(float)
    dataset["Valoriz_Total_Fondo"] = dataset.groupby("Run_Fondo")["Valoriz_Cierre"].transform(sum)
    dataset["Weight"] = dataset["Valoriz_Cierre"]/dataset["Valoriz_Total_Fondo"]
    del dataset["Valoriz_Total_Fondo"]
    return dataset



def upload_dataset_db(dataset):
    '''
    UPLOAD DATASET BBDD

    '''
    dataset_tuplas = fs.format_tuples(df = dataset)
    print("Uploading historical data...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_Carteras_Industria_FFMM VALUES (%s,%d,%s,%s,%s,%s,%s,%s,%d,%s,%s,%s,%s,%d,%d,%d,%d,%d,%s,%d,%s,%s,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)



def delete_old_data():
    '''
    Borra la cartera acumulada de la base de datos.
    '''
    print("Deleting old data...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    delete_statement = "DELETE FROM ZHIS_Carteras_Industria_FFMM WHERE 1=1"
    fs.run_sql(conn, delete_statement)
    fs.disconnect_database(conn)


def select_path(start_date, end_date):
    '''
    Abre el archivo de texto de una fecha determinada.
    '''

    daterange = pd.date_range(start_date, end_date, freq="M")
    dataset1 = pd.DataFrame()
    for single_date in daterange:        
        date = single_date.strftime("%Y%m")
        path_nac = ".\\input\\FFM_INV_NACI_" + date + ".txt"
        path_internac = ".\\input\\FFM_INV_EXTR_" + date + ".txt"
        path_futur = ".\\input\\FFM_INV_FUTU_" + date + ".txt"
        try:
            #aca acumulamos, con date de las carteras igual a single_date
            # Bajamos los 3 dataset
            dataset_nac = cartera_nacional(path_nac,path_columns_nac, date=single_date)
            dataset_internac = cartera_internacional(path_internac, path_columns_internac, date=single_date)
            new_dataset_futur = cartera_futuros(path_futur,path_columns_futur, date=single_date)
            # juntamos todo
            dataset = merge_dataframes(dataset_nac, dataset_internac, new_dataset_futur)
            dataset1 = dataset1.append(dataset, ignore_index=True)   
        except:
            pass       
    return dataset1
    

print("Starting...")
# Definimos variables de input
path_columns_nac = ".\\columns.json"
path_columns_internac = ".\\columns_internac.json"
path_columns_futur = ".\\columns_futuros.json"
start_date = "12/31/2016"
end_date =  fs.get_ndays_from_today(0)
dataset = select_path(start_date, end_date)
delete_old_data()
upload_dataset_db(dataset)













'''
posibles diccionarios útiles a futuro:

dict_tipo_interés = {"NL" : "Nominal lineal","NC" : "Nominal compuesto","RL" : "Real lineal","RC" : "Real compuesto",
"NA" : "No aplicable" }

dict_situcaion_inst = {"1" : "Instrumento no sujeto a restricciones",
"2" : "Instrumento sujeto a compromiso",
"3" : "Instrumento entregado como margen o garantía por operaciones en derivados y venta corta",
"4" : "Instrumento sujeto a otra restricción",
"5" : "Instrumento entregado en préstamo para operaciones de venta corta"}

'''