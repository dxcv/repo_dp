
import numpy as np
import pandas as pd
import xlwings as xw

def clear_sheet_excel(wb, sheet):
    '''
    Borra Excel.
    '''
    wb.sheets[sheet].clear()

def paste_value_excel(wb, sheet, row, column, value):
    '''
    Inserta un valor en un excel.
    '''
    wb.sheets[sheet].range((row,column)).value = value

def read_table_excel(wb, sheet, row, column, index):
    '''
    Lee un a tabla de Excel en un dataframe.
    '''
    raw_table = wb.sheets[sheet].range((row,column)).expand("table").value
    columns = raw_table[0]
    data = raw_table[1:]
    table = pd.DataFrame(data=data, columns=columns).set_index(index)

    return table

def read_inputs():
    '''
    Lee inputs.
    '''
    wb = xw.Book("inputs.xlsx")
    rentabilidades = read_table_excel(wb, "rentabilidad", 1, 1, "year")
    rentabilidades.index = rentabilidades.index.astype(int)
    flujos = read_table_excel(wb, "flujos", 1, 1, "year")
    flujos.index = flujos.index.astype(int)
    shocks = read_table_excel(wb, "shocks", 1, 1, "year")
    shocks.index = shocks.index.astype(int)
    shocks = shocks.reindex(flujos.index)
    shocks = shocks.fillna(0.0)
    flujos["flujo"] += shocks["shock"]
    #wb.close()
    #app = wb.app
    #app.quit()
    return rentabilidades, flujos

def insert_output(matriz_patrimonio, matriz_reservas, matriz_gastos, matriz_gastos_rentabilidad, matriz_gastos_reservas, serie_tiempo_retencion, matriz_ex_gastos, otros, matriz_regla_simple):
    '''
    Lee inputs.
    '''
    wb = xw.Book("inputs.xlsx")
    clear_sheet_excel(wb, "matriz_patrimonio")
    clear_sheet_excel(wb, "matriz_reservas")
    clear_sheet_excel(wb, "matriz_gastos")
    clear_sheet_excel(wb, "matriz_gastos_rentabilidad")
    clear_sheet_excel(wb, "matriz_gastos_reservas")
    clear_sheet_excel(wb, "serie_tiempo_retencion")
    clear_sheet_excel(wb, "matriz_ex_gastos")
    clear_sheet_excel(wb, "otros")
    clear_sheet_excel(wb, "matriz_regla_simple")
    paste_value_excel(wb, "matriz_patrimonio", 1, 1, matriz_patrimonio)
    paste_value_excel(wb, "matriz_reservas", 1, 1, matriz_reservas)
    paste_value_excel(wb, "matriz_gastos", 1, 1, matriz_gastos)
    paste_value_excel(wb, "matriz_gastos_rentabilidad", 1, 1, matriz_gastos_rentabilidad)
    paste_value_excel(wb, "matriz_gastos_reservas", 1, 1, matriz_gastos_reservas)
    paste_value_excel(wb, "serie_tiempo_retencion", 1, 1, serie_tiempo_retencion)
    paste_value_excel(wb, "matriz_ex_gastos", 1, 1, matriz_ex_gastos)
    paste_value_excel(wb, "otros", 1, 1, otros)
    paste_value_excel(wb, "matriz_regla_simple", 1, 1, matriz_regla_simple)


