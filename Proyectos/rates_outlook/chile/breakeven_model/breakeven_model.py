"""
Created on Fri Dec 22 11:00:00 2017

@author: Fernando Suarez & Francisca Martinez
"""

import sys
sys.path.insert(0, "../../../libreria/")
import libreria_fdo as fs
import collections
# Para desabilitar warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=FutureWarning)
import datetime
import pandas as pd
import datetime
import numpy as np
from sklearn.linear_model import ElasticNet 
import statsmodels.api as sm
from workalendar.america import Chile



def compute_breakeven_model(breakeven_params, clf_spot_dataset_training, clf_fwd_dataset_training, clf_spot_dataset_forecast, clf_fwd_dataset_forecast, model_tenor):
    '''
    Calcula el modelo de breakeven dei nflacion
    - en fecha actual deberia ir la fecha de hoy
    - si el ultimo rando es mayor a 16 tira error
    - si ElasticNet_alpha es O --> Regression lineal
    - si ElasticNet_li_lasso es 1 --> Lasso
    - si ElasticNet_li_lasso es 0 --> Ridge
    - si betas son 0 --> disminuir ElasticNer_alpha (0.000001)
    '''
    #previous_betas_2y = [0.012307383045647808, 0.5042655254294204, 0.4905152380079181, 0.3143653351653262]
    previous_betas_2y = [0.015104327627037803, 0.07359549991756871, 0.6868546566827871, 0.00200408502915919]
    #previous_betas_5y = [0.019835814861141304, 0.19346821223278252, 0.2607094360930141, 0.20392963009223886]
    previous_betas_5y = [0.02267762695746316, 0.027859157371334167, 0.31036295600212427, 0.00014258720970678103]

    trainning = breakeven_params.loc["trainning"]["data"]
    if trainning is True:
        matriz_precio, matriz_fecha, matriz_swap = crear_inputs(clf_spot_dataset_training, clf_fwd_dataset_training)
        betas, testt, r2 = entrenar_modelo(matriz_fecha=matriz_fecha,
                                              matriz_precio=matriz_precio,
                                              matriz_swap=matriz_swap,
                                              dic=breakeven_params,
                                              plazo_swap=model_tenor)
        # print(betas)
        # print(testt)
        # print(r2)
    else:
        if model_tenor == 2:
            betas = previous_betas_2y
        elif model_tenor ==5:
            betas = previous_betas_5y
    breakeven_model = crear_output(breakeven_params, betas, clf_spot_dataset_forecast, clf_fwd_dataset_forecast, model_tenor)

    return breakeven_model

def crear_inputs(uf_matriz, matriz):
    '''
    Genera los inputs del programa
    '''
    matriz_precio = generar_matriz_precio(uf_matriz, matriz)
    matriz_fecha = generar_matriz_fechas(matriz)
    matriz_swap = generar_matriz_swap_cupon(matriz)

    print(matriz_swap)
    print(matriz_fecha)
    print(matriz_precio)
    exit()
    return matriz_precio, matriz_fecha, matriz_swap

def generar_matriz_swap_cupon(matriz):
    '''
    Genera una matriz con los swaps cupon
    '''
    matriz = matriz.loc[:, ['CHSWP2 Curncy', 'CHSWP5 Curncy', 'CHSWC2 Curncy', 'CHSWC5 Curncy']]
    return matriz


'''FUNCIONES PARA CREAR LA MATRIZ DE LOS PRECIOS'''


def generar_matriz_precio(uf_matriz, matriz):
    '''
    Crea una matriz con los valores de la UF
    '''
    nombre_filas = matriz.index.tolist()
    tasas = agregar_columnas_existentes(matriz)
    lista_uf_normal = uf_matriz.loc[:, "CHUF Index"].tolist()[:len(nombre_filas)]
    tasas["UF_real"] = pd.Series(lista_uf_normal, index=matriz.index.tolist())
    listaUf = generar_columna_uf(nombre_filas, uf_matriz)
    tasas["CHUF Index"] = pd.Series(listaUf, index=nombre_filas[:len(listaUf)])
    tasas = reordenar_columnas(tasas)
    tasas = revisar_filas_incompletas(nombre_filas, tasas)
    return tasas


