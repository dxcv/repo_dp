import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import paramiko
import os
import libreria_fdo as fs
import numpy as np

dic_currencies = {'UF': [23,'$'], 'US$': [66,'$'], 'MX':[85,'$'], 'ARS': [605,'US$'], 'PEN':[595,'US$'], 'PPE':[595,'US$'], 'SOL':[595,'US$']}



def get_fecha_habil_anterior(date):

    query = "Select fecha from Fechas_habiles where id in (Select id-1 from Fechas_Habiles where fecha='AUTODATE')"
    query=query.replace("AUTODATE", str(date))
    fecha_habil_anterior = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    
    fecha_habil_anterior = fecha_habil_anterior.date()

    if (fecha_habil_anterior.month==12 and fecha_habil_anterior.day==31):
        query_bancario = "select Fecha from fechas_habiles where id in (select id-1 from Fechas_habiles where fecha='AUTODATE')"
        query_bancario = query_bancario.replace("AUTODATE", str(fecha_habil_anterior))
        fecha_habil_anterior = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query_bancario)
        fecha_habil_anterior = fecha_habil_anterior.date()



    #retorno un datetime.date
    return fecha_habil_anterior

def get_fecha_habil_posterior(date):

    query = "Select fecha from Fechas_habiles where id in (Select id+1 from Fechas_Habiles where fecha='AUTODATE')"
    query=query.replace("AUTODATE", str(date))
    
    fecha_habil_anterior = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    #retorno un datetime.date
    return fecha_habil_anterior.date()

def get_fecha_contado_normal(date):

    query = "Select fecha from Fechas_habiles where id in (Select id+2 from Fechas_Habiles where fecha='AUTODATE')"
    query=query.replace("AUTODATE", str(date))
    
    fecha_habil_anterior = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    #retorno un datetime.date
    return fecha_habil_anterior.date()

def get_fechas_habiles():

    query = "Select Fecha from Fechas_habiles"
    fechas_hab = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query)

    #fechas_hab['Fecha'] = fechas_hab['Fecha'].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))
    return fechas_hab

def get_fechas_habiles_all(date, index_term):

    #feriados como el de iglesias evangelicas, encuentro de dos mundos, viernes santo y san pedro san pablo cambian año a año asi que no los puse.
    holidays =  [{'D-M': '1-1'},{'D-M': '1-5'},{'D-M': '21-5'},{'D-M': '16-7'},{'D-M': '15-8'},{'D-M': '18-9'},{'D-M': '19-9'},{'D-M': '1-11'},{'D-M': '8-12'},{'D-M': '25-12'}]
    holidays = pd.DataFrame(holidays)
    
    fechas_habiles_short = get_fechas_habiles()
    

    fecha_inicio = fechas_habiles_short['Fecha'].max() +  datetime.timedelta(days=1)
    
    end_date = pd.Timestamp(datetime.date(date.year + index_term, date.month,date.day))

    fechas_habiles_long = pd.date_range(start= fecha_inicio, end =end_date +  datetime.timedelta(days=10), freq='B')
    fechas_habiles_long = pd.DataFrame(fechas_habiles_long).rename(columns={0:'Fecha'})
    
    
    fechas_habiles_long['M'] = pd.DatetimeIndex(fechas_habiles_long['Fecha']).month
    fechas_habiles_long['D'] = pd.DatetimeIndex(fechas_habiles_long['Fecha']).day
    fechas_habiles_long['D-M']=fechas_habiles_long['D'].astype(str)+'-'+fechas_habiles_long['M'].astype(str)
    
    fechas_habiles_long = fechas_habiles_long[fechas_habiles_long['D-M'].isin(holidays['D-M'])==False].drop(columns=['D','M','D-M'])
    fechas = fechas_habiles_short.append(fechas_habiles_long)

    fechas['anterior']=fechas['Fecha'].shift(1)
    fechas['fecha_settle_t2'] = fechas['Fecha'].shift(-2)
    fechas = fechas[(fechas['Fecha']>=date) & (fechas['Fecha']<=end_date)]

    return fechas




def compute_working_dates(instruments):

    fechas = get_fechas_habiles_all(date, 20)

    for index, row in df_forwards.iterrows(): 
        next_working_day = get_nearest_working_day(index)



def get_nearest_working_day(date, working_dates):
    
    list_working_dates = working_dates.values
    
    while date not in list_working_dates:
        date = date + datetime.timedelta(days=1)
    return date

