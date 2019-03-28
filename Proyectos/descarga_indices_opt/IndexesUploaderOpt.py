"""
Created on Thu Oct 06 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
from libreria_fdo import *
import blpapi
from optparse import OptionParser
import json

'''FUNCIONES BLOOMBERG'''

def downloadIndexes(tickers, start_date, end_date, currency, tickers_fallidos):
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
    request.set("maxDataPoints", 100000)
    request.set("currency", currency)
    request.set("nonTradingDayFillOption", "ALL_CALENDAR_DAYS")
    request.set("nonTradingDayFillMethod","PREVIOUS_VALUE")
    # Send the request
    session.sendRequest(request)

    # Process received events
    ev = session.nextEvent()
    ev = session.nextEvent()
    ev = session.nextEvent()
    array_result = []
    for i in range(0, len(tickers)):
        # We provide timeout to give the chance for Ctrl+C handling:
        securities = session.nextEvent()
        for security in securities:
            ticker_security = security.getElement("securityData").getElement("security").getValueAsString()
            data_raw = security.getElement("securityData").getElement("fieldData")
            for j in range(0,data_raw.numValues()):
                date = data_raw.getValue(j).getElement("date").getValueAsDatetime()
                try:
                    px_last = data_raw.getValue(j).getElement("PX_LAST").getValueAsFloat()
                    pair = [ticker_security, date, px_last]
                    array_result.append(pair)
                except:
                    tickers_fallidos.append(ticker_security)        	
    session.stop()
    return array_result

'''FUNCIONES UPLOADER'''

def borrarDatosAntiguos(dia_inic):
    '''
    Borra los indices de los ultimos 10 dias en la base de datos.
    '''
    print("***********************DELETING***********************")
    conn= connectDatabaseUser(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    query=extractTextFile(path+"querys_indexes_uploader\\delete_indexes.sql").replace("AUTODATE", dia_inic)
    runSQL(conn, query)
    disconnectDatabase(conn)


def subirDatosNuevos(tuplas_clp, tuplas_usd):
    '''
    Sube los indices de los ultimos 10 dias a la base de datos.
    '''
    print("***********************UPLOADING***********************")
    conn= connectDatabaseUser(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor=conn.cursor()
    cursor.executemany("INSERT INTO Indices_Dinamica VALUES (%s,%d,%d)", tuplas_usd)
    cursor.executemany("INSERT INTO Indices_Dinamica VALUES (%s,%d,%d)", tuplas_clp)
    conn.commit()
    disconnectDatabase(conn)

def procesarLista(datos_crudos, lista_indices, currency):
    '''
    Procesa los datos que entrega la api para que queden en el formato a subir a la bdd.
    '''
    procesed_indexes_list=[]
    for date_value in datos_crudos:
        for obj in lista_indices:
            if obj["ticker"]==date_value[0] and obj["moneda"]==currency:
                procesed_indexes_list.append(tuple([convertDatetoString(date_value[1]),obj["id"], date_value[2]]))
    return procesed_indexes_list

def leerIndicesJSON():
    '''
    ESTE METODO SE DEJO DE USAR. Lee el archivo JSON con las informacion de los indices y lo introduce en un diccionario.
    '''
    json_dict=convertJSONtoDict(extractTextFile(path + "indices.json"))
    return json_dict

def getIndicesDict():
    '''
    Obtiene de la base de datos la informacion de los indices que descargaremos y la retorna en un diccionario.
    '''
    query="SELECT Index_Id, Ticker, Moneda FROM Indices_Estatica"
    conn= connectDatabaseUser(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor=queryDatabase(conn, query)
    tabla=getTableSQL(cursor)
    disconnectDatabase(conn)
    dic=dict()
    dic["Indices"]=[]
    for i in range(0,len(tabla)):
        dic["Indices"].append(dict())
        dic["Indices"][i]["id"]=int(tabla[i][0])
        dic["Indices"][i]["ticker"]=tabla[i][1]
        dic["Indices"][i]["moneda"]=tabla[i][2]
    return dic

def sendWarningMail(tickers, dia_inic):
    '''
    Envia el mail a fernando suarez 1313. 
    '''
    print("****ENVIANDO MAIL****")
    tema = "WARNING INDICES " + str(dia_inic)
    cuerpo = "Durante la carga de indices del dia " + str(dia_inic) + " ha sido imposible descargar los siguientes tickers: \n\n"
    cuerpo_lista = ""
    for ticker in tickers:
    	cuerpo_lista += "* " + ticker + "\n"
    cuerpo += cuerpo_lista
    correos = ["fsuarez@imtrust.cl", "fsuarez1@uc.cl"]
    sendMail(subject = tema, body = cuerpo, mails = correos)




print("**********************BAJANDO INDICES POR FAVOR NO CERRAR ESTA VENTANA !!!!!!**********************")
print("**********************START**********************")

#OBTENEMOS LA RUTA DEL PROGRAMA
path = getSelfPath()
#FIJAMOS LAS FECHAS ENTRE LAS QUE TRABAJAREMOS
dia_inic = getNDaysFromToday(21)
dia_fin = getNDaysFromToday(0)

#INTRODUCIMOS LA INFORMACION DE LOS INDICES QUE DESCAGAREMOS EN UN DICCIONARIO
#json_dict=leerIndicesJSON()
json_dict = getIndicesDict()

#CREAMOS DOS LISTAS DE TICKERS, UNA PARA INDICES EN USD Y OTRA PARA INDICES EN CLP
codigos_usd = []
codigos_clp = []
for obj in json_dict["Indices"]:
    if obj["moneda"] == "USD":
        codigos_usd.append(obj["ticker"])
    else :
        codigos_clp.append(obj["ticker"])

#PROCESAMOS LA FECHA AL FORMATO QUE USA LA API DE BLOOMGERG
dia_inic_formatted = convertDateAllTogether(convertStringtoDate(dia_inic))
dia_fin_formatted = convertDateAllTogether(convertStringtoDate(dia_fin))

#ARMAMOS UNA LISTA DE TICKERS FALLIDOS PARA ENVIAR CORREO DE WARNING
tickers_fallidos = []

#DESCARGAMOS TODOS LOS INDICES DE AMBAS LISTAS ENTRE LAS FECHAS INDICADAS
print("**FETCHING INDEXES FROM "+dia_inic+" TO "+dia_fin+"**")
array_indexes_usd = downloadIndexes(tickers = codigos_usd,start_date = dia_inic_formatted, end_date = dia_fin_formatted, currency = "USD", tickers_fallidos = tickers_fallidos)
array_indexes_clp = downloadIndexes(tickers = codigos_clp,start_date = dia_inic_formatted, end_date = dia_fin_formatted, currency = "CLP", tickers_fallidos = tickers_fallidos)

#PROCESAMOS LAS LISTAS DE INDICES CON FECHA Y TICKER BAJADAS PAR QUE TENGAN EL FORMATO A SUBIR EN LA BDD, POR EJEMPLO SE LE AGREGA EL ID
procesed_indexes_list_usd = procesarLista(datos_crudos = array_indexes_usd, lista_indices = json_dict["Indices"], currency = "USD")
procesed_indexes_list_clp = procesarLista(datos_crudos = array_indexes_clp, lista_indices = json_dict["Indices"], currency = "CLP")

#SE BORRA DE LA BDD LAS TUPLAS DE INDICES A PARTIR DE LA FECHA DE INICIO
borrarDatosAntiguos(dia_inic)

#INSERTAMOS LAS NUEVAS TUPLAS A LA BDDD
subirDatosNuevos(tuplas_clp = procesed_indexes_list_clp, tuplas_usd = procesed_indexes_list_usd)

#SI FALLARON TICKERS ENVIAMOS UN CORREO CON ELLOS
if len(tickers_fallidos) > 0:	
    tickers_fallidos = list(set(tickers_fallidos))
    sendWarningMail(tickers = tickers_fallidos, dia_inic = dia_inic)

#IMPRIMIMOS LA INFORMACION PROCESADA
print("***********************RESULTS***********************")
print("total tickers requested:" +str(len(json_dict["Indices"])))
print("tickers usd requested: "+str(len(codigos_usd)))
print("tickers clp requested: "+str(len(codigos_clp)))
print("raw usd tuples: "+str(len(array_indexes_usd)))
print("raw clp tuples: "+str(len(array_indexes_clp)))
print("procesed usd tuples: "+str(len(procesed_indexes_list_usd)))
print("procesed clp tuples: "+str(len(procesed_indexes_list_clp)))
print("tickers fallidos: " + str(tickers_fallidos))
print("***********************END***********************")

