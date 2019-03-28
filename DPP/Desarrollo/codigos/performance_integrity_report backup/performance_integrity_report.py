"""
Created on Fri Jan 18 11:00:00 2018

@author: Francisca Martinez 
"""


import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import paramiko
import os

def rentabilidad(date):
    '''
    Genera la rentabilidad de los fondos
    '''
    df_risk_2 = compute_df_risk(date)
    #obtenemos la info de risk del dia anterios para sacar el valor cuota
    df_risk_1 = compute_df_risk(get_previous_weekdays(date))
    df_risk = compute_df_final(df_risk_2, df_risk_1[['valor', 'tasa', 'duration']], risk=True)
    df_sql = compute_df_sql(date)

    df = compute_df_final(df_sql, df_risk)
    rezagados = compute_rezagados(df_sql, df_risk)

    
    df_nacional = df.loc[df["tasa_2"].notnull(), ['moneda', 'codigo_fdo','weight','tasa_2','tasa_1', 'duration_1']]
    df_internacional = df.loc[df["precio_risk"].notnull(), ['moneda','codigo_fdo','weight','precio_risk','precio_sql', 'duration']]
    #recalculamos los pesos considerando el leverage
    df, df_aum, df_extra = compute_final_weight(date, df)
    df_retorno_fondos, df_retorno_instrumentos = comput_all_prof(df, date, df_aum, df_extra)
    return df_retorno_fondos, df_retorno_instrumentos, df_nacional, df_internacional, rezagados


def compute_rezagados(df_sql, df_risk):
    '''
    Obtenemos el dataframe final al cruzar ambos df
    '''
    lsuffix = '_sql'
    rsuffix = '_risk'
    rezagados_df= df_sql.join(df_risk, how='left', lsuffix=lsuffix, rsuffix=rsuffix)
    rezagados_df = rezagados_df.loc[rezagados_df["tasa_2"].isnull() & rezagados_df["precio_risk"].isnull()]
    rezagados_df = rezagados_df[["codigo_fdo","moneda","duration","weight"]]
    
    return(rezagados_df)


def compute_df_risk(date):
    '''
    Genera el dataframe final de la info de riskamerica
    '''
    #Obtenemos la lista de los archivos de la fecha correspondiente
    file_list = get_xml_svc(date)
    df_risk = None
    #primero obtenemos la info de los archivos nacionales
    for file in file_list[0]:
        df_aux = compute_xml_nat(file)
        if df_risk is not None:
            df_risk = compute_join_frame(df_risk, df_aux)
        else:
            df_risk = df_aux
    df_risk_int = None
    #Despues obtenemos la info de los archivos internacionales
    for file in file_list[1]:
        df_aux = compute_xml_int(file)
        if df_risk_int is not None:
            df_risk_int = compute_join_frame(df_risk_int, df_aux)
        else:
            df_risk_int = df_aux
    df_risk = df_risk.append(df_risk_int)
    return df_risk

def compute_join_frame(df1, df2):
    '''
    Eliminamos los duplicados de los dos dataframe
    '''

    df = df1.append(df2)
    df = df.reset_index().drop_duplicates(
        subset='index', keep='last').set_index('index')
    return df

def get_devengo_tasa(ins, tasa):
    
    cod = ins[:2]

    if cod == "FN":
        devengo = tasa/30

    elif cod in ['FU','F*']:
        devengo = tasa/360
    
    else:
        devengo = (1+tasa)**(1/365)-1

    return devengo



def compute_df_sql(date):
    '''
    Gemera el dataframe final de la info de sql, es decir, los depositos y los bonos
    '''
    df_sql = get_data('bond.txt', date, new_index='codigo_ins').append(
        compute_dep_frame(date))
    return df_sql

def compute_dep_frame(date):
    '''
    Genera un frame de los nombres de los depositos segu riskamerica
    '''
    df = get_data('dep.txt', date)
    df = comput_nemo(df)
    return df


