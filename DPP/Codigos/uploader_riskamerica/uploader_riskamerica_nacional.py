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
import numpy as np


def download_national_data(date):
    '''
    Genera el dataframe final de la info de riskamerica
    '''
    #Obtenemos la lista de los archivos de la fecha correspondiente
    file_list = utiles.get_xml_svc(date)
    
    df_risk = None
    #primero obtenemos la info de los archivos nacionales
    for file in file_list[0]:
        df_aux = compute_xml_nat(file)
        if df_risk is not None:
            df_risk = utiles.append_without_duplicates(df_risk, df_aux)
        else:
            df_risk = df_aux
  
    return df_risk

def compute_xml_nat(xml_name):
    '''
    Genera un dataframe a partir de un xml de los archivos nacionales
    '''
    infile = open(xml_name, "r")
    
    contents = infile.read()
    soup = BeautifulSoup(contents, 'html.parser')
    dic_xml = {}
    registro = soup.find_all('registro')
    for r in registro:
        nemo = BeautifulSoup(str(r), 'html.parser').findAll('nemo')
        if nemo[0].get_text() == 'PAGARE NR':
            pass
        else:
            resultado = BeautifulSoup(str(r), 'html.parser').findAll('resultado')
            if int(resultado[0].get_text()) == 0:
                tasa = BeautifulSoup( str(r), 'html.parser').findAll('tasa-estimada')
                duration = BeautifulSoup(str(r), 'html.parser').findAll('duration')
                cantidad = BeautifulSoup(str(r), 'html.parser').findAll('cantidad')
                monto = BeautifulSoup(str(r), 'html.parser').findAll('monto-valorizado')
                # if nemo[0].get_text()=="BACEN-A1":
                #     print( nemo[0].get_text() + " esta")
                if float(cantidad[0].get_text())>0:
                    dic_xml[nemo[0].get_text()] = {'Tasa': float(tasa[0].get_text()), 'Duration': float(duration[0].get_text()), 'Cantidad': float(cantidad[0].get_text()), 'Precio': 100*float(monto[0].get_text())/float(cantidad[0].get_text())}
    df = utiles.dict_to_dataframe(dic_xml)
    
    return df

def get_currency_type(date, df_risk):

    date_anterior = utiles.get_fecha_habil_anterior(date)
    path = ".\\querys\\mapping_cinta.sql"
    query = fs.read_file(path=path).replace("AUTODATE", str(date_anterior))
    cinta_ra = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query)

    cinta_ra.set_index(["Codigo_Ins"], inplace=True)

    df_mapped = df_risk.merge(cinta_ra, how='left', left_index=True, right_index=True)

    
    return df_mapped

def mapea_nulls(nemo):
    

    if ('BNPDBC' in nemo) or ('FN'==nemo[:2]):
        moneda='$'
        tipo_instrumento='Deposito'

    elif ('FU'==nemo[:2]):
        print(nemo + " mapeadooo ctm")
        moneda='UF'
        tipo_instrumento='Deposito'
        
    elif ('BVIVO-B'== nemo) or ('BVIVO-C'== nemo) or ('BAGUA-Z'== nemo) or ('BARAU-R'==nemo):
        moneda='UF'
        tipo_instrumento = 'Bono Corporativo'

    else:
        print(nemo+" no quedo mapeado el tipo")
        moneda=""
        tipo_instrumento=""

    print(nemo + " moneda: "+moneda +" tipo: "+tipo_instrumento)
    return moneda, tipo_instrumento






def get_instrument_returns(date_spot, date_anterior, df_risk_mapped, is_first_day_of_year):

    
    delta_dias_valorizacion = (date_spot - date_anterior).days
    currency_dic = utiles.compute_currency_prof(date_spot)
    #print(currency_dic)
    df_risk_mapped['Retorno_1D'] = df_risk_mapped['Precio_spot']/df_risk_mapped['Precio_anterior']-1
    df_risk_mapped['Tipo_retorno'] = 'RA'
    df_risk_mapped['Retorno_Moneda_1D'] = None
    #esta función hay que arreglarla
    #print(currency_dic)

    for i, row in df_risk_mapped.iterrows():
    
        nemo = i
        tipo_instrumento = str(row['tipo_instrumento'])
        moneda = row['Moneda']
        retorno_ins = row['Retorno_1D']



        if tipo_instrumento=='nan':
            moneda, tipo_instrumento = mapea_nulls(nemo)
            df_risk_mapped.loc[i,'Moneda'] = moneda 
            df_risk_mapped.loc[i,'tipo_instrumento'] = tipo_instrumento 

        retorno_moneda = currency_dic[moneda] 
        
        tasa_spot = float(row['Tasa_spot'])
        devengo_tasa = utiles.get_devengo_tasa_old(nemo, tasa_spot/100)
        df_risk_mapped.loc[i,'Retorno_Moneda_1D'] = retorno_moneda 
        df_risk_mapped.loc[i,'Devengo_1D'] = devengo_tasa 

        #HAY QUE PONERSE EN EL CASO DE DEPOSITOS EN USD
        if moneda =='UF':
            retorno_backoffice = retorno_ins - (delta_dias_valorizacion-1)*(devengo_tasa+retorno_moneda)
        else:
            retorno_backoffice = retorno_ins - (delta_dias_valorizacion-1)*devengo_tasa

        # tratar de hacer esto mas eficiente sin ifs

        if retorno_ins <= -0.005:
            retorno_ins= 0 
            df_risk_mapped.loc[i,'Tipo_retorno'] = 'E'
            tasa_anterior = float(row['Tasa_anterior'])
            
            duration_anterior = float(row['Duration_anterior'])
            dur_mod = duration_anterior/(1+tasa_anterior/100)
            retorno_tasa = -dur_mod*(tasa_spot-tasa_anterior)/100
            
            retorno_ins = retorno_tasa + (devengo_tasa + retorno_moneda)*delta_dias_valorizacion

            if moneda =='UF':
                retorno_backoffice = retorno_tasa + devengo_tasa + retorno_moneda
            else:
                retorno_backoffice = retorno_tasa + devengo_tasa

        if is_first_day_of_year is True:
            # si es el primer dia habil del año hay que considerar la rentabilidad desde el 01 de enero
            first_day = datetime.date(date_spot.year,1,1)
            delta_dias_first_day_of_year = (date_spot - first_day).days 
            retorno_ins = retorno_backoffice + delta_dias_first_day_of_year*(devengo_tasa+retorno_moneda)
        
        df_risk_mapped.loc[i,'Retorno_1D'] = retorno_ins
        df_risk_mapped.loc[i,'Retorno_BBOO_1D'] = retorno_backoffice

    df_risk_mapped['Fecha'] = date_spot   
    return df_risk_mapped

