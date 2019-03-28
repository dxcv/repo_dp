
import sys
import numpy as np
import xlwings as xw
import libreria_fdo as fs
import datetime as date
import dateutil.relativedelta as rd


def get_buckets_soberanos(cartera_govt):

	conditions = [
	(cartera_govt["duration"]<1.5),
	(cartera_govt["duration"]<3),
	(cartera_govt["duration"]<5),
	(cartera_govt["duration"]<9),
	(cartera_govt["duration"]<15.5) & (cartera_govt["moneda"]=='UF'),
	(cartera_govt["duration"]<12.5) & (cartera_govt["moneda"]=='CLP')]
		
	
	buckets=[1,3,5,10,20,20]

	cartera_govt["bucket"]=np.select(conditions,buckets,default=30)

	return cartera_govt



def update_carteraAFP_govt(cartera_date):

	filename = str(cartera_date.year) + str('{:02}'.format(cartera_date.month)) + str('{:02}'.format(cartera_date.day))
	print (filename)
	wb = fs.open_workbook(".\\"+filename+".xlsx", True, True)
	array_columns = ["clase_activo","tipo_RA", "tipo_instrumento","moneda","emisor","nemo"]
	fs.paste_val_xl(wb, "Sheet0", 1, 1, array_columns)
	cartera_govt = fs.get_frame_xl(wb, "Sheet0", 1, 1, [5])
	
	cartera_govt = cartera_govt[["tipo_instrumento","moneda","% Fondo","% Familia Activo","Duración"]]
	cartera_govt.rename(columns={'Duración':'duration'}, inplace=True)
	types=["BCP","BTP","BCU","BTU"]
	cartera_govt=cartera_govt.loc[cartera_govt["tipo_instrumento"].isin(types)]

	cartera_govt = get_buckets_soberanos(cartera_govt)
	cartera_govt["date"]=cartera_date
	cartera_govt=cartera_govt.reset_index()
	cartera_govt.set_index(['date'], inplace=True)
	tuples=cartera_govt.to_records().tolist() 
	print(cartera_govt)
	upload_data(tuples)
	
	return cartera_govt

def Consolidate_AFP_info(cartera_govt):

	Consolidate_AFP_info=cartera_govt.groupby(["moneda","bucket"])["% Familia Activo"].agg(['sum'])
	return Consolidate_AFP_info

def upload_data(tuplas):
    '''
    Sube los indices de los ultimos 10 dias a la base de datos.
    '''
    print("Uploading historical data...")
    conn = fs.connect_database_user(server="Puyehue",
                                 database="MesaInversiones",
                                 username="usrConsultaComercial",
                                 password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO Cartera_Gob_AFP_E (Fecha, Nemo, Tipo, Moneda, Weight_fondo, Weight_RF_Nacional, duration, Year_bucket) VALUES (%s,%s,%s,%s,%d,%d,%d,%d)", tuplas)
    conn.commit()
    fs.disconnect_database(conn)



cartera_date = (date.date.today() + rd.relativedelta(months=-1)).replace(day=1)
#cartera_date = date.date(2017,11,1)
cartera_govt = update_carteraAFP_govt(cartera_date)






