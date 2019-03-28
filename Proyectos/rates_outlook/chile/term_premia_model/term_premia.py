"""
Created on Mon Jan 08 11:00:00 2017

@author: Fernando Suarez & Francisca Martinez
"""

import itertools
import libreria_fdo as fs
import statsmodels.api as sm
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def compute_term_premia_model(term_premia_dataset):
    '''
    Calcula el modelo de term premia en base a regresores
    '''
    # ponemos los inputs para toda las veces
    dic = {'TPM': {datetime.datetime(2014, 6, 1): 0.0425},'Fechas': [5, 10, 20]}
    trainning = False

    # inputs solo necesarion si no seva a corrar el trainning       
    dic_tp = {'Min': {10: 0.0035617206566562823, 20: 0.006614283456341359, 5: 0.0003573373471135871},
                'Last': {10: 0.013786646799787354, 20: 0.01455316913100263, 5: 0.010381629263063089},
                'Avg': {10: 0.008051824838726102, 20: 0.01018199245042781, 5: 0.004856335096156647},
                'Max': {10: 0.01671856896501829, 20: 0.01711913587372834, 5: 0.013540389726700922}}
    betas = [[0.007626830632716096, -0.00042026812505820306, 5.6110411616008506e-05, 1.7563138107367926],
            [0.012414733664592304, -2.201013110212986e-05, -0.0004055770079703545, 5.038465856972826e-05, 2.282568948679651],
            [0.013603938192614065, -1.701636398627878e-05, -0.00031895105237597816, 3.8257326274883355e-05, 1.7961296632286214]]
    combinacion =[('USDCLPV1M BGN Curncy', 'RIAMPDU7_Stdev', 'Breakeven_Stdev'),
                    ('CCHIL1U5 CBIN Curncy', 'USDCLPV1M BGN Curncy', 'RIAMPDU7_Stdev', 'Breakeven_Stdev'),
                    ('CCHIL1U5 CBIN Curncy', 'USDCLPV1M BGN Curncy', 'RIAMPDU7_Stdev', 'Breakeven_Stdev')]
    #corremos el programa
    if trainning is True:
        dic_tp, dataframe_y = tp.compute_tpremium(dic)
        combinacion, betas, tvalues, r2 = tp.compute_trainning(dic, dataframe_x, dataframe_y)
        print(combinacion)
        print(betas)
        print(tvalues)
        print(r2)

    dataframe_tp = compute_new_tp(betas,
                                  combinacion,
                                  term_premia_dataset,
                                  dic_tp,
                                  dic)
    return dataframe_tp


def compute_trainning(dic, dataframe_x, dataframe_y):
    '''
    Genera los parametros a usar en los modelos 
    '''
    factores = dataframe_x.columns.tolist()
    combinaciones = []
    list_betas = []
    list_tvalues = []
    list_r2 = []
    for i in dic['Fechas']:
        combinacion, betas, tvalues, r2= get_best_model(
            dataframe_y, i, dataframe_x, factores)
        combinaciones.append(combinacion)
        list_betas.append(betas)
        list_tvalues.append(tvalues)
        list_r2.append(r2)
    return combinaciones, list_betas, list_tvalues, list_r2


def get_best_model(dataframe_y, plazo, dataframe_x=None, factores=None):
    '''
    Nos entrega el mejor modelo segun el criterio BIC
    '''
    combinations_list = compute_combinations(factores)
    best_model = None
    for combination in combinations_list:
        new_model = compute_ols(dataframe_x, dataframe_y, combination, plazo)
        if best_model is None:
            best_model = new_model
            best_combination = combination
        best_model, best_combination = get_best_bic(best_model, new_model, best_combination, combination)
    return best_combination, best_model.params.tolist(), best_model.tvalues.tolist(),  best_model.rsquared


def compute_combinations(params):
    '''
    Genera todas las combinaciones de factores posibles
    '''
    combinations_list = []
    for i in range(len(params)):
        combinacion = itertools.combinations(params, i+1)
        combinations_list += list(combinacion)
    return combinations_list


def compute_ols(input_x, input_y, factores, plazo):
    '''
    Generamos la regresion de los breakeven, se obtiene los valores de los parametros
    '''
    x, y = compute_ols_input(input_x, input_y, factores, plazo)
    x = sm.add_constant(x)
    model = sm.OLS(y, x).fit()
    return model


