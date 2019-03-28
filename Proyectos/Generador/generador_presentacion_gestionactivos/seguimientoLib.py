# pylint: disable-msg=C0103,C0111

import sys
from datetime import timedelta as td
import math
import itertools
from datetime import datetime
import pandas as pd
import numpy as np
sys.path.insert(0, '../libreria/')
import libreria_fdo as Mesa

# Constantes

# Clasificacion de Instrumentos
# NOTE: Si se cambia como se definen Corto y Largo para los instrumentos, basta
#       cambiar el valor de DURATION a continuacion
DURATION = 5    # DURATION > 5 largo, DURATION <= 5 corto

# Queries
BENCHMARKNAMEQUERY = "./queries_generador/benchmarkName.sql"
DATAQUERY = "./queries_generador/getRawDataQuery.sql"
PORTFOLIOQUERY = "./queries_generador/getPortfolio.sql"
PORTFOLIOINFOQUERY = "./queries_generador/portfolioInfo.sql"

# Hojas
CARTERACOMPLETA = "CarteraCompleta"
DATOS = "Datos"
DATAEVOLUCION = "DataEvolucion"
EVOLUCION = "Evolucion"
MOVIMIENTOS = "Movimientos"
SEGUIMIENTO = "Seguimiento"

# Headers de tablas en base de datos:
ASSETCLASS = "Asset_Class"
CANTIDAD = "Cantidad"
CLASIFICACIONRIESGO = "Clasificacion_Riesgo"
CORTOLARGO = "Corto_Largo"
DURACIONMONEDA = "Duracion_Moneda"
DURATIONHEADER = "Duration"
FECHA = "Fecha"
MONEDA = "Moneda"
MONTO = "Monto"
NOMBREEMISOR = "Nombre_Emisor"
NOMBREINSTRUMENTO = "Nombre_Instrumento"
PORCENTAJE = "Porcentaje"
PRECIO = "Precio"
RENTA = "Renta"
RIESGO = "Riesgo"
RIESGODURACION = "Riesgo_Duracion"
RIESGODURACIONMONEDA = "Riesgo_Duracion_Moneda"
SUBCLASS = "Subclase"
SECTOR = "Sector"
TASA = "Tasa"
TIPOINSTRUMENTO = "Tipo_Instrumento"
TIPOINSTRUMENTOLARGO = "TipoInstrumento_Largo"
TIPOINSTRUMENTOMONEDA = "TipoInstrumento_Moneda"
TIPOMOVIMIENTO = "Tipo Movimiento"
ZONA = "Zona"

# Tipos de Instrumento
FIJA = "Fija"
LETRAHIPOTECARIA = "Letra Hipotecaria"
FACTURA = "Factura"
BONOGOBIERNO = "Bono de Gobierno"
DEPOSITO = "Deposito"
BONOCORPORATIVO = "Bono Corporativo"

'''
    UTILIDAD: Dada una conexion a la base de datos, a este metodo se le puede
    entregar una query con sus parametros y la devuelve entera sin procesamiento
    alguno.

    USO: En la query, se pueden poner placeholders segun los acepta pymssql
    (con %s). En parameters, se pone una tupla ordenada de parametros para
    reemplazar cada placeholder.

    Por ejemplo:
      query = SELECT * FROM Example WHERE ExampleArgument1 = %s
              AND ExampleArgument2 < %s
      parameters = (5, 10)

    Es equivalente a hacer la query:
              SELECT * FROM Example WHERE ExampleArgument1 = 5
              AND ExampleArgument2 < 10

    data = (connection, query, (5, 10))

    NOTA: Cada fila de la base de datos se toma como un objeto Tuple, el cual es
    inmutable para Python
 '''
# TODO Testing a cada query con este metodo
def getData(connection, query, parameters):
    print("Esperando respuesta de Base de Datos")
    try:
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        headers = [i[0] for i in cursor.description]
        data = cursor.fetchall()
        print(">>> OK")
        return (headers, data)

    except BaseException:
        print("ERROR: Consulta no realizada")
        return [[],[]]

'''
    UTILIDAD: Con los datos de los valores del fondo/cartera y su benchmark, este
    metodo retorna los retornos mensuales y anuales de cada uno en forma de tupla
    de (retornos mensuales, retornos anuales). A su vez, cada elemento en esa tupla
    es un arreglo de arreglos de la forma [mes (o año), retorno del periodo para
    cartera, retorno del periodo para benchmark].

    USO: Se le entregan los datos de los valores en el campo 'data' de la forma
    [[fecha, valor cartera/fondo, valor benchmark]] y se le entrega el indice en
    que se encuentra el valor cartera (en este caso index = 1). Es posible modificar
    el metodo y quitar index, pero mantenerlo deja la opcion de reutilizarlo o
    modificarlo mas facilmente en el futuro. Datos deben venir ordenados de forma
    descendiente por fecha para funcionar, o bien modificar metodo para generar este
    orden al inicio

    NOTA: Logica del metodo es comenzar con la fecha mas reciente (tupla 0 del
    arreglo 'data') e iterar hacia abajo hasta verificar un cambio de mes. Cuando
    se oberva cambio de mes, calcular retorno mensual. Tambien en el cambio de mes
    se verifica cambio de anio y se calcula retorno anual. Finalmente se agrega los
    valores de retorno del ultimo mes y anio
'''
def calculateReturns(data):  # 1 para fondo, 2 para benchmark
    currentDayForMonth = data[0] # Init values FIXME: Usar indice fecha
    currentDayForYear = data[0]
    monthlyReturns = []
    yearlyReturns = []

    # NOTE Datos ya vienen ordenados en forma desc
    for day in data:
        if currentDayForMonth[0].month != day[0].month:
            currentMonthReturn = currentDayForMonth[1] / day[1] - 1
            currentMonthBenchmarkReturn = currentDayForMonth[2] / day[2] - 1
            monthlyReturns.append([str(currentDayForMonth[0].month)
                                   + "/" + str(currentDayForMonth[0].year),
                                   currentMonthReturn,
                                   currentMonthBenchmarkReturn])
            currentDayForMonth = day
            if currentDayForYear[0].year != day[0].year:
                currentYearReturn = currentDayForYear[1] / day[1] - 1
                currentYearBenchmarkReturn = currentDayForYear[2] / day[2] - 1
                yearlyReturns.append([currentDayForYear[0].year,
                                      currentYearReturn,
                                      currentYearBenchmarkReturn])
                currentDayForYear = day

    # Incluir ultimo mes
    last = data[len(data) - 1]
    if currentDayForMonth[0].month == last[0].month:
        lastMonthReturn = currentDayForMonth[1] / last[1] - 1
        lastMonthBenchmarkReturn = currentDayForMonth[2] / last[2] - 1
        monthlyReturns.append([str(last[0].month) + "/" + str(last[0].year),
                               lastMonthReturn, lastMonthBenchmarkReturn])

    # Incluir ultimo anio
    if currentDayForYear[0].year == last[0].year:
        lastYearReturn = currentDayForYear[1] / last[1] - 1
        lastYearBenchmarkReturn = currentDayForYear[2] / last[2] - 1
        yearlyReturns.append([last[0].year, lastYearReturn, lastYearBenchmarkReturn])

    return (monthlyReturns, yearlyReturns)

