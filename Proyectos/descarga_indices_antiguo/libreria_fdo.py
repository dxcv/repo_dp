"""
Created on Thu May 01 11:00:00 2016

@author: Fernando Suarez
"""

#from pptx import Presentation
import os
import xlwings as xw
import math
from os import getenv
import pymssql
import datetime as dt
from win32com import client
from PyPDF2 import PdfFileReader, PdfFileMerger
import win32com.client
from win32com.client import Dispatch, constants
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import random
import paramiko


'''FUNCIONES VARIAS'''
def getSelfPath():
	'''
	Retorna la fecha del dia de ayer.
	'''
	self_path=os.path.dirname(os.path.realpath(sys.argv[0]))+"\\"
	return self_path

def getDatesBetween(date_inic, date_fin):
	'''
	Retorna una lista con todas las fechas entre dos fechas dadas.
	'''
	day_list=pd.date_range(date_inic, date_fin).tolist()
	return day_list

def getCurrentDaysMonth(date):
	'''
	Retorna la cantidad de dias hasta el ultimo dia del mes pasado.
	'''
	days= date.timetuple().tm_mday+1
	return days

def getCurrentDaysYear(date):
	'''
	Retorna la cantidad de dias hasta el anio pasado.
	'''
	days= date.timetuple().tm_yday+1
	return days

def getDatesSince(start_date, end_date):
	'''
	Retorna una lista con todas las fechas entre dos fechas particular.
	'''
	day_list=[]
	delta = end_date - start_date
	for i in range(delta.days + 1):
		day_list.append(start_date + dt.timedelta(days=i)) 

def getNDaysFromToday(days):
	'''
	Retorna la fecha n dias desde hoy.
	'''
	date = dt.datetime.now() - dt.timedelta( days = days )
	date=str(date.strftime('%Y-%m-%d'))
	return date


def getNDaysFromDate(days, date_string):
	'''
	Retorna la fecha n dias desde hoy.
	'''
	date = convertStringtoDate(date_string) - dt.timedelta( days = days )
	date=str(date.strftime('%Y-%m-%d'))
	return date

def convertDatetoString(date):
	'''
	Retorna la fecha en formato de string, dado el objeto date.
	'''
	date_string=str(date.strftime('%Y-%m-%d'))
	return date_string

def convertStringtoDate(date_string):
	'''
	Retorna la fecha en formato date.
	'''
	date_formated=dt.datetime.strptime(date_string, '%Y-%m-%d').date()
	return date_formated

def convertDateAllTogether(date):
	'''
	Retorna la fecha en formato con todos los caracteres juntos.
	'''
	date_formated=str(date.strftime('%Y%m%d'))
	return date_formated

def mergePDF(path, output_name):
	'''
	Concatena todos los archivos PDF en una ubicacion dada y lo guarda en otro PDF con un nombre dado.
	'''
	files_dir = path
	pdf_files = [f for f in os.listdir(files_dir) if f.endswith(".PDF")]
	merger = PdfFileMerger()
	for filename in pdf_files:
	    merger.append(PdfFileReader(os.path.join(files_dir, filename), "rb"))
	merger.write(os.path.join(files_dir, output_name))

def deleteFile(path):
	'''
	Borra un archivo.
	'''
	os.remove(path)

def deleteFolder(path):
	'''
	Borra una carpeta.
	'''
	os.rmdir(path)


def extractTextFile(path):
	'''
	Lee un archivo de texto y lo retorna como string.
	'''
	f=open(path,'r')
	file_string=f.read()
	f.close()
	return file_string

def convertJSONtoDict(json_string):
	'''
	Lee un string en formato JSON y lo retorna en un dictionary.
	'''
	json_dict=json.loads(json_string)
	return json_dict

	
'''FUNCIONES MATRICIALES'''
def arrayToNumPy(arr):
	'''
	Transforma una matriz normal en una de numpy.
	'''
	return np.array(arr)

