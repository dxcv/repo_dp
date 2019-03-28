import sys
sys.path.insert(0, '../portfolio_analytics/utiles')
sys.path.insert(0, "../libreria")

import libreria_fdo as fs
import utiles as utiles
import pandas as pd
import numpy as np
import datetime as dt
from win32com import client
import win32com.client

JeanPaul = 'jcelery@credicorpcapital.com'
Alvaro = 'adarquea@credicorpcapital.com'
Diego = 'dposch@credicorpcapital.com'
Matias = 'mcortes@credicorpcapital.com'
Ayli = 'afuentes@credicorpcapital.com'

# 


def send_mail(subject, body, mails):
    '''
    #Envia un mail a todos los correos en el arreglo mails.
    '''
    # os.startfile("outlook") #antes lo hacia con esto pero el problema es que
    # no se puede cerrar outlook
    const = win32com.client.constants
    olMailItem = 0x0
    obj = win32com.client.gencache.EnsureDispatch("Outlook.Application")
    #obj = win32com.client.Dispatch("Outlook.Application")
    obj.Visible = True
    newMail = obj.CreateItem(olMailItem)
    newMail.Subject = subject
    newMail.HTMLBody = body
    cadena = ""
    for mail in mails:
        mail = mail + ";"
        cadena = cadena + mail
    cadena = cadena[:-1]  # los mails se mandan separados por ; en una cadena
    newMail.To = cadena
    try:
        newMail.Send()
        print("Correo enviado")
    except:
        print("Fallo el envio del correo")


def send_mail_attach(subject, body, mails, attachment_paths):
    '''
    #Envia un mail a todos los correos en el arreglo mails y les adjunta todos los archivos del otro arreglo.
    '''
    # os.startfile("outlook") #antes lo hacia con esto pero el problema es que
    # no se puede cerrar outlook
    const = win32com.client.constants
    olMailItem = 0x0
    obj = win32com.client.gencache.EnsureDispatch("Outlook.Application")
    #obj = win32com.client.Dispatch("Outlook.Application")
    obj.Visible = True
    newMail = obj.CreateItem(olMailItem)
    newMail.Subject = subject
    newMail.HTMLBody = body
    cadena = ""
    for mail in mails:
        mail = mail + ";"
        cadena = cadena + mail
    cadena = cadena[:-1]  # los mails se mandan separados por ; en una cadena
    newMail.To = cadena
    for att in attachment_paths:
        newMail.Attachments.Add(Source=att)
    #attachment1 = at
    # newMail.Attachments.Add(Source=attachment1)
    # print(newMail.display())
    # newMail.Send()
    try:
        newMail.Send()
        print("Correo enviado")
    except:
        print("Fallo el envio del correo")


def get_ndays_from_today_future(days):
    '''Retorna la fecha n dias desde hoy.'''
    date = dt.datetime.now() + dt.timedelta(days=days)
    date = str(date.strftime('%Y-%m-%d'))
    return date


def carga_fdos():
    """Consulta la base de datos para obtener todos los fondos de renta fija con los que se trabajará """
    query = "SELECT Codigo_Fdo as Fondo, Codigo_Largo, Moneda FROM [Puyehue].[MesaInversiones].[dbo].[FondosIR] WHERE (estrategia = 'renta fija' or estrategia = 'credito') and Codigo_Fdo not in ('LATAM', 'INTERNAC', 'CC_GBI')"
    print(query)
    df = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)
    return df


def fondos_fwd(fondos, today, days=40):
    """Función que crea el DataFrame y consulta para todos los fondos y todos los días para forwards y swaps."""
    df_final = pd.DataFrame(columns=['Fondo', 'FechaOperacion', 'Vencimiento',
                                     'Moneda_Compra', 'Moneda_Venta', 'Nominal_Compra', 'Nominal_Venta'])
    for day in range(days):
        date = get_ndays_from_today_future(day)
        for fondo in fondos['Fondo']:
            query = "SELECT Codigo_Fdo as Fondo, fecha_op as FechaOperacion, fecha_vcto as Vencimiento, Moneda_Compra, Moneda_Venta, Nominal_Compra, Nominal_Venta FROM [Puyehue].[MesaInversiones].[dbo].[FWD_Monedas_Estatica] WHERE Codigo_Fdo = '{}' AND fecha_vcto = '{}'".format(
                fondo, date)
            # print(query)
            df = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)
            # print(df)
            df_final = df_final.append(df, ignore_index=True)
    df_final.sort_values(by=['Vencimiento', 'Fondo'], ascending=[
                         True, False]).reset_index(drop=True, inplace=True)
    # Hacemos el group by
    grouped = df_final.groupby(
        by=['Vencimiento', 'Fondo', 'Moneda_Compra']).sum()
    grouped['Nominal_Compra'] = grouped['Nominal_Compra'] / 1000
    grouped['Nominal_Venta'] = grouped['Nominal_Venta'] / 1000
    print(grouped.columns)
    grouped.rename(columns={'Nominal_Compra': 'Nominal Compra (M)',
                            'Nominal_Venta': 'Nominal Venta (M)'}, inplace=True)
    return df_final, grouped