def generar_columna_uf(nombre_filas, uf_matriz):
    '''
    Genera una columna con los ultimos valores de las UF conocidos para cada fecha
    '''
    # print('uf_matriz')
    # print(uf_matriz)
    aux_listaUF = []
    # print('nombre_filas')
    # print(nombre_filas)
    for fecha in nombre_filas:
        try:
            if type(fecha) is not datetime.datetime:
                fecha = fecha.to_pydatetime().date()
            f_venc = obtener_fecha_uf(fecha)
            #print(f_venc)
            aux_actual = uf_matriz.loc[f_venc, "CHUF Index"]
            aux_listaUF.append(aux_actual)
        except:
            pass
    #print('aux_lista_uf')
    #print(aux_listaUF)
    return aux_listaUF


def agregar_columnas_existentes(matriz):
    '''
    Agrega las columnas existentes a un DataFrame
    '''
    dic_matriz = {}
    counter = 1
    for i in range(24):
        columna='CFNP{} BDCH Curncy'.format(i+1) #bdch
        dic_matriz[counter] = pd.Series(matriz.loc[:, columna].tolist(), index=matriz.index.tolist())
        counter += 1
    dic = collections.OrderedDict(sorted(dic_matriz.items()))
    tasas = pd.DataFrame(dic)
    return tasas


def revisar_filas_incompletas(nombre_filas, tasas):
    '''
    Se revisan las filas con problemas, y se eliminan
    '''
    # print("nombre_filas")
    # print(nombre_filas)
    # print(tasas)
    
    aux = pd.isna(tasas['CHUF Index'])
    for fecha in nombre_filas:
        print(fecha)
        if aux.loc[fecha] is np.True_:
            tasas = tasas.drop(fecha)
    return tasas


'''FUNCIONES PARA CREAR LA MATRIZ DE LAS FECHAS'''


def generar_matriz_fechas(matriz):
    '''
    Genera una matriz para el input con las fechas de vencimiento forwards
    '''
    nombre_filas = matriz.index.tolist()
    listaUf = generar_columna_fecha_uf(nombre_filas)
    tasas = agregar_columas(matriz)
    tasas["CHUF Index"] = pd.Series( listaUf, index=nombre_filas)
    tasas = reordenar_columnas(tasas)
    return tasas


def generar_columna_fecha_uf(nombre_filas):
    '''
    Obtiene las fechas de las ultimas UF conocidas para cada fecha (el 9 siguiente)
    '''
    aux_lista_fechas = []
    for fecha in nombre_filas:
        if type(fecha) is not datetime.datetime:
            fecha = fecha.to_pydatetime().date()
        f_venc = obtener_fecha_uf(fecha)
        aux_lista_fechas.append(f_venc)
    return aux_lista_fechas


def obtener_siguiente_fecha(columna_uf, mes):
    '''
    Obtiene la fecha de vencimiento de los forwards siguientes
    '''
    aux_lista_fecha = []
    for fecha in columna_uf:
        if fecha.month + mes > 24:
            nueva_fecha = datetime.datetime(fecha.year + 2, fecha.month + mes - 24, 9)
        elif fecha.month + mes > 12:
            nueva_fecha = datetime.datetime(fecha.year + 1, fecha.month + mes - 12, 9)
        else:
            nueva_fecha = datetime.datetime(fecha.year, fecha.month + mes, 9)
        nueva_fecha = encontrar_dia_habil(nueva_fecha)
        aux_lista_fecha.append(nueva_fecha)
    return aux_lista_fecha


def agregar_columas(matriz):
    '''
    Agregar las columnas de las fechas a un DataFrame
    '''
    dic_matriz = {}
    for columna in range(24):
        dic_matriz[columna + 1] = pd.Series(obtener_siguiente_fecha(matriz.index.tolist(), columna + 1),
                                            index=matriz.index.tolist())
    dic = collections.OrderedDict(sorted(dic_matriz.items()))
    tasas = pd.DataFrame(dic)
    return tasas


'''FUNCIONES AUXILIARES'''


