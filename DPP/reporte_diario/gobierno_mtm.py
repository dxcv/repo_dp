import pandas as pd
import numpy as np
import libreria_fdo as fs


def get_govt_rates(today):
	query_est = "SELECT Codigo_ins, Moneda, Benchmark as Duration FROM gobierno_benchmarks"
	bonos = fs.get_frame_sql('Puyehue', 'MesaInversiones', query_est)
	query_din = "SELECT Codigo_ins, Tasa, Tasa_anterior FROM Performance_Nacionales where Codigo_ins in {} and Fecha = '{}'".format(tuple(bonos['Codigo_ins']), today)
	df = fs.get_frame_sql('Puyehue', 'MesaInversiones', query_din)
	df = df.merge(bonos, on='Codigo_ins')
	df['Number'] = df['Duration'].str.rstrip('Y').astype(int)
	df.replace(to_replace=-1000, value=-1, inplace=True)
	df['Delta'] = df['Tasa'] - df['Tasa_anterior']
	df = df.groupby(['Duration', 'Moneda']).sum()
	df.sort_values(by='Number', inplace=True)
	df.drop(columns=['Number'], inplace=True)
	