def calcular_matriz_gastos(rentabilidades, flujos, acumulacion_min, rentabilidad_min, rentabilidad_max, rentabilidad_target, periodo_movil, rf, n_simulaciones, gasto_regla_simple, patrimonio_t0, reserva_t0):
    '''
    Calcula las matrices de gastos.
    '''
    
    serie_flujos = flujos["flujo"]

    # Definimos tre matrices de patrimonio, reservas y gastos
    matriz_patrimonio = pd.DataFrame()
    matriz_reservas = pd.DataFrame()
    matriz_gastos = pd.DataFrame()
    matriz_gastos = pd.DataFrame()
    matriz_gastos_rentabilidad = pd.DataFrame()
    matriz_gastos_reservas = pd.DataFrame()
    serie_tiempo_retencion = pd.DataFrame(columns=["tiempo_retencion"])
    matriz_ex_gastos = pd.DataFrame()
    matriz_regla_simple = pd.DataFrame()

    for i in rentabilidades.columns[:n_simulaciones]:
        print("running simulation " + str(i))
        serie_retornos = rentabilidades[i]
        serie_patrimonio, serie_reservas, serie_gastos, serie_gastos_rentabilidad, serie_gastos_reservas, tiempo_retencion, serie_ex_gastos, serie_regla_simple = calcular_gastos(serie_retornos,
                                                                                                                                                                                  serie_flujos,
                                                                                                                                                                                  acumulacion_min,
                                                                                                                                                                                  rentabilidad_min,
                                                                                                                                                                                  rentabilidad_max,
                                                                                                                                                                                  rentabilidad_target,
                                                                                                                                                                                  periodo_movil,
                                                                                                                                                                                  rf,
                                                                                                                                                                                  gasto_regla_simple,
                                                                                                                                                                                  patrimonio_t0,
                                                                                                                                                                                  reserva_t0)
        matriz_patrimonio[str(i)] = serie_patrimonio 
        matriz_reservas[str(i)] = serie_reservas 
        matriz_gastos[str(i)] = serie_gastos 
        matriz_gastos_rentabilidad[str(i)] = serie_gastos_rentabilidad
        matriz_gastos_reservas[str(i)] = serie_gastos_reservas
        serie_tiempo_retencion.loc[i, "tiempo_retencion"] = tiempo_retencion
        matriz_ex_gastos[str(i)] = serie_ex_gastos
        matriz_regla_simple[str(i)] = serie_regla_simple



    return matriz_patrimonio, matriz_reservas, matriz_gastos, matriz_gastos_rentabilidad, matriz_gastos_reservas, serie_tiempo_retencion, matriz_ex_gastos, matriz_regla_simple