def extractByTimedelta(data, delta, dateIndex):
    firstDate = data[0][dateIndex]
    i = 0
    for entry in data:
        dateDifference = firstDate - entry[dateIndex]
        if dateDifference.days > delta:
            break
        else:
            i += 1
    if i == len(data):
        return []
    else:
        return data[:i]

# NOTE: Varianza sobre vector creado da Tracking Error entregado por este metodo. Vale decir:
# Tracking Error = Var(|AlphaDiario|) = Var(|Rportafolio - Rbenchmark|)
# NOTE: Entregar datos que se quieren analizar por caad vez (EJ: Datos de 2015)
def getStatistics(data):
    # NOTE: Adaptado de: http://gouthamanbalaraman.com/blog/calculating-stock-beta.html
    # Alpha, Beta, Tracking Error, Volatilidad Cartera, Volatilidad Benchmark

    statistics = {}

    timeSeriesDataFrame = pd.DataFrame(data[1], columns=["Date", "Portfolio", "Benchmark"])
    timeSeriesDataFrame = timeSeriesDataFrame.set_index("Date")
    monthlyDataFrame = timeSeriesDataFrame.resample('W').last()

    # Calcular retornos mensuales
    monthlyDataFrame[['portfolio_returns', 'benchmark_returns']] = monthlyDataFrame[['Portfolio', 'Benchmark']]/\
        monthlyDataFrame[['Portfolio', 'Benchmark']].shift(1) - 1
    monthlyDataFrame = monthlyDataFrame.dropna()

    # Matriz de covarianza
    covmat = np.cov(monthlyDataFrame["portfolio_returns"], monthlyDataFrame["benchmark_returns"])
    if math.isnan(covmat[0, 0]):
        statistics["alpha"] = None
        statistics["beta"] = None
        statistics["tracking_error"] = None
        statistics["r_squared"] = None
        statistics["portfolio_volatility"] = None
        statistics["benchmark_volatility"] = None
        return statistics

    # Alpha y Beta
    beta = covmat[0, 1] / covmat[1, 1]
    alpha = np.mean(monthlyDataFrame["portfolio_returns"]) - beta * np.mean(monthlyDataFrame["benchmark_returns"])
    # Tracking Error
    trackingError = np.sqrt(np.var(monthlyDataFrame["portfolio_returns"] -
                            monthlyDataFrame["benchmark_returns"]))

    # R cuadrado
    ypred = alpha + beta * monthlyDataFrame["benchmark_returns"]
    SS_res = np.sum(np.power(ypred - monthlyDataFrame["portfolio_returns"], 2))
    SS_tot = covmat[0, 0] * (len(monthlyDataFrame) - 1) # SS_tot is sample_variance*(n-1)
    r_squared = 1 - SS_res/SS_tot

    # Anualizar numeros
    periods = 365 / 7
    alpha = alpha * periods
    trackingError = trackingError * np.sqrt(periods)
    portfolio_volatility = np.sqrt(covmat[0, 0] * periods)
    benchmark_volatility = np.sqrt(covmat[1, 1] * periods)

    statistics["alpha"] = alpha
    statistics["beta"] = beta
    statistics["tracking_error"] = trackingError
    statistics["r_squared"] = r_squared
    statistics["portfolio_volatility"] = portfolio_volatility
    statistics["benchmark_volatility"] = benchmark_volatility

    return statistics

'''
    UTILIDAD: Devuelve la clase de activo en siglas (RFL, RFI, RVL o RVI).
    USO: clase = getClass("Fija", "Desarrollado", "US")
    >> clase = "RFI"
'''
def getClass(incomeType, zone, country):
    assetClass = ""
    if incomeType != "NULL" and zone != "NULL":
        assetClass = "Renta " + incomeType + " "
        assetClass += "Local" if (zone == "Local" or country == "CL") else "Internacional"
    return assetClass


def detectWrongClassification(instrument):
    for i in instrument:
        if i == "" or i is None:
            return True
    return False

'''
    UTILIDAD: Devuelve la subclase del instrumento ([Gobierno $ Corto, Gobierno $ Largo,
    Gobierno UF Corto, Gobierno UF Largo, Deposito $, Deposito UF, Corporativo Alto Riesgo
    Corto, Corporativo Alto Riesgo Corto, Corporativo Bajo Riesgo Corto, Corporativo Bajo
    Riesgo Largo, Letras, Facturas, Fondos, Liquidez $, Liquidez USD])
'''
def getSubclass(zone, currency, risk, instrumentType, duration, incomeType, country):
    # Si es renta fija local:
    if incomeType == FIJA and (zone == "Local" or country == "CL"):
        subclass = instrumentType
        if instrumentType != LETRAHIPOTECARIA and instrumentType != FACTURA:
            if instrumentType == BONOGOBIERNO:
                subclass += " " + currency + " " + duration
            elif instrumentType == DEPOSITO:
                subclass += " " + currency
            elif instrumentType == BONOCORPORATIVO:
                subclass += " " + risk + " " + duration
        return subclass

    # Todos los otros tipos
    else:
        if incomeType != "NULL" and incomeType is not None:
            return "Renta " + incomeType + " " + zone
        else: return "NULL"

