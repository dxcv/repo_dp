import sys
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

    
    df.set_index(['Instrumento'], inplace=True)
    df = df[['moneda','Fecha_corte','Cantidad_corte','Vencimiento']]

    print(df)
    
    
    df['Fecha_corte'] = pd.to_datetime(df['Fecha_corte'])
    df['Vencimiento'] = pd.to_datetime(df['Vencimiento'])

    
    
    
    
    tuplas = df.to_records().tolist()
    print(tuplas)
    conn = fs.connect_database_user (server = "Puyehue", database = "MesaInversiones", username = "usrConsultaComercial", password = "Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO RF_Cupones (Instrumento, moneda, Fecha_corte, Cantidad_corte, Vencimiento) VALUES (%s,%s,%s,%d,%s)",tuplas)

    conn.commit()
    fs.disconnect_database(conn)

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
    yesterday = fs.get_prev_weekday(str(dt.datetime.now().date()))

    funds  = utiles.get_FI_funds()
    df_bonos = utiles.get_updated_RFI(funds)
    df_depositos = utiles.get_updated_IIF(funds)


    #query_f = "SELECT Codigo_Fdo FROM [MesaInversiones].[dbo].[FondosIR]"
    #df_fondos = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_f)
    #query_c = "SELECT Codigo_Fdo FROM [MesaInversiones].[dbo].[Perfil Clientes]"
    #df_carteras = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_c)
    #fondos =  df_fondos['Codigo_Fdo'].values.tolist()
    #carteras = df_carteras['Codigo_Fdo'].values.tolist()
    #df_f = df.loc[(df['codigo_fdo'].isin(fondos))]
    #df_c = df.loc[(df['codigo_fdo'].isin(carteras))]

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