def encontrar_dia_habil(date):
    '''
    Encontramos el dia habil anterior más cercano a una fecha dada
    '''
    dia_feriado = check_holyday(date)
    dia_findesemana = chequear_findesemana(date)
    while dia_feriado is True and dia_findesemana is True:
        date -= datetime.timedelta(days=1)
        dia_feriado = check_holyday(date)
        dia_findesemana = chequear_findesemana(date)
    return date


def obtener_fecha_uf(date):
    '''
    Fecha de la ultima UF conocida (el próximo 9)
     '''
    if date.day != 9:
        if date.day > 9:
            if date.month == 12:
                date = datetime.datetime(date.year + 1, 1, 9)
            else:
                date = datetime.datetime(date.year, date.month + 1, 9)
        else:
            date = datetime.datetime(date.year, date.month, 9)

    #date = encontrar_dia_habil(date)
    return date


def chequear_findesemana(date):
    '''
    Chequea si una fecha es fin de semana
    '''
    if date.weekday() == 5 or date.weekday() == 6:
        return True
    else:
        return False


def check_holyday(date):
    '''
    Chequeamos si una fecha es feriado en CHILE
    '''
    cal = Chile()
    if cal.is_working_day(date) is False:
        return True
    else:
        return False


def reordenar_columnas(tasas):
    '''
    Pasa la ultima columna (UF) al comienzo
    '''
    cols = tasas.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    tasas = tasas[cols]
    return tasas


def crear_ecxel(matriz, nombre):
    '''
     A partir de un DataFrame se escribe el esxcel correspondiente
    '''
    try:
        writer = pd.ExcelWriter(nombre, engine='xlsxwriter')
        matriz.to_excel(writer, sheet_name='Sheet1')
        writer.save()
    except PermissionError:
        print("ERROR: Se tiene que cerrar el archivo excel utilizado")
'''CREANMOS LOS OUTPUTS DEL PROGRAMA'''


def crear_output(dic, betas, uf_matriz, matriz, plazo_swap):
    '''
    Se generan los outputs del programa
    '''
    #print(dic)
    
    # print(uf_matriz)
    # print(matriz)
    # print(plazo_swap)
    fecha_actual = dic.loc['fecha actual']['data']
    print("fecha actual " +str(fecha_actual))
    intervalo = dic.loc['delta tiempo']['data']
    rangos = dic.loc['rangos']['data'].split(',')
    dummy = dic.loc['Dummy']['data']
    lista_fechas, lista_inflacion = calcuar_lista_inflacion(fecha_actual, intervalo, betas, rangos, dummy, uf_matriz, matriz)

    lista_breakeven = obtener_lista_breakeven(fecha_actual, lista_fechas, plazo_swap)

    matriz = crear_dataframe(nombre_fechas=lista_fechas,
                             columnas=[['Regresion'] + lista_inflacion, ['Breakeven'] + lista_breakeven])
    return matriz



def crear_dataframe(nombre_fechas, columnas):
    '''
    Genera el DataFrame con el output
    '''
    dic_matriz = {}
    for i in range(len(columnas)):
        dic_matriz[columnas[i][0]] = pd.Series(
            columnas[i][1:], index=nombre_fechas[:len(columnas[i][1:])])
    matriz = pd.DataFrame(dic_matriz)
    return matriz


'''FUNCIONES PARA CREAR LA CURVA DE LOS DATOS DE LA REGRESION'''


def calcuar_lista_inflacion(fecha_actual, intervalo, lista_parametros, rangos, dummy, uf_matriz, matriz):
    '''
    Se crea la lista con los breakevens y las fechas respectivas a partir de los betas calculados
    '''

    matriz_precio, matriz_fecha = generar_matrices_input(fecha_actual, uf_matriz, matriz)
    
    fecha_partida = fecha_actual
    #print(fecha_partida)
    lista_breakeven = []
    lista_fechas = []
    dif_dias = calcular_dias_sobrantes(rangos)
    while dif_dias > 0:
        lista_inflacion = generar_serie_inflaciones(fecha_partida, rangos, matriz_fecha, matriz_precio, dummy, fecha_actual)
        breakeven = funcion_breakeven(lista_parametros, lista_inflacion)
        lista_breakeven.append(breakeven)
        lista_fechas.append(fecha_partida)
        fecha_partida += datetime.timedelta(days=intervalo)
        dif_dias -= intervalo
    return lista_fechas, lista_breakeven


