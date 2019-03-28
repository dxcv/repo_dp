import sys
import os
import datetime as dt
import libreria_fdo as fs
import pandas as pd
# from tia.bbg import v3api
from sqlalchemy import create_engine, types
import locale

locale.setlocale(locale.LC_ALL, 'deu_deu')

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


def check_excel():
    today = str(dt.datetime.now().date())
    yesterday = fs.get_prev_weekday(str(dt.datetime.now().date()))
    excel = fs.get_self_path() + "Cupones_{}".format(today) + ".xlsx"
    wb = fs.open_workbook(excel, True, True)
    df = fs.get_frame_xl(wb, "Hoja1", 2, 3, [0])
    fs.close_workbook(wb)


    query_bonos = ("SELECT [codigo_ins], [codigo_fdo], [nominal], [fec_vcto] FROM [MesaInversiones].[dbo].[ZHIS_Carteras_Main] WHERE [fecha] = '{}' AND ([codigo_ins] NOT LIKE '{}' AND [codigo_ins] NOT LIKE '{}') AND [codigo_fdo] IN ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}') AND [Tipo_Instrumento] NOT IN ('{}', '{}')").format(
        yesterday, 'PAGARE%', 'PDBC%', 'SPREADCORP', 'DEUDA CORP', 'DEUDA 360', 'LIQUIDEZ', 'M_MARKET', 'MACRO CLP3', 'MACRO 1.5', 'RENTA', 'IMT E-PLUS', 'Cuota de Fondo', 'Letra Hipotecaria')
    df_bonos = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_bonos)
    
    query_depositos = ("SELECT [codigo_ins], [codigo_fdo], [nominal], [codigo_emi], [Moneda], [fec_vcto] FROM [MesaInversiones].[dbo].[ZHIS_Carteras_Main] WHERE [fecha] = '{}' AND ([codigo_ins] LIKE '{}' OR [codigo_ins] LIKE '{}') AND [codigo_fdo] in ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')").format(  ##(Tipo_Instrumento IN ('Bono Corporativo', 'Deposito', 'Bono de Gobierno', 'Letra Hipotecaria', 'Factura', 'RF LATAM') OR Tipo_Instrumento is NULL)").format(
        yesterday, 'PAGARE%', 'PDBC%', 'SPREADCORP', 'DEUDA CORP', 'DEUDA 360', 'LIQUIDEZ', 'M_MARKET', 'MACRO CLP3', 'MACRO 1.5', 'RENTA', 'IMT E-PLUS')
    df_depositos = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_depositos)

    query_cupones = "SELECT * FROM [MesaInversiones].[dbo].[Cupones_RF]"
    df_cupones = fs.get_frame_sql_user("Puyehue", "MesaInversiones", "usuario1", "usuario1", query_cupones)

    df_bonos_t = df_bonos.loc[df_bonos['fec_vcto'] == today]
    df_depositos = df_depositos.loc[df_depositos['fec_vcto'] == today]

    df_excel = pd.DataFrame(columns=['Fondo', 'Cupones', 'Vencimiento D', 'Vencimiento B', 'Total'])


    for row in df.iterrows():
        fondo = row[0].strip()
        vencimiento_recibido_pdf_d = float(str(row[1]['Vencimiento D']).replace('.','').replace(',','.'))
        vencimiento_recibido_base_d = 0
        vencimiento_recibido_pdf_b = float(str(row[1]['Vencimiento B']).replace('.','').replace(',','.'))
        vencimiento_recibido_base_b = 0
        recibido_base = 0
        total_recibido_cupones = float(str(row[1]['Cupones']).replace('.','').replace(',','.'))
        for line in df_depositos.iterrows():
            if line[1]['codigo_fdo'].strip() == fondo:
                vencimiento_recibido_base_d += float(line[1]['nominal'])
        for linea in df_bonos_t.iterrows():
            instrumento = linea[1]['codigo_ins']
            df_cupon = df_cupones.loc[df_cupones['Instrumento'] == instrumento]
            for i in df_cupon.iterrows():
                vencimiento_recibido_base_b += i[1]['Cantidad_corte']

        if vencimiento_recibido_pdf_d != vencimiento_recibido_base_d:
            ### Acá agregar que pasa si es que los vencimientos del pdf no coinciden con los vencimientos de la base de datos 
            pass
        excel_row = [fondo, locale.format("%f", total_recibido_cupones, grouping=True, monetary=True)[:-5], locale.format("%f", vencimiento_recibido_base_d, grouping=True, monetary=True)[:-5],
                    locale.format("%f", vencimiento_recibido_base_b, grouping=True, monetary=True)[:-5], locale.format("%f", total_recibido_cupones + vencimiento_recibido_base_d + vencimiento_recibido_base_b, grouping=True, monetary=True)[:-5]]
        df_excel = df_excel.append(pd.DataFrame([excel_row], columns=['Fondo', 'Cupones', 'Vencimiento D', 'Vencimiento B', 'Total']),
                    ignore_index=True)

    excel = resource_path("Cupones_" + today + ".xlsx")
    writer = pd.ExcelWriter(excel)

    #### Escribe el dataframe del resumen de los fondos corregidos en una página del excel
    df_excel.to_excel(writer, sheet_name='Resumen', startrow=1, startcol=1)
    writer.sheets['Resumen'].column_dimensions['C'].width = 13
    writer.sheets['Resumen'].column_dimensions['D'].width = 14
    writer.sheets['Resumen'].column_dimensions['E'].width = 14
    writer.sheets['Resumen'].column_dimensions['F'].width = 14
    writer.sheets['Resumen'].column_dimensions['G'].width = 14
    writer.save()

    ### Imprime solo el resumen de los fondos en un PDF
    #fs.export_sheet_pdf_jp(0, fs.get_self_path()+"Cupones_" + today + ".xlsx", fs.get_self_path()+"Informe_cupones_" + today + "_corregido.pdf")


    fondos = ['SPREADCORP', 'DEUDA CORP', 'DEUDA 360', 'LIQUIDEZ', 'M_MARKET', 'MACRO CLP3', 'MACRO 1.5', 'RENTA', 'IMT E-PLUS', 'None']
    
    for fondo in fondos:
        df_sheet = pd.DataFrame(columns=['Fondo', 'Instrumento', 'Emisor' 'Ingreso'])
        for line in df_depositos.iterrows():
            if line[1]['codigo_fdo'].strip() == fondo:
                row = [fondo, line[1]['codigo_ins'].strip(), line[1]['codigo_emi'].strip(), locale.format("%f", float(line[1]['nominal']), grouping=True, monetary=True)[:-5]]
                print(row)
                df_sheet = df_sheet.append(pd.DataFrame([row], columns=['Fondo', 'Instrumento', 'Emisor', 'Ingreso']),
                    ignore_index=True)

        for fila in df_cupones.loc[df_cupones['Fecha_corte'] == today].iterrows():
            instrumento = fila[1]['Instrumento']
            for linea in df_bonos.iterrows():
                if instrumento == linea[1]['codigo_ins'] and fondo == linea[1]['codigo_fdo']:
                    row = [fondo, instrumento, None, locale.format("%f", ((float(linea[1]['Cantidad_corte']) / 1000000) * linea[1]['nominal']), grouping=True, monetary=True)[:-5]]
                    df_sheet = df_sheet.append(pd.DataFrame([row], columns=['Fondo', 'Instrumento', 'Emisor', 'Ingreso']),
                        ignore_index=True)
                    
                    print(row)
        #### Escribe el detalle de todos los intrumentos de cada fondo que reportan ingresos
        df_sheet.to_excel(writer, sheet_name=fondo, startrow=1, startcol=1)
        print('-------------' + fondo + '-------------')
        print(df_sheet)

    for fon in fondos:
        writer.sheets[fon].column_dimensions['C'].width = 14
        writer.sheets[fon].column_dimensions['D'].width = 14
        writer.sheets[fon].column_dimensions['E'].width = 14
        writer.sheets[fon].column_dimensions['F'].width = 14
        writer.sheets[fon].column_dimensions['G'].width = 15

    writer.save()
    writer.close()
    #### Imprime el detalle de todos los fondos en un PDF (la primera lista indica los indices del excel que quiero pasar a PDF,
    #### deberían llegar hasta el 10 para que los imprima todos, pero tira un error de list index que no he podido arreglar)
    fs.export_sheet_pdf_multiple_index([1,2,3,4,5,6,7,8,9,10], fs.get_self_path()+"Cupones_" + today + ".xlsx", fs.get_self_path()+"Informe_cupones_" + today + "_detalle.pdf")


check_excel()