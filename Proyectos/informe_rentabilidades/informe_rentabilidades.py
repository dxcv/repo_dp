import sys
sys.path.insert(0, '../libreria/')
sys.path.insert(0, '../portfolio_analytics/utiles')
import libreria_fdo as fs
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import paramiko
import os
import utiles as utiles
import numpy as np

tasa_pacto = 0.0026

def calcula_rentabilidad_diaria(date):

	date_anterior = utiles.get_fecha_habil_anterior(date)

	
	#Saco la info del día de ayer de AUM, Pactos y carteras ya que a la hora que corre este scrip no se tienen los datos spot
	df_funds_currency = utiles.get_funds_currency()
	df_aum = utiles.get_funds_aum(date_anterior)
	df_leverage = utiles.get_leverage(date_anterior)
	df_carteras_fondos = utiles.get_carteras_fondos(date_anterior)

	df_info_fondos = df_funds_currency.join(df_aum, how = 'inner').join(df_leverage, how='left').fillna(0)
	df_info_fondos['Patrimonio'] = df_info_fondos['AUM'] - df_info_fondos['monto_pactado']
	df_info_fondos['Ratio_Leverage'] = df_info_fondos['AUM']/df_info_fondos['Patrimonio']
	# Saco la info de risk
	df_risk_spot, int_data_available_spot = compute_df_risk(date)
	df_risk_anterior, int_data_availabe_anterior = compute_df_risk(date_anterior)
	df_risk_anterior=df_risk_anterior[['precio', 'tasa', 'duration']]

	df_risk = df_risk_spot.join(df_risk_anterior, how='inner', lsuffix='_spot', rsuffix='_anterior')

	#Guardo todos los instrumentos que no entran en el cálculo
	df_rezagados = get_instrumentos_no_considerados(df_carteras_fondos,df_risk)

	df_rentorno_ins = df_carteras_fondos.join(df_risk, how='inner')
	df_rentorno_ins.index.name='codigo_ins'
	df_rentorno_ins.reset_index(inplace=True)
	df_rentorno_ins.set_index('codigo_fdo', inplace=True)

	df_rentorno_ins = df_rentorno_ins.join(df_info_fondos, how='left')
	df_rentorno_ins.reset_index(inplace=True)
	df_rentorno_ins.set_index('codigo_ins',inplace=True)

	df_monedas = utiles.get_currencys(date)
	
	df_rentorno_ins = calcula_rentabilidad_instrumentos(date,df_rentorno_ins, df_monedas)
	df_forwards = calcula_rentabilidad_forwards(date, df_monedas, df_info_fondos)

	df_retorno_fondos = calcula_retorno_total_fondo(df_info_fondos, df_rentorno_ins, df_forwards)

	return df_retorno_fondos,df_rentorno_ins,df_forwards,df_rezagados, df_info_fondos, df_monedas, int_data_available_spot



def calcula_retorno_total_fondo(df_info_fondos, df_rentorno_ins, df_forwards):
	
	df_devengo_pactos = (df_info_fondos[['Ratio_Leverage']].round(3)-1)*tasa_pacto
	df_moneda_fondos = df_info_fondos[['moneda_fondo']]
	df_retorno_fondos = df_rentorno_ins.groupby(['codigo_fdo']).agg({'CTR_Ins':'sum'})
	df_retorno_fondos = df_retorno_fondos.join(df_forwards[['CTR_Forwards']], how='left')
	df_retorno_fondos = df_retorno_fondos.join(df_devengo_pactos, how='left')
	df_retorno_fondos = df_retorno_fondos.join(df_moneda_fondos, how='left')
	df_retorno_fondos = df_retorno_fondos.fillna(0)
	df_retorno_fondos.rename(columns={'CTR_Ins':'Instrumentos', 'CTR_Forwards':'Forwards', 'Ratio_Leverage':'Pactos'}, inplace=True)

	df_retorno_fondos['Retorno_Fondo'] = df_retorno_fondos['Instrumentos'] + df_retorno_fondos['Forwards'] + df_retorno_fondos['Pactos']

	df_retorno_fondos = df_retorno_fondos[['moneda_fondo','Retorno_Fondo','Instrumentos', 'Forwards','Pactos']]
	
	df_retorno_fondos = df_retorno_fondos.reset_index()

	df_retorno_fondos = df_retorno_fondos.set_index(['codigo_fdo','moneda_fondo'])
	df_retorno_fondos = df_retorno_fondos*10000

	return df_retorno_fondos


