"""
Created on Thu May 01 11:00:00 2016

@author: Fernando Suarez
"""

import os
import xlwings as xw
import pymssql
import datetime as dt
from win32com import client
from PyPDF2 import PdfFileReader, PdfFileMerger
import win32com.client
import json
import numpy as np
import pandas as pd
import sys
import paramiko
from tkinter import Tk
from tkinter.filedialog import asksaveasfilename
import re
import matplotlib.pyplot as plt
import seaborn as sns
from shutil import copyfile

'''FUNCIONES VARIAS'''

def dictinvert(mydict):
    '''
    Invierte un diccionario.
    '''
    return dict([[v,k] for k,v in mydict.items()])


def custom_round(x, base):
    '''
    Redondea un porcentaje a un multiplo, sirve
    para aplicar una funcion landa a un dataframe.
    '''
    return int(10000 * base * round(float(x)/base))/10000


def format_separators(n):
    '''
    Formatea un float n con comas y puntos decimales
    '''
    return  "{:,}".format(n)


def truncate(f, n):
    '''
    Trunca un numero a n digitos
    '''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])


def get_self_path():
	'''
	Retorna la ruta del codigo en python que lo llama.
	'''
	self_path=os.path.dirname(os.path.realpath(sys.argv[0]))+"\\"
	return self_path


def get_current_time():
	'''
	Retorna la hora actual.
	'''
	return dt.datetime.now().time().strftime("%H:%M:%S")


def get_prev_weekday(adate):
	'''
	Retorna la fecha en string del ultimo weekday dado una fecha en string.
	'''
	adate = convert_string_to_date(date_string = adate)
	adate -= dt.timedelta(days=1)
	while adate.weekday() > 4: # Mon-Fri are 0-4
		adate -= dt.timedelta(days=1)
	adate = convert_date_to_string(adate)
	return adate


def get_next_weekday(adate):
	'''
	Retorna la fecha en string del proximo weekday dado una fecha en string.
	'''
	adate = convert_string_to_date(date_string = adate)
	adate += dt.timedelta(days=1)
	while adate.weekday() > 4: # Mon-Fri are 0-4
		adate += dt.timedelta(days=1)
	adate = convert_date_to_string(adate)
	return adate


def get_dates_between(date_inic, date_fin):
	'''
	Retorna una lista con todas las fechas entre dos fechas dadas.
	'''
	day_list=pd.date_range(date_inic, date_fin).tolist()
	return day_list


def get_weekdays_dates_between(date_inic, date_fin):
	'''
	Retorna una lista con todas las fechas habiles entre dos fechas dadas.
	'''
	day_list =pd.date_range(date_inic, date_fin)
	day_list = day_list[day_list.dayofweek < 5].tolist()
	return day_list


def get_current_days_month(date):
	'''
	Retorna la cantidad de dias hasta el ultimo dia del mes pasado.
	'''
	days= date.timetuple().tm_mday+1
	return days


def get_current_days_year(date):
	'''
	Retorna la cantidad de dias hasta el anio pasado.
	'''
	days= date.timetuple().tm_yday+1
	return days

def get_current_weekdays_week(date):
	'''
	Retorna la cantidad de dias habiles hasta la semana pasada.
	'''
	return 2 +  date.weekday()


def get_current_weekdays_month(date):
	'''
	Retorna la cantidad de dias habiles hasta el ultimo dia del mes pasado.
	'''
	businessdays = 0
	for i in range(1, 32):
		try:
			thisdate = dt.date(date.year, date.month, i)
		except(ValueError):
			break
		if thisdate.weekday() < 5 and thisdate <= date: # Monday == 0, Sunday == 6 
			businessdays += 1
	return businessdays +1


def get_current_weekdays_year(date):
	'''
	Retorna la cantidad de dias habiles hasta el anio pasado.
	'''
	return np.busday_count( dt.date(date.year, 1, 1), date ) + 2


def get_dates_since(start_date, end_date):
	'''
	Retorna una lista con todas las fechas entre dos fechas particular.
	'''
	day_list=[]
	delta = end_date - start_date
	for i in range(delta.days + 1):
		day_list.append(start_date + dt.timedelta(days=i)) 

def get_ndays_from_today(days):
	'''
	Retorna la fecha n dias desde hoy.
	'''
	date = dt.datetime.now() - dt.timedelta( days = days )
	date=str(date.strftime('%Y-%m-%d'))
	return date