'''
    UTILIDAD: Para subclasificaciones de los instrumentos (se arman ya que no
    estan persentes en Base de Datos)

    USO: Se le entrega la informacion sin procesar de la cartera completa

    NOTA: Se buscan indices para dejar codigo mantenible en lugar de hardcodearlos.
    Esto se debe a que en el futuro, orden de columnas en tabla  -o tabla completa-
    podria cambiar.
'''
def subclassify(portfolio):
    # Indices de columnas
    instrumentCodeIndex = portfolio[0].index("Codigo_Ins")
    emmitterIndex = portfolio[0].index("Codigo_Emi")
    instrumentTypeIndex = portfolio[0].index(TIPOINSTRUMENTO)
    zoneIndex = portfolio[0].index(ZONA)
    durationIndex = portfolio[0].index(DURATIONHEADER)
    riskIndex = portfolio[0].index(CLASIFICACIONRIESGO)
    currencyIndex = portfolio[0].index(MONEDA)
    incomeTypeIndex = portfolio[0].index(RENTA)
    amountIndex = portfolio[0].index(MONTO)
    countryIndex = portfolio[0].index("Pais_Emisor")

    i = 0
    totalAmount = np.sum(row[amountIndex] for row in portfolio[1])

    for instr in portfolio[1]:
        # Pais emisor
        country = instr[countryIndex] if instr[countryIndex] is not None else ""
        # Porcentaje
        percentage = float(instr[amountIndex] / totalAmount) # NOTE: Float necesario por bug xlwing
        # Zona
        zone = instr[zoneIndex] if instr[zoneIndex] is not None else ""
        # Corto_Largo
        short_long = 'Corto' if instr[durationIndex] <= DURATION else 'Largo'
        # Moneda
        currency = instr[currencyIndex] if instr[currencyIndex] is not None else ""
        # Tipo de instrumento
        instrumentType = instr[instrumentTypeIndex] if instr[instrumentTypeIndex] is not None else ""
        # Tipo de renta --> Fija, Mixta, Variable
        incomeType = instr[incomeTypeIndex] if instr[incomeTypeIndex] is not None else ""
        # Clasificacion_Riesgo --> Alto o Bajo
        risk = instr[riskIndex] if instr[riskIndex] is not None else ""
        # Riesgo_Duracion_Moneda
        risk_duration_currency = risk + " " + short_long + " " + currency
        # Riesgo_Duracion
        risk_duration = risk + " " + short_long
        # Duracion_moneda
        duration_currency = short_long + " " + currency
        # Tipopapel_Moneda
        instrumentType_Currency = instrumentType + " " + currency
        # TipoInstrumento_Largo
        instrumentType_duration = instrumentType + " " + short_long

        # Asset Class y Subclass, tomando en consideracion que podrian ser liquidez
        if "CFM8401" in instr[instrumentCodeIndex] or instr[emmitterIndex] in ["LIQUIDEZ", "CAJA"]:
            assetClass = "Liquidez " + instr[currencyIndex]
            subclass = "Liquidez " + instr[currencyIndex]
        else:
            assetClass = getClass(incomeType, zone, country)
            subclass = getSubclass(zone, currency, risk, instrumentType, short_long, incomeType, country)

        # Clasificacion Falsa para detectar incorrectos
        if detectWrongClassification(instr):
            assetClass = "NC"
            subclass = "NC"

        # Extender todo
        instr += (percentage,
                  short_long,
                  risk_duration_currency,
                  risk_duration,
                  duration_currency,
                  instrumentType_Currency,
                  instrumentType_duration,
                  assetClass,
                  subclass)

        portfolio[1][i] = instr
        i += 1


    # Agregar nuevos titulos
    portfolio[0].extend(["Porcentaje",
                         CORTOLARGO,
                         RIESGODURACIONMONEDA,
                         RIESGODURACION,
                         DURACIONMONEDA,
                         TIPOINSTRUMENTOMONEDA,
                         TIPOINSTRUMENTOLARGO,
                         ASSETCLASS,
                         SUBCLASS])

    return portfolio

'''
    UTILIDAD: Agarra conjunto de instrumentos en forma de arreglo de tuplas y los devuelve ordenados
    en un diccionario con la subclase como llave

    NOTA: Facilmente extendible a cualquier indice para funcionar como llave
'''
def assetClassBreakdown(headers, subportfolio):
    if subportfolio != []:
        subclassIndex = headers.index(SUBCLASS)
        subclasses = set(np.column_stack(subportfolio)[subclassIndex])
        # Crea diccionario con sublases como llave
        instrumentsDictionary = dict((i, []) for i in subclasses)

        for instrument in subportfolio:
            instrumentsDictionary[instrument[subclassIndex]].append(instrument)

        return instrumentsDictionary
    else:
        return []

def benchmarkComposition(benchmark):
    benchmark[0].extend([ASSETCLASS])
    incomeTypeIndex = benchmark[0].index(RENTA)
    zoneIndex = benchmark[0].index(ZONA)
    i = 0
    for index in benchmark[1]:
        assetClass = "Renta " + index[incomeTypeIndex] + " " + index[zoneIndex]
        index += (assetClass, "")[:-1]
        benchmark[1][i] = index
        i += 1
    return benchmark

'''
    UTILIDAD: Se devuelve los montos invertidos (y el porcentaje que representa) en alguna
    categoria de una cartera en forma de diccionario.

    USO: Se le entrega el indice en el que se encuetran las llaves del diccionario, el indice en que
    se encuentra el monto invertido en el instrumento y la matriz del portafolio completo.
    Ejemplo:
    indiceMoneda = 3
    indiceMonto = 5
    totales = totalPerType(indiceMoneda, indiceMonto, carteraCompleta)
    >> totales = {$: [10.000.000, 0,2], US: [40.000.000, 0,8]}
'''
def totalPerType(typeIndex, amountIndex, matrix):
    if matrix == []:
        return matrix

    types = set(np.column_stack(matrix)[typeIndex])
    # Crea diccionario con tipo como llave
    totalsDictionary = dict((i, [0, 0]) for i in types)
    total = 0

    for row in matrix:
        totalsDictionary[row[typeIndex]][0] += row[amountIndex]
        total += row[amountIndex]

    for row in matrix:
        totalsDictionary[row[typeIndex]][1] += float(row[amountIndex] / total)

    return totalsDictionary

'''
    UTILIDAD: De una matriz completa, devuelve solo la matriz con ciertas colummnas.

    USO:
    matriz = [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
    >> matriz = |1   2   3|
    >>          |4   5   6|
    >>          |7   8   9|
    submatriz = extractSubmatrix(matriz, (0, 2))
    >> submatriz = |1   3|
    >>             |4   6|
    >>             |7   9|
'''
def extractSubmatrix(matrix, indexes):
    submatrix = []
    for row in matrix:
        subRow = []
        for index in indexes:
            subRow.append(row[index])
        submatrix.append(subRow)
    return submatrix

'''
    UTILIDAD: Convierte un indice a numero de columna en excel. Por ejemplo:
    numberToExcelColumnString(28) ==> 'AB'
'''
def numberToExcelColumnString(n):
    div = n
    string = ""
    while div > 0:
        module = (div - 1) % 26
        string = chr(65 + module) + string
        div = int((div - module) / 26)
    return string