def get_FI_funds():
    
    funds_list = "'RENTA','IMT E-PLUS','DEUDA CORP','DEUDA 360','SPREADCORP', 'LIQUIDEZ','MACRO 1.5', 'MACRO CLP3', 'M_MARKET'"
    return funds_list


def get_updated_RFI(funds_list):
    
    spot = fs.get_ndays_from_today(0)
    yesterday = fs.get_ndays_from_today(1)
    query = " select codigo_ins, fondo, SUM(Cantidad) as nominal, SUM(Monto) as monto from (select codigo_fdo COLLATE DATABASE_DEFAULT as fondo, codigo_ins COLLATE DATABASE_DEFAULT as codigo_ins, cantidad, monto from zhis_carteras_main where fecha='YESTERDAY' and codigo_ins not like 'PAGARE%' and Tipo_Instrumento not in ('Cuota de Fondo','Letra Hipotecaria') UNION ALL select compra COLLATE DATABASE_DEFAULT as fondo, instrumento COLLATE DATABASE_DEFAULT as codigo_ins, sum(cantidad), sum(Monto) from TransaccionesIRF where fecha='SPOT_DATE' and compra is not null group by Instrumento, compra UNION ALL select vende COLLATE DATABASE_DEFAULT as fondo, instrumento COLLATE DATABASE_DEFAULT as codigo_ins, -sum(cantidad), -sum(Monto) from TransaccionesIRF where fecha='SPOT_DATE' and vende is not null group by Instrumento, vende) T1 where fondo in (FUNDS_LIST) group by fondo, codigo_ins"
    query = query.replace("SPOT_DATE", str(spot))
    query = query.replace("YESTERDAY", str(yesterday))
    query = query.replace("FUNDS_LIST", str(funds_list))
    print(query)
    irf_portfolio = fs.get_frame_sql_user(server="puyehue", database="MesaInversiones", username="usuario1", password="usuario1", query=query)

    return irf_portfolio

def get_updated_IIF(funds_list):
    
    spot = fs.get_ndays_from_today(0)
    yesterday = fs.get_ndays_from_today(1)
    query = "select codigo_ins, fondo, SUM(cantidad) as nominal, codigo_emi, moneda, fec_vcto, SUM(Monto) as monto from (select codigo_fdo COLLATE DATABASE_DEFAULT as fondo, codigo_ins COLLATE DATABASE_DEFAULT as codigo_ins, codigo_emi, moneda,fec_vcto, cantidad, monto from zhis_carteras_main where fecha='YESTERDAY' and (codigo_ins like 'PAGARE%' or codigo_ins like 'PDBC%') UNION ALL select compra COLLATE DATABASE_DEFAULT as fondo, instrumento COLLATE DATABASE_DEFAULT as codigo_ins, emisor COLLATE DATABASE_DEFAULT as codigo_emi, moneda COLLATE DATABASE_DEFAULT as moneda, DATEADD(DAY, dias, Fecha) as fec_vcto,  sum(rescate) as cantidad, sum(captacion) as monto from TransaccionesIIF where fecha='SPOT_DATE' and compra is not null group by fecha, instrumento, emisor,moneda, dias, compra UNION ALL select vende COLLATE DATABASE_DEFAULT as fondo, instrumento COLLATE DATABASE_DEFAULT as codigo_ins, emisor COLLATE DATABASE_DEFAULT as codigo_emi, moneda COLLATE DATABASE_DEFAULT as moneda, DATEADD(DAY, dias, Fecha) as fec_vcto,  -sum(rescate) as cantidad, -sum(captacion) as monto from TransaccionesIIF where fecha='SPOT_DATE' and vende is not null group by fecha, instrumento, emisor,moneda, dias, vende ) T1 where fondo in (FUNDS_LIST) group by fondo, codigo_ins, codigo_emi, moneda, fec_vcto"
    query = query.replace("SPOT_DATE", str(spot))
    query = query.replace("YESTERDAY", str(yesterday))
    query = query.replace("FUNDS_LIST", str(funds_list))
   
    iif_portfolio = fs.get_frame_sql_user(server="puyehue", database="MesaInversiones", username="usuario1", password="usuario1", query=query)

    return iif_portfolio


def timestamp_column_to_datetime(df, column):

    df[column] = df[column].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))
    df[column] = df[column].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date())
    return df

