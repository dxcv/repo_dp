import sys
sys.path.insert(0, '../uploader_riskamerica')
sys.path.insert(0, '../portfolio_analytics/utiles')
sys.path.insert(0, '../libreria')
import pandas as pd
import libreria_fdo as fs
import utiles

today = fs.get_ndays_from_today(1)
print(today)

def irf(today):
	# Venta
	path1 = ".\\Querys\\vende_irf.sql"
	query1 = fs.read_file(path1).replace('AUTODATE', today)
	irf_venta = fs.get_frame_sql('Puyehue', 'MesaInversiones', query1)
	irf_venta['Tipo Operacion'] = 'V'
	# Compra
	path2 = ".\\Querys\\compra_irf.sql"
	query2 = fs.read_file(path2).replace('AUTODATE', today)
	irf_compra = fs.get_frame_sql('Puyehue', 'MesaInversiones', query2)
	irf_compra['Tipo Operacion'] = 'C'
	df_irf = pd.concat([irf_compra, irf_venta], ignore_index=True)
		
	return df_irf

def iif(today):
	# Venta
	query = "SELECT Fecha, Moneda, Emisor, Dias, Nemotecnico, tasa as tasa_op, Vende as Fondo from TransaccionesIIF where fecha = '{}' AND Vende in ('DEUDA 360','DEUDA CORP','IMT E-PLUS','ARGENTIN','MACRO 1.5','MACRO CLP3','RENTA','SPREADCORP')".format(today)
	df_venta = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)
	df_venta['Tipo Operacion'] = 'V'
		# Compra
	query = "SELECT Fecha, Moneda, Emisor, Dias, Nemotecnico, tasa as tasa_op, Compra as Fondo from TransaccionesIIF where fecha = '{}' AND Compra in ('DEUDA 360','DEUDA CORP','IMT E-PLUS','ARGENTIN','MACRO 1.5','MACRO CLP3','RENTA','SPREADCORP')".format(today)
	df_compra = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)
	df_compra['Tipo Operacion'] = 'C'

	df = pd.concat([df_compra, df_venta], ignore_index=True)
	dic_em = utiles.get_dic_em()
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
	query1 = "SELECT Codigo_ins as Nemotecnico, Tasa as tasa_risk from Performance_Nacionales where Tipo_ins = 'Deposito' and fecha = '{}'".format(today)
	df_risk = fs.get_frame_sql('Puyehue', 'MesaInversiones', query1)
	df = df.merge(df_risk, on='Nemotecnico')
	# Agrupamos
	df_iif = df.groupby(by=['Fondo', 'codigo_emi', 'Dias', 'Moneda']).sum()

	return df_iif
	
		

	