def get_ndays_from_date(days, date_string):
	'''
	Retorna la fecha n dias desde hoy.
	'''
	date = convert_string_to_date(date_string) - dt.timedelta( days = days )
	date=str(date.strftime('%Y-%m-%d'))
	return date


def get_nweekdays_from_date(days, date_string):
	'''
	Retorna la fecha n dias desde hoy.
	'''
	adate = convert_string_to_date(date_string = date_string)
	counter = -1
	while True:
		if adate.weekday() <= 4:
			counter += 1
		if counter == days:
			break 
		adate -= dt.timedelta(days = 1)
	return str(adate)


def convert_date_to_string(date):
	'''
	Retorna la fecha en formato de string, dado el objeto date.
	'''
	date_string=str(date.strftime('%Y-%m-%d'))
	return date_string


def convert_string_to_date(date_string):
	'''
	Retorna la fecha en formato date.
	'''
	date_formated=dt.datetime.strptime(date_string, '%Y-%m-%d').date()
	return date_formated


def convert_date_all_together(date):
	'''
	Retorna la fecha en formato con todos los caracteres juntos.
	'''
	date_formated=str(date.strftime('%Y%m%d'))
	return date_formated


def merge_pdf(path, output_name):
	'''
	Concatena todos los archivos PDF en una ubicacion dada y lo guarda en otro PDF con un nombre dado.
	'''
	files_dir = path
	pdf_files = [f for f in os.listdir(files_dir) if f.endswith(".PDF") or f.endswith(".pdf")]
	merger = PdfFileMerger()
	for filename in pdf_files:
	    merger.append(PdfFileReader(os.path.join(files_dir, filename), "rb"))
	merger.write(os.path.join(files_dir, output_name))


def delete_file(path):
	'''
	Borra un archivo.
	'''
	os.remove(path)


def delete_folder(path):
	'''
	Borra una carpeta.
	'''
	os.rmdir(path)


def read_file(path):
	'''
	Lee un archivo de texto y lo retorna como string.
	'''
	f=open(path,'r')
	file_string=f.read()
	f.close()
	return file_string


def copy_file(src, dst):
	'''
	Copia un archivo a otra ubicacion.
	'''
	copyfile(src, dst)


def open_file(path):
	'''
	Abre un archivo.
	'''
	os.startfile(path)


def convert_json_to_dict(json_string):
	'''
	Lee un string en formato JSON y lo retorna en un dictionary.
	'''
	json_dict=json.loads(json_string)
	return json_dict

	
'''FUNCIONES MATRICIALES'''
def array_to_numpy(arr):
	'''
	Transforma una matriz normal en una de numpy.
	'''
	return np.array(arr)


def get_vect_column(matrix, col_number):
	'''
	Dada una lista de listas retorna un vector con la columna.
	'''
	matrix_np=np.array(matrix)
	column=matrix_np[:,col_number]
	return column


def format_tuples(df):
    '''
    Transforma un dataframe en una lista de tuplas.
    '''
    serie_tuplas = [tuple(x) for x in df.values]
    return serie_tuplas


def print_full(x):
    '''
    Imprime un dataframe entero
    '''
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')


'''FUNCIONES SQL'''

def connect_database(server, database):
	'''
	Se conecta a una base de datos y retorna el objecto de la conexion, usando windows authentication.
	'''
	conn= pymssql.connect(host=server, database=database)
	return conn


def connect_database_user(server, database, username, password):
	'''
	Se conecta a una base de datos y retorna el objecto de la conexion, usando un usuario.
	'''
	conn= pymssql.connect(host=server, database=database, user=username, password=password)
	return conn


def query_database(conn, query):
	'''
	Consulta la la base de datos(conn) y devuelve el cursor asociado a la consulta.
	'''
	cursor=conn.cursor()
	cursor.execute(query)
	return cursor


def get_table_sql(cursor):
	'''
	Recibe un cursor asociado a una consulta en la BDD y la transforma en una matriz.
	'''
	table=[]
	row = cursor.fetchone()
	ncolumns=len(cursor.description)
	while row:
		col=0	
		vect=[]
		while col<ncolumns:
			vect.append(row[col])
			col=col+1
		row = cursor.fetchone()
		table.append(vect)
	return table


def get_list_sql(cursor):
	'''
	Recibe un cursor asociado a una consulta en la BDD y la transforma en un lista, solo usarlo cuando la consulta retorne una columna.
	'''
	lista=[]
	row = cursor.fetchone()
	while row:	
		escalar=row[0]
		row = cursor.fetchone()
		lista.append(escalar)
	return lista


