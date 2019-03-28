"""
Created on Tue Aug 22 11:00:00 2017

@author: Ashley Mac Gregor
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np
import re as re
from bs4 import BeautifulSoup
from datetime import datetime



def read_file(path):
	'''
	Lee archivo .xml en utf8.
	'''
	f = open(path, encoding="utf8")
	cartera_xml = f.read()
	f.close()
	y = BeautifulSoup(cartera_xml, "html.parser")
	return y

def file_date(path):
	'''
	Lee la fecha del archivo .xml (desde el path), y luego la transforma de str a datetime (esto para luego poder identificar las tablas con las fechas que les corresponden)
	'''
	date = path[16:22]
	date = datetime.strptime(date, "%Y%m")
	return date

def cuadro_2(y, date):
	'''
	Cuadro 2: CARTERA AGREGADA DE LOS FONDOS DE PENSIONES TIPO E POR AFP
	'''
	#se definen los nombres de las columnas del dataframe
	columnas = y.find_all("listado")[1].find_all("tipofondo")[4].find_all("fila")[0].find_all("afp")
	nombre_columnas = ["Tipo_Instrumento",]
	for t in columnas:
		nombre_afp = t.find("nombre").text
		nombre_columnas.append(nombre_afp)
		if nombre_afp == "PROVIDA":
			nombre_columnas.append("Total(monto)")
			nombre_columnas.append("Total(porcentaje)")

	#se obtiene la data que va a componer el dataframe
	fila = y.find_all("listado")[1].find_all("tipofondo")[4].find_all("fila")
	total_filas = []
	for filas in fila:
		datos_fila = [filas.find("glosa").text,]
		afp_fila = filas.find_all("afp")
		for t in afp_fila:
			monto_dolares = t.find("monto_dolares").text
			datos_fila.append(monto_dolares)
			
		total_fila = filas.find_all("total")
		for t in total_fila:
			total_monto = t.find("monto_dolares").text
			total_porcentaje = t.find("porcentaje").text
			datos_fila.append(total_monto)
			datos_fila.append(total_porcentaje)
		total_filas.append(datos_fila)

	#se arma el dataframe 
	cuadro_2 = pd.DataFrame(total_filas, columns=nombre_columnas)
	#se llenan las celdas vacías con ceros para poder luego pasar los datos a float y poder trabajarlos
	cuadro_2 = cuadro_2.convert_objects(convert_numeric=True).fillna(0)
	cuadro_2["CAPITAL"] = cuadro_2["CAPITAL"].astype(float)
	cuadro_2["CUPRUM"] = cuadro_2["CUPRUM"].astype(float)
	cuadro_2["HABITAT"] = cuadro_2["HABITAT"].astype(float)
	cuadro_2["MODELO"] = cuadro_2["MODELO"].astype(float)
	cuadro_2["PLANVITAL"] = cuadro_2["PLANVITAL"].astype(float)
	cuadro_2["PROVIDA"] = cuadro_2["PROVIDA"].astype(float)
	cuadro_2["Total(monto)"] = cuadro_2["Total(monto)"].astype(float)
	cuadro_2["Total(porcentaje)"] = cuadro_2["Total(porcentaje)"].astype(float)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_2["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_2 = cuadro_2[['Fecha','Tipo_Instrumento','CAPITAL','CUPRUM','HABITAT','MODELO','PLANVITAL','PROVIDA','Total(monto)','Total(porcentaje)']]
	return cuadro_2


def cuadro_3(y, date):
	'''
	Cuadro 3: ACTIVOS DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO, DIVERSIFICACIÓN POR INSTRUMENTOS FINANCIEROS
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_3 = y.find_all("listado")[2].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_3 = ["",]
	for t in columnas_3:
		tipo_fondo = t["codigo"]
		nombre_columnas_3.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_3.append("MM$")
			nombre_columnas_3.append("MMUS$")
			nombre_columnas_3.append("%Fondo")
	
	#se obtiene la data que va a componer el dataframe
	fila_3 = y.find_all("listado")[2].find_all("fila")
	total_filas_3 = []
	for filas in fila_3:
		datos_fila_3 = [filas.find("glosa").text,]
		tipofondo_fila = filas.find_all("tipofondo")
		for t in tipofondo_fila:
			datos = t.find(True).text
			datos_fila_3.append(datos)
		total_fila = filas.find_all("total")
		for t in total_fila:
			monto_pesos = t.find("monto_pesos").text
			monto_dolares = t.find("monto_dolares").text
			porcentaje = t.find("porcentaje").text
			datos_fila_3.append(monto_pesos)
			datos_fila_3.append(monto_dolares)
			datos_fila_3.append(porcentaje)
		total_filas_3.append(datos_fila_3)

	#se arma el dataframe 
	cuadro_3 = pd.DataFrame(total_filas_3, columns=nombre_columnas_3)
	#se llenan las celdas vacías con ceros para poder luego pasar los datos a float y poder trabajarlos
	cuadro_3 = cuadro_3.convert_objects(convert_numeric=True).fillna(0)
	cuadro_3["A"] = cuadro_3["A"].astype(float)
	cuadro_3["B"] = cuadro_3["B"].astype(float)
	cuadro_3["C"] = cuadro_3["C"].astype(float)
	cuadro_3["D"] = cuadro_3["D"].astype(float)
	cuadro_3["E"] = cuadro_3["E"].astype(float)
	cuadro_3["MM$"] = cuadro_3["MM$"].astype(float)
	cuadro_3["MMUS$"] = cuadro_3["MMUS$"].astype(float)
	cuadro_3["%Fondo"] = cuadro_3["%Fondo"].astype(float)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_3["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_3 = cuadro_3[['Fecha','','A','B','C','D','E','MM$','MMUS$','%Fondo']]
	return cuadro_3


def cuadro_4_a(y, date):
	'''
	CUADRO Nº 4_a: TASAS DE VALORACIÓN POR TIPO DE INSTRUMENTO FINANCIERO DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO (Tasa de Interes)
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_4_a = y.find_all("listado")[3].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_4_a = ["Tipo de instrumento","Unidad de Indexación",]
	for t in columnas_4_a:
		tipo_fondo = t["codigo"]
		nombre_columnas_4_a.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_4_a.append("Total")

	#se obtiene la data que va a componer el dataframe
	fila_4_a = y.find_all("listado")[3].find_all("fila")
	total_filas_4_a = []
	for filas in fila_4_a:
		datos_fila_4_a = [filas.find("glosa").text,filas.find("unidad_indexada").text,]
		tipofondo_fila = filas.find_all("tipofondo")
		for t in tipofondo_fila:
			datos = t.find("tasa_interes").text
			datos_fila_4_a.append(datos)
		total_fila = filas.find_all("total")
		for t in total_fila:
			datos = t.find("tasa_interes").text
			datos_fila_4_a.append(datos)
		total_filas_4_a.append(datos_fila_4_a)

	#se arma el dataframe 
	cuadro_4_a = pd.DataFrame(total_filas_4_a, columns=nombre_columnas_4_a)
	#se llenan las celdas vacías con ceros para poder luego pasar los datos a float y poder trabajarlos
	cuadro_4_a = cuadro_4_a.convert_objects(convert_numeric=True).fillna(0)
	cuadro_4_a["A"] = cuadro_4_a["A"].astype(float)
	cuadro_4_a["B"] = cuadro_4_a["B"].astype(float)
	cuadro_4_a["C"] = cuadro_4_a["C"].astype(float)
	cuadro_4_a["D"] = cuadro_4_a["D"].astype(float)
	cuadro_4_a["E"] = cuadro_4_a["E"].astype(float)
	cuadro_4_a["Total"] = cuadro_4_a["Total"].astype(float)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_4_a["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_4_a = cuadro_4_a[['Fecha','Tipo de instrumento','Unidad de Indexación','A','B','C','D','E','Total']]
	return cuadro_4_a


def cuadro_4_b(y, date):
	'''
	CUADRO Nº 4_b: TASAS DE VALORACIÓN POR TIPO DE INSTRUMENTO FINANCIERO DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO (% Invertido)
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_4_b = y.find_all("listado")[3].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_4_b = ["Tipo de instrumento","Unidad de Indexación",]
	for t in columnas_4_b:
		tipo_fondo = t["codigo"]
		nombre_columnas_4_b.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_4_b.append("Total")

	#se obtiene la data que va a componer el dataframe
	fila_4_b = y.find_all("listado")[3].find_all("fila")
	total_filas_4_b = []
	for filas in fila_4_b:
		datos_fila_4_b = [filas.find("glosa").text,filas.find("unidad_indexada").text,]
		tipofondo_fila = filas.find_all("tipofondo")
		for t in tipofondo_fila:
			datos = t.find("porcentaje").text
			datos_fila_4_b.append(datos)
		total_fila = filas.find_all("total")
		for t in total_fila:
			datos = t.find("porcentaje").text
			datos_fila_4_b.append(datos)
		total_filas_4_b.append(datos_fila_4_b)

	#se arma el dataframe 
	cuadro_4_b = pd.DataFrame(total_filas_4_b, columns=nombre_columnas_4_b)
	#se llenan las celdas vacías con ceros para poder luego pasar los datos a float y poder trabajarlos
	cuadro_4_b = cuadro_4_b.convert_objects(convert_numeric=True).fillna(0)
	cuadro_4_b["A"] = cuadro_4_b["A"].astype(float)
	cuadro_4_b["B"] = cuadro_4_b["B"].astype(float)
	cuadro_4_b["C"] = cuadro_4_b["C"].astype(float)
	cuadro_4_b["D"] = cuadro_4_b["D"].astype(float)
	cuadro_4_b["E"] = cuadro_4_b["E"].astype(float)
	cuadro_4_b["Total"] = cuadro_4_b["Total"].astype(float)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_4_b["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_4_b = cuadro_4_b[['Fecha','Tipo de instrumento','Unidad de Indexación','A','B','C','D','E','Total']]
	return cuadro_4_b


def cuadro_7(y, date):
	'''
	CUADRO Nº 7: PLAZO PROMEDIO DE LAS INVERSIONES DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO E INSTRUMENTO (1)
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_7 = y.find_all("listado")[6].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_7 = ["Instituciones",]
	for t in columnas_7:
		tipo_fondo = t["codigo"]
		nombre_columnas_7.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_7.append("Sistema")

	#se obtiene la data que va a componer el dataframe
	fila_7 = y.find_all("listado")[6].find_all("fila")
	total_filas_7 = []
	for filas in fila_7:
		datos_fila_7 = [filas.find("glosa").text,]
		tipofondo_fila = filas.find_all("tipofondo")
		for t in tipofondo_fila:
			datos = t.find("plazo").text
			datos_fila_7.append(datos)
		total_fila = filas.find_all("total")
		for t in total_fila:
			datos = t.find("plazo").text
			datos_fila_7.append(datos)
		total_filas_7.append(datos_fila_7)

	#se arma el dataframe
	cuadro_7 = pd.DataFrame(total_filas_7, columns=nombre_columnas_7)
	#se llenan las celdas vacías con ceros para poder luego pasar los datos a float y poder trabajarlos
	cuadro_7 = cuadro_7.convert_objects(convert_numeric=True).fillna(0)
	cuadro_7["A"] = cuadro_7["A"].astype(float)
	cuadro_7["B"] = cuadro_7["B"].astype(float)
	cuadro_7["C"] = cuadro_7["C"].astype(float)
	cuadro_7["D"] = cuadro_7["D"].astype(float)
	cuadro_7["E"] = cuadro_7["E"].astype(float)
	cuadro_7["Sistema"] = cuadro_7["Sistema"].astype(float)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_7["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_7 = cuadro_7[['Fecha','Instituciones','A','B','C','D','E','Sistema']]
	return cuadro_7


def cuadro_22(y, date):
	'''
	CUADRO Nº 22: INVERSIÓN EN EL EXTRANJERO DE LOS FONDOS DE PENSIONES, DIVERSIFICACIÓN POR TIPO DE FONDO Y MONEDA
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_22 = y.find_all("listado")[21].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_22 = ["Moneda",]
	for t in columnas_22:
		tipo_fondo = t["codigo"]
		nombre_columnas_22.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_22.append("Total")
			nombre_columnas_22.append("% sobre el total del Fondo de Pensiones")
			nombre_columnas_22.append("% sobre inversion total extranjero")

	#se obtiene la data que va a componer el dataframe
	fila_22 = y.find_all("listado")[21].find_all("fila")
	total_filas_22 = []
	for filas in fila_22:
		datos_fila_22 = [filas.find("glosa").text,]
		tipofondo_fila = filas.find_all("tipofondo")
		for t in tipofondo_fila:
			datos = t.find("monto_dolares").text
			datos_fila_22.append(datos)
		total_fila = filas.find_all("total")
		for t in total_fila:
			datos_monto = t.find("monto_dolares").text
			datos_porcentaje = t.find("porcentaje").text
			datos_porcentaje_sobre_extranjero = t.find("porcentaje_sobre_extranjero").text
			datos_fila_22.append(datos_monto)
			datos_fila_22.append(datos_porcentaje)
			datos_fila_22.append(datos_porcentaje_sobre_extranjero)
		total_filas_22.append(datos_fila_22)

	#se arma el dataframe 
	cuadro_22 = pd.DataFrame(total_filas_22, columns=nombre_columnas_22)
	#se llenan las celdas vacías con ceros para poder luego pasar los datos a float y poder trabajarlos
	cuadro_22 = cuadro_22.convert_objects(convert_numeric=True).fillna(0)
	cuadro_22["A"] = cuadro_22["A"].astype(float)
	cuadro_22["B"] = cuadro_22["B"].astype(float)
	cuadro_22["C"] = cuadro_22["C"].astype(float)
	cuadro_22["D"] = cuadro_22["D"].astype(float)
	cuadro_22["E"] = cuadro_22["E"].astype(float)
	cuadro_22["Total"] = cuadro_22["Total"].astype(float)
	cuadro_22["% sobre el total del Fondo de Pensiones"] = cuadro_22["% sobre el total del Fondo de Pensiones"].astype(float)
	cuadro_22["% sobre inversion total extranjero"] = cuadro_22["% sobre inversion total extranjero"].astype(float)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_22["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_22 = cuadro_22[['Fecha','Moneda','A','B','C','D','E','Total','% sobre el total del Fondo de Pensiones','% sobre inversion total extranjero']]
	return cuadro_22


def cuadro_25(y, date):
	'''
	CUADRO Nº 25: CARTERA DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO, INVERSIÓN EN EL EXTRANJERO POR EMISOR
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_25 = y.find_all("listado")[24].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_25 = ["Institucion","Nemotecnico",]
	for t in columnas_25:
		tipo_fondo = t["codigo"]
		nombre_columnas_25.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_25.append("Total")
			nombre_columnas_25.append("% sobre el total del Fondo de Pensiones")

	#se obtiene la data que va a componer el dataframe
	fila_25 = y.find_all("listado")[24].find_all("fila")
	total_filas_25 = []
	for filas in fila_25:
		datos_fila_25 = [filas.find("glosa").text,]
		if filas.find("nemotecnico") is not None:
			nemo = filas.find("nemotecnico").text
		else:
			nemo = ""
		datos_fila_25.append(nemo)	
		tipofondo_fila = filas.find_all("tipofondo")
		for t in tipofondo_fila:
			datos = t.find("monto_dolares").text
			datos_fila_25.append(datos)
		total_fila = filas.find_all("total")
		for t in total_fila:
			datos_monto = t.find("monto_dolares").text
			datos_porcentaje = t.find("porcentaje").text
			datos_fila_25.append(datos_monto)
			datos_fila_25.append(datos_porcentaje)
		total_filas_25.append(datos_fila_25)

	#se arma el dataframe 
	cuadro_25 = pd.DataFrame(total_filas_25, columns=nombre_columnas_25)
	#se llenan las celdas vacías con ceros para poder luego pasar los datos a float y poder trabajarlos
	cuadro_25 = cuadro_25.convert_objects(convert_numeric=True).fillna(0)
	cuadro_25["A"] = cuadro_25["A"].astype(float)
	cuadro_25["B"] = cuadro_25["B"].astype(float)
	cuadro_25["C"] = cuadro_25["C"].astype(float)
	cuadro_25["D"] = cuadro_25["D"].astype(float)
	cuadro_25["E"] = cuadro_25["E"].astype(float)
	cuadro_25["Total"] = cuadro_25["Total"].astype(float)
	cuadro_25["% sobre el total del Fondo de Pensiones"] = cuadro_25["% sobre el total del Fondo de Pensiones"].astype(float)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_25["Fecha"] = date
	return cuadro_25


def cuadro_25_ajus(y, date):
	'''
	CUADRO Nº 25 Ajustado: CARTERA DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO, INVERSIÓN EN EL EXTRANJERO POR EMISOR (se le sacan los subtotales, y se le asigna una nueva columna con el subgrupo al cual pertenece la fila en cuestión)
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_25_ajus = y.find_all("listado")[24].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_25_ajus = ["Institucion","Nemotecnico",]
	for t in columnas_25_ajus:
		tipo_fondo = t["codigo"]
		nombre_columnas_25_ajus.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_25_ajus.append("Total")
			nombre_columnas_25_ajus.append("% sobre el total del Fondo de Pensiones")
			nombre_columnas_25_ajus.append("Clasificacion")

	#se obtiene la data que va a componer el dataframe
	fila_25_ajus = y.find_all("listado")[24].find_all("fila")
	total_filas_25_ajus = []
	for filas in fila_25_ajus:
		#se eliminan los subtotales de la tabla
		if str(filas.find("glosa").text).startswith('TOTAL')==False:
			datos_fila_25_ajus = [filas.find("glosa").text,]
			if filas.find("nemotecnico") is not None:
				nemo = filas.find("nemotecnico").text
			else:
				nemo = ""
			datos_fila_25_ajus.append(nemo)	
			tipofondo_fila = filas.find_all("tipofondo")
			for t in tipofondo_fila:
				datos = t.find("monto_dolares").text
				datos_fila_25_ajus.append(datos)
			total_fila = filas.find_all("total")
			for t in total_fila:
				datos_monto = t.find("monto_dolares").text
				datos_porcentaje = t.find("porcentaje").text
				datos_fila_25_ajus.append(datos_monto)
				datos_fila_25_ajus.append(datos_porcentaje)
			#se asigna a cada fila la identificación de qué clasificación se trata
			d=[]
			for f in filas.find_next_siblings():
				if str(f.find("glosa").text).startswith('TOTAL')==True and f.find("nemotecnico") is None:
					clasificacion = f.find("glosa").text
					d.append(clasificacion)
					break
			datos_fila_25_ajus.extend(d)
			total_filas_25_ajus.append(datos_fila_25_ajus)

	#se arma el dataframe 
	cuadro_25_ajus = pd.DataFrame(total_filas_25_ajus, columns=nombre_columnas_25_ajus)
	#se llenan las celdas vacías con ceros para poder luego pasar los datos a float y poder trabajarlos
	cuadro_25_ajus = cuadro_25_ajus.convert_objects(convert_numeric=True).fillna(0)
	cuadro_25_ajus["A"] = cuadro_25_ajus["A"].astype(float)
	cuadro_25_ajus["B"] = cuadro_25_ajus["B"].astype(float)
	cuadro_25_ajus["C"] = cuadro_25_ajus["C"].astype(float)
	cuadro_25_ajus["D"] = cuadro_25_ajus["D"].astype(float)
	cuadro_25_ajus["E"] = cuadro_25_ajus["E"].astype(float)
	cuadro_25_ajus["Total"] = cuadro_25_ajus["Total"].astype(float)
	cuadro_25_ajus["% sobre el total del Fondo de Pensiones"] = cuadro_25_ajus["% sobre el total del Fondo de Pensiones"].astype(float)
	#le sacamos la palabra "TOTAL" que está al comienzo de toda la columna de clasificación
	cuadro_25_ajus["Clasificacion"] = cuadro_25_ajus["Clasificacion"].str[6:]
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_25_ajus["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_25_ajus = cuadro_25_ajus[['Fecha','Institucion','Nemotecnico','Clasificacion','A','B','C','D','E','Total','% sobre el total del Fondo de Pensiones']]
	return cuadro_25_ajus


def cuadro_27_28(y, date):
	'''
	CUADRO Nº 27 y 28: CARTERA DE LOS FONDOS DE PENSIONES EN INSTRUMENTOS FORWARD NACIONALES Y EXTRANJEROS EN FUNCION DEL ACTIVO OBJETO MONEDA, 
	MONEDA CONTRAPARTE Y POR TIPO DE FONDO (1)
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_27_28 = y.find_all("listado")[26].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_27_28 = [y.find_all("listado")[26].find_all("fondos_por_moneda_objeto")[0].find("fondos_por_agrupacion")["agrupacion_instrumentos"],
	"Nac/Internac", "Moneda Objeto",]
	for t in columnas_27_28:
		tipo_fondo = t["codigo"]
		nombre_columnas_27_28.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_27_28.append("Total")

	#se obtiene la data que va a componer el dataframe 27
	moneda_objeto_27 = y.find_all("listado")[26].find_all("fondos_por_moneda_objeto")
	total_filas_27 = []
	for i in moneda_objeto_27:
		fila_27 = i.find_all("fila")
		for filas in fila_27:
			#agregamos la moneda objeto correspondiente en una nueva columna, y la definición de moneda nacional
			datos_fila_27 = [filas.find("glosa").text,"Nacional",i["moneda_objeto"],]
			tipofondo_fila = filas.find_all("tipofondo")
			for t in tipofondo_fila:
				datos = t.find("monto_dolares").text
				datos_fila_27.append(datos)
			total_fila = filas.find_all("total")
			for t in total_fila:
				datos_monto = t.find("monto_dolares").text
				datos_fila_27.append(datos_monto)

			total_filas_27.append(datos_fila_27)

	#se obtiene la data que va a componer el dataframe 28
	moneda_objeto_28 = y.find_all("listado")[27].find_all("fondos_por_moneda_objeto")
	total_filas_28 = []
	for i in moneda_objeto_28:
		fila_28 = i.find_all("fila")
		for filas in fila_28:
			#agregamos la moneda objeto correspondiente en una nueva columna, y la definición de moneda internacional
			datos_fila_28 = [filas.find("glosa").text,"Internacional",i["moneda_objeto"],]
			tipofondo_fila = filas.find_all("tipofondo")
			for t in tipofondo_fila:
				datos = t.find("monto_dolares").text
				datos_fila_28.append(datos)
			total_fila = filas.find_all("total")
			for t in total_fila:
				datos_monto = t.find("monto_dolares").text
				datos_fila_28.append(datos_monto)
			total_filas_28.append(datos_fila_28)

	#se une la data de ambos cuadros (nacional e internacional)
	total_filas_27_28 = total_filas_27 + total_filas_28

	#se arma el dataframe 
	cuadro_27_28 = pd.DataFrame(total_filas_27_28, columns=nombre_columnas_27_28)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_27_28["Fecha"] = date
	return cuadro_27_28


def cuadro_27_28_ajus(y, date):
	'''
	CUADRO Nº 27 y 28 Ajustada: CARTERA DE LOS FONDOS DE PENSIONES EN INSTRUMENTOS FORWARD NACIONALES Y EXTRANJEROS EN FUNCION DEL ACTIVO OBJETO MONEDA, 
	MONEDA CONTRAPARTE Y POR TIPO DE FONDO (1)
	'''
	#se definen los nombres de las columnas del dataframe
	columnas_27_28_ajus = y.find_all("listado")[26].find_all("fila")[0].find_all("tipofondo")
	nombre_columnas_27_28_ajus = [y.find_all("listado")[26].find_all("fondos_por_moneda_objeto")[0].find("fondos_por_agrupacion")["agrupacion_instrumentos"],
	"Nac/Internac", "Moneda Objeto",]
	for t in columnas_27_28_ajus:
		tipo_fondo = t["codigo"]
		nombre_columnas_27_28_ajus.append(tipo_fondo)
		if tipo_fondo == "E":
			nombre_columnas_27_28_ajus.append("Total")
			nombre_columnas_27_28_ajus.append("V/C")

	#se obtiene la data que va a componer el dataframe 27 ajustada (se le saca las filas que son subtotales, ej:WEMV), y se ponde esta data en una columna aparte indicando la correspondiente para cada fila
	moneda_objeto_27_ajus = y.find_all("listado")[26].find_all("fondos_por_moneda_objeto")
	total_filas_27_ajus = []
	for i in moneda_objeto_27_ajus:
		fila_27_ajus = i.find_all("fila")
		for filas in fila_27_ajus:
			#sacamos los subtotales o subgrupos (compra o venta) de entremedio de la tabla:
			if filas.find("glosa").text.isupper()==False:
				datos_fila_27_ajus = [filas.find("glosa").text,"Nacional",i["moneda_objeto"],]
				tipofondo_fila = filas.find_all("tipofondo")
				for t in tipofondo_fila:
					datos = t.find("monto_dolares").text
					datos_fila_27_ajus.append(datos)
				total_fila = filas.find_all("total")
				for t in total_fila:
					datos_monto = t.find("monto_dolares").text
					datos_fila_27_ajus.append(datos_monto)
				#se asigna a cada fila la identificación si se trata de compra o venta:
				d=[]   
				for f in filas.find_previous_siblings(): 
					if f.find("glosa").text.isupper()==True: 
						c_v = f.find("glosa").text
						d.append(c_v)
						break
				datos_fila_27_ajus.extend(d)
				total_filas_27_ajus.append(datos_fila_27_ajus)

	#se obtiene la data que va a componer el dataframe 28 ajustada (se le saca las filas que son subtotales, ej:WEMV), y se ponde esta data en una columna aparte indicando la correspondiente para cada fila
	moneda_objeto_28_ajus = y.find_all("listado")[27].find_all("fondos_por_moneda_objeto")
	total_filas_28_ajus = []
	for i in moneda_objeto_28_ajus:
		fila_28_ajus = i.find_all("fila")
		for filas in fila_28_ajus:
			#sacamos los subtotales o subgrupos (compra o venta) de entremedio de la tabla:
			if filas.find("glosa").text.isupper()==False:
				datos_fila_28_ajus = [filas.find("glosa").text,"Internacional",i["moneda_objeto"],]
				tipofondo_fila = filas.find_all("tipofondo")
				for t in tipofondo_fila:
					datos = t.find("monto_dolares").text
					datos_fila_28_ajus.append(datos)
				total_fila = filas.find_all("total")
				for t in total_fila:
					datos_monto = t.find("monto_dolares").text
					datos_fila_28_ajus.append(datos_monto)
				#se asigna a cada fila la identificación si se trata de compra o venta:
				d=[]   
				for f in filas.find_previous_siblings(): 
					if f.find("glosa").text.isupper()==True: 
						c_v = f.find("glosa").text
						d.append(c_v)
						break
				datos_fila_28_ajus.extend(d)
				total_filas_28_ajus.append(datos_fila_28_ajus)

	#se unen ambos conjuntos de filas nacional e internacional
	total_filas_27_28_ajus = total_filas_27_ajus + total_filas_28_ajus
	#se crea el dataframe conjunto: nacional+internacional
	cuadro_27_28_ajus = pd.DataFrame(total_filas_27_28_ajus, columns=nombre_columnas_27_28_ajus)
	#se crea una nueva columna que sólo indica la letra "C"= compra o "V"= venta
	cuadro_27_28_ajus["V_C"] = cuadro_27_28_ajus["V/C"].str[-1:]
	#se llenan las celdas vacías de la tabla con ceros, para poder luego transformar la columna de string a float y poder así luego trabajar los numeros
	cuadro_27_28_ajus = cuadro_27_28_ajus.convert_objects(convert_numeric=True).fillna(0)
	cuadro_27_28_ajus["E"] = cuadro_27_28_ajus["E"].astype(float)
	cuadro_27_28_ajus["A"] = cuadro_27_28_ajus["A"].astype(float)
	cuadro_27_28_ajus["B"] = cuadro_27_28_ajus["B"].astype(float)
	cuadro_27_28_ajus["C"] = cuadro_27_28_ajus["C"].astype(float)
	cuadro_27_28_ajus["D"] = cuadro_27_28_ajus["D"].astype(float)
	cuadro_27_28_ajus["Total"] = cuadro_27_28_ajus["Total"].astype(float)
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_27_28_ajus["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_27_28_ajus = cuadro_27_28_ajus[['Fecha','Forward','Nac/Internac','Moneda Objeto','V_C','A','B','C','D','E','Total']]
	return cuadro_27_28_ajus


def total_activos(cuadro_2):
	'''
	calculamos el total de Activos Fondo E (suma de la fila TOTAL ACTIVOS del cuadro 2)
	'''
	total_activos = cuadro_2.loc[cuadro_2["Tipo_Instrumento"] == "TOTAL ACTIVOS", "Total(monto)"].sum()
	return total_activos


def cuadro_resumen_forwards(cuadro_27_28_ajus, total_activos, date):
	'''
	TABLA RESUMEN FORWARDS FONDO E
	'''
	columns = ["Moneda", "Compra", "Venta"]

	#se hcae un select distinct de las monedas de las columnas "Forward" y "Moneda Objeto", para así tener una lista de las monedas únicas para la tabla
	list_moneda_obj = cuadro_27_28_ajus["Moneda Objeto"].unique()
	list_moneda_forward = cuadro_27_28_ajus["Forward"].unique()
	list_monedas = []
	list_monedas.extend(list_moneda_obj)
	list_monedas.extend(list_moneda_forward)

	moneda_unique = []
	for l in list_monedas:
		if l not in moneda_unique:
			moneda_unique.append(l)

	#para cada moneda de la lista única anterior, se busca en el cudro 27_28_ajus los montos, cagrupándolos por compra y venta
	#para generar los datos de la tabla, se crean listas de tres componentes: moneda, monto compra, monto venta
	datos = []
	for moneda in moneda_unique:
		fila_i = [moneda,]
		compra_a = cuadro_27_28_ajus.loc[(cuadro_27_28_ajus["V_C"] == "C") & (cuadro_27_28_ajus["Moneda Objeto"] == moneda), "E"].sum()
		compra_b = cuadro_27_28_ajus.loc[(cuadro_27_28_ajus["V_C"] == "V") & (cuadro_27_28_ajus["Forward"] == moneda), "E"].sum()
		venta_a = cuadro_27_28_ajus.loc[(cuadro_27_28_ajus["V_C"] == "V") & (cuadro_27_28_ajus["Moneda Objeto"] == moneda), "E"].sum()
		venta_b = cuadro_27_28_ajus.loc[(cuadro_27_28_ajus["V_C"] == "C") & (cuadro_27_28_ajus["Forward"] == moneda), "E"].sum()
		compra = compra_a + compra_b
		venta = venta_a + venta_b
		fila_i.append(compra)
		fila_i.append(venta)
		datos.append(fila_i)

	#se crea el dataframe
	cuadro_resumen_forwards = pd.DataFrame(datos, columns=columns)
	#se crean las columnas Diferencia y Porcentaje
	cuadro_resumen_forwards["Diferencia"] = cuadro_resumen_forwards["Compra"] - cuadro_resumen_forwards["Venta"]
	cuadro_resumen_forwards["Porcentaje"] = (cuadro_resumen_forwards["Diferencia"]/total_activos)*100
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_resumen_forwards["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_resumen_forwards = cuadro_resumen_forwards[['Fecha','Moneda','Compra','Venta','Diferencia','Porcentaje']]
	if round(cuadro_resumen_forwards["Compra"].sum()-cuadro_resumen_forwards["Venta"].sum(), 6) == 0:
		return cuadro_resumen_forwards
	else:
	   print("Error: Cuadro resumen forwards NO suma cero")


def cuadro_resumen_físico_extranjero(cuadro_22, total_activos, date):
	'''
	TABLA RESUMEN FÍSICO EXTRANJERO FONDO E (cuadro 22)
	'''
	#se obtiene a partir del cuadro 22, la moneda y monto del fondo E
	cuadro_resumen_físico_extranjero = cuadro_22[["Moneda","E"]]
	cuadro_resumen_físico_extranjero = cuadro_resumen_físico_extranjero.convert_objects(convert_numeric=True).fillna(0)
	cuadro_resumen_físico_extranjero["E"] = cuadro_resumen_físico_extranjero["E"].astype(float)
	#se agrega una columna de Porcentaje
	cuadro_resumen_físico_extranjero["Porcentaje"] = (cuadro_resumen_físico_extranjero["E"]/total_activos)*100
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_resumen_físico_extranjero["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe, y se le saca la última fila ya que es el total extranjero
	cuadro_resumen_físico_extranjero = cuadro_resumen_físico_extranjero[['Fecha','Moneda','E','Porcentaje']][:-1]
	return cuadro_resumen_físico_extranjero


def cuadro_resumen_fisico_local(cuadro_4_b, cuadro_2, date):
	'''
	TABLA RESUMEN FÍSICO LOCAL FONDO E (cuadro 4_b)
	'''
	#localizamos la fila a partir de la cual comienzan los datos extranjeros (del cuadro 4_b que tiene el dato del %invertido), y eliminamos las filas a partir de ella (filas extranjeras)
	fila_EXTS = cuadro_4_b["Tipo de instrumento"].str.startswith('EXTS', na=False)
	index_EXTS = cuadro_4_b.index[fila_EXTS==True].tolist()[0].astype(int) # FERNANDO: CAMBIE ESTO
	# index_EXTS = cuadro_4_b.index[fila_EXTS==True].astype(int)[0]
	#keep top filas (nacionales)
	cuadro_resumen_fisico_local = cuadro_4_b[:index_EXTS] 
	cuadro_resumen_fisico_local = cuadro_resumen_fisico_local[["Unidad de Indexación","E"]] 
	cuadro_resumen_fisico_local = cuadro_resumen_fisico_local.groupby("Unidad de Indexación", as_index=False).sum()

	#se crea un diccionario que iguala la unidad de indexación del cuadro 4_b con el nombre completo de la moneda a la que corresponde (esto para después poder hacer el match con las demás tablas de moneda, y llegar al resumen final)
	moneda_dict = {"EUR":"Euro(EUR)",
	   "IPC":"IPC",
	   "NO":"Pesos",
	   "UF":"Unidad de Fomento",
	   "US$":"Dólar estadounidense(US$)"}
	#se reemplaza la unidad de indexación por el nombre de la moneda, utilizando el diccionario
	cuadro_resumen_fisico_local["Unidad de Indexación"] = cuadro_resumen_fisico_local["Unidad de Indexación"].map(moneda_dict)

	#a continuación se suman al porcentaje en pesos anterior (que solo toma RF local), los porcentajes en pesos (del cuadro 2) en Renta Variable,Fondos Mutuos y de Inversión,Disponible(1), DERIVADOS, OTROS NACIONALES(2) y (del cuadro 4_b) RF local: 
	#localizamos la fila a partir de la cual comienzan los datos extranjeros, y eliminamos las filas a partir de ella (filas extranjeras)
	fila_inv_ext = cuadro_2["Tipo_Instrumento"].str.startswith('INVERSIÓN EXTRANJERA TOTAL', na=False)
	index_inv_ext = cuadro_2.index[fila_inv_ext==True].tolist()[0].astype(int) # FERNANDO: CAMBIE ESTO
	# index_inv_ext = cuadro_2.index[fila_inv_ext==True].astype(int)[0]

	#keep top filas (nacionales)
	cuadro_2_new = cuadro_2[:index_inv_ext] 
	#sumamos los porcentajes en pesos (del cuadro 2) en Renta Variable,Fondos Mutuos y de Inversión,Disponible(1), DERIVADOS, OTROS NACIONALES(2) y (del cuadro 4_b) RF local 
	pesos = cuadro_2_new.loc[cuadro_2_new["Tipo_Instrumento"]=="RENTA VARIABLE","Total(porcentaje)"].tolist()[0] + cuadro_2_new.loc[cuadro_2_new["Tipo_Instrumento"]=="Fondos Mutuos y de Inversión","Total(porcentaje)"].tolist()[0] + cuadro_2_new.loc[cuadro_2_new["Tipo_Instrumento"]=="Disponible(1)","Total(porcentaje)"].tolist()[0] + cuadro_2_new.loc[cuadro_2_new["Tipo_Instrumento"]=="DERIVADOS","Total(porcentaje)"].tolist()[0] + cuadro_2_new.loc[cuadro_2_new["Tipo_Instrumento"]=="OTROS NACIONALES(2)","Total(porcentaje)"].tolist()[0] + cuadro_resumen_fisico_local.loc[cuadro_resumen_fisico_local["Unidad de Indexación"]=="Pesos","E"].tolist()[0]
	#reemplazamos el valor en pesos del cuadro_resumen_fisico_local (que solo toma RF local), por el monto total en pesos calculado en la línea anterior (que también incluye este)
	cuadro_resumen_fisico_local.loc[cuadro_resumen_fisico_local['Unidad de Indexación'] == 'Pesos', 'E'] = pesos

	#cambiamos el nombre de las columnas de la tabla, para que coincida con las otras dos, y luego poder concatenar los dataframes
	cuadro_resumen_fisico_local.columns = ["Moneda","Porcentaje"]
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_resumen_fisico_local["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_resumen_fisico_local = cuadro_resumen_fisico_local[['Fecha','Moneda','Porcentaje']]
	return cuadro_resumen_fisico_local


def cuadro_moneda_final(cuadro_resumen_forwards, cuadro_resumen_físico_extranjero, cuadro_resumen_fisico_local, date):
	'''
	CUADRO MONEDA FINAL
	'''
	#concatenamos los 3 dataframes de moneda
	cuadro_moneda_final = pd.concat([cuadro_resumen_forwards[["Moneda","Porcentaje","Fecha"]],cuadro_resumen_físico_extranjero[["Moneda","Porcentaje","Fecha"]],cuadro_resumen_fisico_local[["Moneda","Porcentaje","Fecha"]]])
	#usamos groupby para mostrar una sola fila por moneda y su porcentaje
	cuadro_moneda_final = cuadro_moneda_final.groupby("Moneda", as_index=False).sum()
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_moneda_final["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_moneda_final = cuadro_moneda_final[['Fecha','Moneda','Porcentaje']]
	return cuadro_moneda_final


def cuadro_duracion(cuadro_7, cuadro_3, date):
	'''
	CUADRO DURACION FINAL
	'''
	cuadro_7_E = cuadro_7[["Instituciones","E"]]
	#dejamos solo los totales relevantes para el cuadro de duracion resumen
	cuadro_duracion = cuadro_7_E.loc[cuadro_7_E["Instituciones"].isin(["TOTAL INSTITUCIONES ESTATALES","TOTAL EMPRESAS","TOTAL EXTRANJERO"])]
	#se crea un diccionario que iguala la institucion del cuadro duracion con el nombre que lo queremos llamar
	instituciones_dict = {"TOTAL INSTITUCIONES ESTATALES":"Gobierno_BancoCentral",
	   "TOTAL EMPRESAS":"Corporativos_Empresa",
	   "TOTAL EXTRANJERO":"Extranjero"}
	#se reemplaza la institucion por el nombre de la clasificación, utilizando el diccionario
	cuadro_duracion["Instituciones"] = cuadro_duracion["Instituciones"].map(instituciones_dict)
	#para corporativos_bancarios y depositos_letras: obtenemos los valores de las duraciones y porcentajes individuales de cada instrumento, y luego se hace el weighted average para calcular la duración de la clasificacion en cuestión (bucket)
	dur_BEF = cuadro_7_E.loc[(cuadro_7_E["Instituciones"] == "BEF"), "E"].sum()
	dur_BHM = cuadro_7_E.loc[(cuadro_7_E["Instituciones"] == "BHM"), "E"].sum()
	dur_BSF = cuadro_7_E.loc[(cuadro_7_E["Instituciones"] == "BSF"), "E"].sum()
	por_BEF = cuadro_3.loc[(cuadro_3[""] == "BEF"), "E"].sum()
	por_BHM = cuadro_3.loc[(cuadro_3[""] == "BHM"), "E"].sum()
	por_BSF = cuadro_3.loc[(cuadro_3[""] == "BSF"), "E"].sum()
	corporativos_bancarios = ((dur_BEF*por_BEF)+(dur_BHM*por_BHM)+(dur_BSF*por_BSF))/(por_BEF+por_BHM+por_BSF)
	dur_DPF = cuadro_7_E.loc[(cuadro_7_E["Instituciones"] == "DPF"), "E"].sum()
	dur_LHF = cuadro_7_E.loc[(cuadro_7_E["Instituciones"] == "LHF"), "E"].sum()
	por_DPF = cuadro_3.loc[(cuadro_3[""] == "DPF"), "E"].sum()
	por_LHF = cuadro_3.loc[(cuadro_3[""] == "LHF"), "E"].sum()
	depositos_letras = ((dur_DPF*por_DPF)+(dur_LHF*por_LHF))/(por_DPF+por_LHF)
	#se crea un dataframe adicional con estas dos clasificaciones, para luego agregarlo al cuadro resumen
	datos_df_adicional = [('Corporativos_Bancarios',corporativos_bancarios),('Depositos_Letras',depositos_letras)]
	columnas_df_adicional = ["Instituciones", "E"]
	df_adicional = pd.DataFrame(datos_df_adicional, columns=columnas_df_adicional)
	#se concatenan ambos dataframes para llegar al cuadro resumen final
	cuadro_duracion_final = pd.concat([cuadro_duracion[["Instituciones","E"]],df_adicional[["Instituciones","E"]]])
	#se divide por 365 para pasar la duracion en dias a años
	cuadro_duracion_final["E"] = cuadro_duracion_final["E"]/365
	#se agrega la columna "fecha" para reconocer de qué periodo son los datos
	cuadro_duracion_final["Fecha"] = date
	#se pone la fecha como la primer columna del dataframe
	cuadro_duracion_final = cuadro_duracion_final[['Fecha','Instituciones','E']]
	return cuadro_duracion_final

def delete_old_data(tabla, date_string):
    '''
    Borra la cartera acumulada de la base de datos.
    '''
    print("Deleting old data...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    delete_statement = "DELETE FROM tabla WHERE 1=1 and Fecha='date_string'"
    delete_statement = delete_statement.replace("tabla", tabla)
    delete_statement = delete_statement.replace("date_string", date_string)
    fs.run_sql(conn, delete_statement)
    fs.disconnect_database(conn)


def upload_cuadro_2(cuadro_2):
    '''
    UPLOAD cuadro_2 DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFP_cuadro_2", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_2)
    print("Uploading historical data cuadro_2...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFP_cuadro_2 VALUES (%s,%s,%d,%d,%d,%d,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_3(cuadro_3):
    '''
    UPLOAD cuadro_3 DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFP_cuadro_3", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_3)
    print("Uploading historical data cuadro_3...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFP_cuadro_3 VALUES (%s,%s,%d,%d,%d,%d,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_4_a(cuadro_4_a):
    '''
    UPLOAD cuadro_4_a DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFP_cuadro_4_a", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_4_a)
    print("Uploading historical data cuadro_4_a...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFP_cuadro_4_a VALUES (%s,%s,%s,%d,%d,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_4_b(cuadro_4_b):
    '''
    UPLOAD cuadro_4_b DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFP_cuadro_4_b", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_4_b)
    print("Uploading historical data cuadro_4_b...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFP_cuadro_4_b VALUES (%s,%s,%s,%d,%d,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_7(cuadro_7):
    '''
    UPLOAD cuadro_7 DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFP_cuadro_7", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_7)
    print("Uploading historical data cuadro_7...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFP_cuadro_7 VALUES (%s,%s,%d,%d,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_22(cuadro_22):
    '''
    UPLOAD cuadro_22 DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFP_cuadro_22", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_22)
    print("Uploading historical data cuadro_22...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFP_cuadro_22 VALUES (%s,%s,%d,%d,%d,%d,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_25(cuadro_25_ajus):
    '''
    UPLOAD cuadro_25 DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFP_cuadro_25", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_25_ajus)
    print("Uploading historical data cuadro_25...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFP_cuadro_25 VALUES (%s,%s,%s,%s,%d,%d,%d,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_27_28(cuadro_27_28_ajus):
    '''
    UPLOAD cuadro_27_28 DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFP_cuadro_27_28", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_27_28_ajus)
    print("Uploading historical data cuadro_27_28...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFP_cuadro_27_28 VALUES (%s,%s,%s,%s,%s,%d,%d,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_resumen_forwards(cuadro_resumen_forwards):
    '''
    UPLOAD cuadro_resumen_forwards DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFPE_resumen_forwards", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_resumen_forwards)
    print("Uploading historical data AFPE_resumen_forwards...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFPE_resumen_forwards VALUES (%s,%s,%d,%d,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_resumen_físico_extranjero(cuadro_resumen_físico_extranjero):
    '''
    UPLOAD cuadro_resumen_físico_extranjero DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFPE_resumen_físico_extranjero", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_resumen_físico_extranjero)
    print("Uploading historical data AFPE_resumen_físico_extranjero...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFPE_resumen_físico_extranjero VALUES (%s,%s,%d,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_resumen_físico_local(cuadro_resumen_físico_local):
    '''
    UPLOAD cuadro_resumen_físico_local DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFPE_resumen_físico_local", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_resumen_físico_local)
    print("Uploading historical data AFPE_resumen_físico_local...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFPE_resumen_físico_local VALUES (%s,%s,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_moneda_final(cuadro_moneda_final):
    '''
    UPLOAD cuadro_moneda_final DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFPE_moneda_final", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_moneda_final)
    print("Uploading historical data AFPE_moneda_final...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFPE_moneda_final VALUES (%s,%s,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def upload_cuadro_duracion(cuadro_duracion):
    '''
    UPLOAD cuadro_duracion DATAFRAME TO BBDD
    '''
    delete_old_data("ZHIS_AFPE_duracion", date_string)
    dataset_tuplas = fs.format_tuples(df = cuadro_duracion)
    print("Uploading historical data AFPE_duracion...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_AFPE_duracion VALUES (%s,%s,%d)", dataset_tuplas)
    conn.commit()
    fs.disconnect_database(conn)


#leer .xml de la super de pensiones
path = "cartera_agregada201708.xml"
y = read_file(path)

#extraer la fecha del path para agregársela como columna a todos los cuadros
date = file_date(path)
date_string = date.strftime('%Y-%m-%d')

#cuadros AFPs
cuadro_2 = cuadro_2(y, date)
cuadro_3= cuadro_3(y, date)
cuadro_4_a = cuadro_4_a(y, date)
cuadro_4_b = cuadro_4_b(y, date)
cuadro_7 = cuadro_7(y, date)
cuadro_22 = cuadro_22(y, date)
cuadro_25 = cuadro_25(y, date)
cuadro_25_ajus = cuadro_25_ajus(y, date)
cuadro_27_28 = cuadro_27_28(y, date)
cuadro_27_28_ajus = cuadro_27_28_ajus(y, date)

#PROYECTO E PLUS
total_activos = total_activos(cuadro_2)
		#print("Total activos Fondo E=",total_activos)
cuadro_resumen_forwards = cuadro_resumen_forwards(cuadro_27_28_ajus, total_activos, date)
cuadro_resumen_físico_extranjero = cuadro_resumen_físico_extranjero(cuadro_22, total_activos, date)
cuadro_resumen_fisico_local = cuadro_resumen_fisico_local(cuadro_4_b, cuadro_2, date)
cuadro_moneda_final = cuadro_moneda_final(cuadro_resumen_forwards, cuadro_resumen_físico_extranjero, cuadro_resumen_fisico_local, date)
		#print("Total=",cuadro_moneda_final["Porcentaje"].sum())
cuadro_duracion = cuadro_duracion(cuadro_7, cuadro_3, date)

#UPLOAD TO BBDD
upload_cuadro_2(cuadro_2)
upload_cuadro_3(cuadro_3)
upload_cuadro_4_a(cuadro_4_a)
upload_cuadro_4_b(cuadro_4_b)
upload_cuadro_7(cuadro_7)
upload_cuadro_22(cuadro_22)
upload_cuadro_25(cuadro_25_ajus)
upload_cuadro_27_28(cuadro_27_28_ajus)
upload_cuadro_resumen_forwards(cuadro_resumen_forwards)
upload_cuadro_resumen_físico_extranjero(cuadro_resumen_físico_extranjero)
upload_cuadro_resumen_físico_local(cuadro_resumen_fisico_local)
upload_cuadro_moneda_final(cuadro_moneda_final)
upload_cuadro_duracion(cuadro_duracion)