def get_full_nacional_df(date_spot, date_anterior, df_risk_nacional_spot, df_risk_nacional_anterior, is_first_day_of_year):

    df_risk_nacional = df_risk_nacional_spot.merge(df_risk_nacional_anterior, how='left', left_index=True, right_index=True, suffixes=('_spot', '_anterior'))
    df_risk_nacional = get_currency_type(date_spot,df_risk_nacional)
    
    
    df_risk_nacional = get_instrument_returns(date_spot, date_anterior,df_risk_nacional, is_first_day_of_year)

    df_risk_nacional = df_risk_nacional.reset_index().rename(columns={'index':'Codigo_Ins'})
    df_risk_nacional = df_risk_nacional.loc[:,['Fecha','Codigo_Ins','Moneda','tipo_instrumento','Tipo_retorno','Precio_spot','Precio_anterior','Tasa_spot','Tasa_anterior','Duration_spot','Retorno_1D','Retorno_Moneda_1D', 'Devengo_1D', 'Retorno_BBOO_1D']]
    df_risk_nacional.set_index(['Fecha','Codigo_Ins'], inplace=True)
    df_risk_nacional['Retorno_1D'] = df_risk_nacional['Retorno_1D']*100
    df_risk_nacional['Retorno_Moneda_1D'] = df_risk_nacional['Retorno_Moneda_1D']*100
    df_risk_nacional['Devengo_1D'] = df_risk_nacional['Devengo_1D']*100
    df_risk_nacional['Retorno_BBOO_1D'] = df_risk_nacional['Retorno_BBOO_1D']*100
    
    df_risk_nacional = df_risk_nacional.fillna({'Precio_anterior':-1000, 'Tasa_anterior':-1000, 'Retorno_1D':-1000, 'Retorno_BBOO_1D':-1000})
    df_risk_nacional.sort_index(inplace=True)

    return df_risk_nacional

def upload_DB(df_risk_nacional):

    tuplas = df_risk_nacional.to_records().tolist()

    conn = fs.connect_database_user(server="Puyehue",
                                 database="MesaInversiones",
                                 username="usrConsultaComercial",
                                 password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO Performance_Nacionales (Fecha, Codigo_Ins, Moneda, Tipo_ins, Tipo_retorno, Precio, Precio_anterior, Tasa, Tasa_anterior, Duration, Retorno_1D, Retorno_Moneda_1D, Devengo_1D, Retorno_BBOO_1D) VALUES (%s,%s,%s,%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d)", tuplas)
    conn.commit()
    fs.disconnect_database(conn)
    
 
def write_excel(df_risk_nacional):
    wb = fs.open_workbook("data_riskamerica_nacional.xlsx", True, True)
    fs.clear_sheet_xl(wb, "data")
    fs.paste_val_xl(wb, "data", 1, 1, df_risk_nacional)



fechas_hab=utiles.get_fechas_habiles()
fechas_hab['Fecha'] = fechas_hab['Fecha'].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))



#es muy importante que este sea falso siempre que no sea el primer dia habil del año
is_first_day_of_year = False
date_spot = datetime.date.today()

if str(date_spot) in fechas_hab['Fecha'].values:
        
print(str(date_spot))


date_anterior = utiles.get_fecha_habil_anterior(date_spot)

df_risk_nacional_spot= download_national_data(date_spot)
df_risk_nacional_anterior = download_national_data(date_anterior)
df_risk_nacional = get_full_nacional_df(date_spot, date_anterior, df_risk_nacional_spot, df_risk_nacional_anterior, is_first_day_of_year)
        
upload_DB(df_risk_nacional)

        






