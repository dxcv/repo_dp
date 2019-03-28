import sys
sys.path.insert(0,'../libreria/')
sys.path.insert(0,'../portfolio_analytics/utiles')
import os
import datetime as dt
import libreria_fdo as fs
import pandas as pd
import utiles
from tia.bbg import v3api
from sqlalchemy import create_engine, types



def is_weekend(date_inic, date_fin):
    days = fs.get_dates_between(date_inic, date_fin)
    if len(days) == 4:
        return True
    return False

def resource_path(relative_path):
    '''
    Retorna el path absoluto del path entregado.
    '''
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_ndays_from_date(days, date_string):
    '''
    Retorna la fecha n dias desde hoy.
    '''
    date = fs.convert_string_to_date(date_string) + dt.timedelta( days = days )
    date=str(date.strftime('%Y-%m-%d'))
    return date

def timestamp_to_string(timestamp):
    date = timestamp.to_pydatetime()
    return date.strftime('%Y-%m-%d')

def insert_into_database(df):

    df = df[['Instrumento','moneda','Fecha_corte','Cantidad_corte','Vencimiento']]

    #tuplas = df.to_records().tolist()
    #print(tuplas)
    #conn = fs.connect_database_user (server = "Puyehue", database = "MesaInversiones", username = "usrConsultaComercial", password = "Comercial1w")
    #cursor = conn.cursor()
    #cursor.executemany("INSERT INTO RF_Cupones (Instrumento, moneda, Fecha_corte, Cantidad_corte, Vencimiento) VALUES (%s,%s,%s,%d,%s)",tuplas)

    #conn.commit()
    #fs.disconnect_database(conn)

    engine = create_engine('mssql+pymssql://'+ "usrConsultaComercial" + ':' + "Comercial1w" +'@' + "Puyehue" + '/' + "MesaInversiones")

    con = engine.connect()
   
    df.to_sql('RF_Cupones', con, if_exists = 'replace', index = False, schema = 'dbo',
                    dtype = {'Instrumento': types.VARCHAR(length=100), 'moneda': types.VARCHAR(length=100), 'Fecha_corte': types.DATE(),
                            'Cantidad_corte': types.FLOAT(), 'Vencimiento': types.DATE()})
    con.close()

def setFrameSql(server, database, dataframe, username, password):
    '''
    Actualiza la tabla de SQL a partir de un Dataframe
    '''
    # engine = create_engine('mssql+pymssql://' + server + '/' + database)
    engine = create_engine('mssql+pymssql://'+ username + ':' + password +'@' + server + '/' + database)

    con = engine.connect()
   
    dataframe.to_sql('RF_Cupones', con, if_exists = 'replace', index = False, schema = 'dbo',
                    dtype = {'Instrumento': types.VARCHAR(length=100), 'moneda': types.VARCHAR(length=100), 'Fecha_corte': types.DATE(),
                            'Cantidad_corte': types.FLOAT(), 'Vencimiento': types.DATE()})
    con.close()

def nemo_depo(emisor, moneda, fecha, frame_emisores):
    df_emisor = frame_emisores
    nemo = ''
    pre = ''
    if emisor.strip() == 'CENTRAL':
        nemo = 'BNPDBC'
        pre = ''
    else:
        try:
            for j in df_emisor.loc[(df_emisor['Emisor'] == emisor)].iterrows():
                nemo = j[1]['Codigo_SVS'].strip()
            if not nemo:
                return ''
        except:
            print('No se encuentra emisor: {}').format(emisor)
            return ''
        if moneda == '$':
            pre = 'FN'
        elif moneda == 'UF':
            pre = 'FU'
        elif moneda == 'US$':
            pre = 'F*'

    fecha_nemo = '-' + fecha[8:10] + fecha[5:7] + fecha[2:4]
    
    nemo_final = pre + nemo 
    nemo_fecha = pre + nemo + fecha_nemo
    return nemo_fecha        

