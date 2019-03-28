import sys
sys.path.insert(0,'../libreria/')
sys.path.insert(0,'../portfolio_analytics/utiles')
import os
import datetime as dt
import libreria_fdo as fs
import pandas as pd
import utiles
from tia.bbg import v3api
import vencimientos_cupones
import carry

def get_govt_rates(today):
	
	query_est = "SELECT Codigo_ins, Moneda, Benchmark as Duration FROM gobierno_benchmarks"
	bonos = fs.get_frame_sql('Puyehue', 'MesaInversiones', query_est)
	query_din = "SELECT Codigo_ins, Tasa, Tasa_anterior FROM Performance_Nacionales where Codigo_ins in {} and Fecha = '{}'".format(tuple(bonos['Codigo_ins']), today)
	df = fs.get_frame_sql('Puyehue', 'MesaInversiones', query_din)
	df = df.merge(bonos, on='Codigo_ins')
	df['Number'] = df['Duration'].str.rstrip('Y').astype(int)
	df.replace(to_replace=-1000, value=-1, inplace=True)
	df['Delta'] = df['Tasa'] - df['Tasa_anterior']
	df_uf = df[df['Moneda']=='UF']
	df_clp = df[df['Moneda']=='$']
	df_uf = df.groupby(['Duration', 'Moneda']).sum()
	df_uf.sort_values(by='Number', inplace=True)
	df_uf.drop(columns=['Number'], inplace=True)
	df_clp = df.groupby(['Duration', 'Moneda']).sum()
	df_clp.sort_values(by='Number', inplace=True)
	df_clp.drop(columns=['Number'], inplace=True)

	return df_clp, df_uf

def irf(date):
	
	# Venta
	path1 = ".\\Querys\\vende_irf.sql"
	query1 = fs.read_file(path1).replace('AUTODATE', date)
	irf_venta = fs.get_frame_sql('Puyehue', 'MesaInversiones', query1)
	irf_venta['Tipo Operacion'] = 'V'
	# Compra

	path2 = ".\\Querys\\compra_irf.sql"
	query2 = fs.read_file(path2).replace('AUTODATE', date)
	irf_compra = fs.get_frame_sql('Puyehue', 'MesaInversiones', query2)
	irf_compra['Tipo Operacion'] = 'C'
	df_irf = pd.concat([irf_compra, irf_venta], ignore_index=True)
	df_irf = df_irf.groupby(by=['Fecha','Fondo', 'Instrumento', 'Liq', 'Moneda', 'TIR_Operacion', 'TIR_Risk', 'Tipo Operacion']).agg({'Cantidad':'sum'})

	return df_irf

def iif(date, funds_list):
	
	# Venta
	query = "SELECT Fecha, Moneda, Emisor, Dias, Nemotecnico, tasa as tasa_op, Vende as Fondo from TransaccionesIIF where fecha = 'AUTODATE' AND Vende in (" + funds_list + ")"
	query = query.replace("AUTODATE", date)
	df_venta = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)
	df_venta['Tipo Operacion'] = 'V'
	
	# Compra
	query = "SELECT Fecha, Moneda, Emisor, Dias, Nemotecnico, tasa as tasa_op, Compra as Fondo from TransaccionesIIF where fecha = 'AUTODATE' AND Compra in (" + funds_list + ")"
	query = query.replace("AUTODATE", date)
	df_compra = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)
	df_compra['Tipo Operacion'] = 'C'

	df = pd.concat([df_compra, df_venta], ignore_index=True)
	dic_em = utiles.get_dic_em().reset_index()

	df = df.merge(dic_em, on='Emisor')
	df['codigo_emi'] = df['Emisor']


	lista = []
	monda = []
	for i,j in df.iterrows():
		vcto = fs.get_ndays_from_date(-1*int(df.loc[i]['Dias']), df.loc[i]['Fecha'])
		lista.append(vcto)
		if df.loc[i]['Moneda'] == 'CH$' or df.loc[i]['Moneda'] == 'CH4' or df.loc[i]['Moneda'] == 'CLP':
			monda.append('$')
		elif df.loc[i]['Moneda'] == 'UF':
			monda.append('UF')
		else:
			monda.append('US$')
	df['fec_vcto'] = lista
	df['Moneda'] = monda
	df = df[['Fecha', 'Fondo', 'Tipo Operacion', 'Moneda', 'codigo_emi', 'Codigo_SVS', 'Dias','fec_vcto', 'Nemotecnico', 'tasa_op']]
	query1 = "SELECT Codigo_ins as Nemotecnico, Tasa as tasa_risk from Performance_Nacionales where Tipo_ins = 'Deposito' and fecha = '{}'".format(date)
	df_risk = fs.get_frame_sql('Puyehue', 'MesaInversiones', query1)
	df = df.merge(df_risk, on='Nemotecnico')
	# Agrupamos
	df_iif = df.groupby(by=['Fondo', 'codigo_emi', 'Dias', 'Moneda']).sum()

	return df_iif

def export(df_caja, df_carry, df_irf, df_iif, df_govt_clp, df_govt_uf):

	wb = fs.open_workbook("daily_report.xlsx", True, True)
	
	initial_row = 2
	n_caja = df_caja.shape[0] + 2
	n_carry = df_carry.shape[0] + 2
	n_irf = df_irf.shape[0] + 2
	n_iif = df_iif.shape[0] + 2
	n_govt_clp = df_govt_clp.shape[0] + 2
	n_govt_uf = df_govt_uf.shape[0] + 2

	print(n_caja)
	print(n_carry)
	print(n_irf)
	print(n_iif)
	print(n_govt_clp)

	fs.clear_sheet_xl(wb, "summary")
	fs.paste_val_xl(wb, "summary", initial_row, 2, df_caja)
	fs.paste_val_xl(wb, "summary", initial_row , 11, df_carry)
	fs.paste_val_xl(wb, "summary", initial_row + n_caja, 2, df_irf)
	fs.paste_val_xl(wb, "summary", initial_row + n_caja + n_irf, 2, df_iif)
	fs.paste_val_xl(wb, "summary", initial_row + n_caja + n_irf + n_iif, 2, df_govt_clp)
	fs.paste_val_xl(wb, "summary", initial_row + n_caja + n_irf + n_iif , 8, df_govt_clp)


	#fs.save_workbook(wb=wb)
	#fs.close_excel(wb=wb)

print('running daily report ...')
funds_list = utiles.get_FI_funds()
today = fs.get_ndays_from_today(1)
date_anterior = str(utiles.get_fecha_habil_anterior(today))


df_compra_venta = utiles.get_flujo_compras_ventas(date_anterior)
df_vencimientos_cupones = vencimientos_cupones.get_vencimientos_cupones_fondos()
df_caja = df_vencimientos_cupones.join(df_compra_venta, how  = 'outer').fillna(0)
df_carry = carry.get_carry(funds_list, date_anterior)
df_govt_clp, df_govt_uf = get_govt_rates(date_anterior)
df_irf = irf(date_anterior)
df_iif = iif(date_anterior, funds_list)
export(df_caja, df_carry, df_irf, df_iif, df_govt_clp, df_govt_uf)