'''
    Algoritmo comun para obtener digito verificador del rut, explicado aca:
    https://users.dcc.uchile.cl/~mortega/microcodigos/validarrut/algoritmo.html
'''
def verificadorRUT(rut):
    suma = 0
    iterador = 0
    for k in [int(i) for i in (str(rut)[::-1])]:
        multiplicador = ((iterador % 6) +  2)
        suma += multiplicador * k
        iterador += 1
    verificador = 11 - suma % 11
    if verificador == 11:
        return 0
    elif verificador == 10:
        return "k"
    else:
        return verificador

'''
    UTILIDAD: Separa cartera en RFL, RVI, RVL, RFI
'''
def portfolioBreakdown(portfolio):
    portfolioRFL = []
    portfolioRVL = []
    portfolioRFI = []
    portfolioRVI = []
    noClass = []
    portfoliosByClass = [portfolioRFL, portfolioRVL, portfolioRFI, portfolioRVI, noClass]

    try:
        assetClassIndex = portfolio[0].index(ASSETCLASS)
        for instrument in portfolio[1]:
            # Renta Fija Local
            if instrument[assetClassIndex] == 'Renta Fija Local':
                portfoliosByClass[0].append(instrument)

            # Renta Variable Local
            elif instrument[assetClassIndex] == 'Renta Variable Local':
                portfoliosByClass[1].append(instrument)

            # Renta Fija Internacional
            elif instrument[assetClassIndex] == 'Renta Fija Internacional':
                portfoliosByClass[2].append(instrument)

            # Renta Variable Internacional
            elif instrument[assetClassIndex] == 'Renta Variable Internacional':
                portfoliosByClass[3].append(instrument)

            # Mal Clasificados
            elif instrument[assetClassIndex] == 'NC':
                portfoliosByClass[4].append(instrument)

        return portfoliosByClass
    except BaseException:
        print ("ERROR: No se ha podido desglosar cartera")

# HACK para encontrar fecha minima mas rapidamente
def binarySearchFirstEntry(connection, ticker, query, initDate, endDate, threshold):
    delta = endDate - initDate
    middleDate = initDate + (delta / 2)
    if delta.days <= threshold:
        return middleDate

    data = []

    for i in range(-math.floor(threshold / 2), math.floor(threshold / 2)):
        dateString = dateToString(middleDate + td(days=i))
        auxQuery = query.replace("AUTODATE", dateString)
        data = getData(connection, auxQuery, ticker)
        if data[1] != []:
            break

    if data[1] != []:
        # Vacio. Ir hacia la izquierda de arreglo
        return binarySearchFirstEntry(connection, ticker, query, initDate, middleDate, threshold)
    else:
        # No mínimo. Ir hacia la derecha de arreglo
        return binarySearchFirstEntry(connection, ticker, query, middleDate, endDate, threshold)

def dateToString(date):
    return date.strftime("%Y-%m-%d")

def getLastPortfolioOfMonth(connection, ticker, date, query):
    portfolio = [[], []]
    i = 0
    while portfolio[1] == [] and i < 45:
        auxDate = date - td(days=i)
        dateStr = dateToString(auxDate)
        auxQuery = query.replace("AUTODATE", dateStr)
        try:
            portfolio = getData(connection, auxQuery, ticker)
        except:
            portfolio = []
        i += 1
    return portfolio

# FIXME REFACTOR Menos acoplamiento entre portfolioCompositionTimeSeries y getLastPortfolioOfMonth
def portfolioCompositionTimeSeries(connection, ticker, initDate, endDate, query):
    totals = []
    threshold = 5
    minDate = binarySearchFirstEntry(connection, ticker, query, initDate, endDate, threshold)
    delta = endDate - minDate
    dates = []
    # NOTE: empieza desde 1 para no contar primer dia
    for i in range(1, delta.days + 1):
        dates.append(minDate + td(days=i))

    samples = pd.DataFrame(dates, columns=["Date"])
    samples = samples.set_index("Date")
    samples = samples.resample('M').last()
    samples.reset_index(drop=False, inplace=True)
    samples.drop(0, inplace=True)

    # Para encontrar index una sola vez:
    # NOTE: Primer portafolio no  es necesariamente el ultimo dia del mes. Se suma threshold porque
    #       si o si dato tiene que estar en ese rango
    firstPortfolio = getLastPortfolioOfMonth(connection, ticker, (minDate + td(days=threshold)), query)
    if firstPortfolio[1] == []:
        return totals
    firstPortfolio = subclassify(firstPortfolio)

    assetClassIndex = firstPortfolio[0].index(ASSETCLASS)
    currencyIndex = firstPortfolio[0].index(MONEDA)
    zoneIndex = firstPortfolio[0].index(ZONA)
    amountIndex = firstPortfolio[0].index(MONTO)

    assetClassTotals = totalPerType(assetClassIndex, amountIndex, firstPortfolio[1])
    currencyTotals = totalPerType(currencyIndex, amountIndex, firstPortfolio[1])
    zoneTotals = totalPerType(zoneIndex, amountIndex, firstPortfolio[1])

    totals.append([minDate.date(), assetClassTotals, currencyTotals, zoneTotals])

    wrongClassifications = []
    # ERROR: El error esta dentro de este for
    for index, row in samples.iterrows():
        date = row['Date']
        monthPortfolio = getLastPortfolioOfMonth(connection, ticker, date, query)
        if monthPortfolio[1] == []:
            return []
        monthPortfolio = subclassify(monthPortfolio)
        wrong = list(filter(lambda x: x[assetClassIndex] == 'NC', monthPortfolio[1]))
        wrongClassifications.extend(wrong)
        assetClassTotals = totalPerType(assetClassIndex, amountIndex, monthPortfolio[1])
        currencyTotals = totalPerType(currencyIndex, amountIndex, monthPortfolio[1])
        zoneTotals = totalPerType(zoneIndex, amountIndex, monthPortfolio[1])

        totals.append([date, assetClassTotals, currencyTotals, zoneTotals])

    wrongClassifications = list(set(wrongClassifications))
    return (totals, wrongClassifications)

'''
    UTILIDAD: Se utiliza dentro de la parte de "except" en un "try/except". Imprime un error y sale
    del programa

    NOTA: Idealmente contener excepcion de python junto con mensaje para mayor matnenibilidad
'''
def errorHandler(workbook, message):
    workbook.app.screen_updating = True
    print(message)

'''
    UTILIDAD: Devuelve las tuplas de los últimos N dias. Puede haber mas de una tupla por dia
'''
def getLastNDays(matrix, days):
    tuples = []

    dateFormat = "%Y" + "-" + "%m" + "-" + "%d"
    dateIndex = matrix[0].index(FECHA)
    firstDate = matrix[1][0][dateIndex]
    a = datetime.strptime(firstDate, dateFormat)

    for i in range(0, len(matrix[1])):
        currentDate = matrix[1][i][dateIndex]
        b = datetime.strptime(currentDate, dateFormat)
        delta = a - b
        if delta.days <= days:
            tuples.append(matrix[1][i])
        else:
            break
    return (matrix[0], tuples)