def eliminar_bonos_vencidos():
    today = str(dt.datetime.now().date())
    #today = dt.datetime.now()
    query_cupones = "SELECT * FROM [MesaInversiones].[dbo].[RF_Cupones]" ##WHERE [Fecha_corte] <= '{}' OR [Vencimiento] <= '{}'".format(today, today)
    df_cupones = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_cupones)
    indices = df_cupones[(df_cupones['Fecha_corte'] <= today) | (df_cupones['Vencimiento'] <= today)].index.tolist()
    print('----------------indices----------------')
    print(len(indices))
    df_cupones = df_cupones.drop(indices)
    insert_into_database(df_cupones)
    #setFrameSql("Puyehue", "MesaInversiones", df_cupones, "usrConsultaComercial", "Comercial1w")

def refreh_sql():
    
    
    funds  = utiles.get_FI_funds()
    df_bonos = utiles.get_updated_RFI(funds)
    df_depositos = utiles.get_updated_IIF(funds)

    query_cupones = "SELECT * FROM [MesaInversiones].[dbo].[RF_Cupones]"
    df_cupones = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_cupones)
    cupones = df_cupones['Instrumento'].values.tolist()
    print('----------------cupones----------------')
    print(len(cupones))
    df_emisor = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", "SELECT RTRIM(LTRIM([Emisor])) AS [Emisor], [Codigo_SVS] FROM EmisoresIIF")
    set_bonos = {row[1]['codigo_ins'].strip() + ' Corp' for row in df_bonos.iterrows()}
    print(set_bonos)
    set_depositos = {nemo_depo(row[1]['codigo_emi'].strip(), row[1]['moneda'].strip(), row[1]['fec_vcto'].strip(), df_emisor) + ' M-Mkt': [row[1]['fec_vcto'], row[1]['moneda']] for row in df_depositos.iterrows()}
    

    LocalTerminal = v3api.Terminal('localhost', 8194)

    fails = []
    for instrumento in set_bonos:
        if instrumento[:-5] not in cupones:
            try:
                final_row = []
                response = LocalTerminal.get_reference_data(instrumento, ['TRADE_CRNCY', 'NEXT_CASH_FLOW_DT', 'NEXT_CASH_FLOW', 'MATURITY'])
                bloombergData = response.as_frame().replace('nan',0)
                final_row.append(instrumento[:-5])
                final_row.append(bloombergData.iloc[0]['TRADE_CRNCY'])
                final_row.append(timestamp_to_string(bloombergData.iloc[0]['NEXT_CASH_FLOW_DT']))
                final_row.append(bloombergData.iloc[0]['NEXT_CASH_FLOW'])
                final_row.append(timestamp_to_string(bloombergData.iloc[0]['MATURITY']))
                df_cupones = df_cupones.append(pd.DataFrame([final_row], columns=['Instrumento', 'moneda', 'Fecha_corte', 'Cantidad_corte', 'Vencimiento']),
                            ignore_index=True)
            except Exception as e:
                print(e)
                print(instrumento)
                fails.append(instrumento)

    for instrumento in set_depositos:
        if instrumento[:-6] not in cupones:
            try:
                final_row = []
                final_row.append(instrumento[:-6])
                moneda = set_depositos[instrumento][1].strip()
                if moneda == '$':
                    moneda = 'CLP'
                elif moneda == 'US$':
                    moneda = 'USD'
                elif moneda == 'UF':
                    moneda = 'CLF'
                final_row.append(moneda)
                final_row.append(None)
                final_row.append(1000000)
                final_row.append(set_depositos[instrumento][0])
                df_cupones = df_cupones.append(pd.DataFrame([final_row], columns=['Instrumento', 'moneda', 'Fecha_corte', 'Cantidad_corte', 'Vencimiento']),
                            ignore_index=True)
            except Exception as e:
                print(e)
                print(instrumento)
                fails.append(instrumento)

    insert_into_database(df_cupones)
    print('----------------fails----------------')
    print(len(fails))
    print(fails)


    
eliminar_bonos_vencidos()
refreh_sql()


    
