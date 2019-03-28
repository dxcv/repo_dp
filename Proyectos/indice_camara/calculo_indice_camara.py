import sys
sys.path.insert(0, '../portfolio_analytics/utiles')
sys.path.insert(0, '../libreria')
import libreria_fdo as fs
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import paramiko
import os
import utiles
import time
import numpy as np

def get_tpm_and_icp(date):

	date_ayer = utiles.get_fecha_habil_anterior(date)
	date_ante_ayer = utiles.get_fecha_habil_anterior(date_ayer)

	query_tpm = "Select Fecha, valor from Indices_Dinamica where Index_Id=459 and Fecha>='DATE_1' and Fecha<='DATE_2'"
	query_tpm = query_tpm.replace('DATE_1',str(date_ante_ayer)).replace('DATE_2', str(date_ayer))
	
	df_tpm = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query_tpm)

	query_icp = "Select valor from Indices_Dinamica where Index_Id=4 and Fecha='DATE'"
	query_icp = query_icp.replace('DATE', str(date))
	print(query_icp)
	icp = fs.get_val_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query_icp)

	return df_tpm, icp

def add_tpm_and_icp(date,indice_camara):

	df_tpm, icp = get_tpm_and_icp(date)
	indice_camara.loc[0,'icp_dove'] = icp
	indice_camara.loc[0,'icp_central'] = icp
	indice_camara.loc[0,'icp_hawk'] = icp
	
	indice_camara.loc[0,'dove'] = df_tpm.loc[0,'valor']
	indice_camara.loc[0,'central'] = df_tpm.loc[0,'valor']
	indice_camara.loc[0,'hawk'] = df_tpm.loc[0,'valor']
	
	indice_camara.loc[1,'dove'] = df_tpm.loc[1,'valor']
	indice_camara.loc[1,'central'] = df_tpm.loc[1,'valor']
	indice_camara.loc[1,'hawk'] = df_tpm.loc[1,'valor']


	return indice_camara

def get_index_values(date, indice_camara):


	for i in range(1,indice_camara.index.get_level_values(None).max()+1):
		
		indice_previo_dove = indice_camara.loc[i-1,'icp_dove']
		indice_previo_central = indice_camara.loc[i-1,'icp_central']
		indice_previo_hawk = indice_camara.loc[i-1,'icp_hawk']

		retorno_icp_dove = indice_camara.loc[i,'retorno_icp_dove']
		retorno_icp_central = indice_camara.loc[i,'retorno_icp_central']
		retorno_icp_hawk = indice_camara.loc[i,'retorno_icp_hawk']

		indice_camara.loc[i,'icp_dove'] = round(indice_previo_dove*retorno_icp_dove,2)
		indice_camara.loc[i,'icp_central'] = round(indice_previo_central*retorno_icp_central,2)
		indice_camara.loc[i,'icp_hawk'] = round(indice_previo_hawk*retorno_icp_hawk,2)


	return indice_camara
'''
def get_fechas_habiles(date, index_term):

    #feriados como el de iglesias evangelicas, encuentro de dos mundos, viernes santo y san pedro san pablo cambian año a año asi que no los puse.
    holidays =  [{'D-M': '1-1'},{'D-M': '1-5'},{'D-M': '21-5'},{'D-M': '16-7'},{'D-M': '15-8'},{'D-M': '18-9'},{'D-M': '19-9'},{'D-M': '1-11'},{'D-M': '8-12'},{'D-M': '25-12'}]
    holidays = pd.DataFrame(holidays)
    
    fechas_habiles_short = utiles.get_fechas_habiles()
    

    fecha_inicio = fechas_habiles_short['Fecha'].max() +  datetime.timedelta(days=1)
    
    end_date = pd.Timestamp(datetime.date(date.year + index_term, date.month,date.day))

    fechas_habiles_long = pd.date_range(start= fecha_inicio, end =end_date +  datetime.timedelta(days=10), freq='B')
    fechas_habiles_long = pd.DataFrame(fechas_habiles_long).rename(columns={0:'Fecha'})
    
    
    fechas_habiles_long['M'] = pd.DatetimeIndex(fechas_habiles_long['Fecha']).month
    fechas_habiles_long['D'] = pd.DatetimeIndex(fechas_habiles_long['Fecha']).day
    fechas_habiles_long['D-M']=fechas_habiles_long['D'].astype(str)+'-'+fechas_habiles_long['M'].astype(str)
    
    fechas_habiles_long = fechas_habiles_long[fechas_habiles_long['D-M'].isin(holidays['D-M'])==False].drop(columns=['D','M','D-M'])
    fechas = fechas_habiles_short.append(fechas_habiles_long)

    fechas['anterior']=fechas['Fecha'].shift(1)
    fechas['fecha_settle_t2'] = fechas['Fecha'].shift(-2)
    fechas = fechas[(fechas['Fecha']>=date) & (fechas['Fecha']<=end_date)]

    return fechas
'''