def comput_nemo(df):
    '''
    Creamos la matriz con los nemos correctos de los depositos
    '''
    list_empresas = ['BICECORP', 'TANNER SF']
    dic_emi = get_dic_em()
    dic_moneda = {'$': 'N', 'UF': 'U', 'US$': '*'}
    list_aux = []
    for i in df.index.tolist():
        date = convert_date_to_string(df.loc[i]['fec_vcto'])
        moneda = dic_moneda[df.loc[i]['moneda']]
        emisor = dic_emi.loc[df.loc[i]['codigo_emi']]['Codigo_SVS']
        if df.loc[i]['codigo_emi'] in list_empresas:
            list_aux.append('S'+moneda+emisor+date)
        else:
            list_aux.append('F'+moneda+emisor+'-'+date)
    df['codigo_ins'] = pd. Series(list_aux, index=df.index)
    df.set_index(["codigo_ins"], inplace=True)
    df = delate_columns(df, ['codigo_emi'])
    return df


def compute_df_final(df_sql, df_risk, risk=None):
    '''
    Obtenemos el dataframe final al cruzar ambos df
    '''
    
    lsuffix = '_risk'
    rsuffix = '_sql'
    if risk is True:
        lsuffix = '_1'
        rsuffix = '_2'
    df = df_risk.join(df_sql, how='inner', lsuffix=lsuffix, rsuffix=rsuffix)
    return(df)


def compute_final_weight(date, df):
    '''
    Obtener los pesos finales, los cuales incluyen el apalancamiento
    '''
    leverage = get_data('leverage.txt', date, new_index='codigo_fdo')
    patrimonio = get_data('monto.txt', date, new_index='codigo_fdo')
    df_aum, df_extra = compute_aum(leverage, patrimonio)
    df = replace_weight(df, df_aum)
    return df, df_aum, df_extra

def compute_aum(df_asset, df_monto):
    '''
    obtiene el monto total de cada fondo, incluyendo las deudas
    '''

    df = df_monto.join(df_asset)
    df = df.fillna(0)
    aux = []
    df['AUM'] = df['monto']-df['balance']
    for fund in df.index.tolist():
        aux.append((-1*float(df.loc[fund]['balance'])
                    * 0.0026)/(float(df.loc[fund]['AUM'])*30))
    df['extra'] = pd.Series(aux, index=df.index)
    return df[['AUM']], df[['extra']]

def replace_weight(df_total, df_aum):
    '''
    re calculamos los pesos incluyendo el apalancamiento
    '''
    aux = []
    for index, row in df_total.iterrows():
        fdo = row['codigo_fdo']
        aux.append(row['monto']/df_aum.loc[fdo]['AUM'])
    df_total['weight'] = aux
    return df_total


def comput_all_prof(df, date, df_aum, df_extra):
    '''
    Calcula la rentabilidad de todos los fondos, entrega un dataframe espeicifo y otro general
    '''
    df_retorno_instrumentos = pd.DataFrame()
    df_retorno_fondos = pd.DataFrame(columns=['r_Fondo','Forwards','Instrumentos','Pacto'])
    list_fund, dic_currency, df_currency, df_fowards, dic_price, list_currency = compute_inputs(
        date)
    for fund in list_fund:
        #Obtenemos el retorno por fowards
        r_forwards = compute_rent_all_fowards(df_fowards, fund, df_aum.loc[fund]['AUM'], dic_price, list_currency, dic_currency)
        #Obtenemos el retorno por instrumento, y el general para el fdo
        df_ins, r_total_ins = compute_prof(fund, df, date, df_currency.loc[fund]['moneda'], dic_currency)
        df_retorno_instrumentos = df_retorno_instrumentos.append(df_ins)
        r_devengo_pactos = df_extra.loc[fund]['extra']
        #rentabilidad final
        r_fondo = r_total_ins + r_forwards + r_devengo_pactos
        df_retorno_fondos.loc[fund] = [r_fondo, r_forwards, r_total_ins, r_devengo_pactos]
    return df_retorno_fondos, df_retorno_instrumentos


