"""
Created on Tue Mon 23 11:00:00 2017

@author: Fernando Suarez & Francisca Martinez
"""

import sys
sys.path.insert(0, "../../../libreria/")
import libreria_fdo as fs

# Para desabilitar warnings
import warnings
warnings.filterwarnings("ignore") 



import libreria_fdo as fs
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima_model import ARIMA
import pandas as pd
import numpy as np
from statsmodels.graphics.tsaplots import plot_pacf, plot_acf
from sklearn.metrics import mean_squared_error
import datetime as dt


def compute_df_spread(days, params, clp_mkt, clf_mkt, clp_exp, clf_exp, swap_clp, swap_clf, df_inflacion):
    '''
    Genera el dataframe con los spreads y distintos campos
    '''
    date = fs.convert_string_to_date(fs.get_prev_weekday(((fs.get_ndays_from_today(4)))))
    print("spreads date: "+str(date))
    #date = fs.convert_string_to_date(fs.get_prev_weekday(((fs.get_ndays_from_today(2)))))
    # obtenemos los spred mkt promedio por Bucket y la diferencia del esperado
    df = get_spread(date, params)
    
    df = compute_spread_exp(days, df)
    df, df_diff_spread = compute_diff_spread_types(df, date)
    # obtenemos las yield de mercado, los esperados y sus direfencias pára
    # cada escenario
    df = compute_yld_col(df, clp_mkt['yield'], clf_mkt['yield'], 'yld_mkt')
    df = compute_yld_exp(df, clp_exp, clf_exp, swap_clp, swap_clf)
    # obtenemos el carri y los retornos esperados
    df = compute_carry(days, df, df_inflacion)
    df = compute_g(days, df)
    df = compute_r(df)
    df=df[['tipo','moneda', 'Bucket_Duration', 'rating', 'carry', 'g_expected', 'r_expected']]
    df["Bucket_Duration"] = df["Bucket_Duration"].astype(str)

    return df, df_diff_spread


def get_spread(date, params):
    '''
    Obtiene los spread por tipo de instrumento
    '''
    aux_g = ''
    aux_s = ''
    for i in params:
        aux_s += ' ltrim(rtrim({})) as {},'.format(i, i)
        aux_g += ' {} ,'.format(i)
    query = "select  {}, avg(SpreadAvg) as avg_spread ,avg(DurationAvg) as duration   from Indices_corporativosrfl where fecha = '{}' and moneda!='US$' group by  {}".format(
        aux_s[:-1], date, aux_g[:-1])
    
    dataframe = fs.get_frame_sql_user(server="puyehue",
                                      database="MesaInversiones",
                                      username="usuario1",
                                      password="usuario1",
                                      query=query)
    dataframe['avg_spread']=dataframe['avg_spread']/100
    return dataframe

def compute_spread_exp(days, df):
    '''
    Del arima genera el spread esperado para n dias
    '''
    forescast_uf_mayor = compute_model(days, 'UF', '>=', p=6, d=1, q=3)
    forescast_clp_mayor = compute_model(days, 'NO', '>=', p=6, d=1, q=3)
    forescast_uf_menor = compute_model(days, 'UF', '<', p=6, d=1, q=3)
    forescast_clp_menor = compute_model(days, 'NO', '<', p=6, d=1, q=3)
    list_forescast = []
    for index, row in df.iterrows():
        if row['moneda'] == '$'and row['duration']>=5:
            list_forescast.append(forescast_clp_mayor/100)
        elif row['moneda'] == '$'and row['duration']<5:
            list_forescast.append(forescast_clp_menor/100)
        elif row['moneda'] == 'UF'and row['duration']>=5:
            list_forescast.append(forescast_uf_mayor/100)
        else:
            list_forescast.append(forescast_uf_menor/100)
    df['spread_exp'] = pd.Series(list_forescast, index=df.index)
    return df

def compute_diff_spread_types(df, date):
    '''
    generamos las diff spread segun tipo
    '''
    avg_spread_uf_mayor = get_avg_spread(date, 'UF', '>=')
    avg_spread_uf_menor = get_avg_spread(date, 'UF', '<')
    avg_spread_clp_mayor = get_avg_spread(date, 'NO', '>=')
    avg_spread_clp_menor = get_avg_spread(date, 'NO', '<')
    df, df_diff_spread = compute_diff_spread(df, avg_spread_uf_mayor, avg_spread_uf_menor, avg_spread_clp_mayor, avg_spread_clp_menor)
    return df, df_diff_spread