def calcular_dias_sobrantes(rangos):
    '''
    Calculas la cantidad de dias de holgura que se tienen para proyectar el breakeven
    '''
    ultimo=int(rangos[-1])
    dias = (24 - ultimo) * 30
    return dias


def funcion_breakeven(lista_parametros, lista_inflaciones):
    '''
    Entrega el valor un  breakeven, dado sus betas y sus inlfaciones explicativas
    '''
    breakeven = lista_parametros[0]
    for i in range(len(lista_parametros) - 1):
        breakeven += lista_parametros[i + 1] * lista_inflaciones[i]
    return breakeven


'''FUNCIONES PARA CREAR LA CURVA DE LOS DATOS DE LOS SWAP'''


def obtener_lista_breakeven(fecha_actual, lista_fechas, plazo_swap):
    '''
    Entrega la lista de breakeven  de los swaps´
    '''
    plazo_swap *= 365
    data_uf, data_clp = generar_data()
    lista_breakeven = []
    for fecha in lista_fechas:
        largo_dias = len(fs.get_dates_between(fecha_actual, fecha))
        breakeven = calcular_breakeven(fecha_actual, largo_dias, plazo_swap, data_uf, data_clp)
        lista_breakeven.append(breakeven)
    return lista_breakeven


def calcular_breakeven(fecha, plazo_1, plazo_swap, data_uf, data_clp):
    '''
    Calcula el breakeven para una fecha dada
    '''
    f_uf = calcular_fxy(fecha, plazo_1, plazo_swap, data_uf)
    f_clp = calcular_fxy(fecha, plazo_1, plazo_swap, data_clp)
    breakeven = ((1 + f_clp) / (1 + f_uf)) - 1
    return breakeven


def calcular_fxy(fecha, plazo_1, plazo_swap, data):
    '''
    Calcula la tasa forward entre dos fechas
    '''
    tasa_1 = obtener_tasa_swap(fecha, plazo_1, data)
    tasa_2 = obtener_tasa_swap(fecha, plazo_swap, data)
    fxy = (((1 + tasa_2) ** (plazo_swap / 365) / (1 + tasa_1) **
            (plazo_1 / 365)) ** (365 / (plazo_swap - plazo_1))) - 1
    return fxy


def obtener_tasa_swap(fecha, plazo_swap, data):
    '''
    Para una fecha y un plazo dado se calcula su breakeven
    '''
    dias = plazo_swap
    tasa_swap = data.loc[(data['Tenor'] == dias), 'Yield']
    tasa = tasa_swap.tolist()[0]
    return tasa / 100

def cargar_excel(nombre, hoja):
    '''
    Carga un excel dado en un dataframe, segun su nombre y hoja
    '''
    wb = fs.open_workbook(nombre, False, False)
    dataframe = fs.get_frame_xl(wb, hoja, 1, 1, [0])
    fs.close_excel(wb)
    return dataframe


def generar_data():
    '''
    Genera la informacion de las swaps uf y clp
    '''
    data_tasas_uf = obtener_lista_tasas('UF')
    data_tasas_clp = obtener_lista_tasas('CLP')
    return data_tasas_uf, data_tasas_clp

def generar_matrices_input(fecha_actual, uf_matriz, matriz):
    '''
    Se generar las matrices de input
    '''
    matriz_precio = generar_matriz_precio_2(fecha_actual, uf_matriz, matriz)
    matriz_fecha = generar_matriz_fecha(fecha_actual, matriz)
    return matriz_precio, matriz_fecha

def obtener_lista_tasas(moneda):
    '''
    Obtiene las tasas  de los swap zero
    '''
    query = "select  Date, Curve_Name, Tenor, Yield from ZHIS_RA_Curves where Curve_Name = 'Swap {}/Camara' and date = (select top 1 date from ZHIS_RA_Curves order by date desc)".format(moneda)
    tasa_swap_uf = fs.get_frame_sql_user(server="puyehue",
                                         database="MesaInversiones",
                                         username="usuario1",
                                         password="usuario1",
                                         query=query)

    return tasa_swap_uf


