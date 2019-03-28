"""
Created on Thu Jul 22 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
from libreria_fdo import *

def send_mail_report():
    '''
    Envia el mail a fernando suarez 1313. 
    '''
    print("****ENVIANDO MAIL****")
    path_agf = get_self_path() + "output_return_report\\AGF\\"
    path_comercial = get_self_path() + "output_return_report\\Comercial\\"
    path_carteras = get_self_path() + "output_return_report\\Carteras\\"
    tema="Reporte de rentabilidad"
    cuerpo="Estimados, adjunto el reporte diario de rentabilidad de fondos. \nSaludos"
    correos=["fsuarez@credicorpcapital.com", "fsuarez1@uc.cl"]
    rutas=[path_agf + "Rentabilidades_Fondos_AGF.pdf", path_comercial + "Rentabilidades_Fondos_Area_Comercial.pdf", path_carteras + "Rentabilidades_Carteras.pdf"]
    send_mail_attach(subject=tema, body=cuerpo, mails=correos, attachment_paths=rutas)
    delete_file(path_agf + "Rentabilidades_Fondos_AGF.pdf")
    delete_file(path_comercial + "Rentabilidades_Fondos_Area_Comercial.pdf")
    delete_file(path_carteras + "Rentabilidades_Carteras.pdf")

def print_report_pdf(wb, tabla_carteras, tipos_carteras):
	'''
	Imprime el nuevo informe en pdf. 
	'''
	print("*********IMPRIMIENDO INFORME*******")
	#Se sacan los path de cada archivo a enviar
	path = get_self_path()
	path_agf=path + "output_return_report\\AGF\\"
	path_comercial=path + "output_return_report\\Comercial\\"
	path_carteras=path + "output_return_report\\Carteras\\"
	path_pdf=path_agf + "Rentabilidades_Fondos.PDF"
	path_pdf_lux=path_agf + "Rentabilidades_Fondos_Lux.PDF"
	path_pdf_comercial=path_comercial + "Rentabilidades_Fondos_Comercial.PDF"
	path_pdf_lux_comercial=path_comercial + "Rentabilidades_Fondos_Lux_Comercial.PDF"
	export_sheet_pdf(sheet_index = 0, path_in = path, path_out = path_pdf)
	export_sheet_pdf(sheet_index = 3, path_in = path, path_out = path_pdf_lux)
	export_sheet_pdf(sheet_index = 2, path_in = path, path_out = path_pdf_comercial)
	export_sheet_pdf(sheet_index = 4, path_in = path, path_out = path_pdf_lux_comercial)
	merge_pdf(path = path_comercial, output_name = "Rentabilidades_Fondos_Area_Comercial.pdf")
	merge_pdf(path = path_agf, output_name = "Rentabilidades_Fondos_AGF.pdf")
	delete_file(path_pdf)
	delete_file(path_pdf_lux)
	delete_file(path_pdf_comercial)
	delete_file(path_pdf_lux_comercial)
	
	#Por cada tipo de cartera se generara un PDF, debemos ir pegando el valor en la hoja inputs
	for tipo in tipos_carteras:
		clear_table_xl(wb = wb, sheet="Inputs",row=3, column=57)
		paste_val_xl(wb = wb, sheet="Inputs", row=8, column=32, value=tipo)
		row = 3
		#Agregamos el nombre de cada cartera a la hoja del reporte para un tipo dado (asi puedo filtrar con Excel)
		for cartera in tabla_carteras:
			nombre_cartera = cartera[1]
			nombre_benchmark = cartera[2]
			if tipo == nombre_benchmark:
				paste_val_xl(wb = wb, sheet="Inputs", row=row, column=57, value=nombre_cartera)
				row+=1
		path_tipo=path_carteras+tipo+".PDF"
		export_sheet_pdf(sheet_index=5, path_in=path, path_out=path_tipo)
	#Juntamos todos los pdf en uno para enviar
	merge_pdf(path = path_carteras, output_name="Rentabilidades_Carteras.pdf")
	#Borramos los archivos de cada tipo de cartera
	for tipo in tipos_carteras:
		path_tipo = path_carteras+tipo+".PDF"
		delete_file(path_tipo)

	# Guardamos backup
	name = "Return_Report_AGF_" + get_ndays_from_today(0).replace("-","") + ".pdf"
	src = ".\\output_return_report\\AGF\\Rentabilidades_Fondos_AGF.pdf"
	dst = "L:\\Rates & FX\\fsb\\reporting\\return_report_backup\\" + name
	copy_file(src, dst)

	name = "Return_Report_Comercial_" + get_ndays_from_today(0).replace("-","") + ".pdf"
	src = ".\\output_return_report\\Comercial\\Rentabilidades_Fondos_Area_Comercial.pdf"
	dst = "L:\\Rates & FX\\fsb\\reporting\\return_report_backup\\" + name
	copy_file(src, dst)

	name = "Return_Report_Carteras_" + get_ndays_from_today(0).replace("-","") + ".pdf"
	src = ".\\output_return_report\\Carteras\\Rentabilidades_Carteras.pdf"
	dst = "L:\\Rates & FX\\fsb\\reporting\\return_report_backup\\" + name
	copy_file(src, dst)



def get_serie_cuota_cc(dia_inic, dia_fin, codigo_fdo, serie):
    '''
    Retorna un vector con la serie del valor cuota con comision y ajustado entre las fechas indicadas.
    '''
    query_valores_cuota = read_file(".\\querys_return_report\\valores_cuota.sql").replace("AUTODATE1", dia_inic).replace("AUTOFONDO", codigo_fdo).replace("AUTOSERIE", serie).replace("AUTODATE2", dia_fin)
    conn = connect_database_user(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor = query_database(conn, query_valores_cuota)
    vect_valores_cuota_cc = array_to_numpy(get_list_sql(cursor))
    disconnect_database(conn)
    return vect_valores_cuota_cc

def get_serie_cuota_lux(dia_inic, dia_fin, ticker):
    '''
    Retorna un vector con la serie del valor cuota de un fondo lux entre ambas fechas.
    '''
    query_valores_cuota = read_file(".\\querys_return_report\\valores_cuota_lux.sql").replace("AUTODATE1", dia_inic).replace("AUTOTICKER", ticker).replace("AUTODATE2", dia_fin)
    conn = connect_database_user(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor = query_database(conn, query_valores_cuota)
    vect_valores_cuota_cc = array_to_numpy(get_list_sql(cursor))
    disconnect_database(conn)
    return vect_valores_cuota_cc


def get_serie_benchmark(dia_inic, dia_fin, benchmark_id):
	'''
	Retorna un vector con la serie del benchmark entre las fechas indicadas.
	'''
	query_serie_benchmark=read_file(".\\querys_return_report\\serie_benchmark.sql").replace("AUTODATE1", dia_inic).replace("AUTOBENCHMARK", str(benchmark_id)).replace("AUTODATE2", dia_fin)
	conn = connect_database_user(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
	cursor = query_database(conn, query_serie_benchmark)
	vect_benchmark = array_to_numpy(get_list_sql(cursor))
	disconnect_database(conn)
	return vect_benchmark

def compute_portfolio_return(dia_inic, dia_fin, wb, wtd_dias, mtd_dias, ytd_dias, fondo, fila_fondo):
	'''
	Calcula la rentabilidad de un fondo y su benchmark para las granularidades del informe, devuelve una lista con rentabilidades por granularidad.
	'''
	datos_fondo = []
	codigo_fdo = fondo[0]
	serie = fondo[1]
	nombre_fdo = fondo[2]
	benchmark_id = fondo[3]
	estrategia = fondo[4]
	moneda = 	fondo[5]
	#Obtenemos un vector con la serie del benchmark
	vect_benchmark = get_serie_benchmark(dia_inic = dia_inic, dia_fin = dia_fin, benchmark_id = benchmark_id)
	#Obtenemos un vector con la serie del valor cuota con comision
	vect_valores_cuota_cc = get_serie_cuota_cc(dia_inic = dia_inic, dia_fin = dia_fin, codigo_fdo = codigo_fdo, serie = serie)
	#Obtenemos un vector con la serie del tac diario
	tacs = get_serie_tac(dia_inic = dia_inic, dia_fin = dia_fin, codigo_fdo = codigo_fdo, serie = serie)
	vect_valores_cuota_sc = get_serie_cuota_sc(serie_cuota_cc = vect_valores_cuota_cc, serie_tac = tacs)
	#Imprimimos informacion relevante del fondo
	print("FONDO: " + codigo_fdo)
	print("SERIE: " + serie)
	print("BENCHMARK ID: " + str(benchmark_id))
	#Para cada bucket de tiempo calculamos la rentabilidad acumulada del benchmark, el fondo con comision y el fondo sin comision
	#DTD
	if vect_valores_cuota_cc.size > 2:
		rentabilidad_1d_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - 2]) - 1
		rentabilidad_1d_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - 2]) - 1
		rentabilidad_1d_sc = (vect_valores_cuota_sc[vect_valores_cuota_sc.size - 1] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - 2]) - 1
	else:
		rentabilidad_1d_bmk = "-"
		rentabilidad_1d_cc = "-"
		rentabilidad_1d_sc = "-"
	#12M
	if vect_valores_cuota_cc.size > 264:
		rentabilidad_12m_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - 263]) - 1
		rentabilidad_12m_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - 263]) - 1
		rentabilidad_12m_sc = (vect_valores_cuota_sc[vect_valores_cuota_sc.size - 1] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - 263]) - 1	
	else:
		rentabilidad_12m_bmk = "-"
		rentabilidad_12m_cc = "-"
		rentabilidad_12m_sc = "-"
	'''
	#24M
	if vect_valores_cuota_cc.size > 524:
		rentabilidad_24m_bmk = (vect_benchmark[vect_benchmark.size - 1]/vect_benchmark[vect_benchmark.size-524])-1
		rentabilidad_24m_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - 524]) - 1
		rentabilidad_24m_sc = (vect_valores_cuota_sc[vect_valores_cuota_sc.size - 1] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - 524]) - 1		
	else:
		rentabilidad_24m_bmk = "-"
		rentabilidad_24m_cc = "-"
		rentabilidad_24m_sc = "-"
	'''
	#WTD
	if vect_valores_cuota_cc.size > wtd_dias:
		rentabilidad_wtd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - wtd_dias]) - 1
		rentabilidad_wtd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - wtd_dias]) - 1
		rentabilidad_wtd_sc = (vect_valores_cuota_sc[vect_valores_cuota_sc.size - 1] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - wtd_dias]) - 1		
	else:
		rentabilidad_wtd_bmk = "-"
		rentabilidad_wtd_cc = "-"
		rentabilidad_wtd_sc = "-"
	#MTD
	if vect_valores_cuota_cc.size > mtd_dias:
		rentabilidad_mtd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - mtd_dias]) - 1
		rentabilidad_mtd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - mtd_dias]) - 1
		rentabilidad_mtd_sc = (vect_valores_cuota_sc[vect_valores_cuota_sc.size - 1] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - mtd_dias]) - 1		
	else:
		rentabilidad_mtd_bmk = "-"
		rentabilidad_mtd_cc = "-"
		rentabilidad_mtd_sc = "-"
	#YTD
	if vect_valores_cuota_cc.size > ytd_dias:
		rentabilidad_ytd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - ytd_dias]) - 1
		rentabilidad_ytd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias]) - 1
		rentabilidad_ytd_sc = (vect_valores_cuota_sc[vect_valores_cuota_sc.size - 1] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - ytd_dias]) - 1		
	else:
		rentabilidad_ytd_bmk = "-"
		rentabilidad_ytd_cc = "-"
		rentabilidad_ytd_sc = "-"
	#QUARTERS SEPARADOS
	#1Q
	if ytd_dias > 65 and vect_valores_cuota_cc.size > ytd_dias - 0:
		rentabilidad_1q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 64] / vect_benchmark[vect_benchmark.size - ytd_dias + 0]) - 1
		rentabilidad_1q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 64] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 0]) - 1
		rentabilidad_1q_sc= (vect_valores_cuota_sc[vect_valores_cuota_sc.size - ytd_dias + 64] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - ytd_dias + 0]) - 1		
	else:
		rentabilidad_1q_bmk = "-"
		rentabilidad_1q_cc = "-"
		rentabilidad_1q_sc = "-"
	#2Q
	if ytd_dias > 130 and vect_valores_cuota_cc.size > ytd_dias - 64:
		rentabilidad_2q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 129] / vect_benchmark[vect_benchmark.size - ytd_dias + 64]) - 1
		rentabilidad_2q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 129] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 64]) - 1
		rentabilidad_2q_sc = (vect_valores_cuota_sc[vect_valores_cuota_sc.size - ytd_dias + 129] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - ytd_dias + 64]) - 1
	else:
		rentabilidad_2q_bmk = "-"
		rentabilidad_2q_cc = "-"
		rentabilidad_2q_sc = "-"
	#3Q
	if ytd_dias > 196 and vect_valores_cuota_cc.size > ytd_dias - 130:
		rentabilidad_3q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 195] / vect_benchmark[vect_benchmark.size - ytd_dias + 129]) - 1
		rentabilidad_3q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 195] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 129]) - 1
		rentabilidad_3q_sc = (vect_valores_cuota_sc[vect_valores_cuota_sc.size - ytd_dias + 195] / vect_valores_cuota_sc[vect_valores_cuota_sc.size - ytd_dias + 129]) - 1
	else:
		rentabilidad_3q_bmk = "-"
		rentabilidad_3q_cc = "-"
		rentabilidad_3q_sc = "-"


	#Insertamos todas las rentabilidades al vector del fondo y la serie default
	datos_fondo.append(estrategia)
	datos_fondo.append(codigo_fdo)
	datos_fondo.append(serie)
	datos_fondo.append(nombre_fdo)
	datos_fondo.append(rentabilidad_1d_cc)
	datos_fondo.append(rentabilidad_1d_sc)
	datos_fondo.append(rentabilidad_1d_bmk)
	datos_fondo.append(rentabilidad_wtd_cc)
	datos_fondo.append(rentabilidad_wtd_sc)
	datos_fondo.append(rentabilidad_wtd_bmk)
	datos_fondo.append(rentabilidad_mtd_cc)
	datos_fondo.append(rentabilidad_mtd_sc)
	datos_fondo.append(rentabilidad_mtd_bmk)
	datos_fondo.append(rentabilidad_ytd_cc)
	datos_fondo.append(rentabilidad_ytd_sc)
	datos_fondo.append(rentabilidad_ytd_bmk)
	datos_fondo.append(rentabilidad_1q_cc)
	datos_fondo.append(rentabilidad_1q_sc)
	datos_fondo.append(rentabilidad_1q_bmk)
	datos_fondo.append(rentabilidad_2q_cc)
	datos_fondo.append(rentabilidad_2q_sc)
	datos_fondo.append(rentabilidad_2q_bmk)
	datos_fondo.append(rentabilidad_3q_cc)
	datos_fondo.append(rentabilidad_3q_sc)
	datos_fondo.append(rentabilidad_3q_bmk)
	datos_fondo.append(rentabilidad_12m_cc)
	datos_fondo.append(rentabilidad_12m_sc)
	datos_fondo.append(rentabilidad_12m_bmk)
	'''
	datos_fondo.append(rentabilidad_24m_cc)
	datos_fondo.append(rentabilidad_24m_sc)
	datos_fondo.append(rentabilidad_24m_bmk)
	'''
	datos_fondo.append(moneda)
	

	return datos_fondo


def compute_portfolio_return_lux(dia_inic, dia_fin, wb, wtd_dias, mtd_dias, ytd_dias, fondo, fila_fondo):
	'''
	Calcula la rentabilidad de un fondo de luxemburgo y su benchmark para las granularidades del informe, devuelve una lista con rentabilidades por granularidad.
	'''
	datos_fondo = []
	codigo_fdo = fondo[0]
	nombre_fdo = fondo[1]
	ticker = fondo[2]
	benchmark_id = fondo[3]
	#Obtenemos un vector con la serie del benchmark
	vect_benchmark = get_serie_benchmark(dia_inic=dia_inic, dia_fin=dia_fin, benchmark_id=benchmark_id)
	#Obtenemos un vector con la serie del valor cuota con comision
	vect_valores_cuota_cc = get_serie_cuota_lux(dia_inic=dia_inic, dia_fin=dia_fin, ticker=ticker)
	#Imprimimos informacion relevante del fondo
	print("FONDO: " + codigo_fdo)
	print("BENCHMARK ID: " + str(benchmark_id))
	#Para cada bucket de tiempo calculamos la rentabilidad acumulada del benchmark, el fondo con comision y el fondo sin comision
	#DTD
	if vect_valores_cuota_cc.size > 2:
		rentabilidad_1d_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - 2]) - 1
		rentabilidad_1d_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - 2]) - 1
	else:
		rentabilidad_1d_bmk = "-"
		rentabilidad_1d_cc = "-"
	#12M
	if vect_valores_cuota_cc.size > 264:
		rentabilidad_12m_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - 263]) - 1
		rentabilidad_12m_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - 263]) - 1	
	else:
		rentabilidad_12m_bmk = "-"
		rentabilidad_12m_cc = "-"
	'''
	#24M
	if vect_valores_cuota_cc.size > 524:
		rentabilidad_24m_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - 524]) - 1
		rentabilidad_24m_cc=(vect_valores_cuota_cc[vect_valores_cuota_cc.size-1]/vect_valores_cuota_cc[vect_valores_cuota_cc.size-524])-1	
	else:
		rentabilidad_24m_bmk="-"
		rentabilidad_24m_cc="-"
	'''
	#WTD
	if vect_valores_cuota_cc.size > wtd_dias:
		rentabilidad_wtd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - wtd_dias]) - 1
		rentabilidad_wtd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - wtd_dias]) - 1	
	else:
		rentabilidad_mtd_bmk = "-"
		rentabilidad_mtd_cc = "-"
	#MTD
	if vect_valores_cuota_cc.size > mtd_dias:
		rentabilidad_mtd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - mtd_dias]) - 1
		rentabilidad_mtd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - mtd_dias]) - 1	
	else:
		rentabilidad_mtd_bmk = "-"
		rentabilidad_mtd_cc = "-"
	#YTD
	if vect_valores_cuota_cc.size > ytd_dias:
		rentabilidad_ytd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - ytd_dias]) - 1
		rentabilidad_ytd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias]) - 1	
	else:
		rentabilidad_ytd_bmk = "-"
		rentabilidad_ytd_cc = "-"
	#QUARTERS SEPARADOS
	#1Q
	if ytd_dias > 65 and vect_valores_cuota_cc.size > ytd_dias - 0:
		rentabilidad_1q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 64] / vect_benchmark[vect_benchmark.size - ytd_dias + 0]) - 1
		rentabilidad_1q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size-ytd_dias + 64] / vect_valores_cuota_cc[vect_valores_cuota_cc.size-ytd_dias + 0]) - 1
	else: 
		rentabilidad_1q_bmk = "-"
		rentabilidad_1q_cc = "-"
	#2Q
	if ytd_dias > 130 and vect_valores_cuota_cc.size > ytd_dias - 64:
		rentabilidad_2q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 129] / vect_benchmark[vect_benchmark.size - ytd_dias + 64]) - 1
		rentabilidad_2q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 129] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 64]) - 1
	else:
		rentabilidad_2q_bmk = "-"
		rentabilidad_2q_cc = "-"
	#3Q
	if ytd_dias > 196 and vect_valores_cuota_cc.size > ytd_dias - 130:
		rentabilidad_3q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 195] / vect_benchmark[vect_benchmark.size - ytd_dias + 129]) - 1
		rentabilidad_3q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 195] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 129]) - 1
	else:
		rentabilidad_3q_bmk = "-"
		rentabilidad_3q_cc = "-"
	

	#Insertamos todas las rentabilidades al vector del fondo y la serie default
	datos_fondo.append(codigo_fdo)
	datos_fondo.append(nombre_fdo)
	datos_fondo.append(rentabilidad_1d_cc)
	datos_fondo.append(rentabilidad_1d_bmk)
	datos_fondo.append(rentabilidad_wtd_cc)
	datos_fondo.append(rentabilidad_wtd_bmk)
	datos_fondo.append(rentabilidad_mtd_cc)
	datos_fondo.append(rentabilidad_mtd_bmk)
	datos_fondo.append(rentabilidad_ytd_cc)
	datos_fondo.append(rentabilidad_ytd_bmk)
	datos_fondo.append(rentabilidad_1q_cc)
	datos_fondo.append(rentabilidad_1q_bmk)
	datos_fondo.append(rentabilidad_2q_cc)
	datos_fondo.append(rentabilidad_2q_bmk)
	datos_fondo.append(rentabilidad_3q_cc)
	datos_fondo.append(rentabilidad_3q_bmk)
	datos_fondo.append(rentabilidad_12m_cc)
	datos_fondo.append(rentabilidad_12m_bmk)
	'''
	datos_fondo.append(rentabilidad_24m_cc)
	datos_fondo.append(rentabilidad_24m_bmk)
	'''

	return datos_fondo

def compute_portfolio_return_carteras(dia_inic, dia_fin, wb, wtd_dias, mtd_dias, ytd_dias, fondo, fila_fondo):
	'''
	Calcula la rentabilidad de una cartera administrada y su benchmark para las granularidades del informe, devuelve una lista con rentabilidades por granularidad.
	'''
	datos_fondo = []
	codigo_fdo = fondo[0]
	nombre_fdo = fondo[1]
	nombre_benchmark = fondo[2]
	benchmark_id = fondo[3]
	serie = "1"
	#Obtenemos un vector con la serie del benchmark
	vect_benchmark = get_serie_benchmark(dia_inic = dia_inic, dia_fin = dia_fin, benchmark_id = benchmark_id)
	#Obtenemos un vector con la serie del valor cuota con comision
	vect_valores_cuota_cc = get_serie_cuota_cc(dia_inic = dia_inic, dia_fin = dia_fin, codigo_fdo = codigo_fdo, serie = serie)
	#Imprimimos informacion relevante del fondo
	print("CARTERA: " + codigo_fdo)
	print("BENCHMARK ID: " + str(benchmark_id))
	#Para cada bucket de tiempo calculamos la rentabilidad acumulada del benchmark, el fondo con comision y el fondo sin comision
	#DTD
	if vect_valores_cuota_cc.size > 2:
		rentabilidad_1d_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - 2]) - 1
		rentabilidad_1d_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - 2]) - 1
	else:
		rentabilidad_1d_bmk = "-"
		rentabilidad_1d_cc = "-"
	#12M
	if vect_valores_cuota_cc.size > 264:
		rentabilidad_12m_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - 263]) - 1
		rentabilidad_12m_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - 263]) - 1	
	else:
		rentabilidad_12m_bmk = "-"
		rentabilidad_12m_cc = "-"
	'''
	#24M
	if vect_valores_cuota_cc.size > 524:
		rentabilidad_24m_bmk = (vect_benchmark[vect_benchmark.size-1]/vect_benchmark[vect_benchmark.size-524])-1
		rentabilidad_24m_cc=(vect_valores_cuota_cc[vect_valores_cuota_cc.size-1]/vect_valores_cuota_cc[vect_valores_cuota_cc.size-524])-1	
	else:
		rentabilidad_24m_bmk="-"
		rentabilidad_24m_cc="-"
	'''
	#WTD
	if vect_valores_cuota_cc.size > wtd_dias:
		rentabilidad_wtd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - wtd_dias]) - 1
		rentabilidad_wtd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - wtd_dias]) - 1	
	else:
		rentabilidad_wtd_bmk = "-"
		rentabilidad_wtd_cc = "-"
	#MTD
	if vect_valores_cuota_cc.size > mtd_dias:
		rentabilidad_mtd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - mtd_dias]) - 1
		rentabilidad_mtd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - mtd_dias]) - 1	
	else:
		rentabilidad_mtd_bmk = "-"
		rentabilidad_mtd_cc = "-"
	#YTD
	if vect_valores_cuota_cc.size > ytd_dias:
		rentabilidad_ytd_bmk = (vect_benchmark[vect_benchmark.size - 1] / vect_benchmark[vect_benchmark.size - ytd_dias]) - 1
		rentabilidad_ytd_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - 1] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias]) - 1	
	else:
		rentabilidad_ytd_bmk = "-"
		rentabilidad_ytd_cc = "-"
	#QUARTERS SEPARADOS
	#1Q
	if ytd_dias > 65 and vect_valores_cuota_cc.size > ytd_dias - 0:
		rentabilidad_1q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 64] / vect_benchmark[vect_benchmark.size - ytd_dias + 0]) - 1
		rentabilidad_1q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 64] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 0]) - 1
	else:
		rentabilidad_1q_bmk = "-"
		rentabilidad_1q_cc = "-"
	#2Q
	if ytd_dias > 130 and vect_valores_cuota_cc.size > ytd_dias - 64:
		rentabilidad_2q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 129] / vect_benchmark[vect_benchmark.size - ytd_dias + 64]) - 1
		rentabilidad_2q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 129] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 64]) - 1
	else:
		rentabilidad_2q_bmk = "-"
		rentabilidad_2q_cc = "-"
	#3Q
	if ytd_dias > 196 and vect_valores_cuota_cc.size > ytd_dias - 130:
		rentabilidad_3q_bmk = (vect_benchmark[vect_benchmark.size - ytd_dias + 195] / vect_benchmark[vect_benchmark.size - ytd_dias + 129]) - 1
		rentabilidad_3q_cc = (vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 195] / vect_valores_cuota_cc[vect_valores_cuota_cc.size - ytd_dias + 129]) - 1
	else:
		rentabilidad_3q_bmk = "-"
		rentabilidad_3q_cc = "-"

	#Insertamos todas las rentabilidades al vector del fondo y la serie default
	datos_fondo.append(nombre_benchmark)
	datos_fondo.append(codigo_fdo)
	datos_fondo.append(nombre_fdo)
	datos_fondo.append(rentabilidad_1d_cc)
	datos_fondo.append(rentabilidad_1d_bmk)
	datos_fondo.append(rentabilidad_wtd_cc)
	datos_fondo.append(rentabilidad_wtd_bmk)
	datos_fondo.append(rentabilidad_mtd_cc)
	datos_fondo.append(rentabilidad_mtd_bmk)
	datos_fondo.append(rentabilidad_ytd_cc)
	datos_fondo.append(rentabilidad_ytd_bmk)
	datos_fondo.append(rentabilidad_1q_cc)
	datos_fondo.append(rentabilidad_1q_bmk)
	datos_fondo.append(rentabilidad_2q_cc)
	datos_fondo.append(rentabilidad_2q_bmk)
	datos_fondo.append(rentabilidad_3q_cc)
	datos_fondo.append(rentabilidad_3q_bmk)
	datos_fondo.append(rentabilidad_12m_cc)
	datos_fondo.append(rentabilidad_12m_bmk)
	'''
	datos_fondo.append(rentabilidad_24m_cc)
	datos_fondo.append(rentabilidad_24m_bmk)
	'''

	

	return datos_fondo


def compute_returns(wb, dia_inic, dia_fin, wtd_dias,  mtd_dias, ytd_dias, tabla_fondos_series):
	'''
	Imprime en la hoja inputs los datos de las rentabilidades de los fondos
	'''
	fila_fondo = 3
	for fondo in tabla_fondos_series:
		#Por cada fondo calculamos la su informacion de rentabilidad y la insertamos en una fila
		datos_fondo = compute_portfolio_return(dia_inic = dia_inic, dia_fin = dia_fin, wb = wb, wtd_dias = wtd_dias,  mtd_dias = mtd_dias, ytd_dias = ytd_dias, fondo = fondo, fila_fondo = fila_fondo)
		paste_val_xl(wb = wb, sheet = "Inputs", row = fila_fondo, column = 1, value = datos_fondo)
		fila_fondo += 1

def compute_returns_lux(wb, dia_inic, dia_fin, wtd_dias, mtd_dias, ytd_dias, tabla_fondos_series):
	'''
	Imprime en la hoja inputs los datos de las rentabilidades de los fondos de luxemburgo
	'''
	fila_fondo = 3
	for fondo in tabla_fondos_series:
		#Por cada fondo calculamos la su informacion de rentabilidad y la insertamos en una fila
		datos_fondo = compute_portfolio_return_lux(dia_inic = dia_inic, dia_fin = dia_fin, wb = wb, wtd_dias = wtd_dias, mtd_dias = mtd_dias, ytd_dias = ytd_dias, fondo = fondo, fila_fondo = fila_fondo)
		paste_val_xl(wb = wb, sheet = "Inputs", row = fila_fondo, column = 36, value = datos_fondo)
		fila_fondo += 1

def compute_returns_carteras(wb, dia_inic, dia_fin, wtd_dias, mtd_dias, ytd_dias, tabla_fondos_series):
	'''
	Imprime en la hoja inputs los datos de las rentabilidades de las carteras administradas
	'''
	fila_fondo = 3
	for fondo in tabla_fondos_series:
		#Por cada fondo calculamos la su informacion de rentabilidad y la insertamos en una fila
		datos_fondo = compute_portfolio_return_carteras(dia_inic = dia_inic, dia_fin = dia_fin, wb = wb, wtd_dias = wtd_dias, mtd_dias = mtd_dias, ytd_dias = ytd_dias, fondo = fondo, fila_fondo = fila_fondo)
		paste_val_xl(wb = wb, sheet = "Inputs", row = fila_fondo, column = 60, value = datos_fondo)
		fila_fondo += 1


def get_fondos():
    '''
    Retorna una tabla con la informacion de los fondos que van en el reporte
    '''
    query_fondos_series=read_file(".\\querys_return_report\\codigos_fondos_series.sql")
    conn= connect_database_user(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor=query_database(conn, query_fondos_series)
    tabla_fondos_series=get_table_sql(cursor)
    disconnect_database(conn)
    return tabla_fondos_series

def get_fondos_lux():
    '''
    Retorna una tabla con la informacion de los fondos de Luxemburgo que van en el reporte
    '''
    query_fondos_series=read_file(".\\querys_return_report\\codigos_fondos_series_lux.sql")
    conn= connect_database_user(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor=query_database(conn, query_fondos_series)
    tabla_fondos_series=get_table_sql(cursor)
    disconnect_database(conn)
    return tabla_fondos_series

def get_carteras():
    '''
    Retorna una tabla con la informacion de las carteras que van en el reporte
    '''
    query_fondos_series=read_file(".\\querys_return_report\\codigos_carteras.sql")
    conn= connect_database_user(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor=query_database(conn, query_fondos_series)
    tabla_carteras_series=get_table_sql(cursor)
    disconnect_database(conn)
    return tabla_carteras_series


def get_tipos_carteras():
    '''
    Retorna una lista con todos los tipos de carteras
    '''
    query_fondos_series=read_file(".\\querys_return_report\\tipos_carteras.sql")
    conn= connect_database_user(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor=query_database(conn, query_fondos_series)
    lista_carteras=get_list_sql(cursor)
    disconnect_database(conn)
    return lista_carteras



def delete_old_data(wb):
	'''
	Borra del excel todos los datos de input para la reporteria. 
	'''
	clear_table_xl(wb = wb, sheet="Inputs",row=3, column=1)
	clear_table_xl(wb = wb, sheet="Inputs",row=2, column=32)
	clear_table_xl(wb = wb, sheet="Inputs",row=2, column=34)
	clear_table_xl(wb = wb, sheet="Inputs",row=3, column=36)
	clear_table_xl(wb = wb, sheet="Inputs",row=3, column=57)
	clear_table_xl(wb = wb, sheet="Inputs",row=3, column=60)


def get_serie_tac(dia_inic, dia_fin, codigo_fdo, serie): 
    '''
    Retorna la serie del tac entre dos fechas solo de dias habiles y acumula los sabados y domingos
    '''
    query_tacs = read_file(".\\querys_return_report\\tacs.sql").replace("AUTOFUND", codigo_fdo).replace("AUTOSERIE", serie).replace("AUTODATE1", dia_inic).replace("AUTODATE2", dia_fin)
    tacs = get_frame_sql_user(server = "Puyehue", database = "MesaInversiones", username = "usrConsultaComercial", password = "Comercial1w", query = query_tacs)
    for i, tac in tacs.iterrows():
    	if convert_string_to_date(tac["fecha"]).weekday() == 0:
    		tac["tac"] += tacs.iloc[i-2]["tac"]
    		tac["tac"] += tacs.iloc[i-1]["tac"]
    tacs = tacs.set_index(tacs["fecha"]).drop("fecha", 1)
    tacs.index = tacs.index.to_datetime()
    tacs = tacs[tacs.index.weekday <= 4]
    return tacs

def get_serie_cuota_sc(serie_cuota_cc, serie_tac): 
    '''
    Compone la serie del valor cuota sin comision
    '''
    serie_tac = serie_tac + 1
    serie_tac = serie_tac.cumprod()["tac"]
    serie_cuota_sc = [None] * (len(serie_cuota_cc))
    j_vc = len(serie_cuota_cc) - 1
    j_tac = len(serie_tac) - 1
    for i in range(len(serie_cuota_sc) - 1, -1, -1):
    	serie_cuota_sc[i] = float(serie_cuota_cc[j_vc]) * float(serie_tac[j_tac])
    	j_tac -= 1
    	j_vc -= 1
    return np.array(serie_cuota_sc)

#Cerramos posibles archivos Excel
kill_excel()
#Obtenemos las fechas entre las que trabajaremos
dia_inic = "2011-01-31"
dia_fin = "2017-12-31" #para informe en fehca especifica
#dia_spot = get_ndays_from_today(0)
#dia_fin = get_prev_weekday(dia_spot)
dia_fin_carteras = get_prev_weekday(get_prev_weekday(dia_fin))

#Abrimos el workbook en el que trabajaremos y borramos los datos antiguos
wb = open_workbook(path = ".\\ReturnReport.xlsx", screen_updating = True, visible = True)
delete_old_data(wb)
paste_val_xl(wb = wb, sheet = "Inputs", row = 2, column = 32, value = str(dia_fin))
paste_val_xl(wb = wb, sheet = "Inputs", row = 5, column = 32, value = str(dia_fin_carteras))

#Obtenemos la lista con los distintos tipos de cartera y la pegamos en la hoja de inputs
tipos_carteras = get_tipos_carteras()
paste_col_xl(wb = wb, sheet = "Inputs", row = 2, column = 34, serie = tipos_carteras)

#Calculamos la cantidad de dias que han pasado MTD y YTD
wtd_dias = get_current_weekdays_week(convert_string_to_date(dia_fin))
mtd_dias = get_current_weekdays_month(convert_string_to_date(dia_fin))
ytd_dias = get_current_weekdays_year(convert_string_to_date(dia_fin))
wtd_dias_carteras = get_current_weekdays_week(convert_string_to_date(dia_fin_carteras))
mtd_dias_carteras = get_current_weekdays_month(convert_string_to_date(dia_fin_carteras))
ytd_dias_carteras = get_current_weekdays_year(convert_string_to_date(dia_fin_carteras))
print("*******DATA UP TO DATE: " + dia_inic + " TO " + dia_fin + "***********")
print("MTD: " + str(mtd_dias))
print("YTD: " + str(ytd_dias))

#Obtenemos una tabla con los fondos, la serie, el id de su benchmark y su estrategia de inversion
tabla_fondos_series = get_fondos() 

#Calculamos la rentabilidad de cada fondo y benchmark y los insertamos en el workbook
compute_returns(wb = wb, dia_inic = dia_inic, dia_fin = dia_fin, wtd_dias = wtd_dias, mtd_dias = mtd_dias, ytd_dias = ytd_dias, tabla_fondos_series = tabla_fondos_series)

#Obtenemos una tabla con los fondos de Luxemburgo y el id de su benchmark
tabla_fondos_series_lux = get_fondos_lux()

#Calculamos la rentabilidad de cada fondo de luxemburgo y benchmark y los insertamos en el workbook
compute_returns_lux(wb = wb, dia_inic = dia_inic, dia_fin = dia_fin, wtd_dias = wtd_dias, mtd_dias = mtd_dias, ytd_dias = ytd_dias, tabla_fondos_series = tabla_fondos_series_lux)

#Obtenemos una tabla con las carteras administradas, junto con su id de benchmark y su tipo de cartera
tabla_carteras = get_carteras()

#Calculamos la rentabilidad de cada fondo de las carteras y su benchmark y los insertamos en el workbook
compute_returns_carteras(wb = wb, dia_inic = dia_inic, dia_fin = dia_fin_carteras, wtd_dias = wtd_dias_carteras,  mtd_dias = mtd_dias_carteras, ytd_dias = ytd_dias_carteras, tabla_fondos_series = tabla_carteras)

#Imprimimos el reporte
print_report_pdf(wb =wb, tabla_carteras = tabla_carteras, tipos_carteras = tipos_carteras)

#Guardamos y cerramos Excel
save_workbook(wb = wb)
close_excel(wb = wb)

#Enviamos el correo
send_mail_report()