def dict_to_dataframe(dic):
    '''
    Convierte un dict en un dataframe
    '''
    df = pd.DataFrame.from_dict(dic, orient='index')
    return df

def get_mapping_instrumentos_internacionales():
    '''
    Obtenemos el listado de los nombre de los instrumentos equivalentes para riskamerica
    '''
    query = 'Select ltrim(rtrim(Codigo_Ins)) as Codigo_Ins, ltrim(rtrim(Isin)) as Isin from Mapping_BBL_BCS_diego'
    df = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    df.set_index(["Isin"], inplace=True)
    return df

def get_devengo_tasa_old(ins, tasa):
    
    cod = ins[:2]

    if cod == "FN":
        devengo = tasa/30

    elif cod in ['FU','F*']:
        devengo = tasa/360
    
    else:
        devengo = (1+tasa)**(1/365)-1

    return devengo

def get_devengo_tasa(df_cartera):

    df_cartera = df_cartera.reset_index()
    df_cartera['cod'] = df_cartera.codigo_ins.str[:2]
    
    conditions = [(df_cartera["cod"]=='FN'),(df_cartera["cod"]=='F*') | (df_cartera["cod"]=='FU')]
    devengo=[df_cartera["tasa_anterior"]/3000,df_cartera["tasa_anterior"]/36000]

    df_cartera["devengo"]=np.select(conditions,devengo,default=(1+df_cartera["tasa_anterior"]/100)**(1/365)-1)

    df_cartera = df_cartera.drop(columns=['cod'])
   
    return df_cartera

def show_files(host, username, password, port, path):
    '''
    Muestra los archivos que estan en una carpe especifica desde FTP 
    '''
    sftp = None
    ftp_open = False
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    list_files = sftp.listdir(path)
    transport.close()
    return list_files

def find_file(date, file_list):
    '''
    Encontramos los nombre de los archivos de una fecha dada
    '''
    aux_list = []
    date_yymmdd = fs.convert_date_all_together(date)
    #date_ddmmyy=str(date.strftime('%d%m%Y'))
    for file in file_list:
        if (date_yymmdd in file):
            aux_list.append(file)
    return aux_list

def download_files(server, user, port, password, file_list, svc):
    '''
    Descarga una lista de archivos a la caperta dada
    '''
    for file in file_list:
        curves_path = "./out/{}/{}".format(svc, file)
        output_path = ".\\{}".format(file)
        fs.download_data_sftp(host=server,
                              username=user,
                              password=password,
                              origin=curves_path,
                              destination=output_path,
                              port=port)
'''
def get_xml_svc(date):
   
    #Descarga los archivos de FTP y entrega los nombres de estos para una fecha dada
    server = "sftp.riskamerica.com"
    user = "AGF_Credicorp"
    port = 22
    password = "dX{\"4YjA"
    dic_list = ['SVC', 'SVC_Internacional']
    final_list = []
    for dic in dic_list:
        file_list = []
        aux_date = date
        while not file_list:
            path = "./out/{}".format(dic)
            file_list = show_files(host=server, username=user,
                                   password=password, port=port, path=path)
            file_list = find_file(aux_date, file_list)

            if not file_list:
                print('Los archivos de risk america de la carperta {} no estan actualizados para la fecha {}'.format(dic, aux_date))      
        final_list.append(file_list)
        download_files(server, user, port, password, file_list, dic)
    return final_list
'''

def get_xml_svc(date):
    
    #Descarga los archivos de FTP y entrega los nombres de estos para una fecha dada
    
    server = "sftp.riskamerica.com"
    user = "AGF_Credicorp"
    port = 22
    password = "dX{\"4YjA"
    dic_list = ['SVC', 'SVC_Internacional']
    final_list = []
    for dic in dic_list:
        file_list = []
        aux_date = date
        
        path = "./out/{}".format(dic)
        file_list = show_files(host=server, username=user,password=password, port=port, path=path)
        file_list = find_file(aux_date, file_list)
        
        if not file_list:
            print('Los archivos de risk america de la carperta {} no estan actualizados para la fecha {}'.format(dic, aux_date))      
        final_list.append(file_list)
        download_files(server, user, port, password, file_list, dic)
    return final_list




def append_without_duplicates(df1, df2):
    '''
    Eliminamos los duplicados de los dos dataframe
    '''

    df = df1.append(df2)
    df = df.reset_index().drop_duplicates(
        subset='index', keep='last').set_index('index')
    return df

