"""
Created on Wed Mar 29 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np


def get_portfolios(portfolios_date, spot_date):
    '''
    Entrega los portfolios de los fondos.
    '''
    query_path = ".\\querys\\portfolios.sql"
    query = fs.read_file(query_path)
    query = query.replace("autodate", portfolios_date)
    portfolios = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=query)
    portfolios["dias"] = (pd.to_datetime(portfolios["fec_vcto"] ) - fs.convert_string_to_date(spot_date)).astype('timedelta64[D]')
    portfolios["dias"] = portfolios["dias"].astype(int)
    portfolios = portfolios.drop("fec_vcto", 1)
    portfolios.set_index(["codigo_fdo", "codigo_emi", "codigo_ins", "dias"], inplace=True)
    return portfolios

def get_sell_transactions(date, type):
    '''
    Entrega las ventas del dia.
    '''
    if type == "money_market":
        query_path = ".\\querys\\money_market_sells.sql"
    elif type == "fixed_income":
        query_path = ".\\querys\\fixed_income_sells.sql"
    query = fs.read_file(query_path)
    query = query.replace("autodate", date)
    sell_transactions = fs.get_frame_sql_user(server="Puyehue",
                                              database="MesaInversiones",
                                              username="usrConsultaComercial",
                                              password="Comercial1w",
                                              query=query)
    if type == "money_market":
        sell_transactions.set_index(["codigo_fdo", "codigo_emi", "codigo_ins", "dias"], inplace=True)
    elif type == "fixed_income":
        sell_transactions.set_index(["codigo_fdo", "codigo_ins"], inplace=True)
    return sell_transactions

def get_inconsistent_sells(portfolios, money_market_sell_transactions, fixed_income_sell_transactions):
    '''
    Entrega un dataframe con las ventas inconsistentes.
    '''
    # fs.print_full(portfolios[portfolios.index.get_level_values("codigo_fdo") == "MACRO CLP3"])
    # Chequeamos intermediacion financiera
    #fs.print_full(portfolios)
    #fs.print_full(money_market_sell_transactions)

    money_market_sell_transactions["check"] = None
    for i, instrument in money_market_sell_transactions.iterrows():

        money_market_sell_transactions.set_value(i, "check", 1)

        try:
            print(i, '\n'*2)
            position = portfolios.loc[i, "nominal"]
            if position.values < instrument["nominal"]:
                money_market_sell_transactions.set_value(i, "check", 0)
        except KeyError:
    	       money_market_sell_transactions.set_value(i, "check", 0)

    portfolios = portfolios.reset_index()
    portfolios.set_index(["codigo_fdo", "codigo_ins"], inplace=True)
    fixed_income_sell_transactions["check"] = None
    for i, instrument in fixed_income_sell_transactions.iterrows():
    	fixed_income_sell_transactions.set_value(i, "check", 1)	
    	try:
    	    position = float(portfolios.loc[i, "nominal"])
    	    if position < instrument["nominal"]:
    	    	fixed_income_sell_transactions.set_value(i, "check", 0)
    	except KeyError:
    	    	fixed_income_sell_transactions.set_value(i, "check", 0)
    inconsistent_sells_fixed_income = fixed_income_sell_transactions[fixed_income_sell_transactions["check"] == 0]
    inconsistent_sells_money_market = money_market_sell_transactions[money_market_sell_transactions["check"] == 0]
    
    return inconsistent_sells_money_market, inconsistent_sells_fixed_income

def send_mail_report(inconsistent_sells_money_market, inconsistent_sells_fixed_income):
    '''
    Envia el mail a fernando suarez 1313. 
    '''
    current_time = fs.get_current_time()
    subject = "Reporte de Integridad Operaciones IIF-RF"
    body = "Status de operaciones para las " + str(current_time) + ":"  + "\n\n" + "Inconsistent sells IIF: \n" + str(inconsistent_sells_money_market)+ "\n\n" + "Inconsistent sells IRF: \n" + str(inconsistent_sells_fixed_income)
    mail_list = ["fsuarez@credicorpcapital.com", "dposch@credicorpcapital.com", 
                 "adarquea@credicorpcapital.com", "mcortes@credicorpcapital.com",
                 "jparaujo@credicorpcapital.com", "kkaempfe@credicorpcapital.com",
                 "rbarros@credicorpcapital.com", "coyarzun@credicorpcapital.com"]
    fs.send_mail(subject=subject, body=body, mails=mail_list)


print("getting dates...")
# Obtenemos las fechas
spot_date = fs.get_ndays_from_today(0)
portfolios_date = fs.get_prev_weekday(spot_date)

print("fetching portfolios...")
# Obtenemos los portfolios
portfolios = get_portfolios(portfolios_date, spot_date)


print("fetching transactions...")
# Obtenemos ventas iif
money_market_sell_transactions = get_sell_transactions(spot_date, "money_market")
fixed_income_sell_transactions = get_sell_transactions(spot_date, "fixed_income")


print("verifying status...")
# Chequeamos no haber vendido algo que no teniamos
inconsistent_sells_money_market, inconsistent_sells_fixed_income = get_inconsistent_sells(portfolios,
                                              	                                          money_market_sell_transactions,
	                                                                                      fixed_income_sell_transactions)

print("sending mail...")
# Enviamos el correo
send_mail_report(inconsistent_sells_money_market, inconsistent_sells_fixed_income)
print(inconsistent_sells_money_market)
print(inconsistent_sells_fixed_income)
