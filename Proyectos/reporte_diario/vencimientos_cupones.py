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


def export_sheet_pdf_jp(sheet_index, path_in, path_out):
    '''
    Exporta una hoja de Excel en PDF. 
    '''
    xlApp = client.Dispatch("Excel.Application")
    books = xlApp.Workbooks.Open(path_in)
    ws = books.Worksheets[sheet_index]
    ws.ExportAsFixedFormat(0, path_out)
    books.Close(True)


def get_vencimientos_cupones_fondos():
    
    yesterday = fs.get_prev_weekday(str(dt.datetime.now().date()))
    today = str(dt.datetime.now().date())
    
    str_fondos = utiles.get_FI_funds()
    arr_fondos = str_fondos.split(",")


    query_cupones = "SELECT * FROM [MesaInversiones].[dbo].[RF_Cupones]"
    df_cupones = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_cupones)

    query_fondos = ("SELECT [codigo_ins], RTRIM(LTRIM([codigo_fdo])) As [codigo_fdo], [nominal], [codigo_emi], [moneda], [fec_vcto] FROM [MesaInversiones].[dbo].[ZHIS_Carteras_Main] WHERE [fecha] = '{}' AND [codigo_fdo] in ("+str_fondos+")").format(yesterday)
    df_fondos = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_fondos)
    ### Agregarle los fines de semana
    if not is_weekend(yesterday, today):
        cupones = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Fecha_corte'] == today and row[1]['Vencimiento'] != today}
        vencimientos_dep = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Vencimiento'] == today and row[1]['Fecha_corte'] != row[1]['Vencimiento']}
        vencimientos_bon = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Vencimiento'] == today and row[1]['Fecha_corte'] == row[1]['Vencimiento']}
    else:
        sabado = fs.get_next_day(yesterday)
        domingo = fs.get_next_day(sabado)
        cupones = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Fecha_corte'] == today and row[1]['Vencimiento'] != today)
                or (row[1]['Fecha_corte'] == sabado and row[1]['Vencimiento'] != sabado) or (row[1]['Fecha_corte'] == domingo and row[1]['Vencimiento'] != domingo)}
        vencimientos_dep = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Vencimiento'] == today or row[1]['Vencimiento'] == sabado
                or row[1]['Vencimiento'] == domingo) and (row[1]['Fecha_corte'] != row[1]['Vencimiento'])}
        vencimientos_bon = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Vencimiento'] == today or row[1]['Vencimiento'] == sabado
                or row[1]['Vencimiento'] == domingo) and (row[1]['Fecha_corte'] == row[1]['Vencimiento'])}
    df_vencimiento_cupones = pd.DataFrame(columns=['fondo', 'cupones', 'vencimiento_depos', 'vencimiento_bonos', 'total'])

    df_emisor = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", "SELECT RTRIM(LTRIM([Emisor])) AS [Emisor], [Codigo_SVS] FROM EmisoresIIF")

    for fondo in arr_fondos:
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
        df_vencimiento_cupones = df_vencimiento_cupones.append(pd.DataFrame([excel_row], columns=['fondo', 'cupones', 'vencimiento_depos', 'vencimiento_bonos', 'total']),
                    ignore_index=True)

    df_vencimiento_cupones['fondo'] = df_vencimiento_cupones['fondo'].map(lambda x: x.strip(" ").strip("'"))    
    df_vencimiento_cupones.set_index('fondo', inplace = True)

    fs.print_full(df_vencimiento_cupones)

    return df_vencimiento_cupones
    
   

def get_vencimientos_cupones_carteras():
    
    yesterday = fs.get_prev_weekday(fs.get_prev_weekday(str(dt.datetime.now().date())))
    
    today = str(dt.datetime.now().date())
    query_c = "SELECT Codigo_Fdo FROM [MesaInversiones].[dbo].[Perfil Clientes]"
    df_carteras = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_c)
    carteras = df_carteras['Codigo_Fdo'].values.tolist()

    query_cupones = "SELECT * FROM [MesaInversiones].[dbo].[RF_Cupones]"
    df_cupones = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_cupones)

    query_carteras = ("SELECT [codigo_ins], RTRIM(LTRIM([codigo_fdo])) AS [codigo_fdo], [nominal], [codigo_emi], [moneda], [fec_vcto] FROM [MesaInversiones].[dbo].[ZHIS_Carteras_Main] WHERE [fecha] = '{}' AND [codigo_fdo] in ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')").format(  ##(Tipo_Instrumento IN ('Bono Corporativo', 'Deposito', 'Bono de Gobierno', 'Letra Hipotecaria', 'Factura', 'RF LATAM') OR Tipo_Instrumento is NULL)").format(
        yesterday, 'SPREADCORP', 'DEUDA CORP', 'DEUDA 360', 'LIQUIDEZ', 'M_MARKET', 'MACRO CLP3', 'MACRO 1.5', 'RENTA', 'IMT E-PLUS')
    print(query_carteras)
    df_carteras = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_carteras)

    ### Agregarle los fines de semana
    if not is_weekend(yesterday, today):
        cupones = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Fecha_corte'] == today and row[1]['Vencimiento'] != today}
        vencimientos = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if row[1]['Vencimiento'] == today}
    else:
        sabado = fs.get_next_day(yesterday)
        domingo = fs.get_next_day(sabado)
        cupones = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Fecha_corte'] == today and row[1]['Vencimiento'] != today)
                or (row[1]['Fecha_corte'] == sabado and row[1]['Vencimiento'] != sabado) or (row[1]['Fecha_corte'] == domingo and row[1]['Vencimiento'] != domingo)}
        vencimientos = {row[1]['Instrumento'].strip(): row[1]['Cantidad_corte'] for row in df_cupones.iterrows() if (row[1]['Vencimiento'] == today) or (row[1]['Vencimiento'] == sabado)
                or (row[1]['Vencimiento'] == domingo)}

    df_vencimiento_cupones = pd.DataFrame(columns=['Cartera', 'Cupones', 'Vencimiento', 'Total', 'R Vencimiento'])

    df_emisor = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", "SELECT RTRIM(LTRIM([Emisor])) AS [Emisor], [Codigo_SVS] FROM EmisoresIIF")

    for cartera in carteras:
        df_cartera = df_carteras[df_carteras['codigo_fdo'] == cartera]
        print(cartera)
        print(df_cartera)
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
        df_vencimiento_cupones = df_vencimiento_cupones.append(pd.DataFrame([excel_row], columns=['cartera', 'cupones', 'vencimiento', 'total', 'r_vencimiento']),
                    ignore_index=True)
    
    df_vencimiento_cupones['fondo'] = df_vencimiento_cupones['cartera'].map(lambda x: x.strip(" ").strip("'"))    
    df_vencimiento_cupones.set_index('cartera', inplace = True)

    return df_vencimiento_cupones
    



    