def change_index(dic, df):
    '''
    Cambiamos los indices segun el diccionario. VER BIEN QUE DA
    '''
    as_list = df.index.tolist()
    for i in range(len(as_list)):
        if df.index.tolist()[i] in dic.index:
            as_list[i] = dic.loc[df.index.tolist()[i]]['Codigo_Ins']
            df.index = as_list
    return df

def compute_currency_prof(date):
    '''
    Devuelve el retorno por tipo de cambio para dos fechas
    '''
    list_currency = get_currency_types(date)
    dic_currency = {}
    for c in list_currency:
        dic_currency[c] = get_currency_prof(c, date)
    return dic_currency

def get_currency_types(date):
    '''
    Obtenemos los tipos de moneds de los instrumentos para una fecha
    ESTO SE PUEDE HACER MEJOR
    '''
   
    #date_anterior = fs.convert_date_to_string(get_fecha_habil_anterior(date))
    date_anterior =get_fecha_habil_anterior(date)
   
    #query = "select ltrim(rtrim(c.moneda)) as moneda from ZHIS_Carteras_Recursive as c INNER JOIN fondosir as f ON f.Codigo_fdo = c.codigo_fdo collate database_default where  fecha ='AUTODATE' and c.moneda not in ('$') and Tipo_instrumento in ('Bono Corporativo', 'Bono de Gobierno', 'Deposito') and f.shore= 'onshore' and f.estrategia in ('renta fija' , 'credito', 'retorno absoluto') GROUP BY c.moneda"
    query = "select ltrim(rtrim(c.moneda)) as moneda from ZHIS_Carteras_Recursive as c INNER JOIN fondosir as f ON f.Codigo_fdo = c.codigo_fdo collate database_default where  fecha ='AUTODATE' and Tipo_instrumento in ('Bono Corporativo', 'Bono de Gobierno', 'Deposito') and f.shore= 'onshore' and f.estrategia in ('renta fija' , 'credito', 'retorno absoluto') GROUP BY c.moneda"
    query = query.replace("AUTODATE", str(date_anterior))
  
    df = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)


    return df['moneda'].tolist()

def get_currency_prof(currency, date):
    '''
    Obtiene el retorno por tipo de cambio entre dos fechas
    '''
    retorno = 0
    try:
        c_1, c_0, days_dif = get_currency_value(date, currency)
        if currency == 'UF':
            retorno = ((c_1/c_0)-1)/days_dif
        elif currency=='ARS':
            retorno = ((c_0/c_1)-1)
        elif currency=="$":
            retorno=0
        else:
            retorno = ((c_1/c_0)-1)
    except:
        pass
    return retorno

def get_currency_value(date, name=None):
    '''
    Obtiene los valores de los currency para dos fechas. Cada vez que hay una nueva moneda hay que agregarlo a mano acá.
    '''
    days_dif = 0

    if name.strip() == 'US$':
        date_inc = fs.convert_date_to_string(date)
        date =  fs.convert_date_to_string(get_fecha_habil_posterior(date))
        #date = fs.convert_date_to_string(get_next_weekdays(date))
    else:
        #prev_day = get_previous_weekdays(date)
        prev_day = get_fecha_habil_anterior(date)
        date_inc = fs.convert_date_to_string(prev_day)
        #solo para calcular bien el devengo diario de la uf, los dias lunes
        days_dif = (date - prev_day).days

    dic_id = {'UF': 23, 'US$': 66, 'MX': 85, 'ARS':605}
    currency_id = dic_id[name]
    query = "Select Valor from Indices_Dinamica where Index_ID={} and  fecha in ('{}', '{}')".format(currency_id, date_inc, date)
    df = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    return df.loc[1]['Valor'], df.loc[0]['Valor'], days_dif

def get_dic_em():
    '''
    Obtiene un frame con los nombres de emisor igual al de los de riskamerica
    '''
    query = 'select ltrim(rtrim(Emisor)) as Emisor, ltrim(rtrim(Codigo_SVS)) as Codigo_SVS from EmisoresIIF'
    emisores = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    emisores.set_index(["Emisor"], inplace=True)
    return emisores

def get_nemo_date_to_string(date):
    '''
    Retorna la fecha en formato de string pormado ddmmyy.
    '''
    if date=="2018-08-7 ":
        date = "2018-08-07"
    date_string = str(fs.convert_string_to_date(date).strftime('%d%m%y'))
    return date_string

