import libreria_fdo as fs
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima_model import ARIMA
import pandas as pd
import numpy as np
from statsmodels.graphics.tsaplots import plot_pacf, plot_acf
from sklearn.metrics import mean_squared_error

def compute_model(currency, duration, p, d=None, q=None):
    '''
    Calcula el modelo arima, mostrandos sus distintos graficos para calibrarlo si d=None chequea si el modelo es o no estacionario, y en base a eso designa
    '''
    data = get_data(currency, duration)
    plot_data(data)
    plot_data(data.diff())
    plot_pac(data)
    plot_ac(data)
    model = arima(data=data, p=p,  d=d, q=q)
    summary, params = get_model_summary(model)
    res=residual(model)
    return model, summary, params, res



def get_data(currency, duration):
    '''
    Obtenemos la informacion de sql
    '''
    #query="select AVG(spread) as spread, Fecha as fecha from Cinta_Valorizacion where duration > 720 and tipo in ('DEB', 'BEF') and Moneda in ('UF', 'NO') group by fecha"
    query = "select AVG(spread) as spread, Fecha as fecha from Cinta_Valorizacion where duration > 720 and duration/360 {} 5 and tipo in ('DEB', 'BEF') and Moneda='{}'  group by fecha".format(duration, currency)
    dataframe = fs.get_frame_sql_user(server="puyehue",
                                      database="MesaInversiones",
                                      username="usuario1",
                                      password="usuario1",
                                      query=query)

    dataframe.set_index(['fecha'], inplace=True)
    dataframe.sort_index(inplace=True)
    return dataframe


def get_data_aux():
    '''
    Obtenemos la informacion de sql
    '''
    query = "select avg(SpreadAvg) as spread, fecha FROM Indices_corporativosrfl where moneda!='US$' group by fecha"
    dataframe = fs.get_frame_sql_user(server="puyehue",
                                      database="MesaInversiones",
                                      username="usuario1",
                                      password="usuario1",
                                      query=query)

    dataframe.set_index(['fecha'], inplace=True)
    dataframe.sort_index(inplace=True)
    return dataframe


def plot_data(data):
    '''
    Grafica los datos disponilbes de los spread
    '''
    data.plot()
    plt.title('Avarage Spread')
    plt.ylabel('Spread')
    plt.xlabel('Dates')
    plt.show()


def plot_pac(data):
    '''
    Grafica las autocorrelaciones del os datos
    '''
    data=data.diff().iloc[1:,:]
    plot_pacf(data, zero=False, lags=60)
    plt.show()

def plot_ac(data):
    '''
    Grafica las autocorrelaciones parciales del os datos
    '''
    data=data.diff().iloc[1:,:]
    plot_acf(data, zero=False, lags=60)
    plt.show()



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
    model = model.fit(disp=0, transparams=False)
    #transparams=False
    return model


def check_stationary(data):
    '''
    Retorna True si es estacionaria , y False en caso contrario
    '''
    data = data['spread'].tolist()
    result = adfuller(data)
    print(result)
    if result[0] < result[4]['5%']:
        return True
    else:
        return False


def get_model_summary(model):
    '''
    Obtenemos los parametros y el resumen del modelo
    '''
    return model.summary(), model.params.tolist()


def residual(model):
    '''
    Obtiene los graficos los errores residuales
    '''
    residual = pd.DataFrame(model.resid)
    residual.plot()
    plt.title('Residual Error Line Plot')
    plt.show()
    residual.plot(kind='kde')
    plt.title('Residual Error Line Plot')
    #plt.show()
    residual=residual.describe()
    print(residual)
    return residual


def compute_forecast(model, days=None):
    '''
    Obtine los siguientes 'days' valores
    '''
    if days is None:
        return model.forecast()
    else:
        return model.forecast(steps=days)[0]

def plot_forecast(data):
    '''
    Plotea los resultados de prediccion de la mitad del tiempo pasado
    '''
    X = data.values
    size = int(len(X) * 0.5)
    train, test = X[0:size], X[size:len(X)]
    history = [x for x in train]
    predictions = list()
    for t in range(len(test)):
        model = ARIMA(history, order=(42,1,42))
        model_fit = model.fit(disp=0, transparams=False)
        output = model_fit.forecast()
        yhat = output[0]
        predictions.append(yhat)
        obs = test[t]
        history.append(obs)
    plt.plot(test)
    plt.plot(predictions, color='red')
    plt.show()
    
'''CALCULAMOS LOS ARIMAS POR TIPO DE BONO'''

def compute_arima_all(p,d,q, params, plot=False):
    '''
    entrega los valores del arima para todos los tipos de bonos, en el caso de plot True grafica la serie de tiempo
    '''
    dic={}
    types=get_types(params)
    for index, row in types.iterrows():
        b_type=row.tolist()
        print(b_type)
        type_name=b_type[0]+'/'+ b_type[1]
        model=compute_arima(b_type, p, d, q, params, plot)
        dic[type_name]=model.params
        print(model.params)
    return dic
        
def compute_arima(b_type, p, d, q, params, plot=False):
    '''
    Entregamos el resumen y los parametros  para el arima sobre el spread promedio para el tipo de bono
    '''
    data=get_spread_sql(b_type, params)
    if plot is True:
        plot_data(data['spread'])
    model=arima(data['spread'], p,d,q)
    return model

def plot_data(data):
    '''
    Grafica los datos disponilbes de los spread
    '''
    data.plot()
    plt.title('Avarage Spread')
    plt.ylabel('Spread')
    plt.xlabel('Dates')
    plt.show()


def get_spread_sql(types, params):
    '''
    Obtiene el frame de los spread promedio para un tipo de bono en especifico
    '''

    query = open('query.txt', 'r').read()
    aux_w=''
    for i in range(len(types)):
        aux_w+="  {}= '{}' and".format(params[i], types[i])
    query = query.replace('[WHERE]', aux_w[:-3])
    df = fs.get_frame_sql_user(server="puyehue",
                               database="MesaInversiones",
                               username="usuario1",
                               password="usuario1",
                               query=query)
    df.set_index(["fecha"], inplace=True)
    df.sort_index(inplace=True)
    df = df[~(df == 0).any(axis=1)]
    return df

def get_types(params):
    '''
    Obtenemos los tipos bonos 
    '''
    aux_g=''
    aux_s=''
    for i in params:
        aux_s+=' ltrim(rtrim({})) as {},'.format(i, i)
        aux_g+=' {} ,'.format(i)
    query = "select  {} from Indices_corporativosrfl where fecha = '2017-06-01' and moneda!='US$' group by  {}".format(aux_s[:-1], aux_g[:-1])
    dataframe = fs.get_frame_sql_user(server="puyehue",
                                      database="MesaInversiones",
                                      username="usuario1",
                                      password="usuario1",
                                      query=query)

    return dataframe



if __name__ == "__main__":

    #vamos como se comportan los datos para deperminar p,d y q
    model, summary, params, res = compute_model('UF', '>=',p=8, d=1, q=3)
    d=compute_forecast(model, days=90)
    print(d)
    #arima para todas las combinaciones de bonos
    params=[ 'Moneda',  'Rating']
    #params=['Tipo', 'Moneda', 'Bucket_Duration', 'Rating']
    #result=compute_arima_all(p, d, q, params, plot=True)
    #print(result)