def calcular_gastos(serie_retornos, serie_flujos, acumulacion_min, rentabilidad_min, rentabilidad_max, rentabilidad_target, periodo_movil, rf, gasto_regla_simple, patrimonio_t0, reserva_t0):
    '''
    Calcula la serie de patrimonio, gastos y reserva de una serie. Algunas cosnideraciones:
    * Los flujos entran a fin de anio y no acumulan rentabilidad
    * el gasto se ejecuta a principio de anio
    * la reserva tambien se deposita a principio de anio, por lo tanto acumula rentabilidad de ese anio
    * la rentabilidad target es parametrizada
    * la el monto target es sobre el patrimonio
    * reservas salen del equity 
    '''

    fechas_simulacion = serie_flujos.index
    serie_gastos = pd.Series(index=fechas_simulacion)
    serie_gastos = serie_gastos.fillna(0.0)
    serie_reservas = pd.Series(index=fechas_simulacion)
    serie_reservas = serie_reservas.fillna(0.0)
    serie_patrimonio = pd.Series(index=fechas_simulacion)
    serie_patrimonio = serie_patrimonio.fillna(0.0)
    serie_gastos_rentabilidad = pd.Series(index=fechas_simulacion)
    serie_gastos_rentabilidad = serie_gastos_rentabilidad.fillna(0.0)
    serie_gastos_reservas = pd.Series(index=fechas_simulacion)
    serie_gastos_reservas = serie_gastos_reservas.fillna(0.0)
    serie_ex_gastos = pd.Series(index=fechas_simulacion)
    serie_ex_gastos = serie_ex_gastos.fillna(0.0)
    serie_regla_simple = pd.Series(index=fechas_simulacion)
    serie_regla_simple = serie_regla_simple.fillna(0.0)

    # inicializamos la serie de patrimonio acumulado
    t0 = fechas_simulacion[0]
    serie_patrimonio[t0] = serie_flujos[t0] + patrimonio_t0
    serie_ex_gastos[t0] = serie_flujos[t0] + patrimonio_t0
    serie_regla_simple[t0] = serie_flujos[t0] + patrimonio_t0
    serie_reservas[t0] = reserva_t0

    # acumulamos y buscamos la fecha donde se habilita el gasto
    inic_pinned = False
    for t in fechas_simulacion[1:]:
        if serie_ex_gastos[t-1] >= acumulacion_min and inic_pinned == False:
            t_inic = t
            inic_pinned = True
        patrimonio = (serie_ex_gastos[t-1]*(1+serie_retornos[t])) + serie_flujos[t]
        patrimonio_regla_simple = ((serie_regla_simple[t-1]-gasto_regla_simple)*(1+serie_retornos[t])) + serie_flujos[t]
        if inic_pinned == False:
            serie_patrimonio[t] = patrimonio
        serie_ex_gastos[t] = patrimonio
        serie_regla_simple[t] = patrimonio_regla_simple
    tiempos.append(t_inic)
    # Simulamos regla de gastos desde la fecha de acumulacion
    for t in fechas_simulacion[fechas_simulacion >= t_inic]:

        # obtenemos la rentabilidad al cierre
        rentabilidad = serie_retornos.loc[t]
        
        # calculamos la media movil del instante hasta t-1
        if t > 2021:
            ma = 0.0
            for i in range(1, periodo_movil+1):
                ma += serie_retornos[t-i]
            ma = ma / periodo_movil
        else:
            ma = serie_retornos[t]

        # obtenemos nuestra reserva acumulada y flujo
        patrimonio_prev = serie_patrimonio[t-1]
        reserva_prev = serie_reservas[t-1]
        flujo = serie_flujos[t]

        # Caso en que rentamos mas de nuestro maximo y reservamos
        if ma >= rentabilidad_max:

            outflow_equity = (ma-rentabilidad_min) * patrimonio_prev
            gasto = (rentabilidad_max-rentabilidad_min) * patrimonio_prev
            reserva = (reserva_prev+(outflow_equity-gasto)) * (1+rf)
            patrimonio = ((patrimonio_prev-outflow_equity)*(1+rentabilidad)) + flujo
            gasto_rentabilidad = gasto
            gasto_reservas = 0.0

        # Caso en que rentamos menos del maximo pero mas del target
        elif ma < rentabilidad_max and ma >= rentabilidad_target:

            outflow_equity = (ma-rentabilidad_min) * patrimonio_prev
            gasto = outflow_equity
            reserva = serie_reservas[t-1] * (1+rf)
            patrimonio = ((patrimonio_prev-outflow_equity)*(1+rentabilidad)) + flujo
            gasto_rentabilidad = gasto
            gasto_reservas = 0.0

        # Caso en que rentamos menos del target pero mas que el minimo
        elif ma < rentabilidad_target and ma >= rentabilidad_min:

            outflow_equity = (ma-rentabilidad_min) * patrimonio_prev
            monto_target =  (rentabilidad_target-rentabilidad_min) * patrimonio_prev
            outflow_reserva = monto_target - outflow_equity
            patrimonio = ((patrimonio_prev-outflow_equity)*(1+rentabilidad)) + flujo
            # Vemos si tenemos suficiente en reserva para cubrir el gasto
            if reserva_prev >= outflow_reserva:
                gasto = monto_target
                reserva = (reserva_prev-outflow_reserva) * (1+rf)
            else:
                outflow_reserva = reserva_prev
                gasto =outflow_equity + outflow_reserva
                reserva = 0.0
            gasto_rentabilidad = outflow_equity
            gasto_reservas = outflow_reserva

        # Caso mas negativo, usamos toda la reserva
        elif ma < rentabilidad_min:

            monto_target =  (rentabilidad_target-rentabilidad_min) * patrimonio_prev
            patrimonio = (patrimonio_prev*(1+rentabilidad)) + flujo
            if reserva_prev >= monto_target:
                gasto = monto_target
                reserva = (reserva_prev-monto_target) * (1+rf)
            else:
                gasto = reserva_prev
                reserva = 0.0
            gasto_rentabilidad = 0.0
            gasto_reservas = gasto
        serie_reservas[t] = reserva
        serie_gastos[t] = gasto               
        serie_patrimonio[t] = patrimonio               
        serie_gastos_rentabilidad[t] = gasto_rentabilidad
        serie_gastos_reservas[t] = gasto_reservas

    return serie_patrimonio, serie_reservas, serie_gastos, serie_gastos_rentabilidad, serie_gastos_reservas, t_inic, serie_ex_gastos, serie_regla_simple