'''
    UTILIDAD: Obtener datos de anio especifidcado
'''
def getYearTuples(data, year, dateIndex):
    return [x for x in data if x[dateIndex].year == year]

'''
    UTILIDAD: Suma y resta movimientos de Ingreso y Rescates
'''
def addMovements(movements):
    positive = 0
    negative = 0
    inOutIndex = movements[0].index(TIPOMOVIMIENTO)
    amountIndex = movements[0].index(MONTO)

    for movement in movements[1]:
        if movement[inOutIndex] == 'R': # R = Rescate, I = Ingreso
            negative += movement[amountIndex]
        else:
            positive += movement[amountIndex]

    return (positive, negative)


'''
    ********************************************
    ************** DATA PRINTS *****************
    ********************************************
'''

'''
    UTILIDAD: Imprime el resumen de cartera pero con etiqueta extra para generacion de graficos
    en Excel
'''
def printLabeledSummary(workbook, sheet, totals):
    print("Imprimiendo resumen de cartera con etiquetas")
    column = 1
    sheet = sheet + "Label"
    for total in totals:
        row = 2
        Mesa.pasteValXl(workbook, sheet, row - 1, column + 1, "%")
        for key in total:
            label = ""
            if key is not None:
                label = key + " - " + str(round(total[key][1], 3) * 100) + "%"
            else:
                label = "NULL - " + str(round(total[key][1], 3) * 100) + "%"
            Mesa.pasteValXl(workbook, sheet, row, column, label)
            Mesa.pasteValXl(workbook, sheet, row, column + 1, total[key][1])
            row += 1
        column += 3

'''
    UTILIDAD: Imprime las carteras de manera desglosada en cada pagina segun corresponda
'''
def printPortfolioSummary(workbook, sheet, portfolio, RFL):
    print("Imprimiendo resumen de portafolio")
    amountIndex = portfolio[0].index(MONTO)
    column = 1
    totals = []
    labels = []

    if RFL is False:
        # % por clase de activo
        assetClassIndex = portfolio[0].index(ASSETCLASS)
        assetClassTotals = totalPerType(assetClassIndex, amountIndex, portfolio[1])
        totals.append(assetClassTotals)
        labels.append(ASSETCLASS)

        # % por subclase de activos
        subclassIndex = portfolio[0].index(SUBCLASS)
        subclassTotals = totalPerType(subclassIndex, amountIndex, portfolio[1])
        totals.append(subclassTotals)
        labels.append(SUBCLASS)

        # % por sector
        sectorIndex = portfolio[0].index(SECTOR)
        sectorTotals = totalPerType(sectorIndex, amountIndex, portfolio[1])
        totals.append(sectorTotals)
        labels.append(SECTOR)

        # % por emisor
        emmitterIndex = portfolio[0].index(NOMBREEMISOR)
        emmitterTotals = totalPerType(emmitterIndex, amountIndex, portfolio[1])
        totals.append(emmitterTotals)
        labels.append(NOMBREEMISOR)

        # % por tipo de instrumento
        instrumentTypeIndex = portfolio[0].index(TIPOINSTRUMENTO)
        instrumentTypeTotals = totalPerType(instrumentTypeIndex, amountIndex, portfolio[1])
        totals.append(instrumentTypeTotals)
        labels.append(TIPOINSTRUMENTO)

    else:
        # % por Riesgo_Duracion_Moneda
        RDMIndex = portfolio[0].index(RIESGODURACIONMONEDA)
        RDMTotals = totalPerType(RDMIndex, amountIndex, portfolio[1])
        totals.append(RDMTotals)
        labels.append(RIESGODURACIONMONEDA)

        # % por Riesgo_Duracion
        RDIndex = portfolio[0].index(RIESGODURACION)
        RDTotals = totalPerType(RDIndex, amountIndex, portfolio[1])
        totals.append(RDTotals)
        labels.append(RIESGODURACION)

        # % por Duracion_Moneda
        DMIndex = portfolio[0].index(DURACIONMONEDA)
        DMTotals = totalPerType(DMIndex, amountIndex, portfolio[1])
        totals.append(DMTotals)
        labels.append(DURACIONMONEDA)

        # % por TipoInstrumento_Largo
        TLIndex = portfolio[0].index(TIPOINSTRUMENTOLARGO)
        TLTotals = totalPerType(TLIndex, amountIndex, portfolio[1])
        totals.append(TLTotals)
        labels.append(TIPOINSTRUMENTOLARGO)

        # % por TipoInstrumento_Moneda
        TMIndex = portfolio[0].index(TIPOINSTRUMENTOMONEDA)
        TMTotals = totalPerType(TMIndex, amountIndex, portfolio[1])
        totals.append(TMTotals)
        labels.append(TIPOINSTRUMENTOMONEDA)

        # % por Duracion
        DIndex = portfolio[0].index(CORTOLARGO)
        DTotals = totalPerType(DIndex, amountIndex, portfolio[1])
        totals.append(DTotals)
        labels.append(CORTOLARGO)

        # % por Riesgo
        RIndex = portfolio[0].index(RIESGO)
        RTotals = totalPerType(RIndex, amountIndex, portfolio[1])
        totals.append(RTotals)
        labels.append(RIESGO)

        # % por TipoInstrumento
        TIndex = portfolio[0].index(TIPOINSTRUMENTO)
        TTotals = totalPerType(TIndex, amountIndex, portfolio[1])
        totals.append(TTotals)
        labels.append(TIPOINSTRUMENTO)

        # % por Clasificacion de Riesgo
        CRIndex = portfolio[0].index(CLASIFICACIONRIESGO)
        CRTotals = totalPerType(CRIndex, amountIndex, portfolio[1])
        totals.append(CRTotals)
        labels.append(CLASIFICACIONRIESGO)

        # % por Moneda
        MIndex = portfolio[0].index(MONEDA)
        MTotals = totalPerType(MIndex, amountIndex, portfolio[1])
        totals.append(MTotals)
        labels.append(MONEDA)

    for total in totals:
        row = 2
        Mesa.pasteValXl(workbook, sheet, row - 1, column + 1, "Monto")
        Mesa.pasteValXl(workbook, sheet, row - 1, column + 2, "%")
        sortedTotal = sorted(total.items(), key=lambda e: e[1][0], reverse=True)
        for key in sortedTotal:
            Mesa.pasteValXl(workbook, sheet, row, column, key[0])
            Mesa.pasteValXl(workbook, sheet, row, column + 1, key[1])
            row += 1
        column += 4

    return [labels, totals]

