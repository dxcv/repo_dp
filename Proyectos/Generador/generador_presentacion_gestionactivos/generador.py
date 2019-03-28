# COMENTARIO DE PRUEBA

# TODO: Borrar siguiente linea al finalizar
# TODO: Descomentar los print
# pylint: disable-msg=C0103,C0111

import tkinter as tk
from tkinter import filedialog
import numpy as np
import os
import sys
import datetime
import time

import seguimientoLib as Seguimiento
sys.path.insert(0, '../libreria/')
import libreria_fdo as Mesa

#  ----------------- Constantes de Programa -----------------
'''
    NOTA: Con modificar las constantes a continuacion es posible adaptarse a posibles cambios en
    bases de datos, Excel que acompaña a este archivo, etc.
'''
# Lectura archivo Excel para parametros iniciales
PARAMETERSBEGIN = "B2"
PARAMETERSEND = "B6"
READSHEET = "Control"

# Conexión a Base de Datos en Puyehue
SERVER = "Puyehue"
DATABASE = "MesaInversiones"
USER = "usrConsultaComercial"
PSWD = "Comercial1w"
TIMEOUT = 100

# Clasificacion de Instrumentos
# NOTE: Si se cambia como se definen Corto y Largo para los instrumentos, basta
#       cambiar el valor de DURATION a continuacion
DURATION = 5    # DURATION > 5 largo, DURATION <= 5 corto

# Queries
BENCHMARKCOMPOSITION = "./queries_generador/benchmarkComposition.sql"
BENCHMARKDATEVALUE = "./queries_generador/benchmarkDateValue.sql"
BENCHMARKFIRSTDATE = "./queries_generador/benchmarkFirstDate.sql"
BENCHMARKNAMEQUERY = "./queries_generador/benchmarkName.sql"
CHECKMULTIPLESERIES = "./queries_generador/checkMultipleSeries.sql"
DATAQUERY = "./queries_generador/getRawDataQuery.sql"
DATAWITHSERIES = "./queries_generador/dataWithSeries.sql"
MOVEMENTSQUERY = "./queries_generador/movements.sql"
MOVEMENTSSERIES = "./queries_generador/movementsSeries.sql"
PORTFOLIOFIRSTDATE = "./queries_generador/portfolioFirstDate.sql"
PORTFOLIOSERIESFIRSTDATE = "./queries_generador/portfolioFirstDateSeries.sql"
PORTFOLIODATE = "./queries_generador/portfolioDateValue.sql"
PORTFOLIOHISTORY = "./queries_generador/getPortfolioHistoric.sql"
PORTFOLIONONRECURSIVE = "./queries_generador/getPortfolioNonRecursive.sql"
PORTFOLIOQUERY = "./queries_generador/getPortfolio.sql"
PORTFOLIOINFOQUERY = "./queries_generador/portfolioInfo.sql"
PORTFOLIOINFOSERIES = "./queries_generador/portfolioInfoSeries.sql"


# Hojas Excel
CARTERACOMPLETA = "CarteraCompleta"
CARTERACOMPLETANR = "CarteraCompletaNoRecursiva"
CARTERANEUTRAL = "Cartera-Neutral"
CARTERARFL = "CarteraRFL"
CARTERARVL = "CarteraRVL"
CARTERARFI = "CarteraRFI"
CARTERARVI = "CarteraRVI"
DATOS = "Datos"
MALCLASIFICADOS = "MalClasificados"
MOVIMIENTOS = "Movimientos"
RESUMENCARTERA = "ResumenCartera"
RESUMENCARTERARF = "ResumenCarteraRF"
SEGUIMIENTO = "SEGUIMIENTO"