def comput_nemotecnico_depositos(carteras_depositos, perf_att=True):
    '''
    Creamos la matriz con los nemos correctos de los depositos
    '''

    list_empresas = ['BICECORP', 'TANNER SF']
    dic_emi = get_dic_em()
    dic_moneda = {'$': 'N', 'UF': 'U', 'US$': '*'}
    list_aux = []

    for i in carteras_depositos.index.tolist():
        
        fecha_vencimiento = get_nemo_date_to_string(carteras_depositos.loc[i]['fec_vcto'])
        moneda = dic_moneda[carteras_depositos.loc[i]['Moneda']]
        codigo_emisor_siga = carteras_depositos.loc[i]['codigo_emi']
        emisor = dic_emi.loc[codigo_emisor_siga]['Codigo_SVS']

        if carteras_depositos.loc[i]['codigo_emi'] in list_empresas:
          
          nemo = 'S'+moneda+emisor+fecha_vencimiento
          
        elif carteras_depositos.loc[i]['codigo_emi'] =='CENTRAL':
          
          nemo = 'BNPDBC'+fecha_vencimiento
            
        else:
          nemo = 'F'+moneda+emisor+'-'+fecha_vencimiento
          #print('el emisor de IIF '+codigo_emisor_siga+ 'no esta en la lista SVS. Moneda: '+moneda+ ' fue mapeado a ' +nemo)
        
        list_aux.append(nemo)

    carteras_depositos['Codigo_ins'] = pd.Series(list_aux, index=carteras_depositos.index)
    carteras_depositos.set_index(["Codigo_ins"], inplace=True)
    carteras_depositos = carteras_depositos.drop('codigo_emi', 1)
    carteras_depositos = carteras_depositos.drop('fec_vcto', 1)
    
    if perf_att:
        carteras_depositos = carteras_depositos.loc[:,['Fecha','codigo_fdo','Tipo_ins','Moneda','weight','duration']]
    else:
        carteras_depositos = carteras_depositos.loc[:,['codigo_fdo','Moneda','weight','precio']]
    
    return carteras_depositos

def download_international_data(date):
    '''
    Genera el dataframe final de la info de riskamerica
    '''
    #Obtenemos la lista de los archivos de la fecha correspondiente
    file_list = get_xml_svc(date)
    df_risk_int = None
    int_data_available=True

    if not file_list[1]:
        int_data_available=False
        

    #archivos internacionales
    for file in file_list[1]:
        if file !='99549940201805151010VALINTFI_2.xml':
            df_aux = compute_xml_int(file)
            if df_risk_int is not None:
                df_risk_int = append_without_duplicates(df_risk_int, df_aux)
            else:
                df_risk_int = df_aux

    if df_risk_int is not None:
        df_risk_int['tipo_SVC'] = 'Internacional'
    
    return df_risk_int, int_data_available


def compute_xml_int(xml_name):
    '''
    Genera un dataframe a partir de un xml de los archivos internacionales
    '''
    print(xml_name)
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

            dic_xml[nemo[0].get_text()] = {'precio': precio}
    df_internacional = dict_to_dataframe(dic_xml)
    

    return df_internacional

def download_national_data(date):
    '''
    Genera el dataframe final de la info de riskamerica
    '''
    #Obtenemos la lista de los archivos de la fecha correspondiente
    file_list = get_xml_svc(date)
    nat_data_available=True

    if not file_list[0]:
        nat_data_available=False
    
    df_risk_nat = None
    #primero obtenemos la info de los archivos nacionales
    for file in file_list[0]:
        df_aux = compute_xml_nat(file)
        if df_risk_nat is not None:
            df_risk_nat = append_without_duplicates(df_risk_nat, df_aux)
        else:
            df_risk_nat = df_aux

    df_risk_nat['tipo_SVC'] = 'Nacional'
  
    return df_risk_nat, nat_data_available

def compute_xml_nat(xml_name):
    '''
    Genera un dataframe a partir de un xml de los archivos nacionales
    '''
    print(xml_name)
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
                if float(cantidad[0].get_text())>0:
                    #print(nemo[0].get_text() + " " + tasa[0].get_text())
                    dic_xml[nemo[0].get_text()] = {'tasa': float(tasa[0].get_text()), 'duration': float(duration[0].get_text()), 'cantidad': float(cantidad[0].get_text()), 'precio': 100*float(monto[0].get_text())/float(cantidad[0].get_text())}
    df = dict_to_dataframe(dic_xml)
    
    return df