def fondos_rf(fondos, today, weight, days=5):
    """Función que crea el DataFrame y consulta para todos los fondos y todos los días para renta fija."""
    df_final = pd.DataFrame(columns=[
                            'Fondo', 'Instrumento', 'Emisor', 'Moneda', 'Monto', 'Weight', 'Vencimiento', 'Dias'])
    for day in range(days):
        date = get_ndays_from_today_future(day)
        # Consultamos todos los weights, luego filtraremos
        for fondo in fondos['Fondo']:
            query = "SELECT Codigo_Fdo as Fondo, Codigo_Ins as Instrumento, codigo_emi as Emisor, Moneda, Monto, Weight, fec_vcto as Vencimiento FROM [Puyehue].[MesaInversiones].[dbo].[ZHIS_Carteras_Recursive] WHERE codigo_fdo = '{}' AND fec_vcto = '{}' AND fecha = '{}'".format(
                fondo, date, today)
            df = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)
            df.insert(loc=len(df.columns), column='Dias', value=day + 1)
            df_final = df_final.append(df, ignore_index=True)
    df_final['Weight'] = df_final['Weight'].astype(float)
    df_final['Monto'] = df_final['Monto'].astype(float)
    df_final = df_final[df_final['Weight'] > weight].sort_values(
        by=['Vencimiento', 'Fondo'], ascending=[True, False]).reset_index(drop=True)
    # Hacemos el group by dentro del dataframe, para la pestaña de resumen
    grouped = df_final.groupby(by=['Vencimiento', 'Fondo']).sum()
    grouped['Weight'] = grouped['Weight']
    """
    grouped.rename(columns={'Monto': 'Monto (MM)',
                            'Weight': 'Weight (%)'}, inplace=True)
    """
    return df_final, grouped


