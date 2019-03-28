"""
Created on Thu Aug 10 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../../libreria/')
sys.path.insert(1, '../risk_library/')
import libreria_fdo as fs
import risk as rk
import pandas as pd
import numpy as np
# Para desabilitar warnings
import warnings
warnings.filterwarnings("ignore") 
pd.options.mode.chained_assignment = None 


def compute_table_soberanos(portfolios, ep_benchmark_RF_soberano):

    eplus_portfolio=portfolios.loc["IMT E-PLUS"]
    eplus_gob= eplus_portfolio.loc[(eplus_portfolio["tipo_instrumento"] == 'Bono de Gobierno')]
    eplus_gob= eplus_gob[eplus_gob["moneda"].isin(['$','UF'])]
    eplus_gob = eplus_gob[['moneda', 'weight','duration']]
    eplus_gob = get_buckets_soberanos(eplus_gob)
    eplus_gob["code"] = eplus_gob["bucket"].astype(str)+eplus_gob["moneda"]
    dur_w = eplus_gob.groupby(["code"]).apply( lambda x: np.average(x['duration'], weights=x['weight']))
    eplus_gob = eplus_gob.groupby(["code","moneda"]).agg('sum').drop('duration',1).reset_index().set_index('code')
    eplus = pd.concat([dur_w, eplus_gob], axis=1)
    eplus.rename(columns={0: 'dur_w'}, inplace=True)
    ep_benchmark_RF_soberano["code"] = ep_benchmark_RF_soberano["bucket"].astype(str)+ep_benchmark_RF_soberano["moneda"]
    cartera_afp_sob = ep_benchmark_RF_soberano.set_index(['code'])
    
    table_soberanos = pd.merge( eplus, cartera_afp_sob, how='outer', left_index=True, right_index=True, suffixes=('_eplus', '_afp'))
    table_soberanos["bucket"] = np.where(table_soberanos["bucket_afp"] is None, table_soberanos["bucket_eplus"], table_soberanos["bucket_afp"])
    table_soberanos["moneda"] = np.where(table_soberanos["moneda_afp"] is None, table_soberanos["moneda_eplus"], table_soberanos["moneda_afp"])

    table_soberanos.fillna(0.0,inplace=True)
    table_soberanos = table_soberanos[["bucket","moneda","weight_eplus","weight_afp","dur_w_eplus", "dur_w_afp"]].reset_index(drop=True).set_index(table_soberanos["bucket"].astype(str) + "Y")

    table_soberanos["delta"] = table_soberanos["weight_eplus"] - table_soberanos["weight_afp"]
    table_soberanos["ACT_DV01"] = table_soberanos["dur_w_eplus"] * table_soberanos["weight_eplus"] - table_soberanos["dur_w_afp"]*table_soberanos["weight_afp"]
    table_soberanos["bucket"] = table_soberanos["bucket"].apply(pd.to_numeric)
    table_soberanos = table_soberanos.sort_values(["moneda","bucket"], ascending=[True, True])
    
    return table_soberanos
    
    

def get_buckets_soberanos(cartera_govt):

    conditions = [
    (cartera_govt["duration"]<1.5),
    (cartera_govt["duration"]<3),
    (cartera_govt["duration"]<5),
    (cartera_govt["duration"]<9),
    (cartera_govt["duration"]<15.5) & (cartera_govt["moneda"]=='UF'),
    (cartera_govt["duration"]<12.5) & (cartera_govt["moneda"]=='$')]
        
    
    buckets=[1,3,5,10,20,20]

    cartera_govt["bucket"]=np.select(conditions,buckets,default=30)

    return cartera_govt



def get_re_benchmark_last_date():
    '''
    Retorna la fecha más reciente del portafolio del benchmark del renta
    '''
    path = ".\\querys_portfolio_dashboard\\re_benchmark_last_date.sql"
    query = fs.read_file(path=path)
    bmk_last_date = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    date_string = bmk_last_date.strftime('%Y-%m-%d')
    return date_string


def get_clf():
    '''
    Retorna la uf spot en la base de datos.
    '''
    path = ".\\querys_portfolio_dashboard\\clf.sql"
    query = fs.read_file(path=path)
    forwards_portfolios = []
    clf = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    return clf

def get_subportfolios(date, fund_id):
    '''
    Retorna el portfolio de cuotas de fondos.
    '''
    query = "select codigo_emi as codigo_fdo, cantidad, monto from zhis_carteras_main where fecha = '{}' and codigo_fdo = '{}' and tipo_instrumento = 'cuota de fondo' order by monto desc"
    query = query.format(date, fund_id)
    portfolio = fs.get_frame_sql_user(server="Puyehue",
                                      database="MesaInversiones",
                                      username="usrConsultaComercial",
                                      password="Comercial1w",
                                      query=query)
    portfolio.set_index(["codigo_fdo"], inplace=True)
    
    return portfolio


def get_forwards_portfolios(spot_date, fund_ids):
    '''
    Retorna el portfolio de fx forwards.
    '''

    path = ".\\querys_portfolio_dashboard\\fx_forwards.sql"
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
    forwards_portfolios.set_index(["codigo_fdo", "fecha_op", "codigo_emi", "codigo_ins"], inplace=True)
    forwards_portfolios["days_to_maturity"] = (pd.to_datetime(forwards_portfolios["fec_vcto"] ) - fs.convert_string_to_date(spot_date)).astype('timedelta64[D]')
    forwards_portfolios.sort_values(["days_to_maturity"], inplace=True, ascending=[True])
    
    
    return forwards_portfolios


def get_spreads_portfolios(date):
    '''
    Retorna los portafolios de los spreads.
    '''
    path = ".\\querys_portfolio_dashboard\\portfolio_spreads.sql"
    query = fs.read_file(path=path).replace("autodate", date)
    query_re = query.replace("autofund", "RENTA")
    query_ep = query.replace("autofund", "IMT E-PLUS")
    spreads_re = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query_re)
    spreads_ep = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query_ep)
    spreads_re.set_index(["codigo_fdo", "codigo_ins"], inplace=True)
    spreads_ep.set_index(["codigo_fdo", "codigo_ins"], inplace=True)
    
    return spreads_re, spreads_ep


def reshape_portfolios(portfolios):
    '''
    Formatea el dataframe para trabajarlo mas facil
    '''
    core_columns = ["codigo_fdo", "codigo_emi", "codigo_ins",
                    "fec_vtco", "tipo_instrumento_x", "moneda_x",
                    "weight_x", "monto", "ctd", "ctr", "pcr", 
                    "cantidad", "duration_x", "precio", "tipo_ra"]
    columns_dict = {"tipo_instrumento_x": "tipo_instrumento",
                    "moneda_x": "moneda",
                    "weight_x": "weight",
                    "duration_x": "duration"}
    portfolios = portfolios[core_columns]
    portfolios.rename(columns=columns_dict, inplace=True)
    portfolios = portfolios.reindex()
    portfolios.set_index(["codigo_fdo", "codigo_emi", "codigo_ins", "fec_vtco"], inplace=True)
    portfolios.loc[portfolios["tipo_instrumento"] == "FX", "tipo_instrumento"] = "Cash"
    return portfolios



def compute_grouped_forwards(forwards_portfolios, fund_ids):
    '''
    Agrupa los forwards para ver el total por dia a netear. 
    '''
    grouped_forwards = forwards_portfolios
    # Sacamos todas las monedas para armas las combinacione
    buy_currencies = forwards_portfolios["moneda_compra"]
    buy_currencies = buy_currencies.unique()
    sell_currencies = forwards_portfolios["moneda_venta"]
    sell_currencies = sell_currencies.unique()
    currencies = list(set(buy_currencies).union(sell_currencies))
    currencies.sort()
    # Por cada forward lo tageamos vamos a tagear con su cros respectivo
    # notar quye usdclp y clpusd van al mismo tag
    grouped_forwards["nominal"] = None
    grouped_forwards["currency_pair"] = None
    for index, forward in grouped_forwards.iterrows():
        long_currency = forward["moneda_compra"]
        short_currency = forward["moneda_venta"]
        for i in range(len(currencies)):
            for j in  range(len(currencies)):
                if i > j:
                    currency_pair = [currencies[i], currencies[j]]
                    if long_currency in currency_pair and short_currency in currency_pair:
                        forward["currency_pair"] = currencies[i]+ "-" +currencies[j]
                        grouped_forwards.loc[index] = forward
                        if currencies[j] == forward["moneda_compra"]:
                            forward["nominal"] = -1*forward["nominal_venta"]
                        else:
                            forward["nominal"] = forward["nominal_compra"]
                        grouped_forwards.loc[index] = forward
    # Finalmente agrupamos y sumamos por fondo
    grouped_forwards = grouped_forwards.reset_index()
    grouped_forwards = grouped_forwards.groupby(["codigo_fdo", "fec_vcto", "currency_pair", "days_to_maturity"])["nominal"].sum()
    grouped_forwards = grouped_forwards.reset_index()
    # Luego hacemos el display con columnas por fondo
    matrix_columns = ["fec_vcto", "days_to_maturity", "currency_pair"]
    matrix_columns = matrix_columns + list(fund_ids)
    

    grouped_forwards_aux = grouped_forwards[["fec_vcto", "currency_pair", "days_to_maturity"]]
    grouped_forwards_aux = grouped_forwards_aux.drop_duplicates()
    grouped_forwards_aux = grouped_forwards_aux.set_index(["fec_vcto", "currency_pair"])
    for fund_id in fund_ids:
        grouped_forwards_aux[fund_id] = 0.0
    for i, cash_flow in grouped_forwards.iterrows():
        fund_id = cash_flow["codigo_fdo"] 
        maturity_date = cash_flow["fec_vcto"]
        currency_pair = cash_flow["currency_pair"]
        nominal = cash_flow["nominal"]
        grouped_forwards_aux.loc[(maturity_date, currency_pair)][fund_id] += nominal
    grouped_forwards_aux.sort_values(["days_to_maturity"],
                                       inplace=True,
                                       ascending=[True])
    grouped_forwards = grouped_forwards_aux
    return grouped_forwards



def get_re_benchmark(date):
    '''
    Lee el query del portafolio de competidores, y lo transforma en dataframe
    '''
    path = ".\\querys_portfolio_dashboard\\re_benchmark_portfolios.sql"
    portfolio_query = fs.read_file(path)
    portfolio_query = portfolio_query.replace("autodate", date)
    portfolio = fs.get_frame_sql_user(server="Puyehue",
                                      database="MesaInversiones",
                                      username="usrConsultaComercial",
                                      password="Comercial1w",
                                      query=portfolio_query)
    portfolio = rebalance_benchmark(portfolio)
    portfolio.set_index(["fecha", "run_fondo", "codigo_ins"], inplace=True)
    portfolio["ctd"] = portfolio["weight"] * portfolio["duration"]
    return portfolio



def rebalance_benchmark(portfolio):
    '''
    Agregamos al dataframe una columna Weight, que muestra el peso del instrumento 
    en el portafolio total (compuesto por todos los instrumentos de todos los competidores)
    '''
    portfolio["valoriz_cierre"] = portfolio["valoriz_cierre"].astype(float)
    portfolio["Valoriz_Total_Portfolio"] = portfolio.groupby("fecha")["valoriz_cierre"].transform(sum)
    # portfolio["weight"] = portfolio["valoriz_cierre"] / portfolio["Valoriz_Total_Portfolio"]# para weight por aum
    portfolio["weight"] = portfolio["weight"] / portfolio["weight"].sum()
    
    del portfolio["Valoriz_Total_Portfolio"]
    return portfolio



def compute_dashboardsANTIGUO(portfolios, forwards_portfolios, grouped_forwards, spreads_re, spreads_ep, re_benchmark_portfolio, clf):
    '''
    Formatea el dataframe para trabajarlo mas facil
    '''
    wb = fs.open_workbook("portfolio_dashboard_spanish.xlsx", True, True)
    fs.clear_sheet_xl(wb, "portfolios")
    fs.clear_sheet_xl(wb, "forwards_portfolios")
    fs.clear_sheet_xl(wb, "grouped_forwards")
    fs.clear_sheet_xl(wb, "parameters")
    fs.clear_sheet_xl(wb, "spreads_portfolio_re")
    fs.clear_sheet_xl(wb, "spreads_portfolio_ep")
    fs.clear_sheet_xl(wb, "parameters")
    fs.clear_sheet_xl(wb, "re_benchmark_portfolio")
    fs.paste_val_xl(wb, "portfolios", 1, 1, portfolios)
    fs.paste_val_xl(wb, "forwards_portfolios", 1, 1, forwards_portfolios)
    fs.paste_val_xl(wb, "grouped_forwards", 1, 1, grouped_forwards)
    fs.paste_val_xl(wb, "spreads_portfolio_re", 1, 1, spreads_re)
    fs.paste_val_xl(wb, "spreads_portfolio_ep", 1, 1, spreads_ep)
    fs.paste_val_xl(wb, "parameters", 1, 1, clf)
    fs.paste_val_xl(wb, "re_benchmark_portfolio", 1, 1, re_benchmark_portfolio)

    sheet_index_portfolios = fs.get_sheet_index(wb, "display_portfolios") - 1
    sheet_index_portfolios_forwards = fs.get_sheet_index(wb, "display_portfolios_forwards") - 1
    sheet_index_grouped_forwards = fs.get_sheet_index(wb, "display_grouped_forwards") - 1
    sheet_index_spreads_portfolios = fs.get_sheet_index(wb, "display_spreads_portfolios") - 1
    sheet_index_dashboard_re = fs.get_sheet_index(wb, "display_dashboard_re") - 1
    path_out_portfolios = fs.get_self_path()+"output\\1.pdf"
    fs.export_sheet_pdf(sheet_index_portfolios, ".", path_out_portfolios)
    path_out_portfolios_forwards = fs.get_self_path()+"output\\2.pdf"
    fs.export_sheet_pdf(sheet_index_portfolios_forwards, ".", path_out_portfolios_forwards)
    path_out_grouped_forwards = fs.get_self_path()+"output\\3.pdf"
    fs.export_sheet_pdf(sheet_index_grouped_forwards, ".", path_out_grouped_forwards)
    path_out_spreads_portfolios = fs.get_self_path()+"output\\4.pdf"
    fs.export_sheet_pdf(sheet_index_spreads_portfolios, ".", path_out_spreads_portfolios)
    path_out_dashboard_re = fs.get_self_path()+"output\\5.pdf"
    fs.export_sheet_pdf(sheet_index_dashboard_re, ".", path_out_dashboard_re)
    # Guardamos y cerramos el excel
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)
    # Consolidamos todos los documentos en uno y luego los borramos
    fs.merge_pdf(path=".\\output\\", output_name="dashboard_rates_fx.pdf")
    fs.delete_file(path_out_portfolios)
    fs.delete_file(path_out_portfolios_forwards)
    fs.delete_file(path_out_grouped_forwards)
    fs.delete_file(path_out_spreads_portfolios)
    fs.delete_file(path_out_dashboard_re)

    # Guardamos backup
    name = "Dashboard_Rates_FX_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    src = ".\\output\\dashboard_rates_fx.pdf"
    dst = "L:\\Rates & FX\\fsb\\reporting\\portfolio_dashboard_backup\\" + name
    fs.copy_file(src, dst)


def get_ep_benchmark_last_date():
    '''
    Retorna la fecha más reciente del portafolio del fondo E de AFPs
    '''
    path = ".\\querys_portfolio_dashboard\\ep_benchmark_last_date.sql"
    query = fs.read_file(path=path)
    bmk_last_date = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    date_string = bmk_last_date.strftime('%Y-%m-%d')
    return date_string


def get_ep_benchmark(date):
    '''
    Retorna los cortes del portafolio del fondo E de AFPs
    '''
    path_duration = ".\\querys_portfolio_dashboard\\ep_benchamrk_duracion.sql"
    path_moneda = ".\\querys_portfolio_dashboard\\ep_benchamrk_moneda.sql"
    path_posicionamiento = ".\\querys_portfolio_dashboard\\ep_benchamrk_posicionamiento.sql"
    path_plazos = ".\\querys_portfolio_dashboard\\ep_benchamrk_plazos.sql"
    path_inv_extranjero = ".\\querys_portfolio_dashboard\\ep_benchamrk_inv_extranjero.sql"
    path_RF_soberano = ".\\querys_portfolio_dashboard\\ep_benchmark_RF_soberano.sql"

    query_duration = fs.read_file(path=path_duration).replace("autodate", date)
    query_moneda = fs.read_file(path=path_moneda).replace("autodate", date)
    query_posicionamiento = fs.read_file(path=path_posicionamiento).replace("autodate", date)
    query_plazos = fs.read_file(path=path_plazos).replace("autodate", date)
    query_inv_extranjero = fs.read_file(path=path_inv_extranjero).replace("autodate", date)
    query_RF_soberano = fs.read_file(path=path_RF_soberano)

    ep_benchmark_duration = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query_duration)
    ep_benchmark_moneda = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query_moneda)
    ep_benchmark_posicionamiento = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query_posicionamiento)
    ep_benchmark_plazos = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query_plazos)
    ep_benchmark_inv_extranjero = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query_inv_extranjero)
    ep_benchmark_RF_soberano = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query_RF_soberano)
    ep_benchmark_duration.set_index(["Fecha"], inplace=True)
    ep_benchmark_moneda.set_index(["Fecha"], inplace=True)
    ep_benchmark_posicionamiento.set_index(["Fecha"], inplace=True)
    ep_benchmark_plazos.set_index(["Fecha"], inplace=True)
    ep_benchmark_inv_extranjero.set_index(["Fecha"], inplace=True)
    
    return ep_benchmark_duration, ep_benchmark_moneda, ep_benchmark_posicionamiento, ep_benchmark_plazos, ep_benchmark_inv_extranjero, ep_benchmark_RF_soberano


def compute_dashboards(portfolios, forwards_portfolios, grouped_forwards, spreads_re, spreads_ep, re_benchmark_portfolio, clf, ep_benchmark_posicionamiento, ep_benchmark_moneda, ep_benchmark_duration, ep_benchmark_plazos, ep_benchmark_inv_extranjero, re_subportfolio, ep_subportfolio, table_soberanos, matrix):
    '''
    Formatea el dataframe para trabajarlo mas facil
    '''
    wb = fs.open_workbook("portfolio_dashboard.xlsx", True, True)
    fs.clear_sheet_xl(wb, "portfolios")
    fs.clear_sheet_xl(wb, "forwards_portfolios")
    fs.clear_sheet_xl(wb, "grouped_forwards")
    fs.clear_sheet_xl(wb, "parameters")
    fs.clear_sheet_xl(wb, "spreads_portfolio_re")
    fs.clear_sheet_xl(wb, "spreads_portfolio_ep")
    fs.clear_sheet_xl(wb, "parameters")
    fs.clear_sheet_xl(wb, "re_benchmark_portfolio")
    fs.clear_sheet_xl(wb, "ep_benchmark_portfolio")
    fs.clear_sheet_xl(wb, "re_subportfolio")
    fs.clear_sheet_xl(wb, "ep_subportfolio")
    fs.clear_sheet_xl(wb, "matrix")
    fs.paste_val_xl(wb, "portfolios", 1, 1, portfolios)
    fs.paste_val_xl(wb, "forwards_portfolios", 1, 1, forwards_portfolios)
    fs.paste_val_xl(wb, "grouped_forwards", 1, 1, grouped_forwards)
    fs.paste_val_xl(wb, "spreads_portfolio_re", 1, 1, spreads_re)
    fs.paste_val_xl(wb, "spreads_portfolio_ep", 1, 1, spreads_ep)
    fs.paste_val_xl(wb, "parameters", 1, 1, clf)
    fs.paste_val_xl(wb, "re_benchmark_portfolio", 1, 1, re_benchmark_portfolio)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 1, ep_benchmark_posicionamiento)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 6, ep_benchmark_moneda)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 11, ep_benchmark_duration)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 16, ep_benchmark_plazos)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 21, ep_benchmark_inv_extranjero)
    fs.paste_val_xl(wb, "re_subportfolio", 1, 1, re_subportfolio)
    fs.paste_val_xl(wb, "ep_subportfolio", 1, 1, ep_subportfolio)
    fs.paste_val_xl(wb, "sovereign_comparison", 1, 1, table_soberanos)
    fs.paste_val_xl(wb, "matrix", 1, 1, matrix)

    sheet_index_portfolios = fs.get_sheet_index(wb, "display_portfolios") - 1
    sheet_index_portfolios_forwards = fs.get_sheet_index(wb, "display_portfolios_forwards") - 1
    sheet_index_grouped_forwards = fs.get_sheet_index(wb, "display_grouped_forwards") - 1
    sheet_index_spreads_portfolios = fs.get_sheet_index(wb, "display_spreads_portfolios") - 1
    sheet_index_dashboard_re = fs.get_sheet_index(wb, "display_dashboard_re") - 1
    sheet_index_dashboard_ep = fs.get_sheet_index(wb, "display_dashboard_ep") - 1
    sheet_index_dashboard_macros = fs.get_sheet_index(wb, "display_dashboard_macros") - 1
    path_out_portfolios = fs.get_self_path()+"output\\1.pdf"
    fs.export_sheet_pdf(sheet_index_portfolios, ".", path_out_portfolios)
    path_out_portfolios_forwards = fs.get_self_path()+"output\\2.pdf"
    fs.export_sheet_pdf(sheet_index_portfolios_forwards, ".", path_out_portfolios_forwards)
    path_out_grouped_forwards = fs.get_self_path()+"output\\3.pdf"
    fs.export_sheet_pdf(sheet_index_grouped_forwards, ".", path_out_grouped_forwards)
    path_out_spreads_portfolios = fs.get_self_path()+"output\\4.pdf"
    fs.export_sheet_pdf(sheet_index_spreads_portfolios, ".", path_out_spreads_portfolios)
    path_out_dashboard_re = fs.get_self_path()+"output\\5.pdf"
    fs.export_sheet_pdf(sheet_index_dashboard_re, ".", path_out_dashboard_re)
    path_out_dashboard_ep = fs.get_self_path()+"output\\6.pdf"
    fs.export_sheet_pdf(sheet_index_dashboard_ep, ".", path_out_dashboard_ep)
    path_out_dashboard_macros = fs.get_self_path()+"output\\7.pdf"
    fs.export_sheet_pdf(sheet_index_dashboard_macros, ".", path_out_dashboard_macros)
    # Guardamos y cerramos el excel
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)
    # Consolidamos todos los documentos en uno y luego los borramos
    fs.merge_pdf(path=".\\output\\", output_name="dashboard_rates_fx.pdf")
    fs.delete_file(path_out_portfolios)
    fs.delete_file(path_out_portfolios_forwards)
    fs.delete_file(path_out_grouped_forwards)
    fs.delete_file(path_out_spreads_portfolios)
    fs.delete_file(path_out_dashboard_re)
    fs.delete_file(path_out_dashboard_ep)
    fs.delete_file(path_out_dashboard_macros)

    # Guardamos backup
    name = "Dashboard_Rates_FX_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    src = ".\\output\\dashboard_rates_fx.pdf"
    dst = "L:\\Rates & FX\\fsb\\reporting\\portfolio_dashboard_backup\\" + name
    fs.copy_file(src, dst)

def send_mail_report():
    '''
    Envia el mail a fernando suarez y JPA. 
    '''
    subject = "Dashboard Portfolios Rates & FX"
    body = "Adjunto dashboard de tasas y monedas.\nSaludos,\nBot"
    mail_list = ["dposch@credicorpcapital.com"]
    mail_list = ["fsuarez@credicorpcapital.com", "fsuarez1@uc.cl"]#, "jparaujo@credicorpcapital.com"
    path = fs.get_self_path() + "output\\dashboard_rates_fx.pdf"
    paths = [path]
    fs.send_mail_attach(subject=subject,
                        body=body,
                        mails=mail_list,
                        attachment_paths=paths)
    fs.delete_file(path)




# Cerramos posibles instancias de Excel abiertas
fs.kill_excel()

spot_date = fs.get_ndays_from_today(0)

# Fijamos la fecha en la que empieza el dataset
# de la matriz de varianza covarianza
data_start_date = fs.get_ndays_from_date(365, spot_date)

# Fijamos la fecha para la cual se tomara
# el vector de weights de los portafolios
fund_date = fs.get_prev_weekday(spot_date)


# Fijamos la fecha para la cual se tomara
# el ultimo dato para la matriz de varianza-covarianza
data_end_date = fs.get_prev_weekday(fund_date)


#Fijamos la fecha del benchmark como la más reciente disponible
re_bmk_date = get_re_benchmark_last_date()
ep_bmk_date = get_ep_benchmark_last_date()

fund_ids = ("RENTA", "IMT E-PLUS", "MACRO 1.5", "MACRO CLP3")

# Obtenemos la uf
print("Fetching clf spot...")
clf = get_clf()

# Obtenemos el dataset con toda la informacion historica
print("Fetching historical dataset...")
dataset = rk.get_historical_dataset(data_start_date=data_start_date,
                                    data_end_date=data_end_date)


# Contruimos una matriz de varianza-covarianza
# exponentially weighted en base al dataset
print("Computing exponentially weighted covariance matrix...")
matrix = rk.get_ewma_cov_matrix(data=dataset, landa=0.94)


# Obtenemos la lista de los fondos con su {-informacion basica
# y obtenemos todos los portafolios activos con sus metricas de riesgo
print("Computing ex ante volatility...")
funds = rk.get_funds()
funds = funds[funds["codigo_fdo"].isin(fund_ids)]

# benchmark date e inflation son dummy values porque para
# este monitor y fondos no aplican
portfolios = rk.get_full_portfolio_metrics(matrix=matrix,
                                           funds=funds,
                                           fund_date=fund_date,
                                           benchmark_date=fund_date,
                                           inflation=0.03)

#print(10000*np.sum(portfolios[portfolios["codigo_fdo"]=="MACRO 1.5"]["ctr"]))
#print(portfolios[portfolios["codigo_fdo"]=="MACRO 1.5"].loc[49])
#exit()
# Descargamos los portfolios de forwards
print("Fetching forwards portfolios...")
forwards_portfolios = get_forwards_portfolios(spot_date, fund_ids)

print("Computing grouped forwards...")
# Obtenemos los forwards agrupados
grouped_forwards = compute_grouped_forwards(forwards_portfolios, fund_ids)

print("Computing portfolios spreads...")
# Obtenemos los spreads
spreads_re, spreads_ep = get_spreads_portfolios(data_end_date)


print("Computing benchmark portfolios...")
# Obtenemos la cartera del benchmark del e-plus
ep_benchmark_duration, ep_benchmark_moneda, ep_benchmark_posicionamiento, ep_benchmark_plazos, ep_benchmark_inv_extranjero, ep_benchmark_RF_soberano = get_ep_benchmark(ep_bmk_date)

# Obtenemos la cartera del benchmark del renta
re_benchmark_portfolio = get_re_benchmark(re_bmk_date)

print("Computing subportfolios...")
# Obtenemos las cuotas de fondos en nuestros portfolios
re_subportfolio = get_subportfolios(fund_date, "RENTA")
ep_subportfolio = get_subportfolios(fund_date, "IMT E-PLUS")

print("Computing display...")
# Formateamos los portfolios para el display
portfolios = reshape_portfolios(portfolios)

table_soberanos = compute_table_soberanos(portfolios, ep_benchmark_RF_soberano)

print("Printing dashboard...")
# Imprimimos dashboards en excel
compute_dashboards(portfolios, forwards_portfolios, grouped_forwards, spreads_re, spreads_ep, re_benchmark_portfolio, clf, ep_benchmark_posicionamiento, ep_benchmark_moneda, ep_benchmark_duration, ep_benchmark_plazos, ep_benchmark_inv_extranjero, re_subportfolio, ep_subportfolio, table_soberanos, matrix)

print("Sending mail...")
# Enviamos el dashboard por mail
send_mail_report()
 