def check_currency(currency_ins, currency_fund, dic_currency):
    '''
    Chequeamos tipo de cambio, y si es distinto al fondo entrega el retorno de este
    '''
    if currency_ins != currency_fund:
        if (currency_ins=='ARS') & (currency_fund=='$') :
            retorno_currency = (1+dic_currency[currency_ins])*(1+dic_currency['US$'])-1
            return retorno_currency
        else:
            return dic_currency[currency_ins]
    else:
        return 0

def compute_yesterday_currency(date, list):
    '''
    Devuelve un diccionario con los valores de las monedas de ayer
    '''
    dic = {}
    for i in list:
        try:
            moneda_hoy, moneda_ayer, day_dif = get_currency_value(date, name=i)
        except:
            moneda_ayer = 0
        dic[i] = moneda_ayer
    return dic

def get_funds_currency():
    '''
    Obtenemos los nombres de los fondos a trabajar
    '''
    #query = "select ltrim(rtrim(codigo_fdo)) as codigo_fdo , ltrim(rtrim(moneda))  as moneda_fondo from fondosir where shore= 'onshore' and estrategia in ('renta fija' , 'credito', 'retorno absoluto')"
    query = "select ltrim(rtrim(codigo_fdo)) as codigo_fdo , ltrim(rtrim(moneda))  as moneda_fondo from fondosir where estrategia in ('renta fija' , 'credito', 'retorno absoluto')"
    df_funds_currency = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query) 

    df_funds_currency = df_funds_currency.set_index('codigo_fdo')
    return df_funds_currency

def get_funds_aum(date):

    path = ".\\Querys\\AUM.sql"
    query = fs.read_file(path=path).replace("AUTODATE", str(date))

    df_funds_aum = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query)

    df_funds_aum['AUM'] = df_funds_aum['AUM'].astype('float64')
    df_funds_aum = df_funds_aum.set_index('codigo_fdo')

    return df_funds_aum

def get_currencys(date):
    

    list_currency = get_currency_types(date)
    print(list_currency)
    data = {'currency':['$','US$'], 'paridad': ['$','US$'], 'r_moneda':[0,0]}
    df_monedas = pd.DataFrame(data)
    
    for currency in list_currency:
        df_aux = get_currency_profits(date,currency)
        df_monedas = df_monedas.append(df_aux)

    df_monedas = agrega_paridades_faltantes(df_monedas)
    df_monedas = df_monedas.reset_index(drop=True)

    return df_monedas

def get_currency_profits(date, currency):
    


    currency_id = dic_currencies[currency][0]
    paridad = dic_currencies[currency][1]

    valor_0, valor_1, delta_dias = get_currency_data(date, currency)

    if paridad=='$':
        if currency=='UF':
            retorno_moneda = (valor_1/valor_0-1)/delta_dias
        else:
            retorno_moneda = valor_1/valor_0-1
    else:
        retorno_moneda = valor_0/valor_1-1

    df_moneda = pd.DataFrame({'currency':[currency], 'paridad': [paridad], 'r_moneda':[retorno_moneda]})

    return df_moneda

def get_currency_data(date, currency):

    if currency.strip() == 'US$':
        date_0 = date
        date_1 =  get_fecha_habil_posterior(date)
    else:
        date_0 = get_fecha_habil_anterior(date)
        date_1 = date

    delta_dias = (date_1 - date_0).days

    currency_id = dic_currencies[currency][0]
    paridad = dic_currencies[currency][1]

    query = "Select valor from Indices_Dinamica where Index_ID={} and  fecha in ('{}', '{}')".format(currency_id, date_0, date_1)
    df_ccy_values = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    print(query)
    valor_0= df_ccy_values.loc[0]['valor']
    valor_1= df_ccy_values.loc[1]['valor']

    return valor_0, valor_1, delta_dias
   

