"""
Created on Wed Mar 29 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np



def fetch_nav(type, key):
    '''
    Descarga los nav.
    '''

    path = ".\\querys\\" + type + ".sql"
    query = fs.read_file(path)
    nav= fs.get_frame_sql_user(server="Puyehue",
    	   				       database="MesaInversiones",
    						   username="usrConsultaComercial",
    						   password="Comercial1w",
    						   query=query)
    nav.set_index(key, inplace=True)
    return nav

def fetch_fund_ids():
    '''
    Descarga los id de los fondos.
    '''

    path = ".\\querys\\fund_id.sql"
    query = fs.read_file(path)
    fund_ids= fs.get_frame_sql(server="10.80.154.223",
    	                       database="AndeanDB",
    	                       query=query)
    fund_ids = fund_ids["fund_id"]
    fund_ids = fund_ids.tolist()
    return fund_ids


def delete_old_data(fund_ids):
    '''
    Borra los datos antiguos.
    '''
    statement_fund = "delete from historical_fund_nav where fund_id in " + str(fund_ids).replace("[", "(").replace("]", ")")
    statement_bmk = "delete from historical_benchmark_nav where fund_id in " + str(fund_ids).replace("[", "(").replace("]", ")")
    conn = fs.connect_database(server="10.80.154.223",
                               database="AndeanDB")
    fs.run_sql(conn, statement_fund)
    fs.run_sql(conn, statement_bmk)
    fs.disconnect_database(conn)


def upload_dataset_db(portfolio_nav, benchmark_nav):
    '''
    UPLOAD DATASET BBDD

    '''
    tuplas_portfolio_nav = portfolio_nav.reset_index()
    tuplas_benchmark_nav = benchmark_nav.reset_index()
    tuplas_portfolio_nav = fs.format_tuples(df=tuplas_portfolio_nav)
    tuplas_benchmark_nav = fs.format_tuples(df=tuplas_benchmark_nav)
    conn = fs.connect_database(server="10.80.154.223",
                               database="AndeanDB")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO historical_fund_nav VALUES (%s,%s,%s,%s,%d,%d,%d)", tuplas_portfolio_nav)
    conn.commit()
    cursor.executemany("INSERT INTO historical_benchmark_nav VALUES (%s,%s,%s,%d)", tuplas_benchmark_nav)
    conn.commit()
    fs.disconnect_database(conn)


print("fetching porfolio navs...")
# Obtenemos la serie de los fondos
portfolio_nav = fetch_nav("portfolio_nav", ["date", "fund_id", "country_id", "fund_serie"])

print("fetching benchmark navs...")
# Obtenermos la serie de los benchmark 
benchmark_nav = fetch_nav("benchmark_nav", ["date", "fund_id", "country_id"])

print("fetching fund ids...")
# Obtenemos los codigos de fondo
fund_ids = fetch_fund_ids()

print("deleting old data...")
# Borramos las tuplas antighuas de la bdd
delete_old_data(fund_ids)

print("uploading new data...")
# Borramos las tuplas antighuas de la bdd
upload_dataset_db(portfolio_nav, benchmark_nav)