def get_schema_sql(cursor):
	'''
	Recibe un cursor asociado a una consulta en la BDD y retorna el esquema de la relacion en una lista.
	'''
	schema = []
	for i in range(len(cursor.description)):
		prop = cursor.description[i][0]
		schema.append(prop)
	return schema


def disconnect_database(conn):
	'''
	Se deconecta a una base de la datos.
	'''
	conn.close()


def run_sql(conn, query):
    '''
    Ejecuta un statement en SQL, por ejemplo borrar.
    '''
    cursor=conn.cursor()
    cursor.execute(query)
    conn.commit()


def get_frame_sql_user(server, database, username, password, query):
    '''
    Retorna el resultado de la query en un panda's dataframe con usuario y clave. 
    '''
    conn = connect_database_user(server = server, database = database, username = username, password = password)
    cursor = query_database(conn, query)
    schema = get_schema_sql(cursor = cursor)
    table = get_table_sql(cursor)
    dataframe = pd.DataFrame(data = table, columns = schema)
    disconnect_database(conn)
    return dataframe


def get_frame_sql(server, database, query):
    '''
    Retorna el resultado de la query en un panda's dataframe. 
    '''
    conn = connect_database(server = server, database = database)
    cursor = query_database(conn, query)
    schema = get_schema_sql(cursor = cursor)
    table = get_table_sql(cursor)
    dataframe = pd.DataFrame(data = table, columns = schema)
    disconnect_database(conn)
    return dataframe


def get_val_sql_user(server, database, username, password, query):
    '''
    Retorna el resultado de la query en una variable. 
    '''
    conn = connect_database_user(server = server, database = database, username = username, password = password)
    cursor = query_database(conn, query)
    table = get_table_sql(cursor)
    val = table[0][0]
    disconnect_database(conn)
    return val


def get_val_sql(server, database, query):
    '''
    Retorna el resultado de la query en una variable. 
    '''
    conn = connect_database_user(server = server, database = database)
    cursor = query_database(conn, query)
    table = get_table_sql(cursor)
    val = table[0][0]
    disconnect_database(conn)
    return val


'''FUNCIONES EXCEL'''

def create_workbook():
	'''
	Crea un workbook.
	'''
	wb = xw.Book()
	return wb


def open_workbook(path, screen_updating, visible):
	'''
	Abre un workbook y retorna un objecto workbook de xlwings. Sin screen_updating es false es mas rapido.
	'''
	wb = xw.Book(path)
	if screen_updating == False:		
		wb.app.screen_updating = False
	else:
		wb.app.screen_updating = True
	if visible == False:
		wb.app.visible = False
	else:
		wb.app.visible = True
	return wb


def save_workbook(wb, path = ""):
	'''
	Guarda un workbook.
	'''
	if path == "":
		wb.save()
	else:
		wb.save(path)


def close_workbook(wb):
	'''
	Cierra un workbook.
	'''
	wb.close()


def close_excel(wb):
	'''
	Cierra un Excel.
	'''
	app = wb.app
	app.quit()


def kill_excel():
	'''
	Mata el proceso de Excel.
	'''
	try:
		os.system('taskkill /f /im Excel.exe')
	except:
		print("no hay excels abiertos")


def clear_table_xl(wb, sheet, row, column):
	'''
	Recibe el rango asociado y borra la tabla considerando que el rango esta en el top-left corner de la tabla.
	'''
	wb.sheets[sheet].range(row,column).expand('table').clear_contents()


def clear_column_xl(wb, sheet, row, column):
	'''
	Recibe el rango asociado y borra la tabla considerando que el rango esta en el top-left corner de la tabla.
	'''
	wb.sheets[sheet].range(row,column).expand('down').clear_contents()


def paste_val_xl(wb, sheet, row, column,value):
	'''
	Inserta un valor en una celta de excel dada la hoja. 
	'''
	wb.sheets[sheet].range(row,column).value = value


def paste_col_xl(wb, sheet, row, column, serie):
	'''
	Inserta un valor en una celta de excel dada la hoja. 
	'''
	for val in serie:
		wb.sheets[sheet].range(row,column).value = val
		row += 1