def compute_inputs(date):
    '''
    Calculamos algunos inputs para los retornos
    '''
    #obtenemos la lista de los fondos presentes, y sus prespectivas monedas
    list_fund, df_currency = get_fund_names()
    #Obytenemos el retorno por moneda
    dic_currency = compute_currency_prof(date)
    #Obtenemos los fowards presentes, y los valores de las distintas monedas ayes
    aux_fwd = get_data('fowards.txt', date)
    df_fowards, list_currency = compute_fowards(aux_fwd)

    monedas_ayer = compute_yesterday_currency(date, list_currency)
    return list_fund, dic_currency, df_currency, df_fowards, monedas_ayer, list_currency


def compute_currency_prof(date):
    '''
    Devuelve el retorno por tipo de cambio para dos fechas
    '''
    list_currency = get_currency_types(date)
    dic_currency = {}
    for c in list_currency:
        dic_currency[c] = get_currency_prof(c, date)
    return dic_currency


def compute_fowards(df_fowards):
    '''
    Obtiene las posiciones por fondo y moneda
    '''
    dic = {'CLP': '$', 'USD': 'US$'}
    df = pd.DataFrame(columns=['codigo_fdo', 'moneda', 'monto'])
    list_currency = df_fowards['moneda_compra'].unique()
    list_fund = df_fowards['codigo_fdo'].unique()
    #La posicion por fondo y por moneda
    for fund in list_fund:
        for currency in list_currency:
            monto = 0
            for compra in df_fowards.loc[(df_fowards['moneda_compra'] == currency) & (df_fowards['codigo_fdo'] == fund)]['Monto_Compra'].tolist():
                monto += compra
            for venta in df_fowards.loc[(df_fowards['moneda_venta'] == currency) & (df_fowards['codigo_fdo'] == fund)]['Monto_Venta'].tolist():
                monto -= venta
            df_aux = pd.DataFrame([[fund, dic[currency], monto]], columns=['codigo_fdo', 'moneda', 'monto'])
            df = df.append(df_aux)
    return df, dic.values()


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


def compute_rent_all_fowards(df_fowards, fund, aum, dic_price, list_currency, dic_rentabilidad):
    '''
    Entrega la rentabilidad de todos los fowards segun moneda
    '''
    #print (df_fowards)
    foward = 0
    for currency in list_currency:
        aux = compute_rent_foward(df_fowards, fund, currency, dic_rentabilidad[currency], aum, dic_price[currency])
        foward += aux
    return foward


def compute_rent_foward(df_fowards, fund, moneda, rentabilidad,  aum, precio):
    '''
    Entraga la rentabilidad de los fowards para fondos dados
    '''
    
    fowards = 0
    try:
        aux = df_fowards.loc[(df_fowards['codigo_fdo'] == fund) & (df_fowards['moneda'] == moneda)]['monto'].tolist()
        fowards = ((aux[0] * precio)/(float(aum)))*float(rentabilidad)
    except:
        pass
    return fowards


def compute_prof(fund, df, date, fund_currency, dic_currency):
    '''
    Entrega la rentabilidad de un portafolio dado
    '''
    r_total_adj = 0
    r_tasas = 0
    r_reajuste = 0
    r_devengo = 0
    currency_return = 0
    
    df = df.fillna('No')
    df_ins = pd.DataFrame(columns=('moneda', 'fondo', 'weight', 'r_weighted','% r_total_ins', '% r_tasas', '% r_moneda','devengo_tasa_diario'))
    df = df.loc[df['codigo_fdo'] == fund]
    for ins in df.index.tolist():
        aux_currency = 0
        monto = float(df.loc[ins]['monto'])
        weight = float(df.loc[ins]['weight'])

        #Obtenemos el retorno para los instrumentos nacionales
        if df.loc[ins]['precio_risk'] is 'No':
            instrument_return, devengo_tasa, excepcion = compute_r(date, df, ins, nat=True)
            total_return_adj = instrument_return #Monto valorizado de riskamerica ya está en CLP
            moneda_ins = df.loc[ins]['moneda']

            if excepcion is True: # hay que agregar el devengo de la moneda
                 currency_return = check_currency(moneda_ins, fund_currency, dic_currency)
                 total_return_adj = compute_total_rent(instrument_return, currency_return)

            #En caso de que sea dia lunes se la resta el devengo de los dos dias
            if date.weekday() == 0:
                #print(ins)
                currency_return = check_currency(moneda_ins, fund_currency, dic_currency)
                total_return_adj =instrument_return -2*(currency_return + devengo_tasa)
            
            
        #Obtenemos lo mismo para los intrumentos internacionales, y ademas agregamos el la ganancia por tipo de cambio
        else:
            instrument_return, devengo_tasa, excepcion = compute_r(date, df, ins, nat=False)
            moneda_ins = df.loc[ins]['moneda']
            currency_return = check_currency(moneda_ins, fund_currency, dic_currency)
            total_return_adj = compute_total_rent(instrument_return, currency_return)

        total_return_adj_weighted = total_return_adj*weight
        total_tasas_weighted = instrument_return*weight
        total_reajustes_weighted = currency_return*weight
        total_devengo_weighted = devengo_tasa*weight
        
        r_total_adj += total_return_adj_weighted
        r_tasas += total_tasas_weighted
        r_reajuste += total_reajustes_weighted
        r_devengo += total_devengo_weighted

        df_ins.loc[ins] = [moneda_ins, fund, weight] + ['{0:.10f}'.format(k)for k in [total_return_adj_weighted,total_return_adj, instrument_return, currency_return, devengo_tasa]]
        #agregamos cada instrumento, y lo ponderamos por su peso en el fdo
        #df_ins.loc[ins] = ['{0:.10f}'.format(k*weight)for k in [total_return, instrument_return, currency_return, devengo_tasa]]+[fund, weight]
        
    return df_ins, r_total_adj


