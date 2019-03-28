"""
Created on Thu Apr 03 11:00:00 2018

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import datetime as dt
import numpy as np
import math
import matplotlib.pyplot as plt
import seaborn as sns


def plot_histogram(sorted_serie):
    '''
    '''
    varg = np.percentile(sorted_serie, 5)
    print(varg)
    cvar = 0.0
    i = 0
    for data in sorted_serie:
        cvar += data
        if data >= varg:
            break
        i += 1
    cvar = cvar / i
    print(cvar)

    plt.hist(sorted_serie, normed=True, color='brown', bins=100)
    plt.xlabel('Returns')
    plt.ylabel('Frequency')
    plt.title(r'Histogram of Asset Returns', fontsize=18, fontweight='bold')
    plt.axvline(x=varg, color='r', linestyle='--', label='95% Confidence VaR: ' + "{0:.2f}%".format(varg))
    plt.axvline(x=cvar, color='g', linestyle='--', label='95% Confidence CVaR: ' + "{0:.2f}%".format(cvar))
    plt.legend(loc='upper right', fontsize = 'x-small')
    plt.show()      



def fetch_dataset(ids, start_date, end_date):
    '''
    '''
    
    query = "select fecha, valor as [{}] from indices_dinamica where fecha >= '{}' and fecha <= '{}' and index_id = {} order by fecha asc"
    for index_id in ids:
        query_index = query.format(index_id, start_date, end_date, index_id)
        serie = fs.get_frame_sql_user(server="Puyehue",
                                      database="MesaInversiones",
                                      username="usrConsultaComercial",
                                      password="Comercial1w",
                                      query=query_index)
        serie.set_index(["fecha"], inplace=True)
        if index_id == ids[0]:
            dataset = pd.DataFrame(index=serie.index)
        dataset[index_id] = serie
    dataset = dataset.pct_change()
    dataset = dataset.dropna()

    return dataset


def get_ewma_cov_matrix(data, landa=1):
    '''
    Funcion para calcular la matriz de varianza-covarianza con proceso EWMA. Recibe un dataframe
    en que cada columna es una serie de retornos. Es importante que las series no tengan NaN.
    '''
    # Sacamos el promedio de cada serie y normalizamos los datos
    avg = data.mean(axis=0)
    data_mwb = data - avg
    # Sacamos el vector de landas dandole mas peso a los primeros elementos(datos mas nuevos)
    powers = np.arange(len(data_mwb))
    landavect = np.empty(len(data_mwb))
    landavect.fill(landa)
    landavect = np.power(landavect, powers)
    # Multiplicamos el vector por la matriz de datos normalizada, el vector landa tambien se normaliza con la raiz
    landavectSQRT = np.sqrt(landavect)
    data_tilde = data_mwb.T
    data_tilde = data_tilde * landavectSQRT
    data_tilde = data_tilde.T
    # Multiplicamos la suma de todos los landas con la multiplicacion de la matriz compuesta con ella misma
    sumlanda = np.sum(landavect)
    cov_ewma = (1/(sumlanda-1)) * (data_tilde.T.dot(data_tilde))

    # Para obtener la covarianza/varianza de dos/un indices
    # print(cov_ewma[73].loc[168])
    # para obtener la matriz descorrelacionada
    # cov_ewma = pd.DataFrame(np.diag(np.diag(cov_ewma)),index = cov_ewma.index, columns = cov_ewma.columns)
    
    return cov_ewma

def get_portfolio_metrics(w, matrix):
    '''
    '''
    print(matrix)
    w_marginal = matrix.dot(w)
    print(w_marginal)
    sigma = np.sqrt(w.T.dot(w_marginal))["w"][0]
    print(sigma*math.sqrt(360))

    

spot_date = fs.get_ndays_from_today(0)
end_date = fs.convert_string_to_date(fs.get_prev_weekday(spot_date))
start_date =  fs.convert_string_to_date("2016-01-01")
ids = [153, 620, 624] # IIF, RACL, ARS
w = [0.9, 0.0, 0.10]#[0.7, 0.12, 0.18]
r_lebac = 0.27
r_lebac = ((1+r_lebac)**(1/255)) -1

dataset = fetch_dataset(ids, start_date, end_date)
#w = pd.DataFrame(w, index=dataset.columns, columns=["w"])
#matrix = get_ewma_cov_matrix(dataset, landa=0.94)
#get_portfolio_metrics(w, matrix)

dataset.columns = ["IIF", "Gov", "Arg"]

dataset.loc[pd.Timestamp("2016-01-01")] = [0, 0, 0]
dataset.sort_index(inplace=True)
dataset["Arg"] = (1+dataset["Arg"])*(1+r_lebac) -1 
dataset = dataset + 1
dataset = dataset.cumprod()
dataset = dataset.pct_change(30)
dataset = dataset.dropna()
dataset["portfolio"] = w[0]*dataset["IIF"] + w[1]*dataset["Gov"] + w[2]*dataset["Arg"]



#print(dataset)

serie = dataset["portfolio"].sort_values()*100

plot_histogram(serie)
#print(dataset)
# fs.plot_series([dataset["portfolio"]])#, dataset["Arg"], dataset["Gov"], dataset["IIF"]])