def getVectColumn(matrix, col_number):
	'''
	Dada una lista de listas retorna un vector con la columna.
	'''
	matrix_np=np.array(matrix)
	column=matrix_np[:,col_number]
	return column


'''FUNCIONES SQL'''

def connectDatabase(server, database):
	'''
	Se conecta a una base de datos y retorna el objecto de la conexion, usando windows authentication.
	'''
	conn= pymssql.connect(host=server, database=database)
	return conn

def connectDatabaseUser(server, database, username, password):
	'''
	Se conecta a una base de datos y retorna el objecto de la conexion, usando un usuario.
	'''
	conn= pymssql.connect(host=server, database=database, user=username, password=password)
	return conn


def queryDatabase(conn, query):
	'''
	Consulta la la base de datos(conn) y devuelve el cursor asociado a la consulta.
	'''
	cursor=conn.cursor()
	cursor.execute(query)
	return cursor

def getTableSQL(cursor):
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

def getListSQL(cursor):
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


def getSchemaSQL(cursor):
	'''
	Recibe un cursor asociado a una consulta en la BDD y retorna el esquema de la relacion en una lista.
	'''
	schema = []
	for i in range(len(cursor.description)):
		prop = cursor.description[i][0]
		schema.append(prop)
	return schema

def disconnectDatabase(conn):
	'''
	Se deconecta a una base de la datos.
	'''
	conn.close()

def runSQL(conn, query):
    '''
    Ejecuta un statement en SQL, por ejemplo borrar.
    '''
    cursor=conn.cursor()
    cursor.execute(query)
    conn.commit()

def getFrameSqlUser(server, database, username, password, query):
    '''
    Retorna el resultado de la query en un panda's dataframe con usuario y clave. 
    '''
    conn = connectDatabaseUser(server = server, database = database, username = username, password = password)
    cursor = queryDatabase(conn, query)
    schema = getSchemaSQL(cursor = cursor)
    table = getTableSQL(cursor)
    dataframe = pd.DataFrame(data = table, columns = schema)
    disconnectDatabase(conn)
    return dataframe

def getFrameSql(server, database, query):
    '''
    Retorna el resultado de la query en un panda's dataframe. 
    '''
    conn = connectDatabase(server = server, database = database)
    cursor = queryDatabase(conn, query)
    schema = getSchemaSQL(cursor = cursor)
    table = getTableSQL(cursor)
    dataframe = pd.DataFrame(data = table, columns = schema)
    disconnectDatabase(conn)
    return dataframe


'''FUNCIONES EXCEL'''

def openWorkbook(path):
	'''
	Abre un workbook y retorna un objecto workbook de xlwings.
	'''
	wb=xw.Book(path)
	return wb

def saveWorkbook(wb):
	'''
	Guarda un workbook.
	'''
	wb.save()

def closeWorkbook(wb):
	'''
	Cierra un workbook.
	'''
	wb.close()

def closeExcel(wb):
	'''
	Cierra un Excel.
	'''
	app=wb.app
	app.quit()

def eraseTableXl(sheet, row, column):
	'''
	Recibe el rango asociado y borra la tabla considerando que el rango esta en el top-left corner de la tabla.
	'''
	xw.sheets[sheet].range(row,column).expand('table').clear_contents()

def pasteValXl(sheet, row, column,value):
	'''
	Inserta un valor en una celta de excel dada la hoja. 
	'''
	xw.sheets[sheet].range(row,column).value = value

def pasteColXl(sheet, row, column, lista):
	'''
	Inserta un valor en una celta de excel dada la hoja. 
	'''
	for val in lista:
		xw.sheets[sheet].range(row,column).value = val
		row+=1