'''
    UTILIDAD: Imprime para las hojas RFL, RVL, RFI y RVI las tablas de instrumentos
    separadas por subclases

    USO: Se le entregan los titulos de la tabla de la cartera y una division por clase (RFL, RVL,
    RFI o RVI) de la cartera
'''
def printSubportfolios(sheet, workbook, subportfolio, portfolioHeaders):
    column = 1
    row = 2
    assetsBySubclass = assetClassBreakdown(portfolioHeaders, subportfolio)

    emmitterIndex = portfolioHeaders.index(NOMBREEMISOR)
    subclassIndex = portfolioHeaders.index(SUBCLASS)
    currencyIndex = portfolioHeaders.index(MONEDA)
    durationIndex = portfolioHeaders.index(DURATIONHEADER)
    rateIndex = portfolioHeaders.index(TASA)
    riskIndex = portfolioHeaders.index(RIESGO)
    amountIndex = portfolioHeaders.index(MONTO)
    percentageIndex = portfolioHeaders.index(PORCENTAJE)
    assetClassIndex = portfolioHeaders.index(ASSETCLASS)
    instrumentIndex = portfolioHeaders.index(NOMBREINSTRUMENTO)
    sectorIndex = portfolioHeaders.index(SECTOR)
    quantityIndex = portfolioHeaders.index(CANTIDAD)
    priceIndex = portfolioHeaders.index(PRECIO)

    if subportfolio != []:
        # assetsBySubclass se entrega como diccionario
        if subportfolio[0][assetClassIndex] == "Renta Fija Local":
            headersIndexes = [emmitterIndex,
                              subclassIndex,
                              riskIndex,
                              currencyIndex,
                              durationIndex,
                              rateIndex,
                              amountIndex,
                              percentageIndex]
        elif subportfolio[0][assetClassIndex] == "Renta Variable Local":
            headersIndexes = [instrumentIndex,
                              sectorIndex,
                              priceIndex,
                              quantityIndex,
                              amountIndex,
                              percentageIndex]
        # NOTE: Si esta mal subclasificado, devolver todos los campos
        elif subportfolio[0][assetClassIndex] == "NC":
            headersIndexes = range(0, len(subportfolio[0]))
        else:
            headersIndexes = [instrumentIndex,
                              subclassIndex,
                              currencyIndex,
                              priceIndex,
                              quantityIndex,
                              amountIndex,
                              percentageIndex]

        headers = extractSubmatrix([portfolioHeaders], headersIndexes)

        # Se entrega como diccionario
        for key in assetsBySubclass:
            relevantInformation = extractSubmatrix(assetsBySubclass[key], headersIndexes)
            Mesa.pasteValXl(workbook, sheet, row, column, key)
            Mesa.pasteColXl(workbook, sheet, row + 1, column, headers)
            print("Imprimiendo subportafolio " + key)
            # GROUP BY SOBRE ESTO
            topLeftCorner = numberToExcelColumnString(column)
            sht = workbook.sheets[sheet]
            sht.range(topLeftCorner + str(row + 2)).value = relevantInformation
            column += len(headers[0]) + 1

'''
    UTILIDAD: Imprimir movimientos a hoja correspondiente
'''
def printMovements(workbook, movements):
    print("Imprimiendo movimientos de cartera:")
    topLeftCorner = numberToExcelColumnString(2) + str(3)
    workbook.sheets[MOVIMIENTOS].range(topLeftCorner).value = movements[1]
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 3 + len(movements[1]), 2, "Ingresos Totales")
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 4 + len(movements[1]), 2, "Rescates Totales")
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 5 + len(movements[1]), 2, "Saldo")
    totals = addMovements(movements)
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 3 + len(movements[1]), 3, totals[0])
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 4 + len(movements[1]), 3, totals[1])
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 5 + len(movements[1]), 3, totals[0] - totals[1])

    lastMonth = getLastNDays(movements, 30)
    topLeftCorner = numberToExcelColumnString(7) + str(3)
    workbook.sheets[MOVIMIENTOS].range(topLeftCorner).value = lastMonth[1]
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 3 + len(lastMonth[1]), 7, "Ingresos Totales")
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 4 + len(lastMonth[1]), 7, "Rescates Totales")
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 5 + len(lastMonth[1]), 7, "Saldo")
    lastMonthTotals = addMovements(lastMonth)
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 3 + len(lastMonth[1]), 8, lastMonthTotals[0])
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 4 + len(lastMonth[1]), 8, lastMonthTotals[1])
    Mesa.pasteValXl(workbook, MOVIMIENTOS, 5 + len(lastMonth[1]), 8, lastMonthTotals[0] - lastMonthTotals[1])


'''
    UTILIDAD: Imprimir todo lo posible desde los datos de retorno a la planilla
    Excel.

    USO: Entregar planilla abierta y datos sin procesar de valores de cartera y
    benchmark de la forma (Excel, [[fecha, valor cartera/fondo, valor benchmark]])
'''
def printDataToExcel(workbook, data):
    # Imprimir datos iniciales
    sht = workbook.sheets['Datos']
    try:
        print("Imprimiendo datos de serie\n")
        sht.range('A4').value = data
    except BaseException:
        errorHandler(workbook, "ERROR: No se puede imprimir datos en hoja")

    # Calcular e imprimir retornos mensuales
    try:
        print("Calculando e imprimiendo retornos mensuales en hoja 'Datos'\n")
        returns = calculateReturns(data)
        sht.range('E4').value = returns[0]
    except BaseException:
        errorHandler(workbook, "ERROR: No se pudo calcular retornos mensuales")

    # Calcular e imprimir retornos anuales
    try:
        print("Calculando e imprimiendo retornos anuales en hoja 'Datos'\n")
        sht.range('I4').value = returns[1]
    except BaseException:
        errorHandler(workbook, "ERROR: No se pudo calcular retornos anuales")

    # TODO agregar estadisticas y titulos