def compute_ols_input(input_x, input_y, factores, plazo):
    '''
    Generamos los vectores x e y para la regresion
    '''
    if len(input_x.index) > len(input_y.index):
        date_list = input_x.index.tolist()
        lista_aux = input_y.index.tolist()
    else:
        date_list = input_y.index.tolist()
        lista_aux = input_x.index.tolist()
    x = []
    y = []
    for date in date_list:
        if date in lista_aux:
            y.append(input_y.loc[date][plazo])
            aux = []
            for i in factores:
                if len(factores) is not 1:
                    aux.append(input_x.loc[date][i])
                else:
                    aux = input_x.loc[date][i]
            x.append(aux)
    return x, y


def get_best_bic(model_1, model_2, combinacion1, combinacion2):
    '''
    Elegimos el mejor modelo segun BIC
    '''
    if model_1.bic > model_2.bic:
        return model_2, combinacion2
    else:
        return model_1, combinacion1


def compute_new_tp(lista_betas, combinaciones, dataframe_x, dic_inicial, dic):
    '''
    Obtenemos nuevo term premium con lo regresionado
    '''
    #today = datetime.date.today()
    today = dataframe_x.index.tolist()[0]
    lista_tp = []
    for betas in range(len(lista_betas)):
        tp = lista_betas[betas][0]
        for i in range(len(combinaciones[betas])):
            tp += (lista_betas[betas][i+1]*dataframe_x.loc[today][combinaciones[betas][i]])
        lista_tp.append(tp)
    dataframe= compute_new_dataframe(dic_inicial, lista_tp, dic)
    return dataframe


def compute_new_dataframe(dic_inicial, lista_tp, dic):
    '''
    Genera el dataframe con la nueva informacion
    '''
    dataframe= pd.DataFrame(dic_inicial)
    index = dic['Fechas']
    dataframe['Model'] = pd.Series(lista_tp, index=index)
    return dataframe


def dataframe_to_excel(dataframe, name):
    '''
    Se generan un excel con el dataframe 
    '''
    writer = pd.ExcelWriter(name)
    dataframe.to_excel(writer, 'Sheet1', False)
    writer.save()

'''SE OBTIENEN SE CALCULAN LOS TP  '''

def compute_tpremium(dic):
    '''
    Genera un dataframe con los term premium: el max, min, promedio y actual
    '''
    date_list = get_dates()
    lista_final, lista_total = compute_tp_list(
        date_list, dic['TPM'], dic['Fechas'])
    dataframe = compute_dataframe(lista_final, dic['Fechas'])
    lista_total = add_index(dic['Fechas'], lista_total)
    dataframe_full = compute_dataframe(lista_total, date_list)
    return dataframe.to_dict(), dataframe_full
10

def get_dates():
    '''
    Obtiene la lista de las fechas disponibles de la base de datos 
    '''
    query = "SELECT  DISTINCT date from ZHIS_RA_Curves WHERE Curve_Name='Gob CERO Pesos' and date>='2014-07-01' ORDER BY Date DESC"
    dataframe = fs.get_frame_sql_user(server="puyehue",
                                      database="MesaInversiones",
                                      username="usuario1",
                                      password="usuario1",
                                      query=query)

    return dataframe['date'].tolist()


def compute_tp_list(date_list, dic_tpm, lista_puntos):
    '''
    Genera una lista con las listas de los tp
    '''
    lista = []
    for date in range(len(date_list)):
        tpm = get_last_tpm(dic_tpm, date_list[date])
        dataframe_tasas = get_dataframe_yield(
            date_list[date].to_pydatetime(), lista_puntos)
        for i in range(len(lista_puntos)):
            if date is 0:
                lista.append([dataframe_tasas.loc[dataframe_tasas['tenor'] == (
                    360*lista_puntos[i]), 'forward_rate'].tolist()[0]-tpm])
            else:
                lista[i].append(dataframe_tasas.loc[dataframe_tasas['tenor'] == (
                    360*lista_puntos[i]), 'forward_rate'].tolist()[0]-tpm)
    nueva_lista = []
    for i in range(len(lista)):
        lista_aux = get_summary(lista[i])
        nueva_lista.append(lista_aux)
    lista_final = sort_list(nueva_lista)
    return lista_final, lista


def get_last_tpm(dic, date):
    '''
    Buscamos la ultima tpm vigente
    '''
    if date in dic:
        tpm = dic[date]
    else:
        list_dic = sorted(dic.keys(), reverse=True)
        for i in list_dic:
            if i < date:
                tpm = dic[i]
                break
    return tpm