def compute_r(date, df, ins, nat):
    '''
    Devuelve el retorno de un instrumento internacional
    '''
    devengo_tasa = 0
    excepcion = False
    p1 = 'precio_sql'
    p2 = 'precio_risk'
    if nat is True:
        p1 = 'valor_1'
        p2 = 'valor_2'
        tasa_spot_risk = float(df.loc[ins]['tasa_2'])/100
        devengo_tasa = get_devengo_tasa(ins, tasa_spot_risk)
    valor_2 = float(df.loc[ins][p2])
    valor_1 = float(df.loc[ins][p1])
    instrument_return = (valor_2 / valor_1)-1
    
    if instrument_return <= -0.01 and nat is True:
        tasa_yesterday_risk = float(df.loc[ins]['tasa_1'])/100
        durmod= float(df.loc[ins]['duration_1'])/(1+tasa_yesterday_risk)
        instrument_return = -durmod*(tasa_spot_risk - tasa_yesterday_risk)
        print (ins)
        excepcion = True
        
    return instrument_return, devengo_tasa, excepcion


def compute_total_rent(r_ins, r_currency, devengo=0):
    '''
    Entega la rentabilidad total de un instrumento--> r del intrumento y de la moneda
    '''
    r_ins = (((1+r_ins)*(1+r_currency))-1)
    return r_ins


def check_currency(currency_ins, currency_fund, dic_currency):
    '''
    Chequeamos tipo de cambio, y si es distinto al fondo entrega el retorno de este
    '''
    if currency_ins != currency_fund:
        return dic_currency[currency_ins]
    else:
        return 0


'''OTRAS FUNCIONES'''


def dict_to_dataframe(dic):
    '''
    Convierte un dict en un dataframe
    '''
    df = pd.DataFrame.from_dict(dic, orient='index')
    return df


def delate_columns(df, list):
    '''
    Eliminamos de un dataframe las columnas de la lista
    '''
    for column in list:
        df.drop(column, axis=1, inplace=True)
    return df


def convert_date_to_string(date):
    '''
    Retorna la fecha en formato de string pormado ddmmyy.
    '''
    date_string = str(fs.convert_string_to_date(date).strftime('%d%m%y'))
    return date_string


def change_index(dic, df):
    '''
    Cambiamos los indices segun el diccionario
    '''
    as_list = df.index.tolist()
    for i in range(len(as_list)):
        if df.index.tolist()[i] in dic.index:
            as_list[i] = dic.loc[df.index.tolist()[i]]['Codigo_Ins']
            df.index = as_list
    return df


