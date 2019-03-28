
import sys
print (sys)
sys.path.insert(0, '../../fsb/repositorio/mesagi/Proyectos/libreria/')
import libreria_fdo as lib
import numpy as np
import xlwings as xw

def getInfoIndicesAFP():

    

	path="queryAFPs.sql"
	query = lib.read_file(path=path)
	sqlQuery="SELECT INDEX_ID FROM INDICES_ESTATICA WHERE NOMBRE_INDEX LIKE '%FONDO E%'"
	vals =  lib.get_frame_sql_user(server="Puyehue",
        	                   database="MesaInversiones",
    	                       username="usrConsultaComercial",
    	                       password="Comercial1w", 
    	                       query=query)
	return vals

def world():
    wb = xw.Book.caller()
    wb.sheets[0].range('A1').value = 'Hello World!'