def get_avg_spread(date, currency, duration):
    '''
    Obtiene elo spread promedio para una fecha
    '''
    query = "select AVG(spread) as avg_spread from Cinta_Valorizacion where  Fecha = '{}' and duration > 720 and duration/365 {} 5 and tipo in ('DEB', 'BEF') and Moneda= '{}'".format(date, duration, currency)
    dataframe = fs.get_frame_sql_user(server="puyehue",
                                      database="MesaInversiones",
                                      username="usuario1",
                                      password="usuario1",
                                      query=query)


    return (dataframe.loc[0]['avg_spread'])/100



def compute_diff_spread(df, avg_spread_uf_mayor, avg_spread_uf_menor, avg_spread_clp_mayor, avg_spread_clp_menor):
    '''
    Entrega la diferencia de los spreads
    '''
    list_diff = []
    clp=0
    uf=0
    clp_mayor=0
    
    for index, row in df.iterrows():
        if row['moneda'] == '$' and row['duration']>=5:
            clp_mayor=row['spread_exp']-avg_spread_clp_mayor
            list_diff.append(clp_mayor)
        elif row['moneda'] == '$' and row['duration']<5:
            clp_menor=row['spread_exp']-avg_spread_clp_menor
            list_diff.append(clp_menor)
        elif row['moneda'] == 'UF' and row['duration']>=5:
            uf_mayor=row['spread_exp']-avg_spread_clp_mayor
            list_diff.append(uf_mayor)
        else:
            uf_menor=row['spread_exp']-avg_spread_uf_menor
            list_diff.append(uf_menor)            
    df['diff_spread'] = pd.Series(list_diff, index=df.index)
    df_diff_spread=pd.DataFrame()
    df_diff_spread['diff spread'] = pd.Series([clp_mayor, clp_menor, uf_mayor, uf_menor], index=['CLP =>5años', 'CLP <5años ', 'UF =>5años', 'UF <5años'])
    return df, df_diff_spread

def compute_yld_col(df, clp, clf, name):
    '''
    Crea las columna con los yield 
    '''
    list_yld = []
    for index, row in df.iterrows():
        duration = row['duration']
        if row['moneda'] == '$':
            yld_mkt = get_serie(clp, duration)
        else:
            yld_mkt = get_serie(clf, duration)
        list_yld.append(yld_mkt)
    df[name] = pd.Series(list_yld, index=df.index)
    return df

def compute_yld_exp(df, clp_exp, clf_exp, swap_clp, swap_clf):
    '''
    agregamos las columnas de los yield_exp para los distintos escenarios
    '''
    clp_exp = add_exp_colum(clp_exp, ['swap_cl'], [swap_clp])
    clf_exp = add_exp_colum(clf_exp, ['swap_cl'], [swap_clf])
    for col in clp_exp.columns:
        df = compute_yld_col(df, clp_exp[col], clf_exp[col], 'yld_exp_'+col)
        df = compute_diff_yld(df, col)
    return df

def compute_diff_yld(df, exp):
    '''
    Entrega las diferencias enstre los yield de mercado y esperado
    '''
    df['diff_yld_' + exp] = df['yld_exp_'+exp]-df['yld_mkt']
    return df



def compute_carry(days, df, df_inflacion):
    '''
    Calcula el carry de un tipo dado para n dias
    '''
    df['avg_spread * t'] = df['avg_spread']*(days/365)
    df['mkt_yield * t'] = df['yld_mkt']*(days/365)
    serie_inflacion=compute_inflacion(days, df, df_inflacion)
    df['inflacion'] = serie_inflacion
    df['carry'] = ((df['avg_spread']+df['yld_mkt'])*(days/365))+df['inflacion']
    return df


def compute_inflacion(days, df, df_inflacion):
    '''
    Entrefa la inflacion entre hoy y n dias mas
    '''
    date = df_inflacion.index.tolist()[0]
    uf_actual=df_inflacion[date]
    uf_nuevo=df_inflacion[date+dt.timedelta(days=days)]
    inflacion= (uf_nuevo / uf_actual) - 1
    list_diff = []
    for index, row in df.iterrows():
        if row['moneda'] == '$':
            list_diff.append(0)  
        else:
            list_diff.append(inflacion)            
    serie_inflacion = pd.Series(list_diff, index=df.index)
    return serie_inflacion