def get_previous_weekdays(date):
    '''
    Encontramos el dia habil anterior más cercano a una fecha dada
    '''
    date -= datetime.timedelta(days=1)
    # holyday = check_holyday(date)
    holyday = False
    weekend = check_weekend(date)
    while holyday is True or weekend is True:
        date -= datetime.timedelta(days=1)
        # holyday = check_holyday(date)
        weekend = check_weekend(date)
    return date


def get_next_weekdays(date):
    '''
    Encontramos el dia habil siguiente más cercano a una fecha dada
    '''
    date += datetime.timedelta(days=1)
    #holyday = check_holyday(date)
    holyday = False
    weekend = check_weekend(date)
    while holyday is True or weekend is True:
        date += datetime.timedelta(days=1)
        #holyday = check_holyday(date)
        weekend = check_weekend(date)
    return date


def check_weekend(date):
    '''
    Chequea si una fecha es fin de semana
    '''
    if date.weekday() == 5 or date.weekday() == 6:
        return True
    else:
        return False


def check_holyday(date):
    '''
    Chequeamos si una fecha es feriado en CHILE
    '''
    cal = Chile()
    if cal.is_working_day(date) is False:
        return True
    else:
        return False

'''TRABAJAMOS CON XML'''


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
                dic_xml[nemo[0].get_text()] = {'tasa': tasa[
                    0].get_text(), 'duration': duration[0].get_text(), 'valor': float(monto[0].get_text())/float(cantidad[0].get_text())}
    df = dict_to_dataframe(dic_xml)
    return df


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
            dic_xml[nemo[0].get_text()] = {'precio': tasa[
                0].get_text()}
    df = dict_to_dataframe(dic_xml)
    dic = get_dic_ins()
    df = change_index(dic, df)

    return df



'''TRABAJA CON  FTP'''

def get_xml_svc(date):
    '''
    Descarga los archivos de FTP y entrega los nombres de estos para una fecha dada
    '''
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
                print('Los archivos de risk america de la carperta {} no estan actualizados para la fecha {}'.format(
                    dic, aux_date))
            aux_date = get_previous_weekdays(aux_date)
        final_list.append(file_list)
        download_files(server, user, port, password, file_list, dic)
    return final_list


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
    date = fs.convert_date_all_together(date)
    for file in file_list:
        if date in file:
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

'''CONSULTAS SQL'''

def get_dic_em():
    '''
    Obtiene un frame con los nombres de emisor igual al de los de riskamerica
    '''
    query = 'select ltrim(rtrim(Emisor)) as Emisor, ltrim(rtrim(Codigo_SVS)) as Codigo_SVS from EmisoresIIF'
    df = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    df.set_index(["Emisor"], inplace=True)
    return df


def get_dic_ins():
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


def get_fund_names():
    '''
    Obtenemos los nombres de los fondos a trabajar
    '''
    query = "select ltrim(rtrim(codigo_fdo)) as codigo_fdo , ltrim(rtrim(moneda))  as moneda from fondosir where shore= 'onshore' and estrategia in ('renta fija' , 'credito', 'retorno absoluto') and codigo_fdo not in ('LIQUIDEZ')"
    df = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    df.set_index(['codigo_fdo'], inplace=True)
    return df.index.tolist(), df


def get_currency_types(date):
    '''
    Obtenemos los tipos de moneds de los instrumentos para una fecha
    '''
    date = fs.convert_date_to_string(get_previous_weekdays(date))
    query = open('./querys/currency.txt', 'r').read()
    query = query.replace('[DATE]', "'"+date+"'")
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
        date = fs.convert_date_to_string(get_next_weekdays(date))
    else:
        prev_day = get_previous_weekdays(date)
        date_inc = fs.convert_date_to_string(prev_day)
        #solo para calcular bien el devengo diario de la uf, los dias lunes
        days_dif = (date - prev_day).days

    dic_id = {'UF': 23, 'US$': 66, 'MX': 85}
    currency_id = dic_id[name]
    query = "Select Valor from Indices_Dinamica where Index_ID={} and  fecha in ('{}', '{}')".format(currency_id, date_inc, date)
    df = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    return df.loc[1]['Valor'], df.loc[0]['Valor'], days_dif