'''
    UTILIDAD: Calcula e imprime las estadisticas sobre los datos de valores cuota
'''
def printStatistics(workbook, sheet, data, year1, year2):
    print("Imprimiendo estadísticas:")
    row = 3
    column = 14
    dataset = [data[0], []]

    # 12 meses
    print(">>> Estadísticas 12 meses:")
    dataset[1] = extractByTimedelta(data[1], 365, 0)
    if len(dataset[1]) > 0:
        stats = getStatistics(dataset)
        Mesa.pasteValXl(workbook, sheet, row, column, stats["alpha"])
        Mesa.pasteValXl(workbook, sheet, row + 1, column, stats["beta"])
        Mesa.pasteValXl(workbook, sheet, row + 2, column, stats["tracking_error"])
        Mesa.pasteValXl(workbook, sheet, row + 3, column, stats["r_squared"])
        Mesa.pasteValXl(workbook, sheet, row + 4, column, stats["portfolio_volatility"])
        Mesa.pasteValXl(workbook, sheet, row + 5, column, stats["benchmark_volatility"])
        print(">>>>> OK")
    else:
        print(">>>>> No Data")

    # 24 meses
    print(">>> Estadísticas 24 meses:")
    dataset[1] = extractByTimedelta(data[1], 365 * 2, 0)
    if len(dataset[1]) > 0:
        stats = getStatistics(dataset)
        Mesa.pasteValXl(workbook, sheet, row, column + 1, stats["alpha"])
        Mesa.pasteValXl(workbook, sheet, row + 1, column + 1, stats["beta"])
        Mesa.pasteValXl(workbook, sheet, row + 2, column + 1, stats["tracking_error"])
        Mesa.pasteValXl(workbook, sheet, row + 3, column + 1, stats["r_squared"])
        Mesa.pasteValXl(workbook, sheet, row + 4, column + 1, stats["portfolio_volatility"])
        Mesa.pasteValXl(workbook, sheet, row + 5, column + 1, stats["benchmark_volatility"])
        print(">>>>> OK")
    else:
        print(">>>>> No Data")
    # 36 meses
    print(">>> Estadísticas 36 meses:")
    dataset[1] = extractByTimedelta(data[1], 365 * 3, 0)
    if len(dataset[1]) > 0:
        stats = getStatistics(dataset)
        Mesa.pasteValXl(workbook, sheet, row, column + 2, stats["alpha"])
        Mesa.pasteValXl(workbook, sheet, row + 1, column + 2, stats["beta"])
        Mesa.pasteValXl(workbook, sheet, row + 2, column + 2, stats["tracking_error"])
        Mesa.pasteValXl(workbook, sheet, row + 3, column + 2, stats["r_squared"])
        Mesa.pasteValXl(workbook, sheet, row + 4, column + 2, stats["portfolio_volatility"])
        Mesa.pasteValXl(workbook, sheet, row + 5, column + 2, stats["benchmark_volatility"])
        print(">>>>> OK")
    else:
        print(">>>>> No Data")
    # Inicio
    try:
        print(">>> Estadísticas desde fecha inicial:")
        dataset[1] = data[1]
        stats = getStatistics(dataset)
        Mesa.pasteValXl(workbook, sheet, row, column + 3, stats["alpha"])
        Mesa.pasteValXl(workbook, sheet, row + 1, column + 3, stats["beta"])
        Mesa.pasteValXl(workbook, sheet, row + 2, column + 3, stats["tracking_error"])
        Mesa.pasteValXl(workbook, sheet, row + 3, column + 3, stats["r_squared"])
        Mesa.pasteValXl(workbook, sheet, row + 4, column + 3, stats["portfolio_volatility"])
        Mesa.pasteValXl(workbook, sheet, row + 5, column + 3, stats["benchmark_volatility"])
        print(">>>>> OK")
    except Exception:
        print(">>>>> No Data")

    # Anios de calendario
    for y in range(year1, year2 + 1):
        try:
            print(">>> Estadísticas anio " + str(y) +":")
            column += 1
            dataset[1] = getYearTuples(data[1], y, 0)
            stats = getStatistics(dataset)
            Mesa.pasteValXl(workbook, sheet, row - 1, column + 3, y)
            Mesa.pasteValXl(workbook, sheet, row, column + 3, stats["alpha"])
            Mesa.pasteValXl(workbook, sheet, row + 1, column + 3, stats["beta"])
            Mesa.pasteValXl(workbook, sheet, row + 2, column + 3, stats["tracking_error"])
            Mesa.pasteValXl(workbook, sheet, row + 3, column + 3, stats["r_squared"])
            Mesa.pasteValXl(workbook, sheet, row + 4, column + 3, stats["portfolio_volatility"])
            Mesa.pasteValXl(workbook, sheet, row + 5, column + 3, stats["benchmark_volatility"])
            print(">>>>> OK")
        except Exception:
            print(">>>>> No Data")

'''
    UTILIDAD: Imprime informacion de cartera/fondo a planilla Excel
'''
def printPortfolioToExcel(workbook, sheet, portfolio):
    # Imprimir cartera completa
    try:
        print("Imprimiendo cartera completa\n")
        i = 1
        for header in portfolio[0]:
            Mesa.pasteValXl(workbook, sheet, 1, i, header)
            i += 1
        sht = workbook.sheets[sheet]
        sht.range('A2').value = portfolio[1]
    except BaseException:
        errorHandler(workbook, "ERROR: No se ha podido imprimir cartera")

def printPortfolioInfo(workbook, info):
    RUNIndex = info[0].index("Run")
    info[1][0] = list(info[1][0])
    info[1][0][RUNIndex] = str(info[1][0][RUNIndex]) + " - " + str(verificadorRUT(info[1][0][RUNIndex]))
    try:
        Mesa.pasteColXl(workbook, SEGUIMIENTO, 2, 3, list(info[1][0]))
    except BaseException:
        errorHandler(workbook, "ERROR: No se ha impreso informacion de la cartera")