def generar_resumen_fondos():
    yesterday = fs.get_prev_weekday(str(dt.datetime.now().date()))
    tomorrow = fs.get_next_weekday(str(dt.datetime.now().date()))
    today = str(dt.datetime.now().date())
    fondos = ['SPREADCORP', 'DEUDA CORP', 'DEUDA 360', 'LIQUIDEZ', 'M_MARKET', 'MACRO CLP3', 'MACRO 1.5', 'RENTA', 'IMT E-PLUS']

    query_cupones = "SELECT * FROM [MesaInversiones].[dbo].[RF_Cupones]"
    df_cupones = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_cupones)

    query_fondos = ("SELECT [codigo_ins], RTRIM(LTRIM([codigo_fdo])) As [codigo_fdo], [nominal], [codigo_emi], [moneda], [fec_vcto] FROM [MesaInversiones].[dbo].[ZHIS_Carteras_Main] WHERE [fecha] = '{}' AND [codigo_fdo] in ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')").format(  ##(Tipo_Instrumento IN ('Bono Corporativo', 'Deposito', 'Bono de Gobierno', 'Letra Hipotecaria', 'Factura', 'RF LATAM') OR Tipo_Instrumento is NULL)").format(
        yesterday, 'SPREADCORP', 'DEUDA CORP', 'DEUDA 360', 'LIQUIDEZ', 'M_MARKET', 'MACRO CLP3', 'MACRO 1.5', 'RENTA', 'IMT E-PLUS')
    df_fondos = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_fondos)
    ### Agregarle los fines de semana
    if not is_weekend(today, tomorrow):
        cupones = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Fecha_corte'] == tomorrow and row[1]['Vencimiento'] != tomorrow}
        vencimientos_dep = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Vencimiento'] == tomorrow and row[1]['Fecha_corte'] != row[1]['Vencimiento']}
        vencimientos_bon = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Vencimiento'] == tomorrow and row[1]['Fecha_corte'] == row[1]['Vencimiento']}
    else:
        sabado = fs.get_next_day(today)
        domingo = fs.get_next_day(sabado)
        cupones = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Fecha_corte'] == tomorrow and row[1]['Vencimiento'] != tomorrow)
                or (row[1]['Fecha_corte'] == sabado and row[1]['Vencimiento'] != sabado) or (row[1]['Fecha_corte'] == domingo and row[1]['Vencimiento'] != domingo)}
        vencimientos_dep = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Vencimiento'] == tomorrow or row[1]['Vencimiento'] == sabado
                or row[1]['Vencimiento'] == domingo) and (row[1]['Fecha_corte'] != row[1]['Vencimiento'])}
        vencimientos_bon = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Vencimiento'] == tomorrow or row[1]['Vencimiento'] == sabado
                or row[1]['Vencimiento'] == domingo) and (row[1]['Fecha_corte'] == row[1]['Vencimiento'])}
    df_excel = pd.DataFrame(columns=['Fondo', 'Cupones', 'Vencimiento D', 'Vencimiento B', 'Total'])

    df_emisor = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", "SELECT RTRIM(LTRIM([Emisor])) AS [Emisor], [Codigo_SVS] FROM EmisoresIIF")

    for fondo in fondos:
        df_fondo = df_fondos[df_fondos['codigo_fdo'] == fondo]
        total_recibido_vencimiento_dep = 0
        total_recibido_vencimiento_bon = 0
        total_recibido_cupones = 0
        vencimiento_recibido = False
        for row in df_fondo.iterrows():
            instrumento = row[1]['codigo_ins'].strip()
            if 'PAGARE' in instrumento or 'PDBC' in instrumento:
                instrumento = nemo_depo(row[1]['codigo_emi'].strip(), row[1]['moneda'].strip(), row[1]['fec_vcto'].strip(), df_emisor)
            if instrumento in vencimientos_dep:
                print(instrumento)
                print(float(row[1]['nominal']))
                total_recibido_vencimiento_dep += ((vencimientos_dep[instrumento] / 1000000) * float(row[1]['nominal']))
                vencimiento_recibido = True
            elif instrumento in vencimientos_bon:
                print(instrumento)
                print(float(row[1]['nominal']))
                total_recibido_vencimiento_bon += ((vencimientos_bon[instrumento] / 1000000) * float(row[1]['nominal']))
                vencimiento_recibido = True
            elif instrumento in cupones:
                total_recibido_cupones += ((cupones[instrumento] / 1000000) * row[1]['nominal'])
                print(total_recibido_cupones)
        excel_row = [fondo, total_recibido_cupones, total_recibido_vencimiento_dep, total_recibido_vencimiento_bon, total_recibido_cupones + total_recibido_vencimiento_dep + total_recibido_vencimiento_bon]
        df_excel = df_excel.append(pd.DataFrame([excel_row], columns=['Fondo', 'Cupones', 'Vencimiento D', 'Vencimiento B', 'Total']),
                    ignore_index=True)
        print(excel_row)
        print('----------------------------------------------')

    excel = resource_path("Cupones_" + tomorrow + ".xlsx")
    
    writer = pd.ExcelWriter(excel)
    df_excel.to_excel(writer, sheet_name='Hoja1', startrow=1, startcol=1)
    writer.sheets['Hoja1'].column_dimensions['C'].width = 13
    writer.sheets['Hoja1'].column_dimensions['D'].width = 12
    writer.sheets['Hoja1'].column_dimensions['E'].width = 12
    writer.sheets['Hoja1'].column_dimensions['F'].width = 12
    writer.sheets['Hoja1'].column_dimensions['G'].width = 15
    writer.save()
    writer.close()
    fs.export_sheet_pdf_jp(0, fs.get_self_path()+"Cupones_" + tomorrow + ".xlsx", fs.get_self_path()+"Informe_cupones_" + tomorrow + ".pdf")