def agrega_paridades_faltantes(df_monedas):

    list_aux = []

    r_usd = df_monedas.loc[(df_monedas['currency']=='US$') & (df_monedas['paridad']=='$')]['r_moneda'][0]
    df_nuevas_paridades = pd.DataFrame()

    for index, row in df_monedas.iterrows():

        currency = row['currency']
        paridad = row['paridad']
        retorno = row['r_moneda']
        
        if paridad=='$':
            #if currency=='US$':continue
            nueva_paridad='US$'
            retorno_nueva_paridad = (1+retorno)*(1+r_usd)**(-1)-1
        
        elif paridad=='US$':
            
            #if currency in ['$','US$']: continue
            
            nueva_paridad='$'
            retorno_nueva_paridad = (1+retorno)*(1+r_usd)-1

        list_aux.append([currency,nueva_paridad,retorno_nueva_paridad])


    #me falta agregar la paridad $-UF que es la que me falta
    r_uf_peso = df_monedas.loc[(df_monedas['currency']=='UF') & (df_monedas['paridad']=='$'),'r_moneda'].values[0]
    r_peso_uf = (1+r_uf_peso)**(-1)-1
    list_aux.append(['$','UF',r_peso_uf])

    df_paridades_faltantes = pd.DataFrame(list_aux)
    df_paridades_faltantes.columns = ['currency','paridad','r_moneda']

    df_monedas= df_monedas.append(df_paridades_faltantes)
    df_monedas = df_monedas.drop_duplicates(subset=['currency','paridad'])

    return df_monedas

def get_carteras_fondos(date_anterior):
    path_rf = ".\\Querys\\Bonos.sql"
    path_if = ".\\Querys\\Depositos.sql"
    query_rf = fs.read_file(path=path_rf).replace("AUTODATE", str(date_anterior))
    query_if = fs.read_file(path=path_if).replace("AUTODATE", str(date_anterior))

    cartera_fondos_rf = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query_rf)
    cartera_fondos_rf.set_index(["codigo_ins"], inplace=True)

    cartera_fondos_if = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query_if)


    cartera_fondos_if = comput_nemotecnico_depositos(cartera_fondos_if, perf_att=False)

    cartera_fondos_if.index.name='codigo_ins'
    cartera_fondos = cartera_fondos_rf.append(cartera_fondos_if)
    cartera_fondos['weight'] = cartera_fondos['weight'].astype('float64') 
    
    return cartera_fondos

def get_posiciones_forwards(date):

    path = ".\\Querys\\Forwards.sql"
    query = fs.read_file(path=path).replace("AUTODATE", str(date))

    df_forwards = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query)

    df_forwards = compute_forwards_net_positions(df_forwards)
    df_forwards = df_forwards.set_index('codigo_fdo')

    return df_forwards

def compute_forwards_net_positions(df_forwards):

    '''
    Obtiene las posiciones por fondo y moneda. Se asume que todos los forwards tienen una pata US$ o $
    '''
    dic = {'CLP': '$', 'USD': 'US$', 'UF':'UF', 'ARS' : 'ARS', 'PEN':'PEN'}
    df_posiciones_netas = pd.DataFrame(columns=['codigo_fdo', 'moneda_compra', 'moneda_venta','parity','monto_compra', 'monto_venta'])
    list_currency = df_forwards['moneda_compra'].unique()
    list_fund = df_forwards['codigo_fdo'].unique()

    #La posicion por fondo y por moneda
    for fund in list_fund:
        fund_forwards = df_forwards.loc[df_forwards['codigo_fdo'] == fund,:]

        
        
        for index, row in fund_forwards.iterrows():
            
            moneda_compra = row['moneda_compra']
            moneda_venta = row['moneda_venta']
            monto_compra = row['Monto_Compra']
            monto_venta = row['Monto_Venta']

            paridades_agregadas = df_posiciones_netas.loc[(df_posiciones_netas['codigo_fdo'] == fund),'parity'].tolist()
            parity = dic[moneda_compra]+"-"+dic[moneda_venta]
            parity_2 = dic[moneda_venta]+"-"+dic[moneda_compra]

            if parity_2 in paridades_agregadas:
                
                monto_compra_inicial = df_posiciones_netas.loc[ (df_posiciones_netas['codigo_fdo']==fund) & (df_posiciones_netas['parity']==parity_2), 'monto_compra'].values[0]
                monto_venta_inicial = df_posiciones_netas.loc[ (df_posiciones_netas['codigo_fdo']==fund) & (df_posiciones_netas['parity']==parity_2), 'monto_venta'].values[0]
               
                monto_compra_final = monto_compra_inicial - monto_venta
                monto_venta_final = monto_venta_inicial - monto_compra

                df_posiciones_netas.loc[ (df_posiciones_netas['codigo_fdo']==fund) & (df_posiciones_netas['parity']==parity_2) , 'monto_compra'] = monto_compra_final
                df_posiciones_netas.loc[ (df_posiciones_netas['codigo_fdo']==fund) & (df_posiciones_netas['parity']==parity_2), 'monto_venta'] = monto_venta_final
               

            else:
                df_aux = pd.DataFrame([[fund, dic[moneda_compra], dic[moneda_venta], parity, monto_compra, monto_venta]], columns=['codigo_fdo', 'moneda_compra','moneda_venta','parity','monto_compra', 'monto_venta'])
                df_posiciones_netas = df_posiciones_netas.append(df_aux)

    
    return df_posiciones_netas