def pasteQueryXl(server, database, query, sheet, row, column, with_schema):
	'''
	Consulta a la base de datos y pega el resultado en una hoja de excel en una determinada fila y columna. Si with_schema es verdadero, la pega con
	los nombres de columnas, en otro caso solo pega los valores. 
	'''
	conn= connectDatabase(server,database)
	cursor=queryDatabase(conn, query)
	table=getTableSQL(cursor)
	disconnectDatabase(conn)
	if with_schema:
		schema=getSchemaSQL(cursor)
		pasteValXl(sheet, row, column, schema)
		pasteValXl(sheet, row+1, column, table)
	else:		
		pasteValXl(sheet, row, column, table)

def pasteQueryXlUser(server, database, query, sheet, row, column, with_schema, username, password):
	'''
	Consulta a la base de datos y pega el resultado en una hoja de excel en una determinada fila y columna. Si with_schema es verdadero, la pega con
	los nombres de columnas, en otro caso solo pega los valores. Esta funcion es igual a la anterior pero se conecta a la BDD con usuario y pass.
	'''
	conn= connectDatabaseUser(server,database, username, password)
	cursor=queryDatabase(conn, query)
	table=getTableSQL(cursor)
	disconnectDatabase(conn)
	if with_schema:
		schema=getSchemaSQL(cursor)
		pasteValXl(sheet, row, column, schema)
		pasteValXl(sheet, row+1, column, table)
	else:		
		pasteValXl(sheet, row, column, table)

def getSheetIndex(sheet):
	'''
	Retorna el indice e una hoja, dado su nombre.
	'''
	return xw.Sheet(sheet).index

def exportSheetPDF(sheet_index, path_in, path_out):
	'''
	Exporta una hoja de Excel en PDF. 
	'''
	xlApp = client.Dispatch("Excel.Application")
	books = xlApp.Workbooks(1)
	ws = books.Worksheets[sheet_index]
	ws.ExportAsFixedFormat(0, path_out)

def getColumnXl(sheet, row, column):
	'''
	Retorna la columna en una lista, dado un rango y la hoja.
	'''
	return xw.sheets(sheet).range(row,column).expand('down').value

def getTableXl(sheet, row, column):
	'''
	Retorna la tabla en un arreglo, dado un rango y la hoja.
	'''
	return xw.sheets[sheet].range(row,column).expand('table').value

'''FUNCIONES PPT'''

def openPPT(filename):
	'''
	Abre un ppt en el mismo programa powerpoint 2014.
	'''
	os.system("\"C:\\Program Files\\Microsoft Office\\Office14\\POWERPNT.EXE\" "+ filename)

'''FUNCIONES MAIL'''

def sendMailAttach(subject, body, mails, attachment_paths):
	'''
	#Envia un mail a todos los correos en el arreglo mails y les adjunta todos los archivos del otro arreglo.
	'''
	#os.startfile("outlook") #antes lo hacia con esto pero el problema es que no se puede cerrar outlook
	const=win32com.client.constants
	olMailItem = 0x0
	obj = win32com.client.gencache.EnsureDispatch("Outlook.Application")
	newMail = obj.CreateItem(olMailItem)
	newMail.Subject = subject
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


def sendMail(subject, body, mails):
	'''
	#Envia un mail a todos los correos en el arreglo mails.
	'''
	os.startfile("outlook") #En bbl, sin esto no funciona
	const = win32com.client.constants
	olMailItem = 0x0
	obj = win32com.client.gencache.EnsureDispatch("Outlook.Application")
	newMail = obj.CreateItem(olMailItem)
	newMail.Subject = subject
	newMail.Body = body
	cadena = ""
	for mail in mails:
		mail = mail + ";"
		cadena = cadena+mail
	cadena = cadena[:-1] # los mails se mandan separados por ; en una cadena
	newMail.To = cadena
	try:
		newMail.Send()
		print("Correo enviado")
	except:
		print("Fallo el envio del correo")


'''FUNCIONES FTP'''
def downloadDataSFTP(host, username, password, origin, destination, port):
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