def get_instrumentos_no_considerados(df_carteras_fondos,df_risk):

	rezagados =  df_carteras_fondos.join(df_risk, how='left')
	rezagados = rezagados.loc[rezagados['precio_spot'].isnull() | rezagados['precio_anterior'].isnull()]
	rezagados = rezagados.reset_index()
	return rezagados


def calcula_rentabilidad_instrumentos(date,df_rentorno_ins, df_monedas):

	date_anterior = utiles.get_fecha_habil_anterior(date)
	delta_dias_valorizacion = (date - date_anterior).days


	df_rentorno_ins = join_cartera_monedas(df_rentorno_ins,df_monedas)
	df_rentorno_ins = utiles.get_devengo_tasa(df_rentorno_ins)


	#El weight verdadero de la cartera es corregido por leverage
	df_rentorno_ins['weight_adj'] = df_rentorno_ins['weight']*df_rentorno_ins['Ratio_Leverage']
	df_rentorno_ins['dur_mod'] = df_rentorno_ins['duration_anterior']/(1+df_rentorno_ins['tasa_anterior']/100)
	df_rentorno_ins['r_aprox'] =  -df_rentorno_ins['dur_mod']*(df_rentorno_ins['tasa_spot']-df_rentorno_ins['tasa_anterior'])/100
	df_rentorno_ins['r_1D'] = df_rentorno_ins['precio_spot']/df_rentorno_ins['precio_anterior']-1


	#condiciones para que la rentabilidad no cague cuando haya pago de cupones.
	conditions = [(df_rentorno_ins["tipo_SVC"]=='Nacional') & (df_rentorno_ins['r_1D']<-0.01),
				  (df_rentorno_ins["tipo_SVC"]=='Nacional') & (df_rentorno_ins['r_1D']>=-0.01) & (df_rentorno_ins["Moneda"].isin(['$','UF'])),
				  (df_rentorno_ins["tipo_SVC"]=='Nacional') & (df_rentorno_ins['r_1D']>=-0.01) & (df_rentorno_ins["Moneda"].isin(['$','UF'])==False),
				  (df_rentorno_ins["tipo_SVC"]=='Internacional')]
	
	retorno=[df_rentorno_ins["r_aprox"]+df_rentorno_ins["devengo"]+df_rentorno_ins['r_moneda'],
			df_rentorno_ins["r_1D"]-(delta_dias_valorizacion-1)*(df_rentorno_ins["devengo"]+df_rentorno_ins['r_moneda']),
			df_rentorno_ins["r_1D"]-(delta_dias_valorizacion-1)*(df_rentorno_ins["devengo"]),
			df_rentorno_ins["r_1D"]+df_rentorno_ins['r_moneda']]
	
	df_rentorno_ins['r_ins']=np.select(conditions,retorno,default=df_rentorno_ins['r_1D'])
	df_rentorno_ins['CTR_Ins'] = df_rentorno_ins['weight_adj']*df_rentorno_ins['r_ins']


	return df_rentorno_ins

def calcula_rentabilidad_forwards(date, df_monedas, df_info_fondos):

	
	df_forwards = utiles.get_posiciones_forwards(date)
	df_monedas = df_monedas.set_index(['currency','paridad'])
	df_forwards = df_forwards.join(df_monedas, how='left', on=['moneda_compra','moneda_venta'])
	df_forwards = df_forwards.join(df_info_fondos, how='left')
	df_forwards = utiles.get_forwards_weights(date, df_forwards)
	df_forwards['CTR_Forwards'] = df_forwards['weight_adj'] * df_forwards['r_moneda']
	
	return df_forwards


def join_cartera_monedas(df_rentorno_ins,df_monedas):
	
	df_rentorno_ins.reset_index(inplace=True)
	df_monedas = df_monedas.set_index(['currency','paridad'])
	
	df_rentorno_ins = df_rentorno_ins.join(df_monedas, how='left', on=['Moneda','moneda_fondo'])
	#df_carteras_fondos = pd.merge(df_carteras_fondos, df_monedas, how='inner', left_on=['Moneda','moneda_fondo'], right_on=['currency','paridad'])

	return df_rentorno_ins


def compute_df_risk(date):
    
    df_nat, nat_data_available = utiles.download_national_data(date)
    df_int, int_data_available = utiles.download_international_data(date)
    dic_isin_codigoIns = utiles.get_mapping_instrumentos_internacionales()

    if df_int is not None:
    	df_int = utiles.change_index(dic_isin_codigoIns, df_int)
    df_risk = df_nat.append(df_int)
    df_risk.index.name='codigo_ins'

    return df_risk, int_data_available