def get_forwards_weights(date,df_forwards):

    usd_anterior, usd_spot, delta_dias = get_currency_data(date, 'US$')
    df_forwards.reset_index(inplace=True)
    df_forwards = df_forwards.set_index('codigo_fdo')

    for index, row in df_forwards.iterrows():
        moneda_compra = row['moneda_compra']
        moneda_venta = row['moneda_venta']
        moneda_fondo = row['moneda_fondo']
        monto_compra = row['monto_compra']
        monto_venta = row['monto_venta']
        patrimonio = row['Patrimonio']
       

        if moneda_compra == moneda_fondo:
            monto = monto_compra
        elif moneda_venta == moneda_venta:
            monto = monto_venta
        elif moneda_compra=='$' & moneda_fondo=='US$':
            monto = monto_compra/usd_anterior
        elif moneda_compra=='US$' & moneda_fondo=='$':
            monto = monto_compra * usd_anterior
        elif moneda_venta =='$' & moneda_fondo=='US$':
                monto = monto_venta/usd_anterior
        elif moneda_venta=='US$' & moneda_fondo=='$':
                monto = monto_venta * usd_anterior
        
        weight = monto/patrimonio
        df_forwards.loc[index,'weight_adj'] = weight


    return df_forwards

def get_leverage(date):

    path = ".\\Querys\\Leverage.sql"
    query = fs.read_file(path=path).replace("AUTODATE", str(date))

    df_leverage = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query)

    df_leverage['monto_pactado'] = df_leverage['monto_pactado'].astype('float64')
    df_leverage = df_leverage.set_index('codigo_fdo')

    return df_leverage

def get_liquidacion_transacciones(date):

    query_iif = "Select Fecha, nemotecnico as nemo, vende, compra, captacion as monto from TransaccionesIIF where fecha_liq = 'AUTODATE'"
    query_iif  = query_iif.replace("AUTODATE",str(date))
    query_irf = "Select Fecha, instrumento as nemo, vende, compra, monto from TransaccionesIRF where fecha_liq = 'AUTODATE'"
    query_irf  = query_irf.replace("AUTODATE",str(date))

    df_flujos_iif = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query_iif)

    df_flujos_irf = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query_irf)


    df_flujos = df_flujos_iif.append(df_flujos_irf)

    return df_flujos

def get_flujo_compras_ventas(date):

    df_transacciones = get_liquidacion_transacciones(date)
    df_compras = df_transacciones[df_transacciones.compra.notnull()].groupby(by= ['compra'], as_index = True).agg({'monto':'sum'})
    df_ventas = df_transacciones[df_transacciones.vende.notnull()].groupby(by = ['vende'], as_index = True).agg({'monto':'sum'})
    df_compras.rename(columns={'monto': 'monto_compras'}, inplace = True)
    df_ventas.rename(columns={'monto': 'monto_ventas'}, inplace = True)

    df_compra_venta = df_compras.join(df_ventas, how = 'outer')
    df_compra_venta.fillna(0, inplace = True)
    df_compra_venta['flujo_caja'] = df_compra_venta['monto_ventas'] - df_compra_venta['monto_compras']

    return df_compra_venta

def get_yield_UF(date, periodo):
    """
    Entrega la Yield de la UF para el periodo pedido
    """
    UF_fwd = get_UF_fwd(date, periodo)
    UF_spot = get_UF_spot(date)
    UF_return = (UF_fwd/UF_spot) - 1

    return UF_return


def get_UF_fwd(date, periodo):
    
    query = "SELECT Yield FROM ZHIS_RA_Curves WHERE Curve_name = 'NDF UF/CLP' AND date = '{}' AND tenor = {}".format(date, periodo)
    
    UF_fwd = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    return UF_fwd

def get_UF_spot(date):
    
    query = "SELECT Valor FROM Indices_Dinamica WHERE Index_Id = 23 AND Fecha = '{}'".format(date)
    
    UF_spot = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    return UF_spot



















    











