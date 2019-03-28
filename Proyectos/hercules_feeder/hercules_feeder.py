"""
Created on Wed Mar 29 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import sqlite3


def fetch_indices(ids):
    '''
    Descargamos indices estatica.
    '''
#    query = "select index_id, ticker, moneda, nombre_index, zona, renta from indices_estatica where index_id in " + str(ids)
    query = "select index_id, ticker, moneda, nombre_index, zona, renta from indices_estatica"
    indices = fs.get_frame_sql_user(server = "Puyehue",
                                 database = "MesaInversiones",
                                 username = "usrConsultaComercial",
                                 password = "Comercial1w",
                                 query = query)
    return indices


def fetch_historical_data(data_start_date, ids):
    '''
    Descargamos la data historica de indices dinamica.
    '''
    #query = "select CONVERT(char(10), fecha,126) as fecha, index_id, valor from indices_dinamica where fecha >= 'autodate' and index_id in " + str(ids)
    query = "select CONVERT(char(10), fecha,126) as fecha, index_id, valor from indices_dinamica where fecha >= 'autodate'"
    query = query.replace("autodate", data_start_date)
    data = fs.get_frame_sql_user(server = "Puyehue",
                              database = "MesaInversiones",
                              username = "usrConsultaComercial",
                              password = "Comercial1w",
                              query = query)
    return data


def fetch_local_data(data_start_date, ids):
    '''
    Descargamos la base de datos local.
    '''
    indices = fetch_indices(ids)
    historical_data = fetch_historical_data(data_start_date, ids)
    return indices, historical_data

 
def update_emperor_database(db_name, indices, historical_data):
    '''
    Actualiza localmente emperor.db.
    '''
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM indices_dinamica WHERE 1=1")
    conn.commit()
    cursor.execute("DELETE FROM indices_estatica WHERE 1=1")
    conn.commit()
    indices = fs.format_tuples(indices)
    historical_data = fs.format_tuples(historical_data)
    cursor.executemany('INSERT INTO indices_estatica VALUES (?,?,?,?,?,?)', indices)
    conn.commit()
    cursor.executemany('INSERT INTO indices_dinamica VALUES (?,?,?)', historical_data)
    conn.commit()
    cursor.close()
    conn.close()


def update_hercules(host, port, username, password, db_name):
    '''
    Actualiza hercules.
    '''
    client = fs.connect_ssh(host, username, password, port)
    delete_statement = "cd Desarrollo; rm " + db_name
    stdin, stdout, stderr = client.exec_command(delete_statement)
    sftp = client.open_sftp()
    remote_path = "/home/fsuarez/Desarrollo/" + db_name
    sftp.put(db_name, remote_path)
    client.close()


# Definimos variables a utilizar
spot_date = fs.get_ndays_from_today(0)
data_start_date = "2016-01-01"
host = "hercules.ing.puc.cl"
port = 22
username = "fsuarez"
password = "datapuc" #nomesemiclave si volvemos a manjaro
db_name = "emperor.db"
ids = (209, 184, 250, 235, 201, 207, 438, 189, 472, 473)


print("fetching local database...")
indices, historical_data = fetch_local_data(data_start_date, ids)

print("updating emperor database...")
update_emperor_database(db_name, indices, historical_data)

print("updating hercules...")
update_hercules(host, port, username, password, db_name)


'''
# Nos conectamos al servidor

print("connecting to doge...")
client = fs.connect_ssh(host, username, password, port)

print("cleanning remote database...")
# Borramos indices dinamica del servidor
delete_remote_data(client, open_db_statement)

print("fetching local database...")
indices, historical_data = fetch_local_data(data_start_date, ids)


print("updating remote database...")
upload_data(client, open_db_statement, indices, historical_data)


client.close()
'''

'''
Ejemplos para consultas y updates bdd
query = cd_db_statement + open_db_statement + " \'SELECT * FROM indices_estatica \'"
print(query)

stdin, stdout, stderr = client.exec_command("cd Desarrollo; cd database; sqlite3 emperor.db \'insert into indices_estatica (Index_Id, Ticker, Moneda, Nombre_Index, Zona, Renta) VALUES (2, \"asdf\", \"$\", \"IPSA\", \"Local\", \"Variable\");\'")
print(stderr.readlines())

stdin, stdout, stderr = client.exec_command("cd Desarrollo; cd database; sqlite3 emperor.db \'SELECT * FROM indices_estatica \'")
print(stdout.readlines())

stdin, stdout, stderr = client.exec_command("cd Desarrollo; cd database; sqlite3 emperor.db \'delete from indices_estatica where index_id = 2;\'")
print(stderr.readlines())

stdin, stdout, stderr = client.exec_command("cd Desarrollo; cd database; sqlite3 emperor.db \'SELECT * FROM indices_estatica \'")
print(stdout.readlines())


Ejemplos para manejar archivos etc en ssh

sftp = client.open_sftp()
sftp.put('.\\oli.txt', '/home/fsuarez1/oli.txt')


stdin, stdout, stderr = client.exec_command('ls')
print(stdout.readlines())


stdin, stdout, stderr = client.exec_command('rm oli.txt')
stdin, stdout, stderr = client.exec_command('ls')
print(stdout.readlines())
'cd Desarrollo; cd database; sqlite3 emperor.db insert into indices_estatica (Index_Id, Ticker, Moneda, Nombre_Index, Zona, Renta) VALUES (1, 'Ipsa Index', '$', 'IPSA', 'Local', 'Variable')'

'''