def resource_path(relative_path):
    # Production
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    # Development
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    # Abrir archivo Excel con dialogo
    # NOTE descomentar las 4 de abajo de esta y borrar la apertura hardcodeada
    try:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename()
        workbook = Mesa.openWorkbook(filePath, False, True)
    except BaseException:
        print("ERROR: No es posible abrir archivo")
        sys.exit(0)

    start = time.time()

    # Leer en hoja "Control" las siguiente celdas:
        # *** Control!B2 ---> Cliente/fondo ***
        # *** Control!B3 ---> Fecha Inicio  ***
        # *** Control!B4 ---> Fecha Fin     ***
        # *** Control!B5 ---> Serie         ***
        # *** Control!B6 ---> Lista         ***
    parameters = Mesa.getColumnXl(workbook, READSHEET, PARAMETERSBEGIN, PARAMETERSEND)
        # parameters = [fondo, fechaInicio, fechaFin, serie, lista]

    # Abrir conexión a Base de Datos Puyehue
    try:
        connection = Mesa.connectDatabaseUserTimeout(SERVER, DATABASE, USER, PSWD, TIMEOUT)
    except BaseException:
        print("ERROR: No ha sido posible conectar con servidor")
        sys.exit(0)


    # Verificar que serie sea unica o no para codigo
    query = Mesa.extractTextFile(resource_path(CHECKMULTIPLESERIES))
    multipleSeriesPortfolios = Seguimiento.getData(connection, query, (parameters[2]))
    multipleSeriesPortfolios = set(np.column_stack(multipleSeriesPortfolios[1])[0])

    # Generar booleano para determinar cuando usar queries para multiples series o no
    singleSerie = True if parameters[0] not in multipleSeriesPortfolios else False

    # Datos de rentabilidad de cartera y benchmark. Hoja 'Datos'
    # NOTE: PRIMERO AJUSTAR VALORES DE BENCHMARK POR MEDIO DE MULTIPLICADOR
    query = Mesa.extractTextFile(resource_path(BENCHMARKFIRSTDATE))
    query = query.replace('FONDO', parameters[0])
    benchmarkFirstDate = Seguimiento.getData(connection, query, (""))
    if singleSerie:
        query = Mesa.extractTextFile(resource_path(PORTFOLIOFIRSTDATE))
    else:
        query = Mesa.extractTextFile(resource_path(PORTFOLIOSERIESFIRSTDATE))
        query = query.replace("PLACESERIE", parameters[3])
    query = query.replace("FONDO", parameters[0])
    portfolioFirstDate = Seguimiento.getData(connection, query, (parameters[0]))
    # NOTE: a partir de primera fecha comun a todos (consulta, primera de cartera y primera
    #       de benchmark) se pueden hacer los queries

    # Encontrar primera fecha en que todos existen
    firstDateIntersection = max([parameters[1], portfolioFirstDate[1][0][0], benchmarkFirstDate[1][0][0]])

    # Cambiar valor de fecha inicial en Excel:
    Mesa.pasteValXl(workbook, READSHEET, 3, 2, firstDateIntersection)

    # Obtener primeros valores de portafolio y benchmark
    if singleSerie:
        query = Mesa.extractTextFile(resource_path(PORTFOLIODATE)).replace("FONDO", parameters[0])
    else:
        query = Mesa.extractTextFile(resource_path(PORTFOLIODATE))
        query = query.replace("FONDO", parameters[0])
        query = query.replace("PLACESERIE", parameters[3])
    firstPortfolioValue = (Seguimiento.getData(connection, query, (firstDateIntersection)))[1][0][0]
    query = Mesa.extractTextFile(resource_path(BENCHMARKDATEVALUE)).replace("FONDO", parameters[0])
    firstBenchmarkValue = (Seguimiento.getData(connection, query, (firstDateIntersection)))[1][0][0]

    # Obtener datos de serie
    dataParameters = (firstPortfolioValue, firstBenchmarkValue, firstDateIntersection, parameters[2])

    if singleSerie:
        query = Mesa.extractTextFile(resource_path(DATAQUERY))
        query = query.replace("FONDO", parameters[0])
    else:
        query = Mesa.extractTextFile(resource_path(DATAWITHSERIES))
        query = query.replace("FONDO", parameters[0])
        query = query.replace("PLACESERIE", parameters[3])
    data = Seguimiento.getData(connection, query, dataParameters)
    if data[1] == []:
        Seguimiento.errorHandler(workbook, "No se han encontrado datos para el fondo y fechas especificadas")
    Seguimiento.printDataToExcel(workbook, data[1])
    Seguimiento.printStatistics(workbook, DATOS, data, firstDateIntersection.year, parameters[2].year)
    Seguimiento.getStatistics(data)

    # Evolucion de cartera en el tiempo
    initDate = portfolioFirstDate[1][0][0]
    endDate = parameters[2]
    query = Mesa.extractTextFile(resource_path(PORTFOLIOHISTORY))
    try:
        timeSeries = Seguimiento.portfolioCompositionTimeSeries(connection, parameters[0], initDate, endDate, query)

        evolution = timeSeries[0]
        wrongClassifications = timeSeries[1]
        if evolution != []:
            Seguimiento.printPortfolioEvolution(workbook, evolution)
        else:
            print("No existen datos para generar una evolucion de portafolio")
    except BaseException:
        print("ERROR: Evolucion de cartera no impresa")

    date = Seguimiento.dateToString(parameters[2])

    try:
        # Fondos en cartera. Cartera Completa
        portfolioParameters = (parameters[0])
        query = Mesa.extractTextFile(resource_path(PORTFOLIOQUERY)).replace("AUTODATE", date)
        portfolio = Seguimiento.getData(connection, query, portfolioParameters)
    except BaseException:
        print("Error de lectura de base de datos")

    # Subclasificar fondos en cartera
    if portfolio[0] != []:
        portfolio = Seguimiento.subclassify(portfolio)
        Seguimiento.printPortfolioToExcel(workbook, CARTERACOMPLETA, portfolio)
        portfoliosByAssetClass = Seguimiento.portfolioBreakdown(portfolio)
    else:
        print("Cartera no leida desde base de datos")

    # Imprimir hojas de subcarteras
    try:
        Seguimiento.printSubportfolios(CARTERARFL, workbook,
                                       portfoliosByAssetClass[0], portfolio[0])
        Seguimiento.printSubportfolios(CARTERARVL, workbook,
                                       portfoliosByAssetClass[1], portfolio[0])
        Seguimiento.printSubportfolios(CARTERARFI, workbook,
                                       portfoliosByAssetClass[2], portfolio[0])
        Seguimiento.printSubportfolios(CARTERARVI, workbook,
                                       portfoliosByAssetClass[3], portfolio[0])
    except BaseException:
        Seguimiento.errorHandler(workbook, "ERROR: No se han impreso carteras desglosadas")

    try:
        portfoliosByAssetClass[4].extend(wrongClassifications)
        Seguimiento.printSubportfolios(MALCLASIFICADOS, workbook,
                                       sorted(portfoliosByAssetClass[4]), portfolio[0])
    except BaseException:
        Seguimiento.errorHandler(workbook, "ERROR: No se han impreso instrumentos mal clasificados")


    # Cartera completa no recursiva -> Se utiliza tambien para resumenes
    query = Mesa.extractTextFile(resource_path(PORTFOLIONONRECURSIVE)).replace("AUTODATE", date)
    portfolio = Seguimiento.getData(connection, query, portfolioParameters)
    # Subclasificar fondos en cartera
    if portfolio[0] != []:
        portfolio = Seguimiento.subclassify(portfolio)
        Seguimiento.printPortfolioToExcel(workbook, CARTERACOMPLETANR, portfolio)
    else:
        print("Cartera no leida desde base de datos")


    # Imprimir resumenes de cartera
    try:
        totals = Seguimiento.printPortfolioSummary(workbook, RESUMENCARTERA, portfolio, False)
        totalsRF = Seguimiento.printPortfolioSummary(workbook, RESUMENCARTERARF, portfolio, True)
        Seguimiento.printLabeledSummary(workbook, RESUMENCARTERA, totals[1])
        Seguimiento.printLabeledSummary(workbook, RESUMENCARTERARF, totalsRF[1])
        Seguimiento.printPortfolioCompositionPies(workbook, SEGUIMIENTO,
                                                  RESUMENCARTERA, len(totals[1]), 0)
        Seguimiento.printPortfolioCompositionPies(workbook, SEGUIMIENTO,
                                                  RESUMENCARTERARF, len(totalsRF[1]), len(totals[1]))
    except BaseException:
        Seguimiento.errorHandler(workbook, "ERROR: No se han impreso resumenes de carteras")

    try:
        query = Mesa.extractTextFile(resource_path(BENCHMARKCOMPOSITION))
        query = query.replace("FONDO", parameters[0])
        benchmark = Seguimiento.getData(connection, query, ())
        benchmarkComposition = Seguimiento.benchmarkComposition(benchmark)

        Seguimiento.printBenchmarkComparison(workbook, CARTERANEUTRAL, totals, benchmarkComposition, 1)
    except BaseException:
        Seguimiento.errorHandler(workbook, "ERROR: Cartera Neutral no impresa")

    # Informacion de portafolio
    if singleSerie:
        query = Mesa.extractTextFile(resource_path(PORTFOLIOINFOQUERY))
    else:
        query = Mesa.extractTextFile(resource_path(PORTFOLIOINFOSERIES))

    date = Seguimiento.dateToString(parameters[2])
    query = query.replace("AUTODATE", date)
    try:
        portfolioInfo = Seguimiento.getData(connection, query, (parameters[0]))
        Seguimiento.printPortfolioInfo(workbook, portfolioInfo)
    except BaseException:
        print("ERROR: No se imprimio informacion de cartera")


    # Movimientos
    if singleSerie:
        query = Mesa.extractTextFile(resource_path(MOVEMENTSQUERY))
        parameters = (parameters[0], firstDateIntersection, parameters[2])
        movements = Seguimiento.getData(connection, query, parameters)
    else:
        query = Mesa.extractTextFile(resource_path(MOVEMENTSSERIES))
        parameters = (parameters[0], parameters[3], firstDateIntersection, parameters[2])
        movements = Seguimiento.getData(connection, query, parameters)
    if movements[1] != []:
        Seguimiento.printMovements(workbook, movements)

    # Cierre
    Mesa.disconnectDatabase(connection)
    workbook.save(parameters[0] + "_" + str(parameters[2].year) + str(parameters[2].month) + ".xlsm")
    print("Tiempo ejecución: " + str(time.time() - start))
    workbook.app.screen_updating = True

if __name__ == "__main__":
    main()
