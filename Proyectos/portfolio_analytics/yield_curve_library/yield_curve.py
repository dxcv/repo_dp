"""
Created on Thu Mon 26 11:00:00 2017

@author: Fernando Suarez & Natan Goldberg

"""

import sys
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import leastsq
import seaborn as sns

def nelson_siegel_curve(tenors, date, currency):
	'''
	Dada lista de tenors, modela la curva y obtiene las tasas en los distintos tenors para una fecha indicada.
	'''
	date_start = date
	date_end = date
	curve_points = get_historical_dataset(date_start = date_start, date_end = date_end, currency = currency)
	#2.243807474743995, 0.00022939934798843674
	tau = 0.11
	tau2 = 0.11
	parameters = get_parameters(curve_points = curve_points, tau = tau, tau2 = tau2)
	yields = compute_yields(tenors = tenors, parameters = parameters)
	return yields, parameters


def get_historical_dataset(date_start, date_end, currency):
	'''
	Obtiene la curva historica entre dos fechas desde la base de datos.
	'''
	if currency == "clp":
		query_dataset = fs.read_file(path = "..\\yield_curve_library\\querys_yield_curve\\historical_curves_clp.sql").replace("AUTODATE1", date_start).replace("AUTODATE2", date_end)
	elif currency == "clf":
		query_dataset = fs.read_file(path = "..\\yield_curve_library\\querys_yield_curve\\historical_curves_clf.sql").replace("AUTODATE1", date_start).replace("AUTODATE2", date_end)
	dataset = fs.get_frame_sql_user(server = "Puyehue", database = "MesaInversiones", username = "usrConsultaComercial", password = "Comercial1w", query = query_dataset)
	dataset = dataset.set_index(dataset["fecha"]).drop("fecha", 1)
	return dataset


def compute_yields(tenors, parameters):
	'''
	Calcula la curva utilziando nelson siegel, dados los parametros y los tenors. Retorna una lista con las yields dados los tenors pedidos.
	'''
	b0, b1, b2, b3 = parameters[1:5]
	tau = float(parameters[0])
	tau2 = float(parameters[5])
	yc = b0 * level_exposure(tenors, tau) + b1 * slope_exposure(tenors, tau) + b2 * curvature_exposure(tenors, tau) + b3 * svensson_exposure(tenors, tau2)
	return yc


def level_exposure(tenors, tau):
	'''
	Computa la exposicion o factor loading a nivel.
	'''
	return 1


def slope_exposure(tenors, tau):
	'''
	Computa la exposicion o factor loading a pendiente.
	'''
	return ((1 - np.exp(-tenors / tau)) / (tenors/tau))


def curvature_exposure(tenors, tau):
	'''
	Computa la exposicion o factor loading a curvatura.
	'''
	return (((1 - np.exp(-tenors / tau)) / (tenors/tau) - np.exp(-tenors / tau)))


def svensson_exposure(tenors, tau):
	'''
	Computa la exposicion o factor loading al factor de svensson.
	'''
	return (((1 - np.exp(-tenors / tau)) / (tenors/tau) - np.exp(-tenors / tau)))


def get_parameters(curve_points, tau, tau2):
	'''
	Dados los parametros.
	'''
	tenors = curve_points.columns.astype(float)
	yields = curve_points.values.astype(float)[0]
	#x0 = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
	x0 = np.array([0.1, 0.1, 0.1, 0.1]) 
	x0 = leastsq(nelson_siegel_residuals, x0, args = (tenors, yields, tau, tau2))
	#x0 = leastsq(nelson_siegel_residuals, x0, args = (tenors, yields))
	return [tau] + x0[0].tolist() + [tau2]
	#return x0[0].tolist()


def nelson_siegel_residuals(p, tenors, yields,tau ,tau2):
	'''
	Calcula el error entre las tasas computadas sobre los parametros calculados y los empiricos.
	'''
	b0, b1, b2, b3 = p
	curve_yields = compute_yields(tenors, [tau, b0, b1, b2, b3, tau2])
	err = yields - curve_yields
	err = err.astype(float)
	return err


def plot_curves(curves_parameters):
    '''
    En base a un arreglo de parametros, grafica las curvas.
    '''
    sns.set_style("darkgrid")   
    plt.title("Yield Curve", fontsize=20)
    tenors = []
    days = 0
    for x in range(1, 7200):
        days += (1/360)
        tenors.append(days) 
    tenors = np.array(tenors)
    for parameters in curves_parameters:
        yields = compute_yields(tenors=tenors, parameters=parameters) * 100
        print(yields[359])
        print(yields[719])
        print(yields[-1])
        plt.plot(tenors, yields, linestyle='-', color=np.random.rand(3,))
    plt.xlabel('$tenor$')
    plt.ylabel('$yield$')
    plt.show()