def paste_query_xl(wb, server, database, query, sheet, row, column, with_schema):
	'''
	Consulta a la base de datos y pega el resultado en una hoja de excel en una determinada fila y columna. Si with_schema es verdadero, la pega con
	los nombres de columnas, en otro caso solo pega los valores. 
	'''
	conn= connect_database(server,database)
	cursor=query_database(conn, query)
	table=get_table_sql(cursor)
	disconnect_database(conn)
	if with_schema:
		schema=get_schema_sql(cursor)
		paste_val_xl(wb, sheet, row, column, schema)
		paste_val_xl(wb, sheet, row+1, column, table)
	else:		
		paste_val_xl(wb, sheet, row, column, table)


def paste_query_xl_user(wb, server, database, query, sheet, row, column, with_schema, username, password):
	'''
	Consulta a la base de datos y pega el resultado en una hoja de excel en una determinada fila y columna. Si with_schema es verdadero, la pega con
	los nombres de columnas, en otro caso solo pega los valores. Esta funcion es igual a la anterior pero se conecta a la BDD con usuario y pass.
	'''
	conn= connect_database_user(server,database, username, password)
	cursor=query_database(conn, query)
	table=get_table_sql(cursor)
	disconnect_database(conn)
	if with_schema:
		schema=get_schema_sql(cursor)
		paste_val_xl(wb, sheet, row, column, schema)
		paste_val_xl(wb, sheet, row+1, column, table)
	else:		
		paste_val_xl(sheet, row, column, table)


def get_sheet_index(wb, sheet):
	'''
	Retorna el indice e una hoja, dado su nombre.
	'''
	return wb.sheets[sheet].index


def export_sheet_pdf(sheet_index, path_in, path_out):
	'''
	Exporta una hoja de Excel en PDF. 
	'''
	xlApp = client.Dispatch("Excel.Application")
	books = xlApp.Workbooks(1)
	ws = books.Worksheets[sheet_index]
	ws.ExportAsFixedFormat(0, path_out)


def get_value_xl(wb, sheet, row, column):
	'''
	Retorna el valor de una celda dado un rango y la hoja.
	'''
	return wb.sheets(sheet).range(row,column).value


def get_column_xl(wb, sheet, row, column):
	'''
	Retorna la columna en una lista, dado un rango y la hoja.
	'''
	return wb.sheets(sheet).range(row,column).expand('down').value


def get_table_xl(wb, sheet, row, column):
	'''
	Retorna la tabla en un arreglo, dado un rango y la hoja.
	'''
	return wb.sheets[sheet].range(row,column).expand('table').value


def get_frame_xl(wb, sheet, row, column, index_pos):
	'''
	Retorna la tabla en un dataframe, dado un rango y la hoja.
	Ademas se le da la posicion de las columnas a indexar
	'''
	table = get_table_xl(wb, sheet, row, column)
	data = table[1:]
	columns = np.array(table[0])
	table = pd.DataFrame(data, columns=columns)
	table.set_index(columns[index_pos].tolist(), inplace=True)
	return table


def clear_sheet_xl(wb, sheet):
	'''
	Borra todos los contenidos de una hoja de excel.
	'''
	return wb.sheets[sheet].clear_contents()


'''FUNCIONES PPT'''

def openPPT(filename):
	'''
	Abre un ppt en el mismo programa powerpoint 2014.
	'''
	os.system("\"C:\\Program Files\\Microsoft Office\\Office14\\POWERPNT.EXE\" "+ filename)

'''FUNCIONES MAIL'''

def send_mail_attach(subject, body, mails, attachment_paths, html=False):
	'''
	#Envia un mail a todos los correos en el arreglo mails y les adjunta todos los archivos del otro arreglo.
	'''
	#os.startfile("outlook") #antes lo hacia con esto pero el problema es que no se puede cerrar outlook
	const=win32com.client.constants
	olMailItem = 0x0
	obj = win32com.client.gencache.EnsureDispatch("Outlook.Application")
	newMail = obj.CreateItem(olMailItem)
	newMail.Subject = subject

	if html == True:
		newMail.HTMLBody = body
	else:
		newMail.Body = body

	cadena = ""
	for mail in mails:
		mail = mail+";"
		cadena = cadena+mail
	cadena=cadena[:-1] # los mails se mandan separados por ; en una cadena
	newMail.To = cadena
	for att in attachment_paths:
		newMail.Attachments.Add(Source=att)
	#attachment1 = at
	#newMail.Attachments.Add(Source=attachment1)
	#print(newMail.display())
	#newMail.Send()
	try:
		newMail.Send()
		print("Correo enviado")
	except:
		print("Fallo el envio del correo")