def generar_matriz_precio_2(fecha_actual, uf_matriz, matriz):
    '''
    Crea una matriz con los valores de la UF
    '''
    
    nombre_filas = [fecha_actual]
    tasas = agregar_columnas_existentes(matriz) #mete los forwards en el df "tasas"
    
    lista_uf_normal = uf_matriz.loc[:, "CHUF Index"].tolist()[:len(nombre_filas)]
    
    tasas["UF_real"] = pd.Series(lista_uf_normal, index=matriz.index.tolist())
    
    listaUf = generar_columna_uf(nombre_filas, uf_matriz)
    
    tasas["CHUF Index"] = pd.Series(listaUf, index=nombre_filas[:len(listaUf)])
    
    matriz = reordenar_columnas(tasas)
    print(matriz.values)
    matriz = revisar_filas_incompletas(nombre_filas, matriz)
    return matriz


def generar_matriz_fecha(fecha_actual, matriz):
    '''
    Se crea la matriz con las fechas
    '''
    nombre_filas = [fecha_actual]
    listaUf = generar_columna_fecha_uf(nombre_filas)
    matriz = agregar_columas(matriz)
    matriz["CHUF Index"] = pd.Series(listaUf, index=nombre_filas)
    matriz = reordenar_columnas(matriz)
    return matriz


def generar_excel(dataframe, name):
    '''
    Se generan un excel con el dataframe 
    '''
    writer = pd.ExcelWriter(name)
    dataframe.to_excel(writer, 'Sheet1', False)
    writer.save()

'''FUNCIONES PARA HACER LA REGRESION DEL MODELO'''


def entrenar_modelo(matriz_fecha, matriz_precio, matriz_swap, dic, plazo_swap):
    '''
    Generamos la regresion de los breakeven, se obtiene los valores de los parametros
    '''
    rangos = dic.loc['rangos']['data'].split(',')
    dummy = dic.loc['Dummy']['data']
    alpha = dic.loc['ElasticNet_alpha']['data']
    l1_ratio = dic.loc['ElasticNet_l1_lasso']['data']
    x, y = generar_vectores(rangos, plazo_swap, matriz_fecha, matriz_precio, matriz_swap, dummy)
    if alpha==float(0):
        x = sm.add_constant(x)
        model = sm.OLS(y, x).fit()
        return model.params.tolist(), model.tvalues.tolist(), model.rsquared
    else:
        print(' no int')
        enet = ElasticNet(alpha=alpha, l1_ratio=l1_ratio)
        model = enet.fit(x, y)
        return np.append([model.intercept_.item()], model.coef_) , None, model.score(x,y)

def generar_vectores(rangos, plazo_swap, matriz_fecha, matriz_precio, matriz_swap, dummy):
    '''
    Se generar los vectores  x e y para la regresión
    '''
    vector_x = []
    vector_y = []
    lista_fechas = matriz_precio.index.tolist()
    for fecha in lista_fechas:
        try:
            if type(fecha) == pd._libs.tslib.Timestamp:
                fecha = fecha.to_pydatetime()
            breakeven = get_breakeven(fecha, plazo_swap, matriz_swap)
            lista_inflacion = generar_serie_inflaciones(fecha, rangos, matriz_fecha, matriz_precio, dummy)
            vector_x.append(lista_inflacion)
            vector_y.append(breakeven)
        except:
            pass
    return vector_x, vector_y

def get_breakeven(fecha, plazo_swap, matriz_swap):
    '''
    Para una fecha y un plazo dado se calcula su breakeven
    '''
    tasa_swap_uf = matriz_swap.loc[fecha, 'CHSWC{} Curncy'.format(plazo_swap)]
    tasa_swap_clp = matriz_swap.loc[fecha, 'CHSWP{} Curncy'.format(plazo_swap)]
    breakeven = ((100 + tasa_swap_clp) / (100 + tasa_swap_uf)) - 1
    return breakeven


'''FUNCIONES PARA LAS SERIES DE INFLACIONES'''