def color_negative_red(val):
   
    color = 'red' if val < 0 else 'black'
    return 'color: %s' % color


def send_mail(date, df_retorno_fondos, int_data_available, filename):

    
    df_retorno_fondos = (df_retorno_fondos).round(1)
    print(df_retorno_fondos)

    subject=""
    if int_data_available:
    	subject = "Estimación rentabilidad {}".format(date)
    else:
    	subject = "[Preview] Estimación rentabilidad {}".format(date)

    df_styled = df_retorno_fondos.style\
    .applymap(color_negative_red)\
    .set_caption('Estimación rentabilidad '+str(date) + "  [bps]")\
    .set_properties(**{'text-align': 'center'})\
    .bar(subset='Retorno_Fondo', color='#d65f5f')

    # Render the styled df in html
    body = df_styled.render()
    mails =  ['dposch@credicorpcapital.com'] 

		    
    #mails = ["fsuarez@credicorpcapital.com", "jparaujo@credicorpcapital.com",
    #	"dposch@credicorpcapital.com", "rbarros@credicorpcapital.com",
    #	"adarquea@credicorpcapital.com","pvaldivieso@credicorpcapital.com"] 


    
    path = fs.get_self_path()
    datefile = str(date).replace('-','')+".xlsx"
    old_path = path+filename
    new_path = path+datefile
    os.rename(old_path, new_path)

    attachment_paths = [new_path]
    fs.send_mail_attach(subject, body, mails, attachment_paths, html=True)
    os.rename(new_path, old_path)
    print('mail enviado')

def genera_excel(df_retorno_fondos,df_rentorno_ins,df_forwards,df_rezagados, df_risk, df_monedas):

	df_rentorno_ins = df_rentorno_ins.set_index('codigo_fdo')

	conditions = [df_rentorno_ins["tipo_SVC"]=='Nacional',df_rentorno_ins["tipo_SVC"]=='Internacional']
	values_spot=[df_rentorno_ins["tasa_spot"],df_rentorno_ins["precio_spot"]]
	values_anterior=[df_rentorno_ins["tasa_anterior"],df_rentorno_ins["precio_anterior"]]
	
	df_rentorno_ins['tasa/precio_spot']=np.select(conditions,values_spot,default=None)
	df_rentorno_ins['tasa/precio_anterior']=np.select(conditions,values_anterior,default=None)
	
	df_rentorno_ins = df_rentorno_ins.loc[:,['codigo_ins', 'tipo_SVC','tipo_instrumento','Moneda', 'weight_adj', 'dur_mod','tasa/precio_spot', 'tasa/precio_anterior', 'CTR_Ins', 'r_ins', 'devengo', 'r_moneda']]
	df_forwards = df_forwards[['moneda_compra','moneda_venta','parity','r_moneda','monto_compra', 'monto_venta', 'weight_adj', 'CTR_Forwards']]
	df_rezagados = df_rezagados[['codigo_fdo','codigo_ins','tipo_instrumento','Moneda','weight']]
	df_rezagados.set_index('codigo_fdo',inplace=True)

	df_monedas = df_monedas.set_index(['currency','paridad'])

	wb = fs.open_workbook("output.xlsx", True, True)
	fs.clear_sheet_xl(wb, "fondos")
	fs.clear_sheet_xl(wb, "instrumentos")
	fs.clear_sheet_xl(wb, "forwards")
	fs.clear_sheet_xl(wb, "rezagados")
	fs.clear_sheet_xl(wb, "info_fondos")
	fs.clear_sheet_xl(wb, "paridades")
	fs.paste_val_xl(wb, "fondos", 1, 1, df_retorno_fondos)
	fs.paste_val_xl(wb, "instrumentos", 1, 1, df_rentorno_ins)
	fs.paste_val_xl(wb, "forwards", 1, 1, df_forwards)
	fs.paste_val_xl(wb, "rezagados", 1, 1, df_rezagados)
	fs.paste_val_xl(wb, "info_fondos", 1, 1, df_risk)
	fs.paste_val_xl(wb, "paridades", 1, 1, df_monedas)

	wb.save()
	wb.close()



date = datetime.date(2019,01,9)
print(str(date)+'\ncomputing performance')
df_retorno_fondos,df_rentorno_ins,df_forwards,df_rezagados, df_risk, df_monedas, int_data_available = calcula_rentabilidad_diaria(date)
genera_excel(df_retorno_fondos,df_rentorno_ins,df_forwards,df_rezagados, df_risk ,df_monedas)
send_mail(date,df_retorno_fondos, int_data_available,"output.xlsx")