'''
    LOGICA: PRIMERO ENCONTRAR LAS LLAVES DE CADA
'''
def printPortfolioEvolution(workbook, evolution):
    # NOTE: Primero pasar evolucion a forma matricial, luego imprimir en Excel
    # ----------------- A FORMA MATRICIAL -----------------
    print("Imprimiendo Evolucion de Cartera")
    assetClassKeys = []
    currencyKeys = []
    zoneKeys = []

    # NOTE: Obtener todas las llaves de los diccionarios. En casos donde hay 0%, este no aparece en
    #       ese diccionario y por lo tanto hay que agarrarlos todos antes de iterar
    for month in evolution:
        assetClassKeys.extend(list(month[1].keys()))
        currencyKeys.extend(list(month[2].keys()))
        zoneKeys.extend(list(month[3].keys()))

    assetClassKeys = list(set(assetClassKeys))
    currencyKeys = list(set(currencyKeys))
    zoneKeys = list(set(zoneKeys))

    evolutionMatrix = []

    for month in evolution:
        # Add date
        evolutionRow = (month[0], [], [], [])

        # AssetClass Composition
        for key in assetClassKeys:
            value = month[1].get(key, [None, 0])
            evolutionRow[1].append(value[1])

        # Currency Composition
        for key in currencyKeys:
            value = month[2].get(key, [None, 0])
            evolutionRow[2].append(value[1])

        # Zone Composition
        for key in zoneKeys:
            value = month[3].get(key, [None, 0])
            evolutionRow[3].append(value[1])
        evolutionMatrix.append(evolutionRow)

    # --------------------- IMPRIMIR EN EXCEL ---------------------
    column = 1
    ROW = 3

    dates = extractSubmatrix(evolutionMatrix, [0])

    # assetClass evolution
    topLeftCorner = numberToExcelColumnString(column) + str(ROW)
    workbook.sheets[DATAEVOLUCION].range(topLeftCorner).value = dates
    assetClassEvolution = extractSubmatrix(evolutionMatrix, [1])
    categories = len(assetClassEvolution[0][0])
    for i in range(0, categories):
        if assetClassKeys[i] is not None:
            Mesa.pasteValXl(workbook, DATAEVOLUCION, ROW - 1, column + 1 + i, assetClassKeys[i])
        else:
            Mesa.pasteValXl(workbook, DATAEVOLUCION, ROW - 1, column + 1 + i, "NULL")

    assetClassEvolutionPrint = list(itertools.chain.from_iterable(assetClassEvolution))
    topLeftCorner = numberToExcelColumnString(column + 1) + str(ROW)
    workbook.sheets[DATAEVOLUCION].range(topLeftCorner).value = assetClassEvolutionPrint

    charts = workbook.sheets[EVOLUCION].charts
    topLeftCorner = numberToExcelColumnString(column)
    charts[0].set_source_data(
        workbook.sheets[DATAEVOLUCION].range(topLeftCorner + str(ROW - 1)).expand())


    # Currency evolution
    column += 3 + len(assetClassEvolution[0][0])
    topLeftCorner = numberToExcelColumnString(column) + str(ROW)
    workbook.sheets[DATAEVOLUCION].range(topLeftCorner).value = dates
    currencyEvolution = extractSubmatrix(evolutionMatrix, [2])
    categories = len(currencyEvolution[0][0])
    for i in range(0, categories):
        if currencyKeys[i] is not None:
            Mesa.pasteValXl(workbook, DATAEVOLUCION, ROW - 1, column + 1 + i, currencyKeys[i])
        else:
            Mesa.pasteValXl(workbook, DATAEVOLUCION, ROW - 1, column + 1 + i, "NULL")
    currencyEvolutionPrint = list(itertools.chain.from_iterable(currencyEvolution))
    topLeftCorner = numberToExcelColumnString(column + 1) + str(ROW)
    workbook.sheets[DATAEVOLUCION].range(topLeftCorner).value = currencyEvolutionPrint

    charts = workbook.sheets[EVOLUCION].charts
    topLeftCorner = numberToExcelColumnString(column)
    charts[1].set_source_data(
        workbook.sheets[DATAEVOLUCION].range(topLeftCorner + str(ROW - 1)).expand())

    # Zone evolution
    column += 3 + len(currencyEvolution[0][0])
    topLeftCorner = numberToExcelColumnString(column) + str(ROW)
    workbook.sheets[DATAEVOLUCION].range(topLeftCorner).value = dates
    zoneEvolution = extractSubmatrix(evolutionMatrix, [3])
    categories = len(zoneEvolution[0][0])
    for i in range(0, categories):
        if zoneKeys[i] is not None:
            Mesa.pasteValXl(workbook, DATAEVOLUCION, ROW - 1, column + 1 + i, zoneKeys[i])
        else:
            Mesa.pasteValXl(workbook, DATAEVOLUCION, ROW - 1, column + 1 + i, "NULL")
    zoneEvolutionPrint = list(itertools.chain.from_iterable(zoneEvolution))
    topLeftCorner = numberToExcelColumnString(column + 1) + str(ROW)
    workbook.sheets[DATAEVOLUCION].range(topLeftCorner).value = zoneEvolutionPrint

    charts = workbook.sheets[EVOLUCION].charts
    topLeftCorner = numberToExcelColumnString(column)

    charts[2].set_source_data(
        workbook.sheets[DATAEVOLUCION].range(topLeftCorner + str(ROW - 1)).expand())


'''
    UTILIDAD: Genera los graficos de torta de las composiciones de las
    carteras segun distintos criterios

    NOTA: Los graficos de torta se portan mal si no se especifica bien
    el rango de datos de antemano. Por ello, estos graficos se hacen a
    traves de Python. EL resto de los graficos (linea y barra) se dejaron
    armados en el Excel mismo adjunto a este archivo
'''
def printPortfolioCompositionPies(workbook, sheet, datasourceSheet, piesAmount, lastIndex):
    print("Imprimiendo gráficos de torta")
    charts = workbook.sheets[sheet].charts
    for i in range(0, piesAmount): # TODO: revisar valores limite
        topLeftCorner = numberToExcelColumnString(1 + 3*i)
        charts[lastIndex + i].set_source_data(
            workbook.sheets[datasourceSheet + 'Label'].range(topLeftCorner + "1").expand())
    return lastIndex

def printBenchmarkComparison(workbook, sheet, portfolioComposition, benchmComposition, column):
    portfAssetClassIndex = portfolioComposition[0].index(ASSETCLASS)
    benchmAssetClassIndex = benchmComposition[0].index(ASSETCLASS)
    benchmWeight = benchmComposition[0].index("Weight")

    portfAssetClassComposition = portfolioComposition[1][portfAssetClassIndex]

    comparedTotals = []
    portfKeys = list(portfAssetClassComposition.keys())

    # Unir categorias observadas en benchmark con las del portafolio
    for i in benchmComposition[1]:
        assetClass = i[benchmAssetClassIndex]
        if assetClass in portfKeys:
            assetClassTotal = [assetClass,
                               portfAssetClassComposition[assetClass][0],
                               portfAssetClassComposition[assetClass][1]]
        else:
            assetClassTotal = [assetClass,
                               0,
                               0]
        assetClassTotal.extend([i[benchmWeight]])
        comparedTotals.append(assetClassTotal)

    # Agregar categorias no persentes en benchmark como 0
    for key in portfAssetClassComposition:
        if key not in set(np.column_stack(comparedTotals)[0]):
            assetClassTotal = [key,
                               portfAssetClassComposition[key][0],
                               portfAssetClassComposition[key][1],
                               0]
            comparedTotals.append(assetClassTotal)

    topLeftCorner = numberToExcelColumnString(column) + str(3)
    workbook.sheets[sheet].range(topLeftCorner).value = comparedTotals