def get_dataframe_yield(date, lista_puntos):
    '''
    Obtiene el dataframe de las tasas de la curva cero para una fecha dada
    '''
    query = "select  tenor, yield, date from ZHIS_RA_Curves WHERE Curve_Name='Gob CERO Pesos' and Date = '{}-{}-{}'".format(
        date.year, date.month, date.day)
    dataframe = fs.get_frame_sql_user(server="puyehue",
                                      database="MesaInversiones",
                                      username="usuario1",
                                      password="usuario1",
                                      query=query)
    dataframe["yield"] = dataframe["yield"] / 100
    dataframe = compute_zero_implied_tpm(dataframe)
    return dataframe


def get_summary(tp_list):
    '''
    Obtiene los maximos, minimos, promedios y valores actuales de las tp para una fecha
    '''
    return[max(tp_list), min(tp_list), sum(tp_list)/len(tp_list), tp_list[29]]


def sort_list(lista):
    '''
    Ordena la informacion recien obtenida
    '''
    lista_final = []
    names = ['Max', 'Min', 'Avg',
             'Last']
    for i in range(len(names)):
        lista_aux = [names[i]]
        for sub_lista in lista:
            lista_aux.append(sub_lista[i])
        lista_final.append(lista_aux)
    return lista_final


def compute_dataframe(columns, index):
    '''
    Genera el DataFrame a partir de la informacion en lista
    '''
    dic_matriz = {}
    for i in columns:
        dic_matriz[i[0]] = pd.Series(i[1:], index=index)
    dataframe = pd.DataFrame(dic_matriz)
    return dataframe


def add_index(rangos, lista_total):
    '''
    Le agrega los indices a las columnas segun los rangos dados
    '''
    new_list = []
    for i in range(len(lista_total)):
        new_list.append([rangos[i]]+lista_total[i])
    return new_list


def plot_curves(dataframe):
    '''
    Crear un grafico a partir de un dataframe
    '''
    tenors = dataframe.index.tolist()
    for curve in dataframe:
        plt.plot(tenors, dataframe[curve].tolist(),
                 linestyle='-', color=np.random.rand(3, ))
    plt.xlabel('$x$')
    plt.ylabel('$y$')
    plt.show()


def compute_zero_implied_tpm(market_zero_curve):
    '''
    Construye el display para el monitor
    '''
    # Armamos las columnas desfasadas de yield
    market_zero_curve.rename(columns={"yield": "yield_t2"}, inplace=True)
    market_zero_curve["yield_t1"] = market_zero_curve["yield_t2"].shift(1)
    market_zero_curve["yield_t1"] = market_zero_curve[
        "yield_t1"].fillna(method="bfill")

    # Calculamos la forward instantanea
    market_zero_curve["forward_rate"] = (((1.0+market_zero_curve["yield_t2"])**(market_zero_curve.index)) / (
        (1.0+market_zero_curve["yield_t1"])**(market_zero_curve.index - 1))) - 1.0
    market_zero_curve = market_zero_curve.replace(np.inf, np.nan)
    market_zero_curve = market_zero_curve.fillna(method="ffill")

    # Calculamos moving averagep ara el error
    market_zero_curve["forward_rate_discrete"] = market_zero_curve[
        "forward_rate"]
    market_zero_curve["forward_rate"] = market_zero_curve[
        "forward_rate"].rolling(window=15).mean()
    market_zero_curve["forward_rate"] = market_zero_curve[
        "forward_rate"].fillna(market_zero_curve["forward_rate_discrete"])
    market_zero_curve = market_zero_curve.drop("forward_rate_discrete", 1)
    # Obtenemos la tpm iplicita
    market_zero_curve["implied_tpm"] = market_zero_curve[
        "forward_rate"].apply(lambda x: fs.custom_round(x, base=0.0025))
    market_zero_curve["tenor_date"] = fs.convert_string_to_date(
        fs.get_ndays_from_today(0))
    market_zero_curve["tenor_date"] = pd.to_datetime(
        market_zero_curve["tenor_date"]) + pd.to_timedelta(market_zero_curve.index, unit="D")
    market_zero_curve.set_index(["tenor_date"], inplace=True)
    market_zero_curve.rename(columns={"yield_t1": "zero_curve"}, inplace=True)
    return market_zero_curve