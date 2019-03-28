"""
Created on Fri Jan 18 11:00:00 2018

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import datetime as dt


def compute_report(date_inic, date_fin):
    '''
    entrega el reporte de los errores de concordancia entre posiciones y transacciones
    '''
    aux_date = date_inic
    next_date = get_next_weekdays(aux_date)
    report = pd.DataFrame(columns=['fecha', 'fondo', 'instrumento', 'emisor', 'fec_vcto'])
    while next_date <= date_fin:
        date_report=check_positions(aux_date, next_date)
        report=report.append(date_report)
        aux_date = next_date
        next_date = get_next_weekdays(next_date)
    report=index_ins(report)
    return report


def check_positions(date_inic, date_fin):
    '''
    Chequeamos que entre dos fechas las posiciones concuerden con sus transacciones
    '''
    report = pd.DataFrame( columns=['fecha', 'fondo', 'instrumento', 'emisor', 'fec_vcto'])
    fund_list = get_diff_fund(date_inic)
    positions_inic = get_positions_frame(date_inic)
    positions_fin = get_positions_frame(date_fin)
    transactions_irf = get_transaccionesirf_frame(date_fin, fund_list)
    transactions_iif = get_transaccionesiif_frame(date_fin, fund_list)
    for fund in fund_list:
        bond_report, dep_report =check_fund(fund, positions_inic, positions_fin, transactions_irf, transactions_iif, date_inic, date_fin)
        report=report.append(bond_report)
        report=report.append(dep_report)
    return report

def check_fund(fund, positions_inic, positions_fin, transactions_irf, transactions_iif, date_inic, date_fin):
    '''
    Chequeamos la concordancia en un fondo en especifico
    '''
    list_both, list_inic, list_fin= compute_bond_list(positions_inic, positions_fin, fund)
    bond_report=compare(list_both, list_inic, list_fin, transactions_irf, fund, date_fin)
    list_both, list_inic, list_fin =compute_dep_list(positions_inic, positions_fin, fund)
    dep_report=compare(list_both, list_inic, list_fin, transactions_iif, fund, date_fin)
    return bond_report, dep_report



def compute_bond_list(position_fund_inic, position_fund_fin, fund):
    '''
    Crea las lista de los bonos que estan en ambas fchas, y en alguna de ellas
    '''

    ins_frame_inic = position_fund_inic.loc[(position_fund_inic['codigo_fdo'] == fund )&(position_fund_inic['instrumento'] != 'PAGARE NR') & (position_fund_inic['instrumento'] != 'PAGARE R')& (position_fund_inic['instrumento'] != 'PDBC')]
    ins_frame_fin = position_fund_fin.loc[(position_fund_fin['codigo_fdo'] == fund)&(position_fund_fin['instrumento'] != 'PAGARE NR') & (position_fund_fin['instrumento'] != 'PAGARE R') & (position_fund_fin['instrumento'] != 'PDBC')]
    list_both, list_inic, list_fin = comparar_frame(ins_frame_inic, ins_frame_fin)
    return  list_both, list_inic, list_fin

def compute_dep_list(position_fund_inic, position_fund_fin, fund):
    '''
    Crea las lista de los depositos que estan en ambas fchas, y en alguna de ellas
    '''
    ins_frame_inic = position_fund_inic.loc[(position_fund_inic['codigo_fdo'] == fund ) & ((position_fund_inic['instrumento'] == 'PAGARE NR') | (position_fund_inic['instrumento'] == 'PAGARE R') | (position_fund_inic['instrumento'] == 'PDBC'))]
    ins_frame_fin = position_fund_fin.loc[(position_fund_fin['codigo_fdo'] == fund) & ((position_fund_fin['instrumento'] == 'PAGARE NR') | (position_fund_fin['instrumento'] == 'PAGARE R') | (position_fund_fin['instrumento'] == 'PDBC'))]
    list_both, list_inic, list_fin = comparar_frame(ins_frame_inic, ins_frame_fin)
    return  list_both, list_inic, list_fin



def comparar_frame(ins_frame, ins_frame_1):
    '''
    Creamos los dataframe los que se repiten en ambas fechas y en solo una
    '''
    frame_12=pd.merge(ins_frame, ins_frame_1, how='inner', on=['instrumento', 'emisor','fec_vcto', 'codigo_fdo'], suffixes=('_1', '_2'))
    frame_1=frame_12.append(pd.merge(ins_frame, ins_frame_1, how='left', on=['instrumento', 'emisor','fec_vcto', 'codigo_fdo'], suffixes=('_1', '_2')))
    frame_1=frame_1[frame_1.cantidad_2.notnull() == False]
    frame_2=frame_12.append(pd.merge(ins_frame, ins_frame_1, how='right', on=['instrumento', 'emisor','fec_vcto', 'codigo_fdo'], suffixes=('_1', '_2')))
    frame_2=frame_2[frame_2.cantidad_1.notnull() == False]
    return frame_12, frame_1, frame_2



def compare(frame_12, frame_1, frame_2, transacciones, fund, date_inic):
    '''
    Comparamos si los distintos depositos concuerdan en ambas fechas
    '''
    report = pd.DataFrame( columns=['fecha', 'instrumento', 'emisor', 'fec_vcto'])
    if frame_12.empty is False:
        aux=check(frame_12, transacciones, fund, date_inic, c_1=None, c_2=None)
        report=report.append(aux)
    if frame_1.empty is False:
        aux=check(frame_1, transacciones, fund, date_inic, c_2=0, c_1=None)
        report=report.append(aux)
    if frame_2.empty is False:
        aux=check(frame_2, transacciones, fund, date_inic, c_1=0, c_2=None)
        report=report.append(aux)
    return report

    return report

def check(frame, transacciones, fund, date_inic, c_1=None, c_2=None):
    '''
    Chequeamos cuales si esta ok los dataframes
    '''
    report = pd.DataFrame( columns=['fecha', 'instrumento', 'emisor', 'fec_vcto'])
    for i in frame.index:
        if frame.loc[i]['instrumento'].startswith('CFI')==False and frame.loc[i]['instrumento'].startswith('CFM')==False:
            if c_1 is None:
                aux_1=frame.loc[i]['cantidad_1']
            else:
                aux_1=c_1
            if c_2 is None:
                aux_2=frame.loc[i]['cantidad_2']
            else:
                aux_2=c_2
            diff = float(aux_2)-float(aux_1)
            diff_2 = check_transaction(diff, transacciones, fund, frame.loc[i]['instrumento'], frame.loc[i]['emisor'], frame.loc[i]['fec_vcto'])

            if (diff_2 > 400 or diff_2 < -400) and fs.convert_date_to_string(date_fin) < frame.loc[i]['fec_vcto']:
                report=pd.DataFrame([[date_inic, fund, frame.loc[i]['instrumento'], frame.loc[i]['emisor'] ,frame.loc[i]['fec_vcto']]], columns=['fecha', 'fondo','instrumento', 'emisor', 'fec_vcto'])
        
    return report 

def check_transaction(diff, transacciones, fund, ins, em=None, fec=None):
    '''
    Chequemos las transacciones
    '''
    aux = 0
    frame = transacciones[((transacciones['vende'] == fund) | (transacciones['compra'] == fund)) & (transacciones['instrumento'] == ins)]
    if em !=None and fec!=None and ('emisor' in transacciones.columns):
        frame = transacciones[((transacciones['vende'] == fund) | (transacciones['compra'] == fund)) & (
            transacciones['instrumento'] == ins) & (transacciones['emisor'] == em) & (transacciones['fec_vcto'] == fec)]
    for trans in frame.index.tolist():
        if frame.loc[trans]['vende'] == fund:
            aux -= frame.loc[trans]['cantidad']
        elif frame.loc[trans]['compra'] == fund:
            aux += frame.loc[trans]['cantidad']
    return float(diff) - aux



def index_ins(dataframe):
    '''
    pone como indice los nombres de los intrumentos
    '''
    dataframe.set_index(["instrumento"], inplace=True)
    return dataframe


def get_next_weekdays(date):
    '''
    Encontramos el dia habil anterior más cercano a una fecha dada
    '''
    date += dt.timedelta(days=1)
    holyday = check_weekend(date)
    weekend = check_weekend(date)
    while holyday is True or weekend is True:
        date += dt.timedelta(days=1)
        holyday = check_weekend(date)
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

def get_diff_fund(date):
    '''
    Se obtiene una lista de los diferentes fondos en una fecha en especifica
    '''
    query = "select DISTINCT rtrim(LAGUNILLAS_ZHIS_Carteras_Agregado.codigo_fdo) as codigo_fdo  from LAGUNILLAS_ZHIS_Carteras_Agregado INNER JOIN FONDOSIR ON FONDOSIR.Codigo_fdo = LAGUNILLAS_ZHIS_Carteras_Agregado.codigo_fdo collate database_default WHERE fecha ='{}' AND operador_directo =1".format(
        date)
    fund_names = fs.get_frame_sql_user(server="puyehue",
                                       database="MesaInversiones",
                                       username="usuario1",
                                       password="usuario1",
                                       query=query)
    return fund_names['codigo_fdo'].tolist()


def get_positions_frame(date):
    '''
    Obtiene el frame de las posiciones para una fecha dada
    '''
    query = "select rtrim(LAGUNILLAS_ZHIS_Carteras_Agregado.codigo_fdo) as codigo_fdo ,rtrim(codigo_ins) as codigo_ins , rtrim(codigo_emi) as codigo_emi,  fec_vcto, nominal FROM  LAGUNILLAS_ZHIS_Carteras_Agregado INNER JOIN FONDOSIR ON FONDOSIR.Codigo_fdo = LAGUNILLAS_ZHIS_Carteras_Agregado.codigo_fdo collate database_default WHERE fecha ='{}' AND operador_directo =1".format(
        date)
    positions_frame = fs.get_frame_sql_user(server="puyehue",
                                            database="MesaInversiones",
                                            username="usuario1",
                                            password="usuario1",
                                            query=query)
    positions_frame.rename(columns={"codigo_ins": "instrumento"}, inplace=True)
    positions_frame.rename(columns={"codigo_emi": "emisor"}, inplace=True)
    positions_frame.rename(columns={"nominal": "cantidad"}, inplace=True)
    return positions_frame


def get_transaccionesiif_frame(date, filter_list):
    '''
    Obtiene el frame de las transacciones de los depositos para una fecha
    '''
    filter_list = [x for x in filter_list]
    query = "select  rtrim(instrumento) as instrumento, rtrim(emisor) as emisor, rescate , rtrim(vende) as vende, rtrim(compra) as compra, DATEADD(DAY,dias,fecha) as fec_vcto from TransaccionesIIF where fecha ='{}' ".format(
        date)
    transaction_frame = fs.get_frame_sql_user(server="puyehue",
                                              database="MesaInversiones",
                                              username="usuario1",
                                              password="usuario1",
                                              query=query)
    transaction_frame.rename(columns={"rescate": "cantidad"}, inplace=True)
    filt = (transaction_frame['vende'].isin(filter_list)
            | transaction_frame['compra'].isin(filter_list))
    return transaction_frame[filt]


def get_transaccionesirf_frame(date, filter_list=None):
    '''
    Obtiene el frame de las transacciones de los bonos para una fecha dada
    '''
    filter_list = [x for x in filter_list]
    query = "select   rtrim(instrumento) as  instrumento,  cantidad, rtrim(vende) as vende, rtrim(compra) as compra  from TransaccionesIRF where fecha ='{}'".format(
        date)
    transaction_frame = fs.get_frame_sql_user(server="puyehue",
                                              database="MesaInversiones",
                                              username="usuario1",
                                              password="usuario1",
                                              query=query)
    filt = (transaction_frame['vende'].isin(filter_list)
            | transaction_frame['compra'].isin(filter_list))
    return transaction_frame[filt]


def send_mail_report(report):
    '''
    Envia el mail a fernando suarez 1313. 
    '''
    subject = "Reporte de Inconsistencia Posiciones y transacciones"
    body = str(report)
    body = "Positiones inconsistentes: \n\n" + str(report) + "\n\n Slds"
    mail_list = [ 'fsuarez@credicorpcapital.com']#, "jparaujo@credicorpcapital.com", "dposch@credicorpcapital.com"
    fs.send_mail(subject=subject, body=body, mails=mail_list)


if __name__ == "__main__":
    spot_date = fs.get_ndays_from_today(0)
    date_fin = fs.convert_string_to_date(fs.get_prev_weekday(spot_date))
    date_inic =  fs.convert_string_to_date(fs.get_prev_weekday(fs.convert_date_to_string(date_fin)))
    report=compute_report(date_inic, date_fin)
    print(report)
    send_mail_report(report)