def vencimientos_portfolios():
    # Busca los movimientos realizados el día de hoy y su vencimiento,
    # cruza las tablas Transacciones IIF (transacciones) y ZHIS_Carteras
    # (vencimientos)
    today = dt.date.today()
    yesterday = fs.get_ndays_from_today(1)
    path = ".\\Querys\\consulta_join.sql"
    query = fs.read_file(path=path).replace(
        "AUTODATE_SPOT", fs.convert_date_to_string(today)).replace("AUTODATE_YEST", yesterday)
    # print(query)
    df = fs.get_frame_sql_user(server='Puyehue', database='MesaInversiones',
                                query=query, username='usuario1', password='usuario1')
    df.fillna(value=0, inplace=True)
    # HAY QUE SEPARAR PARA VER CUALES PAGAN EN T+1, T+2 Y PONERLE SIGNO
    # NEGATIVO A LOS QUE COMPRAN

    df_cn_compra = df[(df['Liq'] == 'CN') & (
        df['Compra'] != 0)].reset_index(drop=True)
    df_cn_compra['Monto_Final'] = df_cn_compra['Monto'] * -1
    df_cn_compra['Fondo_Final'] = df_cn_compra['Compra']
    df_cn_compra['Fecha_Settle'] = df_cn_compra['Fecha'].apply(utiles.get_fecha_contado_normal)
    df_cn_compra = df_cn_compra[['Fecha', 'Instrumento', 'Moneda',
                                 'Liq', 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']]

    df_cn_vende = df[(df['Liq'] == 'CN') & (
        df['Vende'] != 0)].reset_index(drop=True)
    df_cn_vende['Monto_Final'] = df_cn_vende['Monto']
    df_cn_vende['Fondo_Final'] = df_cn_vende['Vende']
    df_cn_vende['Fecha_Settle'] = df_cn_vende[
        'Fecha'].apply(utiles.get_fecha_contado_normal)
    df_cn_vende = df_cn_vende[['Fecha', 'Instrumento', 'Moneda',
                               'Liq', 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']]

    df_pm_compra = df[(df['Liq'] == 'PM') & (
        df['Compra'] != 0)].reset_index(drop=True)
    df_pm_compra['Monto_Final'] = df_pm_compra['Monto'] * -1
    df_pm_compra['Fondo_Final'] = df_pm_compra['Compra']
    df_pm_compra['Fecha_Settle'] = df_pm_compra[
        'Fecha'].apply(utiles.get_fecha_habil_posterior)
    df_pm_compra = df_pm_compra[['Fecha', 'Instrumento', 'Moneda',
                                 'Liq', 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']]

    df_pm_vende = df[(df['Liq'] == 'PM') & (
        df['Vende'] != 0)].reset_index(drop=True)
    df_pm_vende['Monto_Final'] = df_pm_vende['Monto']
    df_pm_vende['Fondo_Final'] = df_pm_vende['Vende']
    df_pm_vende['Fecha_Settle'] = df_pm_vende[
        'Fecha'].apply(utiles.get_fecha_habil_posterior)
    df_pm_vende = df_pm_vende[['Fecha', 'Instrumento', 'Moneda',
                               'Liq', 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']]

    df_pmod = df[df['Liq'] == 'PMOD']
    # columns=['Fecha', 'Instrumento', 'Moneda', 'Liq', 'Fec_Vcto',
    # 'Monto_Final', 'Fondo_Final', 'Fecha_Settle'])
    df_pmod_final = pd.DataFrame()
    k = 0
    for i, j in df_pmod.iterrows():
        fecha = df_pmod.loc[i]['Fecha']
        instr = df_pmod.loc[i]['Instrumento']
        moneda = df_pmod.loc[i]['Moneda']
        liq = df_pmod.loc[i]['Liq']
        fec_vcto = df_pmod.loc[i]['Fec_Vcto']
        monto = df_pmod.loc[i]['Monto']
        fondo_compra = df_pmod.loc[i]['Compra']
        fondo_vende = df_pmod.loc[i]['Vende']
        fecha_settle = utiles.get_fecha_habil_posterior(df_pmod.loc[i]['Fecha'])
        row_compra = [[fecha, instr, moneda, liq, fec_vcto,
                       monto * (-1), fondo_compra, fecha_settle]]
        row_vende = [[fecha, instr, moneda, liq,
                      fec_vcto, monto, fondo_vende, fecha_settle]]
        df_pmod_final = df_pmod_final.append(row_compra, ignore_index=True)
        df_pmod_final = df_pmod_final.append(row_vende, ignore_index=True)
    try:
        df_pmod_final.columns = ['Fecha', 'Instrumento', 'Moneda', 'Liq',
                                 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']
    except:
        print('No existen transacciones "PMOD"')
    """
	with pd.option_context('display.max_rows', None, 'display.max_columns', None):
		print(df_cn_compra)
		print(df_cn_vende)
		print(df_pm_compra)
		print(df_pm_vende)
	"""
    df_final = pd.concat([df_cn_compra, df_cn_vende, df_pm_compra,
                          df_pm_vende, df_pmod_final], ignore_index=True)

    print(df_final)
    exit()

    return df_final

def compute_grouped_forwards(forwards_portfolios, fund_ids):
    '''
    Agrupa los forwards para ver el total por dia a netear. 
    '''
    grouped_forwards = forwards_portfolios
    # Sacamos todas las monedas para armar las combinaciones
    buy_currencies = forwards_portfolios["moneda_compra"]
    buy_currencies = buy_currencies.unique()
    sell_currencies = forwards_portfolios["moneda_venta"]
    sell_currencies = sell_currencies.unique()
    currencies = list(set(buy_currencies).union(sell_currencies))
    currencies.sort()
    # Por cada forward lo tageamos vamos a tagear con su cros respectivo
    # notar que usdclp y clpusd van al mismo tag
    grouped_forwards["nominal"] = None
    grouped_forwards["currency_pair"] = None
    for index, forward in grouped_forwards.iterrows():
        long_currency = forward["moneda_compra"]
        short_currency = forward["moneda_venta"]
        for i in range(len(currencies)):
            for j in range(len(currencies)):
                if i > j:
                    currency_pair = [currencies[i], currencies[j]]
                    if long_currency in currency_pair and short_currency in currency_pair:
                        forward["currency_pair"] = currencies[
                            i] + "-" + currencies[j]
                        grouped_forwards.loc[index] = forward
                        if currencies[j] == forward["moneda_compra"]:
                            forward["nominal"] = -1 * forward["nominal_venta"]
                        else:
                            forward["nominal"] = forward["nominal_compra"]
                        grouped_forwards.loc[index] = forward
    # Finalmente agrupamos y sumamos por fondo
    grouped_forwards = grouped_forwards.reset_index()
    grouped_forwards = grouped_forwards.groupby(
        ["codigo_fdo", "fec_vcto", "currency_pair", "days_to_maturity"])["nominal"].sum()
    grouped_forwards = grouped_forwards.reset_index()
    # Luego hacemos el display con columnas por fondo
    matrix_columns = ["fec_vcto", "days_to_maturity", "currency_pair"]
    matrix_columns = matrix_columns + list(fund_ids)
    grouped_forwards_aux = grouped_forwards[
        ["fec_vcto", "currency_pair", "days_to_maturity"]]
    grouped_forwards_aux = grouped_forwards_aux.drop_duplicates()
    grouped_forwards_aux = grouped_forwards_aux.set_index(
        ["fec_vcto", "currency_pair"])
    for fund_id in fund_ids:
        grouped_forwards_aux[fund_id] = 0.0
    for i, cash_flow in grouped_forwards.iterrows():
        fund_id = cash_flow["codigo_fdo"]
        maturity_date = cash_flow["fec_vcto"]
        currency_pair = cash_flow["currency_pair"]
        nominal = cash_flow["nominal"]
        grouped_forwards_aux.loc[(maturity_date, currency_pair)][
            fund_id] += nominal
    grouped_forwards_aux.sort_values(["days_to_maturity"],
                                     inplace=True,
                                     ascending=[True])
    grouped_forwards = grouped_forwards_aux
    return grouped_forwards

def get_forwards_portfolios(spot_date, fund_ids):
    '''
    Retorna el portfolio de fx forwards.
    '''
    path = ".\\querys\\fx_forwards.sql"
    query = fs.read_file(path=path).replace("autodate", spot_date)
    forwards_portfolios = []
    for fund_id in fund_ids:
        query_fund = query.replace("autofund", fund_id)
        fx_forwards = fs.get_frame_sql_user(server="Puyehue",
                                            database="MesaInversiones",
                                            username="usrConsultaComercial",
                                            password="Comercial1w",
                                            query=query_fund)
        forwards_portfolios.append(fx_forwards)
    forwards_portfolios = pd.concat(forwards_portfolios, ignore_index=True)
    forwards_portfolios.set_index(
        ["codigo_fdo", "fecha_op", "codigo_emi", "codigo_ins"], inplace=True)
    forwards_portfolios["days_to_maturity"] = (pd.to_datetime(forwards_portfolios[
                                               "fec_vcto"]) - pd.to_datetime(fs.convert_string_to_date(spot_date))).astype('timedelta64[D]')
    forwards_portfolios.sort_values(
        ["days_to_maturity"], inplace=True, ascending=[True])
    return forwards_portfolios



def forwards_expirations():
    spot_date = fs.get_ndays_from_today(0)
    fund_ids = ("RENTA", "IMT E-PLUS", "MACRO 1.5", "MACRO CLP3", "SPREADCORP", "M_MARKET", "LIQUIDEZ", "DEUDA CORP")
    forwards_portfolios = get_forwards_portfolios(spot_date, fund_ids)
    forwards_expirations = compute_grouped_forwards(forwards_portfolios, fund_ids)
    return forwards_expirations

def get_vencimientos(today, weight_min):
    fondos = carga_fdos()
    df_vencimientos_portfolios = vencimientos_portfolios()
    rf = fondos_rf(fondos, today, weight_min)
    fwd = fondos_fwd(fondos, today)
    df_forwards_expirations = forwards_expirations()

    return fondos, df_vencimientos_portfolios, rf, fwd, df_forwards_expirations

def excel(today, weight_min):
    fondos = carga_fdos()
    df_vencimientos_portfolios = vencimientos_portfolios()
    rf = fondos_rf(fondos, today, weight_min)
    fwd = fondos_fwd(fondos, today)
    df_forwards_expirations = forwards_expirations()
    workbook = fs.open_workbook('Template.xlsx', False, True)
    name = 'Vencimientos ' + str(today) + '.xlsx'
    sht = workbook.sheets['RentaFija']
    sht2 = workbook.sheets['Forwards']
    sht3 = workbook.sheets['Resumen']
    sht4 = workbook.sheets['Hoy']
    sht.range('A1').value = rf[0]
    #sht2.range('A1').value = fwd[0]
    sht3.range('A1').value = rf[1]
    sht3.range('F1').value = fwd[1]
    sht2.range('A1').value = df_forwards_expirations
    sht4.range('A1').value = df_vencimientos_portfolios
    workbook.save(name)
    fs.close_excel(workbook)
    rf_html = rf[1].to_html()
    fwd_html = fwd[1].to_html()
    hoy_html = df_vencimientos_portfolios.to_html()
    forwards_html = df_forwards_expirations.to_html()
    a = 'Posiciones de renta fija próximas a vencer:\n'
    b = '\nPosiciones de forward próximas a vencer:\n'
    c = '\nTransacciones del día:\n'
    d = '\nDashboard'
    #send_mail('Vencimientos Próximos', a + rf_html + b + fwd_html + c + hoy_html + d + dashboard_html, [JeanPaul])
    #send_mail_attach('Vencimiento Instrumentos', a + rf_html + b + fwd_html + c + hoy_html + d + dashboard_html,
     #                [JeanPaul], ['C://Users//jcelerys//Documents//Extension//Renta Fija//2. Vencimientos//portfolio_dashboard//' + name])
    return rf[1], fwd[1]