def generar_serie_inflaciones(fecha_inicio, rangos, matriz_fecha, matriz_precio, dummy, fecha_fila=None):
    '''
    Genera el vector con las inlfaciones explicativas para cada fecha
    '''
    # obriene las fechas en base al rango multiplicado por 30 dias
    lista_fechas = [fecha_inicio] + obtener_fechas_entre_inlfaciones(fecha_inicio, rangos)
    lista_inflacion = []
    for i in range(len(lista_fechas[1:])):
        if fecha_fila is None:
            inflacion = interpolar_inflacion(matriz_precio, matriz_fecha, lista_fechas[i + 1], fecha_inicio,
                                             lista_fechas[i])
        else:
            inflacion = interpolar_inflacion(matriz_precio, matriz_fecha, lista_fechas[i + 1], fecha_fila,
                                             lista_fechas[i])
        lista_inflacion.append(inflacion)
    if dummy is True:
        for i in range(12):
            if fecha_inicio.month == i+1:
                lista_inflacion.append(1)
            else:
                lista_inflacion.append(0)
    return lista_inflacion


def interpolar_inflacion(matriz_precio, matriz_fecha, fecha_1, fecha_fila, fecha_0=None):
    '''
    Dado dos fechas especificas se obtiene su respectiva inflacion
    '''

    lista_fechas = matriz_a_lista(matriz_fecha, fecha_fila)
    lista_fechas = lista_fechas_lista_dias(lista_fechas, fecha_fila)
    lista_precios = matriz_a_lista(matriz_precio, fecha_fila, matriz_fecha)
    inflacion = inflacion_dos_fechas(lista_precios, lista_fechas, fecha_1, fecha_fila, matriz_precio, matriz_fecha)
    aux_inflacion = 0
    if fecha_0 is not None:
        aux_inflacion = inflacion_dos_fechas(lista_precios, lista_fechas, fecha_0, fecha_fila, matriz_precio,
                                             matriz_fecha)
    return inflacion - aux_inflacion


def inflacion_dos_fechas(lista_precios, lista_fechas, fecha, fecha_fila, matriz_precio, matriz_fecha):
    '''
    Retorna la inflacion entre dos fechas
    '''
    inflacion_conocida = (lista_precios[0] / lista_precios[-1]) - 1
    date = fechas_a_dias(fecha, fecha_fila)
    precio = np.interp(date, lista_fechas[:len(lista_precios[:-1])], lista_precios[:-1])
    uf_actual = matriz_precio.loc[matriz_fecha.index.to_pydatetime() == fecha_fila, "CHUF Index"].tolist()
    inflacion = obtener_inflacion(precio, uf_actual)
    return inflacion_conocida + inflacion


def obtener_fechas_entre_inlfaciones(fecha, rangos):
    '''
    Se obtienen las fechas entre las que estran cada inflación explicativa
    '''
    lista_fechas = []

    for i in rangos:
        aux_fecha = fecha + datetime.timedelta(days=30 * int(i))
        lista_fechas.append(aux_fecha)
    return lista_fechas


def obtener_inflacion(uf_nuevo, uf_actual):
    '''
    Obtiene la inflacion de entre dos valores
    '''
    uf_actual = uf_actual[0]
    inflacion = (uf_nuevo / uf_actual) - 1
    return inflacion


'''FUNCIONES AUXILIARES'''


def matriz_a_lista(matriz, fecha, matriz_items=None):
    '''
    Se pasa de matriz a lista LOS precios para poder interpolar
    '''
    if matriz_items is None:
        matriz_items = matriz
    
    lista = matriz.loc[matriz_items.index.to_pydatetime() == fecha]

    lista = lista.iloc[0, :].tolist()
    for i in range(len(lista)):
        if type(lista[i]) is str:
            lista=lista[:i]
            break
    return lista


def lista_fechas_lista_dias(lista_fechas, fecha_fila):
    '''
    Pasa de una lista de fechas a una lista en dias
    '''
    nueva_lista_fecha = []
    for fecha in lista_fechas:
        if type(fecha) == pd._libs.tslib.Timestamp:
            fecha = fecha.to_pydatetime()

        fecha = fechas_a_dias(fecha, fecha_fila)
        nueva_lista_fecha.append(fecha)
    return nueva_lista_fecha


def fechas_a_dias(date, inicio=None):
    '''
    Pasa las fechas a dias para poder interpolar
    '''
    if type(date) is datetime.date:
        date = datetime.datetime(date.year, date.month, date.day)
    diferencia = (date - inicio).days
    return diferencia
