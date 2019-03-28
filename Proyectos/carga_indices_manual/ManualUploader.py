"""
Created on Thu Aug 25 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
from libreria_fdo import *
import blpapi
from optparse import OptionParser


'''FUNCIONES BLOOMBERG'''

def downloadIndexes(tickers, start_date, end_date, currency):
    '''
    Dada una lsita de tickers, una fecha de inicio, otra de fin y una moneda, descarga todos los indices de la lista entre ambas fechas en esa moneda.
    '''
    parser = OptionParser(description="Retrieve reference data.")
    parser.add_option("-a",
                      "--ip",
                      dest="host",
                      help="server name or IP (default: %default)",
                      metavar="ipAddress",
                      default="localhost")
    parser.add_option("-p",
                      dest="port",
                      type="int",
                      help="server port (default: %default)",
                      metavar="tcpPort",
                      default=8194)

    (options, args) = parser.parse_args()
    # Fill SessionOptions
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(options.host)
    sessionOptions.setServerPort(options.port)

    # Create a Session
    session = blpapi.Session(sessionOptions)

    # Start a Session
    if not session.start():
        print("Failed to start session.")
        return

    # Open service to get historical data from
    if not session.openService("//blp/refdata"):
        print("Failed to open //blp/refdata")
        return

    # Obtain previously opened service
    refDataService = session.getService("//blp/refdata")

    # Create and fill the request for the historical data
    request = refDataService.createRequest("HistoricalDataRequest")
    for ticker in tickers:
    	request.getElement("securities").appendValue(ticker)
    request.getElement("fields").appendValue("PX_LAST") 
    request.set("periodicityAdjustment", "ACTUAL")
    request.set("periodicitySelection", "DAILY")
    request.set("startDate", start_date)
    request.set("endDate", end_date)
    request.set("maxDataPoints", 3650)
    request.set("currency", currency)
    request.set("nonTradingDayFillOption", "ALL_CALENDAR_DAYS")
    request.set("nonTradingDayFillMethod","PREVIOUS_VALUE")
    # Send the request
    session.sendRequest(request)

    # Process received events
    ev = session.nextEvent()
    ev = session.nextEvent()
    ev = session.nextEvent()
    array_result=[]
    for i in range(0, len(tickers)):
        # We provide timeout to give the chance for Ctrl+C handling:
        securities = session.nextEvent()
        for security in securities:
            ticker_security=security.getElement("securityData").getElement("security").getValueAsString()
            data_raw=security.getElement("securityData").getElement("fieldData")
            for j in range(0,data_raw.numValues()):
                date=data_raw.getValue(j).getElement("date").getValueAsDatetime()
                px_last=data_raw.getValue(j).getElement("PX_LAST").getValueAsFloat()
                pair=[ticker_security, date, px_last]
                array_result.append(pair)
        	
    session.stop()
    return array_result

def getTupleList(raw_serie):
    '''
    Transforma los datos a tuplas.
    '''
    tuple_list=[]
    for dato in serie:
    	tuple_list.append(tuple([convertDatetoString(dato[1]),index_id, dato[2]]))
    return tuple_list
def subirDatosNuevos(tuplas):
    '''
    Sube los indices a la base de datos.
    '''
    conn= connectDatabaseUser(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor=conn.cursor()
    cursor.executemany("INSERT INTO Indices_Dinamica VALUES (%s,%d,%d)", tuplas)
    conn.commit()
    disconnectDatabase(conn)


#OBTENEMOS LA RUTA DEL PROGRAMA
path=getSelfPath()
#FIJAMOS LAS FECHAS ENTRE LAS QUE TRABAJAREMOS
dia_inic = "2011-01-03" #PONER AQUI FECHA DE INICIO
dia_fin = getNDaysFromToday(1) #PONER AQUI FECHA DE FIN, POR DEFECTO ES EL DIA DE AYER
currency="CLP" #PONER AQUI LA MONEDA
ticker = "IPSA Index" #PONER AQUI EL TICKER
index_id=100 #PONER AQUI EL ID, NOTAR QUE NO VA A FUNCIONAR SI EL ID NO ESTA EN LA TABLA ESTATICA


print('*****START******')
#BAJAMOS LOS DATOS
print('Descargando ' + ticker + '...')
serie = downloadIndexes([ticker], convertDateAllTogether(convertStringtoDate(dia_inic)), convertDateAllTogether(convertStringtoDate(dia_fin)), currency)

#TRANSFORMAMOS LOS DATOS A TUPLAS
tuple_list=getTupleList(raw_serie=serie)

print('Subiendo indices a bdd...')
#SUBIMOS LOS INDICES
subirDatosNuevos(tuplas=tuple_list)


print('*****END******')
