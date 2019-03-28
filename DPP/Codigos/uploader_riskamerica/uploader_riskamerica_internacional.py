import sys
sys.path.insert(0, '../libreria/')
sys.path.insert(0, '../portfolio_analytics/utiles')
import libreria_fdo as fs
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import paramiko
import os
import libreria_fdo as fs
import utiles as utiles



def download_international_data(date):
    '''
    Genera el dataframe final de la info de riskamerica
    '''
    #Obtenemos la lista de los archivos de la fecha correspondiente
    file_list = utiles.get_xml_svc(date)
    df_risk_int = None

    #archivos internacionales
    for file in file_list[1]:
        df_aux = compute_xml_int(file)
        if df_risk_int is not None:
            df_risk_int = utiles.append_without_duplicates(df_risk_int, df_aux)
        else:
            df_risk_int = df_aux
    
    return df_risk_int


def compute_xml_int(xml_name):
    '''
    Genera un dataframe a partir de un xml de los archivos internacionales
    '''
    infile = open(xml_name, "r")
    contents = infile.read()
    soup = BeautifulSoup(contents, 'html.parser')
    dic_xml = {}
    registro = soup.find_all('registro')
    for r in registro:
        nemo = BeautifulSoup(str(r), 'html.parser').findAll('identificador')
        if nemo[0].get_text() == 'PAGARE NR':
            pass
        else:
            tasa = BeautifulSoup(str(r), 'html.parser').findAll('precio')
            try:
                precio = float(tasa[0].get_text())
            except:
                precio=-1000 #pasa cuando riskamerica no devuelve precio

            dic_xml[nemo[0].get_text()] = {'Precio': precio}
    df_internacional = utiles.dict_to_dataframe(dic_xml)
    

    return df_internacional

def get_tipo_instrumento(df_risk_internacional):

    df_risk_internacional['Tipo_instrumento'] = '' 

    for i, row in df_risk_internacional.iterrows():
        
        bloomberg_id = i

        if 'Equity' in bloomberg_id:
            df_risk_internacional.loc[i,'Tipo_instrumento'] = 'RVI'
        else:
            df_risk_internacional.loc[i,'Tipo_instrumento'] = 'RFI'

    return df_risk_internacional

def get_full_international_df(date_spot,df_risk_internacional_spot, df_risk_internacional_anterior):

    df_risk_internacional = df_risk_internacional_spot.merge(df_risk_internacional_anterior, how='left', left_index=True, right_index=True, suffixes=('_spot', '_anterior'))
    df_risk_internacional = get_tipo_instrumento(df_risk_internacional)
    dic_isin_codigoIns = utiles.get_mapping_instrumentos_internacionales()
    df_risk_internacional = utiles.change_index(dic_isin_codigoIns, df_risk_internacional) #Esta funcion hay que revisarla

    df_risk_internacional = df_risk_internacional.reset_index().rename(columns={'index':'Codigo_Ins'})

    df_risk_internacional['Retorno_1D'] = df_risk_internacional['Precio_spot']/df_risk_internacional['Precio_anterior']-1
    df_risk_internacional = df_risk_internacional.fillna({'Precio_anterior':-1000, 'Retorno_1D':-1000})
    df_risk_internacional['Fecha'] = date_spot

    df_risk_internacional = df_risk_internacional.loc[:,['Fecha','Codigo_Ins','Tipo_instrumento','Precio_spot','Precio_anterior','Retorno_1D']]
    df_risk_internacional.set_index(['Fecha','Codigo_Ins'], inplace=True)
    df_risk_internacional['Retorno_1D']=100*df_risk_internacional['Retorno_1D']

    df_risk_internacional.sort_index(inplace=True)

    return df_risk_internacional

def upload_DB(df_risk_internacional):

    tuplas = df_risk_internacional.to_records().tolist()

    conn = fs.connect_database_user(server="Puyehue",
                                 database="MesaInversiones",
                                 username="usrConsultaComercial",
                                 password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO Performance_Internacionales (Fecha, Codigo_Ins, Tipo_ins, Precio_spot, Precio_anterior, Retorno_1D) VALUES (%s,%s,%s,%d,%d,%d)", tuplas)
    conn.commit()
    fs.disconnect_database(conn)
    

def write_excel(df_risk_internacional):

    wb = fs.open_workbook("data_riskamerica_internacional.xlsx", True, True)
    fs.clear_sheet_xl(wb, "data")
    fs.paste_val_xl(wb, "data", 1, 1, df_risk_internacional)






fechas_hab=utiles.get_fechas_habiles()
fechas_hab['Fecha'] = fechas_hab['Fecha'].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))

date_spot = datetime.date.today()

print(str(date_spot))
date_anterior = utiles.get_fecha_habil_anterior(date_spot)
df_risk_internacional_spot= download_international_data(date_spot)
df_risk_internacional_anterior= download_international_data(date_anterior)
df_risk_internacional = get_full_international_df(date_spot, df_risk_internacional_spot, df_risk_internacional_anterior)
upload_DB(df_risk_internacional)
        