def get_extreme_paths(matriz_ex_gastos):
    '''
    Obtiene el mejor y peor path.
    '''
    serie_inic = matriz_ex_gastos["1.0"]
    best_index = 0
    worst_index = 0
    worst_performance = serie_inic[serie_inic.index[-1]]
    best_performance = serie_inic[serie_inic.index[-1]]
    # Sacamos mejor path y peor
    for i in matriz_ex_gastos.columns:
        serie = matriz_ex_gastos[i]
        performance = serie[serie.index[-1]]
        if performance >= best_performance:
            best_performance = performance
            best_index = i

        if performance <= worst_performance:
            worst_performance = performance
            worst_index = i
    
    # Sacamos el promedio
    mean_performance = float(matriz_ex_gastos.loc[matriz_ex_gastos.index[-1]].mean(axis=0))

    return best_performance, best_index, worst_performance, worst_index, mean_performance




if __name__ == "__main__":
    n_simulaciones = 10000
    acumulacion_min = 400000
    rentabilidad_min = 0.0
    rentabilidad_target = 0.02
    rentabilidad_max = 0.04
    periodo_movil = 3 
    rf = 0.01
    gasto_regla_simple = 30000
    costos = 0.15
    patrimonio_t0 = 0.0#400000
    reserva_t0 = 0.0#200000
    otros = pd.DataFrame(columns=["valor"])
    tiempos = []

    print("fetching inputs...")
    rentabilidades, flujos = read_inputs()

    print("computing costs...")
    flujos *= 1 -costos
    

    print("running simulations...")
    matriz_patrimonio, matriz_reservas, matriz_gastos, matriz_gastos_rentabilidad, matriz_gastos_reservas, serie_tiempo_retencion, matriz_ex_gastos, matriz_regla_simple = calcular_matriz_gastos(rentabilidades,
                                                                                                                                                                                                  flujos,
                                                                                                                                                                                                  acumulacion_min,
                                                                                                                                                                                                  rentabilidad_min,
                                                                                                                                                                                                  rentabilidad_max,
                                                                                                                                                                                                  rentabilidad_target,
                                                                                                                                                                                                  periodo_movil,
                                                                                                                                                                                                  rf,
                                                                                                                                                                                                  n_simulaciones,
                                                                                                                                                                                                  gasto_regla_simple,
                                                                                                                                                                                                  patrimonio_t0,
                                                                                                                                                                                                  reserva_t0)
    #print(tiempos)
    #print(sum(tiempos)/float(len(tiempos))-2018) para la tabla de sensibilidad
    
    best_performance, best_index, worst_performance, worst_index, mean_performance = get_extreme_paths(matriz_ex_gastos)
    otros.loc["best_performance", "valor"] = best_performance
    otros.loc["best_index", "valor"] = best_index
    otros.loc["worst_performance", "valor"] = worst_performance
    otros.loc["worst_index", "valor"] = worst_index
    otros.loc["mean_performance", "valor"] = mean_performance

    #print("printing output...")
    insert_output(matriz_patrimonio, matriz_reservas, matriz_gastos, matriz_gastos_rentabilidad, matriz_gastos_reservas, serie_tiempo_retencion, matriz_ex_gastos, otros, matriz_regla_simple)