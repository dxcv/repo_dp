"""
Created on Wed Nov 23 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
from tia.bbg import v3api
import blpapi
from optparse import OptionParser
import pandas as pd
import os
import time

def get_fondos():
    '''
    Obtiene la lista de los fondos que compiten contra benchmark.
    '''
    query = fs.read_file(".\\querys_bmk_uploader\\fondos.sql")
    fondos = fs.get_frame_sql_user(server = "Puyehue",
                                        database = "MesaInversiones",
                                        username = "usrConsultaComercial",
                                        password = "Comercial1w",
                                        query = query)
    return fondos


def get_tuples(dia_inic, dia_fin, dias, codigo_fdo, benchmark_id, fuente, codigo_descarga):
    '''
    Computa una serie de tuplas con la informacion de la cartera diaria del benchmark.
    '''
    tuplas = []
    print("Downloading benchmark for: " + codigo_fdo)
    # Cada fondo es un caso especial ya que los benchmark se descargan de distintas fuentes,
    # algunos son del ftp de RiskAmerica, otros son de Bloomberg y otros de PORT
    if fuente == "RA":
        # Iteramos sobre cada dia y obtenemos la posicion de cada uno para concatenarlo a la lista de tuplas
        for i in range(1, dias + 1):
            dia = fs.get_ndays_from_date(i, dia_fin)
            if fs.convert_string_to_date(dia).weekday() <= 4:
                # En este caso bajamos del FTP de RiskAmerica
                # Lo hacemos con try and catch por si hubo un 
                # feriado y risk no subio los datos
                # en ese caso pisamos el ultimo dia habil
                try:
                    tuplas += get_daily_tuples_ftp(dia=dia,
                                                   benchmark_id=benchmark_id,
                                                   codigo_descarga=codigo_descarga)
                except:
                    dia_reemplazo_feriado = fs.get_prev_weekday(dia)
                    tuplas_feriado = get_daily_tuples_ftp(dia=dia_reemplazo_feriado,
                                                          benchmark_id=benchmark_id,
                                                          codigo_descarga=codigo_descarga)
                    # Hay que actualizar la fecha de las tuplas nuevas
                    tuplas_aux = []
                    for tupla in tuplas_feriado:
                        tupla = list(tupla)
                        if tupla[0] == dia_reemplazo_feriado:
                            tupla[0] = dia
                        tuplas_aux.append(tupla)
                    tuplas_feriado = [tuple(x) for x in tuplas_aux]
                    tuplas += tuplas_feriado   
            else:
                print("El dia " + dia + " es fin de semana")
    elif fuente == "BBL":
        # En este caso necesitamos mapear los tickers al codigo de siga-bcs
        codigos = get_codigos()
        for i in range(1, dias+1):
            # Iteramos sobre cada dia y obtenemos la posicion de cada uno para concatenarlo a la lista de tuplas
            dia = fs.get_ndays_from_date(i, dia_fin)
            # Bajamos solo dias de la semana
            if fs.convert_string_to_date(dia).weekday() <= 4:
                # En este caso bajamos de Bloomberg 
                tuplas += get_daily_tuples_bbl(dia=dia,
                                               benchmark_id=benchmark_id,
                                               codigos=codigos,
                                               codigo_descarga=codigo_descarga)
            else:
                print("El dia " + dia + " es fin de semana")
    elif fuente == "PORT":
        # En este caso necesitamos mapear los tickers al codigo de siga-bcs
        codigos = get_codigos()
        for i in range(1, dias + 1):
            # Iteramos sobre cada dia y obtenemos la posicion de cada uno para concatenarlo a la lista de tuplas
            dia = fs.get_ndays_from_date(i, dia_fin)
            # Bajamos solo dias de la semana
            if fs.convert_string_to_date(dia).weekday() <= 4:
                # En este caso bajamos de Port
                tuplas += get_daily_tuples_port(dia=dia,
                                                benchmark_id=benchmark_id,
                                                codigos=codigos,
                                                codigo_descarga=codigo_descarga)
            else:
                print("El dia " + dia + " es fin de semana")
    return tuplas


def get_daily_tuples_ftp(dia, benchmark_id, codigo_descarga):
    '''
    Descarga y computa una serie de tuplas con la informacion de la cartera del benchmark para un dia en especifico.
    '''
    # Primero definimos la informacion necesaria para conectarnos al servidor ftp
    print("Fetching: " + dia)
    year,mes,dia = dia.split("-") 
    servidor = "sftp.riskamerica.com"
    usuario = "AGF_Credicorp"
    bmk_path = "./out/indices/Composicion_Indice_IMTRUST_" + year + mes + dia + ".csv"
    puerto = 22
    clave = "dX{\"4YjA"
    destino = ".\\output_bmk_uploader\\"+ str(benchmark_id) +".xls"
    # Descargamos por ftp la cartera del dia en un documento excel
    fs.download_data_sftp(host=servidor,
                                  username=usuario,
                                  password=clave,
                                  origin=bmk_path,
                                  destination=destino,
                                  port=puerto)
    # Abrimos el documento excel y leemos lo que hay dentro de el (las filas
    # vienen por linea y separadas las columnas por ;)
    wb = fs.open_workbook(path=destino, screen_updating=True, visible=False)
    esquema = fs.get_table_xl(wb=wb, sheet=0, row=1, column=1)[0].split(";")
    # necesito hacer esto porque cuando hay feriados y subo el archivo a mano se pifea la columna tirval
    esquema = [x.replace(",,,,", "") for x in esquema]
    tabla_raw = fs.get_table_xl(wb=wb, sheet=0, row=2, column=1)
    fs.close_excel(wb=wb)
    tabla_procesada = []
    for fila in tabla_raw:
        fila_procesada = fila.split(";")
        tabla_procesada.append(fila_procesada)
    
    # Cuadramos la data en un dataframe
    cartera_bmk = pd.DataFrame(data=tabla_procesada, columns=esquema)
    # Filtramos porque solo nos interesa el benchmark del fondo en cuestion
    cartera_bmk = cartera_bmk[cartera_bmk["indice"] == codigo_descarga]
    # Agregamos el benchmark id que puede servir para hacer joins con las tablas de benchmark en otras aplicaciones
    cartera_bmk["Benchmark_Id"]  = benchmark_id
    # Ordenamos las columnas de la tabla en el mismo orden que se encuentran en la base de datos
    columnas_nuevas = ["fecha", "Benchmark_Id", "nemo", "ponderacion", "moneda", "tirVal", "duracion", "clasificacion", "tipo", "plazoResidual", "indice"]
    cartera_bmk = cartera_bmk[columnas_nuevas]
    # Parseamos a float los strings que sean necesarios y les quitamos los espacios
    cartera_bmk["moneda"] = cartera_bmk["moneda"].str.replace("CLP", "$").str.strip()
    cartera_bmk["ponderacion"] = cartera_bmk["ponderacion"].str.replace(",", ".").str.strip().astype(float)/100
    # SIRVE PARA DEBUGEAR EN UN EXCEL LOS ERRORES
    '''
    wb = open_workbook("Tester.xlsx", screen_updating = True, visible = True)
    clearSheetXl(sheet = "Hoja1")
    pasteValXl("Hoja1", 1, 1, cartera_bmk)
    saveWorkbook(wb)
    close_excel(wb)
    '''
    for i, instrumento in cartera_bmk.iterrows():
        tir = instrumento["tirVal"].replace(",", ".").strip()
        if tir == "":
            tir = "0.0"
        tir = float(tir)
        cartera_bmk.set_value(i, "tirVal", tir)

    cartera_bmk["duracion"] = cartera_bmk["duracion"].str.replace(",", ".").str.strip().astype(float)
    cartera_bmk["plazoResidual"] = cartera_bmk["plazoResidual"].str.replace(",", ".").str.strip().astype(float)
    # Formateamos el dataframe en un arreglo de tuplas
    serie_tuplas = fs.format_tuples(df = cartera_bmk)
    return serie_tuplas


def get_codigos():
    '''
    Descarga la lista de tickers con codigo SIGA desde Puyehue. 
    Es necesario para mapear los ticker de bloomberg a los de BCS
    y asi despues armar cartera activa para reporting de tracking error.
    '''
    query = fs.read_file(".\\querys_bmk_uploader\\codigos_bbl.sql")
    codigos = fs.get_frame_sql_user(server="Puyehue",
                                         database="MesaInversiones",
                                         username="usrConsultaComercial",
                                         password="Comercial1w",
                                         query=query)
    # Cambiamos al formato CI Equity
    codigos["codigo_ins_bbl"] = codigos["codigo_ins_bbl"].str.replace("CI Equity", "CC").str.strip()
    codigos = codigos.set_index(["codigo_ins_bbl"])
    return codigos


def get_daily_tuples_bbl(dia, benchmark_id, codigos, codigo_descarga):
    '''
    Descarga y computa una serie de tuplas con la informacion de la cartera del benchmark para un dia en especifico.
    '''
    print("Fetching: " + dia)
    # Obtenemos el dia en formato para descarga de Bloomberg
    dia_bbg = fs.convert_date_all_together(fs.convert_string_to_date(dia))
    LocalTerminal = v3api.Terminal('localhost', 8194)
    # Descargamos de bloomberg la posicion de cada ticker en el indice para la fecha
    cartera_bmk = LocalTerminal.get_reference_data(codigo_descarga, 'Indx_mweight_px', end_date_override = dia_bbg)
    cartera_bmk = cartera_bmk.as_frame()["Indx_mweight_px"][0][["Index Member","Percent Weight"]]
    cartera_bmk = cartera_bmk.set_index(["Index Member"])
    # Mapeamos los tickers a los distintos codigos siga-bcs
    cartera_bmk = pd.merge(left=cartera_bmk, right=codigos, how="left",left_index=True, right_index=True).reset_index()
    cartera_bmk = cartera_bmk[["codigo_ins","Percent Weight"]]
    # Pasamos los pesos a weight 0-1
    cartera_bmk["Percent Weight"] = (cartera_bmk["Percent Weight"]/100).astype(float)
    # Rellenamos las distintas columnas que se cargan en Puyehue
    cartera_bmk["Benchmark_Id"]  = int(benchmark_id)
    cartera_bmk["fecha"] = dia
    cartera_bmk["moneda"] = "$"
    cartera_bmk["tirVal"] = 0.0
    cartera_bmk["duration"] = 0.0
    cartera_bmk["clasificacion"] = 'NA'
    cartera_bmk["tipo"] = 'NA'
    cartera_bmk["plazoResidual"] = 0.0
    cartera_bmk["indice"] = codigo_descarga
    # Ordenamos las columnas en el orden de la base de datos
    columnas_nuevas = ["fecha", "Benchmark_Id", "codigo_ins",
                       "Percent Weight", "moneda", "tirVal",
                       "duration", "clasificacion", "tipo",
                       "plazoResidual", "indice"]
    cartera_bmk = cartera_bmk[columnas_nuevas]
    # Formateamos el dataframe en un arreglo de tuplas
    serie_tuplas = fs.format_tuples(df=cartera_bmk)
    return serie_tuplas


def get_daily_tuples_port(dia, benchmark_id, codigos, codigo_descarga):
    '''
    Descarga y computa una serie de tuplas con la informacion de la cartera
    del benchmark para un dia en especifico desde PORT.
    '''
    print("Fetching: " + dia)
    # Pasamos el dia a formato bbl
    dia_bbg = fs.convert_date_all_together(fs.convert_string_to_date(dia))
    # Primero descargamos los weights de la cartera
    portfolio = download_port_weights(port=codigo_descarga, date=dia_bbg)
    # Luego le concatenamos la yield, duration y rating desde BBL
    portfolio = download_portfolio_flds(portfolio=portfolio, date=dia_bbg)
    # Le agregamos los campos faltantes necesarios para la base de datos y reordenamos las columnas
    portfolio = update_portfolio_flds(portfolio=portfolio,
                                      date=dia,
                                      benchmark_id=benchmark_id,
                                      port=codigo_descarga,
                                      codigos=codigos)
    # Pasamos el dataframe a lista de tuplas
    tuples = fs.format_tuples(df=portfolio)
    return tuples


def download_port_weights(port, date):
    '''
    Dada una fecha y el codigo port, descarga los weights del portfolio junto con sus tickers.
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
    request = refDataService.createRequest("PortfolioDataRequest")
    request.getElement("securities").appendValue(port)
    overrides = request.getElement("overrides")
    override1 = overrides.appendElement()
    # Este override permite variar hardcodear la fecha
    override1.setElement("fieldId", "REFERENCE_DATE")
    override1.setElement("value", date)
    # request.getElement("securities").appendValue(ticker)
    request.getElement("fields").appendValue("PORTFOLIO_MEMBERS") 
    request.getElement("fields").appendValue("PORTFOLIO_MWEIGHT") 
    request.getElement("fields").appendValue("PORTFOLIO_DATA") 
    # Send the request
    session.sendRequest(request)

    # Process received events
    ev = session.nextEvent()
    ev = session.nextEvent()
    ev = session.nextEvent()
    ev = session.nextEvent()
    data_iter = ev
    aum = 0
    #Iteramos sobre el evento que tiene solo un elemento
    for data in data_iter:
        # Este comment es por si se quiere hacer por market val
        # constituents = data.getElement("securityData").getValue(0).getElement("fieldData").getElement("PORTFOLIO_DATA")
        constituents = data.getElement("securityData").getValue(0).getElement("fieldData").getElement("PORTFOLIO_MWEIGHT")
        portfolio = pd.DataFrame(columns = ["security", "weight"])
        for j in range(0, constituents.numValues()):
            security = constituents.getValue(j).getElement("Security").getValueAsString()
            security = security.replace("     ", " ")
            # weight = float(constituents.getValue(j).getElement("Market Value").getValueAsString())
            weight = float(constituents.getValue(j).getElement("Weight").getValueAsString())
            portfolio.loc[j] = [security, weight]
            aum += weight
        # Normalizamos por 100 ya que a veces el port no suma 100 (fuck logic)
        portfolio["weight"] = portfolio["weight"]/aum
        break
    session.stop()
    portfolio = portfolio.set_index(["security"])
    return portfolio


def download_portfolio_flds(portfolio, date):
    '''
    Dada la cartera del benchmark y una fecha, descarga la yield,
    duration y rating para concatenarlo al portfolio.
    '''
    portfolio_light = portfolio
    LocalTerminal = v3api.Terminal('localhost', 8194)
    # Descargamos de bloomberg los campos necesarios
    portfolio_flds = LocalTerminal.get_reference_data(portfolio_light.index, ['YLD_YTM_MID', 'DUR_ADJ_MID', 'BB_COMPOSITE', 'CRNCY'], CUST_TRR_START_DT=date, ignore_field_error=1)
    portfolio_flds = portfolio_flds.as_frame()
    # Concatenamos los datos a lo que teniamos
    portfolio_full = pd.merge(portfolio_light, portfolio_flds, how="outer", left_index=True, right_index=True)
    # Cambiamos algunos nombres
    portfolio_full.rename(columns={"weight": "Weight", "YLD_YTM_MID": "Tasa", "DUR_ADJ_MID": "Duration", "BB_COMPOSITE": "Riesgo", "CRNCY": "Moneda"}, inplace=True)
    portfolio_full = portfolio_full.fillna(0.0)
    return portfolio_full


def update_portfolio_flds(portfolio, date, benchmark_id, port, codigos):
    '''
    Agrega los campos faltantes al portfolio del port,
    ademas ordena las columnas en el orden de la base de datos.
    '''
    portfolio = pd.merge(left=portfolio, right=codigos, how="left",left_index=True, right_index=True).reset_index()
    portfolio = portfolio.drop("index", 1)
    portfolio["Fecha"] = date
    portfolio["Benchmark_Id"] = benchmark_id
    
    crncy_mapping = {"CLP": "$",
                     "BRL": "BRL",
                     "COP": "COP",
                     "MXN": "MX",
                     "UYU": "UYU",
                     "PEN": "PEN",
                     "ARS": "ARS",
                     "USD": "US$"}
    
    portfolio["Moneda"] = portfolio["Moneda"].replace(crncy_mapping)

    portfolio["Tipo"] = "BLATAM"
    portfolio["Plazo"] = 0
    portfolio["Nombre_Bmk"] = port
    new_columns = ["Fecha", "Benchmark_Id", "codigo_ins", 
                   "Weight", "Moneda", "Tasa", "Duration",
                   "Riesgo", "Tipo", "Plazo", "Nombre_Bmk"]
    portfolio = portfolio[new_columns]
    return portfolio


def delete_old_data(dia_inic):
    '''
    Borra las carteras de los ultimos dias, dada la cantidad de dias.
    '''
    print("Deleting historical data...")
    conn = fs.connect_database_user(server="Puyehue",
                                          database="MesaInversiones",
                                          username="usrConsultaComercial",
                                          password="Comercial1w")
    query = fs.read_file(".\\querys_bmk_uploader\\delete_positions.sql").replace("AUTODATE", dia_inic)
    fs.run_sql(conn, query)
    fs.disconnect_database(conn)


def upload_new_data(tuplas):
    '''
    Sube a la base de datos las tuplas nuevas.
    '''
    print("Uploading historical data...")
    conn = fs.connect_database_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w")
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO ZHIS_Carteras_Bmk VALUES (%s,%d,%s, %d, %s, %d, %d, %s, %s, %d, %s)", tuplas)
    conn.commit()
    fs.disconnect_database(conn)


def run_disclaimer():
    '''
    Advierte al usuario de que cierre los excel que este usando.
    '''
    os.system("mode con: cols=210 lines=70")
    print("CARGA DE BENCHMARKS POR INICIAR")
    print("GUARDAR Y CERRAR EXCEL EN 30 SEGUNDOS...")
    for i in range(30):
        print("cerrando en " + str(30-i) + " segundos...")
        time.sleep(1)

# Mostramos el disclaimer
# run_disclaimer()
# Cerramos todos las instancias de exce
fs.kill_excel()
# Fijamos la cantidad de dias que descargaremos de data (por defecto 10 dias)
dias = 4
# dia_fin = "2017-02-25"
dia_fin = fs.get_ndays_from_today(0)
# dia_inic = "2017-02-25"
dia_inic = fs.get_ndays_from_date(dias, dia_fin)
# Obtenemos los fondos que tienen asignado un benchmark a descargar
fondos = get_fondos()
tuplas = []
# Por cada fondo descargamos la cartera de su benchmark y juntamos todas las tuplas en un arreglo
for i, fdo in fondos.iterrows():
    codigo_fdo = fdo["codigo_fdo"]
    benchmark_id = fdo["benchmark_id"]
    fuente = fdo["fuente"]
    codigo_descarga = fdo["codigo_descarga"]
    # Descargamos las tuplas con la posicion de cada instrumento del benchmark
    tuplas += get_tuples(dia_inic=dia_inic,
                                 dia_fin=dia_fin,
                                 dias=dias,
                                 codigo_fdo=codigo_fdo,
                                 benchmark_id=benchmark_id,
                                 fuente=fuente,
                                 codigo_descarga=codigo_descarga)

# Pisamos la cantidad de dias definida con los datos nuevos
delete_old_data(dia_inic=dia_inic)

# Subimos los nuevos
upload_new_data(tuplas=tuplas)

# Cerramos todos las instancias de excel
fs.kill_excel()