def get_data(name, date, new_index=False):
    '''
    Obtiene los leverage de los fondos
    '''
    date = fs.convert_date_to_string(get_previous_weekdays(date))
    query = open('./querys/{}'.format(name), 'r').read()
    query = query.replace('[DATE]', "'"+date+"'")
    df = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    if new_index is not False:
        df.set_index([new_index], inplace=True)
    return df


def check_risk_sql(df_sql, df_risk):
    '''
    Chequeamos que a los datos de risk no le falte ninguno de los de la database de sql
    '''
    aux_list = []
    sql_index = df_sql.index
    risk_index = df_risk.index
    last_ins = None
    for ins in sql_index:
        if last_ins != ins:
            if ins not in risk_index:
                aux_list.append(ins)
                last_ins = ins
    return aux_list


'''GUARDAR EN EXCEL Y MANDAR CORREO'''


def generar_excel(df_retorno_fondos, df_retorno_instrumentos, df_nacional, df_internacional, rezagados,name):
   
    #PARCHE, saco de los dataframes el fondo liquidez, se comsulta en muchos lados asi que es más fácil sacarlo por aca
    df_nacional = df_nacional.loc[df_nacional["codigo_fdo"]!="LIQUIDEZ"]
    rezagados = rezagados.loc[rezagados["codigo_fdo"]!="LIQUIDEZ"]


    wb = fs.open_workbook("rentabilidad.xlsx", True, True)
    fs.clear_sheet_xl(wb, "Resumen_fondos")
    fs.clear_sheet_xl(wb, "Instrumentos")
    fs.clear_sheet_xl(wb, "Nacional_Market")
    fs.clear_sheet_xl(wb, "International_Market")
    fs.clear_sheet_xl(wb, "rezagados")
    fs.paste_val_xl(wb, "Resumen_fondos", 1, 1, df_retorno_fondos)
    fs.paste_val_xl(wb, "Instrumentos", 1, 1, df_retorno_instrumentos)
    fs.paste_val_xl(wb, "Nacional_Market", 1, 1, df_nacional)
    fs.paste_val_xl(wb, "International_market", 1, 1, df_internacional)
    fs.paste_val_xl(wb, "rezagados", 1, 1, rezagados)
    wb.save()
    wb.close()

def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'red' if val < 0 else 'black'
    return 'color: %s' % color


def send_mail(df_retorno_fondos, df2, df_nacional, df_internacional, rezagados, date, filename):
    '''
    Envia el mail. 
    '''

    subject = "Rentabilidad {}".format(date)
    df_retorno_fondos = (df_retorno_fondos*10000).round(1)
    
    df_styled = df_retorno_fondos.style\
    .applymap(color_negative_red)\
    .set_caption('Estimación rentabilidad '+str(date) + "  [bps]")\
    .format("{:.2}")\
    .set_properties(**{'text-align': 'center'})\
    .bar(subset='r_Fondo', color='#d65f5f')


    # Render the styled df in html
    body = df_styled.render()
    #mails =  ['dposch@credicorpcapital.com']
    
    
    mails = ["fsuarez@credicorpcapital.com", "jparaujo@credicorpcapital.com",
              "dposch@credicorpcapital.com", "rbarros@credicorpcapital.com",
              "adarquea@credicorpcapital.com", "adarquea@credicorpcapital.com",
              "pvaldivieso@credicorpcapital.com"]
    
    
    
    path = fs.get_self_path()
    datefile = str(date).replace('-','')+".xlsx"
    old_path = path+filename
    new_path = path+datefile
    os.rename(old_path, new_path)

    attachment_paths = [new_path]
    fs.send_mail_attach(subject, body, mails, attachment_paths, html=True)
    os.rename(new_path, old_path)


date = datetime.date.today()
date = datetime.date(2018, 2, 15)
print("computing performance...")
df_retorno_fondos, df_retorno_instrumentos, df_nacional, df_internacional, rezagados = rentabilidad(date)
print("sending mail...")
filename='rentabilidad.xlsx'
generar_excel(df_retorno_fondos, df_retorno_instrumentos, df_nacional, df_internacional, rezagados, filename)
send_mail(df_retorno_fondos, df_retorno_instrumentos, df_nacional, df_internacional, rezagados, date, filename)
