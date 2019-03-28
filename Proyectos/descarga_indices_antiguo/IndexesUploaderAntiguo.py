"""
Created on Thu May 20 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
from libreria_fdo import *
import blpapi
from optparse import OptionParser
import json

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
    request.set("maxDataPoints", 100)
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
                if ticker_security=="CHILE65 Index":
                    print(str(date)+" "+str(px_last))
        	
    session.stop()
    return array_result

'''FUNCIONES UPLOADER'''

def borrarDatosAntiguos(dia_inic):
    '''
    Borra los indices de los ultimos 10 dias en la base de datos.
    '''
    print("***********************DELETING***********************")
    conn= connectDatabaseUser(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    query=extractTextFile(path+"\\querys_indexes_uploader_antiguo\delete_indexesAntiguo.sql").replace("AUTODATE", dia_inic)
    runSQL(conn, query)
    disconnectDatabase(conn)


def subirDatosNuevos(tuplas_clp, tuplas_usd):
    '''
    Sube los indices de los ultimos 10 dias a la base de datos.
    '''
    print("**********************BAJANDO INDICES POR FAVOR NO CERRAR ESTA VENTANA !!!!!!**********************")
    print("***********************UPLOADING***********************")
    conn= connectDatabaseUser(server="Puyehue", database="MesaInversiones", username="usrConsultaComercial", password="Comercial1w")
    cursor=conn.cursor()
    cursor.executemany("INSERT INTO Indices VALUES (%d, %s, %d)", tuplas_usd)
    cursor.executemany("INSERT INTO Indices VALUES (%d, %s, %d)", tuplas_clp)
    conn.commit()
    disconnectDatabase(conn)

def procesarLista(datos_crudos, lista_indices):
    '''
    Procesa los datos que entrega la api para que queden en el formato a subir a la bdd.
    '''
    procesed_indexes_list=[]
    for date_value in datos_crudos:
        for obj in lista_indices:
            if obj["ticker"]==date_value[0]:
                procesed_indexes_list.append(tuple([obj["id"], convertDatetoString(date_value[1]), date_value[2]]))
    return procesed_indexes_list

def leerIndicesJSON():
    '''
    Lee el archivo JSON con las informacion de los indices y lo introduce en un diccionario.
    '''
    json_dict=convertJSONtoDict(extractTextFile(path+"indicesAntiguo.json"))
    return json_dict

print("**********************BAJANDO INDICES POR FAVOR NO CERRAR ESTA VENTANA !!!!!!**********************")
print("**********************START**********************")

#OBTENEMOS LA RUTA DEL PROGRAMA
path=getSelfPath()
#FIJAMOS LAS FECHAS ENTRE LAS QUE TRABAJAREMOS
dia_inic=getNDaysFromToday(21)
dia_fin=getNDaysFromToday(1)

#INTRODUCIMOS LA INFORMACION DE LOS INDICES QUE DESCAGAREMOS EN UN DICCIONARIO
json_dict=leerIndicesJSON()

#CREAMOS DOS LISTAS DE TICKERS, UNA PARA INDICES EN USD Y OTRA PARA INDICES EN CLP
codigos_usd=[]
codigos_clp=[]
for obj in json_dict["Indices"]:
    if obj["moneda"]=="USD":
        codigos_usd.append(obj["ticker"])
    else :
        codigos_clp.append(obj["ticker"])

#PROCESAMOS LA FECHA AL FORMATO QUE USA LA API DE BLOOMGERG
dia_inic_formatted=convertDateAllTogether(convertStringtoDate(dia_inic))
dia_fin_formatted=convertDateAllTogether(convertStringtoDate(dia_fin))


#DESCARGAMOS TODOS LOS INDICES DE AMBAS LISTAS ENTRE LAS FECHAS INDICADAS
print("**FETCHING INDEXES FROM "+dia_inic+" TO "+dia_fin+"**")
array_indexes_usd=downloadIndexes(tickers=codigos_usd,start_date=dia_inic_formatted, end_date=dia_fin_formatted, currency="USD")
array_indexes_clp=downloadIndexes(tickers=codigos_clp,start_date=dia_inic_formatted, end_date=dia_fin_formatted, currency="CLP")

#PROCESAMOS LAS LISTAS DE INDICES CON FECHA Y TICKER BAJADAS PAR QUE TENGAN EL FORMATO A SUBIR EN LA BDD, POR EJEMPLO SE LE AGREGA EL ID
procesed_indexes_list_usd=procesarLista(datos_crudos=array_indexes_usd, lista_indices=json_dict["Indices"])
procesed_indexes_list_clp=procesarLista(datos_crudos=array_indexes_clp, lista_indices=json_dict["Indices"])

#SE BORRA DE LA BDD LAS TUPLAS DE INDICES A PARTIR DE LA FECHA DE INICIO
borrarDatosAntiguos(dia_inic)

#INSERTAMOS LAS NUEVAS TUPLAS A LA BDDD
subirDatosNuevos(tuplas_clp=procesed_indexes_list_clp, tuplas_usd=procesed_indexes_list_usd)


#IMPRIMIMOS LA INFORMACION PROCESADA
print("***********************RESULTS***********************")
print("total tickers requested:" +str(len(json_dict["Indices"])))
print("tickers usd requested: "+str(len(codigos_usd)))
print("tickers clp requested: "+str(len(codigos_clp)))
print("raw usd tuples: "+str(len(array_indexes_usd)))
print("raw clp tuples: "+str(len(array_indexes_clp)))
print("procesed usd tuples: "+str(len(procesed_indexes_list_usd)))
print("procesed clp tuples: "+str(len(procesed_indexes_list_clp)))
print("***********************END***********************")




#for i in range(0, len(json_dict["Indices"])):
#    for j in range(0, len(json_dict["Indices"])):
#        if i!=j and json_dict["Indices"][i]["ticker"]==json_dict["Indices"][j]["ticker"]:
#           print(json_dict["Indices"][i]["id"])

#for date_value in procesed_indexes_list:
    #print(date_value)




#noesta=False
#for i in range(0, len(codigos_clp)):
#    for j in range(0,len(array_indexes_clp)):
#        if codigos_clp[i]==array_indexes_clp[j][0]:
#            print("ENTROO")
#            break
#        print(codigos_clp[i])




#cods_out=[]
#cambio=True
#for i in range(len(array_indexes_clp)-1):
#    if cambio:
#        cods_out.append(array_indexes_clp[i][0])
#        cambio=False
#    if array_indexes_clp[i][0]!=array_indexes_clp[i+1][0]:
#        cambio=True
#if cambio:
#       cods_out.append(array_indexes_clp[len(array_indexes_clp)-1][0])



#for cod in codigos_clp:
#    if (cod not in cods_out):
#        print(cod)

#print(procesed_indexes_list[0])

#for date_value in procesed_indexes_list_usd:
#    if date_value[0]==1009:
#        print(date_value)


'''
procesed_indexes_list_usd=[]
for date_value in array_indexes_usd:
    for obj in json_dict["Indices"]:
        if obj["ticker"]==date_value[0]:
            procesed_indexes_list_usd.append(tuple([obj["id"], convertDatetoString(date_value[1]), date_value[2]]))

procesed_indexes_list_clp=[]
for date_value in array_indexes_clp:
    for obj in json_dict["Indices"]:
        if obj["ticker"]==date_value[0]:
            procesed_indexes_list_clp.append(tuple([obj["id"], convertDatetoString(date_value[1]), date_value[2]]))

'''