def compute_g(days, df):
    '''
    Calcuamos el ... para n dias
    '''
    df['diff_spread* d'] = df['diff_spread']*df['duration']*-1
    for col in df.columns:
        if col.startswith('diff_yld_'):
            df['g_'+col[9:]] = (df['diff_spread'] + df[col])*df['duration']*-1
            df['diff_'+col[9:]+'* d'] = df[col]*df['duration']*-1
    return df


def compute_r(df):
    '''
    Calculamos la suma de los retornos esperados
    '''
    for col in df.columns:
        if col.startswith('diff_yld_'):
            df['r_'+col[9:]] = (df['g_'+col[9:]] + df['carry'])
    return df


def add_exp_colum(df, list_names, list_new):
    '''
    añadimos las nuevas columas a al dataframe de expected
    '''
    for i in range(len(list_names)):
        df[list_names[i]] = pd.Series(list_new[i], index=df.index)
    return df


def set_index(df):
    '''
    Vuelve a setear los indices con los tenor a una serie
    '''
    df['new'] = pd.Series([i for i in range(len(df.index))], index=df.index)
    df = df.set_index(['new'], inplace=True)
    return df


def get_serie(serie, duration):
    '''
    Obtiene un valor de una serie
    '''
    tenor = int(round(duration*365, 0)-1)
    value = serie.get(tenor)
    return value


def get_inputs(name_input, name_inflacion):
    '''
    Obtenemos inputs para trabajar
    '''
    wb = fs.open_workbook(".\\{}".format(name_input), False, False)
    clp_mkt = fs.get_frame_xl(wb, "clp_mkt", 1, 1, [0])
    clf_mkt = fs.get_frame_xl(wb, "clf_mkt", 1, 1, [0])
    clp_exp = fs.get_frame_xl(wb, "clp_exp", 1, 1, [0])
    clf_exp = fs.get_frame_xl(wb, "clf_exp", 1, 1, [0])
    swap_clp = fs.get_frame_xl(wb, "swap_clp", 1, 1, [0])
    swap_clp = swap_clp['swap_clp']
    swap_clf = fs.get_frame_xl(wb, "swap_clf", 1, 1, [0])
    swap_clf = swap_clf['swap_clf']
    wb = fs.open_workbook(".\\{}".format(name_inflacion), False, False)
    df_inflacion = fs.get_frame_xl(wb, "Hoja1", 1, 1, [0])
    return clp_mkt, clf_mkt, clp_exp, clf_exp, swap_clp, swap_clf, df_inflacion


'''ARIMA'''


def compute_model(days, currency, duration,  p, d=None, q=None):
    '''
    Calcula el modelo arima, mostrandos sus distintos graficos para calibrarlo si d=None chequea si el modelo es o no estacionario, y en base a eso designa
    '''
    data = get_data(currency, duration)
    model = arima(data=data, p=p,  d=d, q=q)
    forescast = compute_forecast(model, days)
    return forescast[-1]


def get_data(currency, duration):
    '''
    Obtenemos la informacion de sql
    '''
    query = "select AVG(spread) as spread, Fecha as fecha from Cinta_Valorizacion where duration > 720 and duration/365 {} 5 and tipo in ('DEB', 'BEF') and Moneda='{}'  group by fecha".format(duration, currency)
    dataframe = fs.get_frame_sql_user(server="puyehue",
                                      database="MesaInversiones",
                                      username="usuario1",
                                      password="usuario1",
                                      query=query)
    dataframe.set_index(['fecha'], inplace=True)
    dataframe.sort_index(inplace=True)
    return dataframe


def arima(data, p, d=None, q=None):
    '''
    Generamos irma sobre los datos
    '''
    X = data.values
    if d is None:
        stationary = check_stationary(data)
        d = 1
        if stationary is True:
            d = 0
    if q is None:
        q = 0
    order = (p, d, q)
    model = ARIMA(X, order)
    model = model.fit(disp=0,  transparams=False)
    return model


def compute_forecast(model, days=None):
    '''
    Obtine los dichuientes 'days' valores
    '''
    if days is None:
        return model.forecast()
    else:
        return model.forecast(steps=days)[0]


def plot_data(data):
    '''
    Grafica los datos disponilbes de los spread
    '''
    data.plot()
    plt.title('Avarage Spread')
    plt.ylabel('Spread')
    plt.xlabel('Dates')
    plt.show()