def generar_resumen_carteras():
    byesterday = fs.get_prev_weekday(fs.get_prev_weekday(str(dt.datetime.now().date())))
    tomorrow = fs.get_next_weekday(str(dt.datetime.now().date()))
    today = str(dt.datetime.now().date())
    query_c = "SELECT Codigo_Fdo FROM [MesaInversiones].[dbo].[Perfil Clientes]"
    df_carteras = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_c)
    carteras = df_carteras['Codigo_Fdo'].values.tolist()

    query_cupones = "SELECT * FROM [MesaInversiones].[dbo].[RF_Cupones]"
    df_cupones = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_cupones)

    query_carteras = ("SELECT [codigo_ins], RTRIM(LTRIM([codigo_fdo])) AS [codigo_fdo], [nominal], [codigo_emi], [moneda], [fec_vcto] FROM [MesaInversiones].[dbo].[ZHIS_Carteras_Main] WHERE [fecha] = '{}' AND [codigo_fdo] in ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')").format(  ##(Tipo_Instrumento IN ('Bono Corporativo', 'Deposito', 'Bono de Gobierno', 'Letra Hipotecaria', 'Factura', 'RF LATAM') OR Tipo_Instrumento is NULL)").format(
        byesterday, 'SPREADCORP', 'DEUDA CORP', 'DEUDA 360', 'LIQUIDEZ', 'M_MARKET', 'MACRO CLP3', 'MACRO 1.5', 'RENTA', 'IMT E-PLUS')
    df_carteras = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_carteras)

    ### Agregarle los fines de semana
    if not is_weekend(today, tomorrow):
        cupones = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Fecha_corte'] == tomorrow and row[1]['Vencimiento'] != tomorrow}
        vencimientos = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Vencimiento'] == tomorrow}
    else:
        sabado = fs.get_next_day(today)
        domingo = fs.get_next_day(sabado)
        cupones = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Fecha_corte'] == tomorrow and row[1]['Vencimiento'] != tomorrow)
                or (row[1]['Fecha_corte'] == sabado and row[1]['Vencimiento'] != sabado) or (row[1]['Fecha_corte'] == domingo and row[1]['Vencimiento'] != domingo)}
        vencimientos = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Vencimiento'] == tomorrow) or (row[1]['Vencimiento'] == sabado)
                or (row[1]['Vencimiento'] == domingo)}

    df_excel = pd.DataFrame(columns=['Cartera', 'Cupones', 'Vencimiento', 'Total', 'R Vencimiento'])

    df_emisor = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", "SELECT RTRIM(LTRIM([Emisor])) AS [Emisor], [Codigo_SVS] FROM EmisoresIIF")

    for cartera in carteras:
        df_cartera = df_carteras[df_carteras['codigo_fdo'] == cartera]
        total_recibido_vencimiento = 0
        total_recibido_cupones = 0
        vencimiento_recibido = False
        for row in df_cartera.iterrows():            
            instrumento = row[1]['codigo_ins'].strip()
            if 'PAGARE' in instrumento or 'PDBC' in instrumento:
                instrumento = nemo_depo(row[1]['codigo_emi'].strip(), row[1]['moneda'].strip(), row[1]['fec_vcto'].strip(), df_emisor)
            if instrumento in vencimientos:
                print(instrumento)
                print(float(row[1]['nominal']))
                total_recibido_vencimiento += ((vencimientos[instrumento] / 1000000) * float(row[1]['nominal']))
                vencimiento_recibido = True
            elif instrumento in cupones:
                total_recibido_cupones += ((cupones[instrumento] / 1000000) * row[1]['nominal'])
        excel_row = [cartera, total_recibido_cupones, total_recibido_vencimiento,  total_recibido_cupones + total_recibido_vencimiento, vencimiento_recibido]
        df_excel = df_excel.append(pd.DataFrame([excel_row], columns=['Cartera', 'Cupones', 'Vencimiento', 'Total', 'R Vencimiento']),
                    ignore_index=True)
        print(excel_row)
        print('----------------------------------------------')

    excel = resource_path("Cupones_carteras_" + tomorrow + ".xlsx")
    writer = pd.ExcelWriter(excel)
    df_excel.to_excel(writer, sheet_name='Hoja1', startrow=1, startcol=1)
    writer.sheets['Hoja1'].column_dimensions['C'].width = 15
    writer.sheets['Hoja1'].column_dimensions['D'].width = 15
    writer.sheets['Hoja1'].column_dimensions['E'].width = 15
    writer.sheets['Hoja1'].column_dimensions['F'].width = 15
    writer.sheets['Hoja1'].column_dimensions['G'].width = 15
    writer.save()
    writer.close()
    fs.export_sheet_pdf_jp(0, fs.get_self_path()+"Cupones_carteras_" + tomorrow + ".xlsx", fs.get_self_path()+"Informe_cupones_carteras_" + tomorrow + ".pdf")



eliminar_bonos_vencidos()
refreh_sql()
generar_resumen_fondos()
generar_resumen_carteras()

    
