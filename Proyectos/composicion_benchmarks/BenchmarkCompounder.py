"""
Created on Thu Dec 13 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
from libreria_fdo import *

'''FUNCIONES COMPOUNDER'''

def insertarBenchmarks(tuple_list):
    '''
    Inserta las tuplas con todos los benchmarks compuestos a la base de datos.
    '''
    print("Tuples to insert: "+str(len(tuple_list)))
    print("***********************INSETING***********************")
    conn = connect_database_user(server ="Puyehue", database = "MesaInversiones", username = "usrConsultaComercial", password = "Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO Benchmarks_Dinamica VALUES (%s,%d,%d)", tuple_list)
    conn.commit()

def borrarDatosAntiguos(dia_inic):
    '''
    Borra los benchmarks de los ultimos 10 dias en la base de datos.
    '''
    print("***********************DELETING***********************")
    conn= connect_database_user(server = "Puyehue", database = "MesaInversiones", username = "usrConsultaComercial", password = "Comercial1w")
    query=read_file(".\\querys_compounder\\delete_benchmarks.sql").replace("AUTODATE", dia_inic)
    run_sql(conn, query)
    disconnect_database(conn)


def getIndexSerie(index_id, dia_inic, dia_fin):
	'''
	Retorna un vector numpy con la serie historia del indice.
	'''
	query_serie = read_file(".\\querys_compounder\\indice_serie.sql").replace("AUTOINDICE", str(index_id)).replace("AUTOINIC", dia_inic).replace("AUTOFIN", dia_fin)
	conn = connect_database_user(server = "Puyehue", database = "MesaInversiones", username = "usrConsultaComercial", password = "Comercial1w")
	cursor = query_database(conn, query_serie)
	serie_vect = array_to_numpy(get_list_sql(cursor))
	disconnect_database(conn)

	return serie_vect

def getBenchmarkWeights(benchmark_id):
	'''
	Retorna una tabla con los weight de cada indice, dado un benchmark.
	'''
	query_indices_weight = read_file(".\\querys_compounder\\indices_weight.sql").replace("AUTOBENCHMARK", str(benchmark_id))
	conn = connect_database_user(server = "Puyehue", database = "MesaInversiones", username = "usrConsultaComercial", password = "Comercial1w")
	cursor = query_database(conn, query_indices_weight)
	indices_weight_table = get_table_sql(cursor)
	disconnect_database(conn)
	return indices_weight_table


def getBenchmarkIds():
	'''
	Retorna todas las ids de los distintos benchmarks.
	'''
	print("**********************FETCHING BENCHMARK IDS**********************")
	query_benchmark_ids=read_file(".\\querys_compounder\\benchmark_ids.sql")
	conn = connect_database_user(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
	cursor = query_database(conn, query_benchmark_ids)
	lista_ids = get_table_sql(cursor)
	disconnect_database(conn)
	return lista_ids


def compoundIndexes(lista_ids, dia_inic, dia_fin, day_list, dia_fin_usd):
	'''
	Retorna todos los indices compuestos en una lista de tuplas para subirlas, dada la lista de benchmark ids.
	'''
	#Por cada benchmark vamos a componer sus indices y insertarlos en la lista de tuplas
	tuple_list = []
	#Guardamos la serie del dolar corrida para homologar todos los benchmark a pesos (por convencion tenemos todos los benchmarks en pesos)
	serie_usd = getIndexSerie(index_id = 66, dia_inic = dia_inic, dia_fin = dia_fin_usd)
	for benchmark in lista_ids:
		benchmark_id = benchmark[0]
		benchmark_currency = benchmark[1]
		print("Compounding benchmark  "+str(benchmark_id))
		#Obtenemos los weight de cada indice
		indices_weight_table = getBenchmarkWeights(benchmark_id = benchmark_id)	
		weighted_tuples = []
		#Por cada indice obtendremos su vector de rentabilidades
		for index_pair in indices_weight_table:
			index_id = index_pair[0]
			index_weight = float(index_pair[1])
			index_currency = index_pair[2]
			#Obtenemos la serie historia del indice en forma de vector numpy
			serie_vect=getIndexSerie(index_id = index_id, dia_inic = dia_inic, dia_fin = dia_fin)
			#En caso de que el indice este en dolares lo mapeamos a pesos para fondos con conta en pesos(notar que se multiplica con un dia de desfase) 
			if index_currency == "US$" and benchmark_currency =="$":
				serie_vect=serie_vect*(serie_usd[1:])
			#Transformamos el vector en un vector de retornos y lo guardamos en la lista de vectores
			weighted_vect = np.log(serie_vect[1:]/serie_vect[:-1])*index_weight
			weighted_tuples.append(weighted_vect)
		#Sumamos todos los vectores, luego obtenemos la rentabilidad acumulada y lo dejamos en base 1000
		temp_vect = np.zeros(len(weighted_tuples[0]))
		for vect in weighted_tuples:
			temp_vect = temp_vect+vect
		compounded_vect = np.exp(temp_vect.cumsum())*1000
		compounded_vect = np.append(1000,compounded_vect)
		#Esto sirve para debugear, imprime el benchmark en pantalla
		#if benchmark_id==9: 
		#	print(compounded_vect.size)
		#	print(compounded_vect)
		#	plt.plot(compounded_vect)
		#	plt.show()
		#Insertamos cada valor del benchmark en la lista de tuplas con la fecha y el benchmark id
		for day_number in range(len(day_list)):
			tuple_list.append(tuple([convert_date_to_string(day_list[day_number]), benchmark_id, compounded_vect[day_number]]))
	return tuple_list


print("**********************START**********************")

#Fijamos como fecha de inicio para empezar a componer el 2011-01-03
dia_inic = "2011-01-03"
dia_spot = get_ndays_from_today(0)
dia_fin = get_prev_weekday(dia_spot)
dia_fin_usd = dia_spot
day_list = get_weekdays_dates_between(convert_string_to_date(dia_inic), convert_string_to_date(dia_fin))
print("Days to update: "+str(len(day_list)))
print("*******FETCHING DATA FROM: "+ dia_inic + " TO " + dia_fin + "***********")

#Sacamos las ids de los benchmarks a actualizar
lista_ids = getBenchmarkIds()
#Componemos los indices y los guardamos en una lista de tuplas
tuple_list = compoundIndexes(lista_ids = lista_ids, dia_inic = dia_inic, dia_fin = dia_fin, day_list = day_list, dia_fin_usd = dia_fin_usd)

#Borramos los benchmarks antiguos de la base de datos
borrarDatosAntiguos(dia_inic = dia_inic)

#Insertamos las tuplas en la base de datos
insertarBenchmarks(tuple_list = tuple_list)

print("**********************END**********************")