def path_scenario_date_mapping(path_scenario, fechas):


	dates = fechas.index.get_level_values('Fecha').tolist()
	max_date = fechas.index.get_level_values('Fecha').max()
	
	#print(date_range)
	for i, row in path_scenario.iterrows():
		
		fecha_mapping = i
		
		if fecha_mapping < max_date:

			#este while es para las fechas del path que pueden ser no habiles
			while (fecha_mapping not in dates):
				fecha_mapping = fecha_mapping + datetime.timedelta(days=1)
			
			fecha_mapping = pd.Timestamp(fecha_mapping)
			fecha_settle_t2 = fechas.loc[fecha_mapping,'fecha_settle_t2']
			path_scenario.loc[i,'Fecha_efectiva_tpm'] = fecha_settle_t2

	path_scenario.reset_index(drop=True, inplace=True)
	path_scenario = path_scenario.rename(columns={'Fecha_efectiva_tpm':'Fecha'})
	path_scenario = path_scenario.set_index(['Fecha'])

	return path_scenario


def get_icp_values(indice_camara):
	
	for i, row in indice_camara.iterrows():

		if i==0:
			indice_camara.loc[i,'icp'] = 100
		else:
			icp_anterior = indice_camara.loc[i-1,'icp']
			icp = 2

	return path_scenario



def indice_camara(date, index_term=20):

	date = pd.Timestamp(fs.convert_string_to_date(date))

	fechas = utiles.get_fechas_habiles_all(date, index_term)
	

	wb = fs.open_workbook(".\\calculo.xlsx", True, True)
    # Obtenemos los paths de politica monetaria
	path_scenario = fs.get_frame_xl(wb, "path", 1, 1, [0])
	path_scenario = utiles.fs.get_frame_xl(wb, "path", 1, 1, [0])


	fechas= fechas.set_index(['Fecha'])
	path_scenario = path_scenario_date_mapping(path_scenario, fechas)
	
	indice_camara = fechas.merge(path_scenario, how='left', left_index=True, right_index=True)
	
	indice_camara = indice_camara.fillna(method='ffill').reset_index()
	print(indice_camara)
	indice_camara['dias_dif'] = (indice_camara['Fecha'] - indice_camara['anterior']) / np.timedelta64(1, 'D')
	indice_camara = add_tpm_and_icp(date,indice_camara)
	print(indice_camara)
	indice_camara['retorno_icp_dove'] = (1+indice_camara['dove']*indice_camara['dias_dif']/36000)
	indice_camara['retorno_icp_central'] = (1+indice_camara['central']*indice_camara['dias_dif']/36000)
	indice_camara['retorno_icp_hawk'] = (1+indice_camara['hawk']*indice_camara['dias_dif']/36000)

	indice_camara.loc[0,'retorno_icp_dove'] = 0
	indice_camara.loc[0,'retorno_icp_central'] = 0
	indice_camara.loc[0,'retorno_icp_hawk'] = 0

	indice_camara = get_index_values(date, indice_camara)
	indice_camara['indice_dove'] = 100*indice_camara['icp_dove']/indice_camara.loc[0,'icp_dove']
	indice_camara['indice_central'] = 100*indice_camara['icp_central']/indice_camara.loc[0,'icp_central']
	indice_camara['indice_hawk'] = 100*indice_camara['icp_hawk']/indice_camara.loc[0,'icp_hawk']

	
	wb = fs.open_workbook("calculo.xlsx", True, True)

	fs.clear_sheet_xl(wb, "indice")
	fs.paste_val_xl(wb, "indice", 1, 1, indice_camara)

	return indice_camara
	



date = fs.get_ndays_from_today(0)
#date = str(datetime.date(2018,2,1))

indice_camara = indice_camara(date)