def send_mail(subject, body, mails, html=False):
	'''
	#Envia un mail a todos los correos en el arreglo mails.
	'''
	#os.startfile("outlook") #antes lo hacia con esto pero el problema es que no se puede cerrar outlook
	const=win32com.client.constants
	olMailItem = 0x0
	obj = win32com.client.gencache.EnsureDispatch("Outlook.Application")
	newMail = obj.CreateItem(olMailItem)
	newMail.Subject = subject
	
	if html == True:
		newMail.HTMLBody = body
	else:
		newMail.Body = body

	cadena = ""
	for mail in mails:
		mail = mail+";"
		cadena = cadena+mail
	cadena=cadena[:-1] # los mails se mandan separados por ; en una cadena
	newMail.To = cadena
	try:
		newMail.Send()
		print("Correo enviado")
	except:
		print("Fallo el envio del correo")


def fetch_attachment(message_regex, attachment_regex, output_path):
    '''
    Descarga un archivo adjunto a un mail dado ambos nombres. Notar, que
    el nombre del mensaje y archivo son automatas finitos deterministas.
    '''
    message_regex = re.compile(message_regex)
    attachment_regex = re.compile(attachment_regex)
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder("6")
    all_inbox = inbox.Items
    for msg in all_inbox:
        if message_regex.match(msg.Subject):
            break
    for att in msg.Attachments:
        if attachment_regex.match(att.FileName):
            att.SaveAsFile(output_path)
            break
    


'''FUNCIONES FTP'''

def download_data_sftp(host, username, password, origin, destination, port):
	'''
	Descarga un archivo desde un SFTP en una ubicacion dada, hay que usar paramiko, si no funciona tal vez bajar el whl. Ejemplo: 
	host = "sftp.riskamerica.com"
	username = "AGF_Credicorp"
	pw = "dX{\"4YjA"
	origin = './out/Composicion_Indice_IMTRUST_20161005.csv'
	dst = 'C://Users/fsuarezb/Desktop/Composicion_Indice_IMTRUST_20161006.csv'
	port = 22
	downloadDataSFTP(host, username, pw, origin, dst, port)
	'''
	sftp = None
	ftp_open = False
	transport = paramiko.Transport((host, port))
	transport.connect(username=username, password=password)
	sftp = paramiko.SFTPClient.from_transport(transport)
	sftp_open = True
	sftp.get(origin, destination)
	if sftp_open:
		sftp.close()
		sftp_open = False
	transport.close()


'''FUNCIONES SSH'''

def connect_ssh(host, username, password, port):
    '''
    Se conecta a un servidor via ssh y devuelve un objeto cliente.
    '''
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port, username, password)
    return client


'''FUNCIONES UI'''

def get_file_path_ui(default_name, extension):
	'''
	Abre un dialog para seleccionar un path con nombre de archivo para guardar. la extension es un string que empieza con un punto.
	'''
	Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
	opts = {}
	opts['initialfile'] = default_name
	opts['filetypes'] = [('Supported types',(extension))]
	file_path = asksaveasfilename(**opts) # show an "Open" dialog box and return the path to the selected file
	return file_path


'''FUNCIONES PARA PLOTEAR'''


def plot_curves_dark(curves, days):
    '''
    Grafica dos curvas.
    '''
    sns.set_style("darkgrid")
    bg_color = 'black'
    fg_color = 'white'
    plt.figure(facecolor=bg_color, edgecolor=fg_color)
    axes = plt.axes((0.1, 0.1, 0.8, 0.8), axisbg=bg_color)
    axes.xaxis.set_tick_params(color=fg_color, labelcolor=fg_color)
    axes.yaxis.set_tick_params(color=fg_color, labelcolor=fg_color)
    for spine in axes.spines.values():
        spine.set_color(fg_color)
    for curve in curves:
        plt.plot(days, curve, linestyle='-', color=np.random.rand(3,))
    plt.xlabel('$date$', color=fg_color)
    plt.ylabel('$gain$', color=fg_color)
    plt.show()

def plot_curves(curves):
    '''
    Grafica dos curvas.
    '''
    tenors = curves[0].index
    sns.set_style("darkgrid")
    for curve in curves:
        plt.plot(tenors, curve, linestyle='-', color=np.random.rand(3,))
    plt.xlabel('$x$')
    plt.ylabel('$y$')
    plt.show()