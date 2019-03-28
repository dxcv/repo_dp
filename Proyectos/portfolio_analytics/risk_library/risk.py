"""
Created on Thu Oct 06 11:00:00 2016

@author: Fernando Suarez

"""

import sys
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np
import math as math


def get_inflation(start_date, end_date):
    '''
    Retorna el retorno entre dos fechas para una moneda, dado el id del fx.
    '''
    path = "..\\risk_library\\querys_risk\\clf.sql"
    query_start = fs.read_file(path=path).replace("autodate", start_date)
    clf_start = fs.get_val_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query_start)
    query_end = fs.read_file(path=path).replace("autodate", end_date)
    clf_end = fs.get_val_sql_user(server="Puyehue",
                                  database="MesaInversiones",
                                  username="usrConsultaComercial",
                                  password="Comercial1w",
                                  query=query_end)
    if fs.convert_string_to_date(end_date).weekday() != 0:
        inflation = ((clf_end/clf_start)-1) * 365
    else:
        inflation = (((clf_end/clf_start)-1) * 365) / 3
    return inflation


def get_historical_dataset(data_start_date, data_end_date):
    '''
    Entrega un dataframe con toda la informacion historica de los indicesc, cada columna es un indice.
    '''
    # obtenemos las querys para indices_estatica e indices_dinamica
    indices_serie_query_path = "..\\risk_library\\querys_risk\\indices_dinamica.sql"
    indices_query_path = "..\\risk_library\\querys_risk\\indices_estatica.sql"
    indices_serie_query = fs.read_file(path=indices_serie_query_path)
    indices_serie_query = indices_serie_query.replace("AUTODATE1", data_start_date).replace("AUTODATE2", data_end_date)
    indices_query = fs.read_file(path=indices_query_path)
    # Descargamos ambas tablas, la dinamica para las fechas parametrizadas
    indices_serie = fs.get_frame_sql_user(server="Puyehue",
                                       database="MesaInversiones",
                                       username="usrConsultaComercial",
                                       password="Comercial1w",
                                       query=indices_serie_query)
    indices_serie.set_index(["fecha", "index_id"], inplace=True)
    indices = fs.get_frame_sql_user(server="Puyehue",
                                 database="MesaInversiones",
                                 username="usrConsultaComercial",
                                 password="Comercial1w",
                                 query=indices_query)
    vectores = []

    # Por cada indice indice obtenemos su serie y calculamos su vector de retornos
    for index_id in indices["index_id"]:
        serie = indices_serie.iloc[indices_serie.index.get_level_values("index_id") == index_id]
        serie.columns = [index_id]
        serie = serie.reset_index().set_index(["fecha"]).drop("index_id", 1).pct_change().fillna(0).replace([np.inf, -np.inf], 0.0)[1:][::-1]
        vectores.append(serie)
    # Agregamos un indice con retorno 0 constante (CLPCLP)
    vectores.insert(0, pd.DataFrame(0.0, index = vectores[0].index, columns=[0]))
    dataset = pd.concat(vectores, axis=1)
    return dataset


def get_ewma_cov_matrix(data, landa=1):
    '''
    Funcion para calcular la matriz de varianza-covarianza con proceso EWMA. Recibe un dataframe
    en que cada columna es una serie de retornos. Es importante que las series no tengan NaN.
    '''
    # Sacamos el promedio de cada serie y normalizamos los datos
    #print(data)
    avg = data.mean(axis=0)
    data_mwb = data - avg
    #print(data_mwb)
    # Sacamos el vector de landas dandole mas peso a los primeros elementos(datos mas nuevos)
    powers = np.arange(len(data_mwb))
    landavect = np.empty(len(data_mwb))
    landavect.fill(landa)
    landavect = np.power(landavect, powers)

    # Multiplicamos el vector por la matriz de datos normalizada, el vector landa tambien se normaliza con la raiz
    landavectSQRT = np.sqrt(landavect)
    
    data_tilde = data_mwb.T
    data_tilde = data_tilde * landavectSQRT
    data_tilde = data_tilde.T
    # Multiplicamos la suma de todos los landas con la multiplicacion de la matriz compuesta con ella misma
    sumlanda = np.sum(landavect)
    cov_ewma = (1/(sumlanda-1)) * (data_tilde.T.dot(data_tilde))


    # Para obtener la covarianza/varianza de dos/un indices
    # print(cov_ewma[73].loc[168])
    # para obtener la matriz descorrelacionada
    # cov_ewma = pd.DataFrame(np.diag(np.diag(cov_ewma)),index = cov_ewma.index, columns = cov_ewma.columns)
    
    return cov_ewma


def get_portfolio(fund_date, fund_id, inflation):
    '''
    Retorna la cartera de un fondo junto con sus posiciones al dia de ayer en un dataframe.
    '''
    path = "..\\risk_library\\querys_risk\\map_master.sql"
    query_portfolio = fs.read_file(path=path).replace("AUTODATE", fund_date).replace("AUTOFUND", fund_id)
    full_portfolio = fs.get_frame_sql_user(server="Puyehue",
                                           database="MesaInversiones",
                                           username="usrConsultaComercial",
                                           password="Comercial1w",
                                           query=query_portfolio)
    # Agregamos la inflacion a las tasa de los bonos reajustables
    for i, instrument in full_portfolio.iterrows():
        if instrument["moneda"] == "UF":
            instrument["tasa"] = instrument["tasa"] + inflation
            full_portfolio.loc[i] = instrument
    
    #if fund_id == "MACRO 1.5":
    #    full_portfolio.loc[19, "monto"] = 1500000000 
    
    return full_portfolio


def get_portfolio_bmk(benchmark_date, benchmark_id):
    '''
    Retorna la cartera de todos los benchmarks junto con sus posiciones al dia de ayer en un dataframe.
    '''
    path = "..\\risk_library\\querys_risk\\map_bmk_master.sql"
    query_portfolio = fs.read_file(path=path).replace("AUTODATE", benchmark_date).replace("AUTOBMK", str(benchmark_id))
    full_portfolio_bmk = fs.get_frame_sql_user(server="Puyehue",
                                               database="MesaInversiones",
                                               username="usrConsultaComercial",
                                               password="Comercial1w",
                                               query=query_portfolio)
    return full_portfolio_bmk


def get_funds():
    '''
    Retorna los fondos con su informacion basica en un dataframe.
    '''
    path = "..\\risk_library\\querys_risk\\fondos.sql"
    query_funds = fs.read_file(path=path)
    funds = fs.get_frame_sql_user(server="Puyehue",
                                  database="MesaInversiones",
                                  username="usrConsultaComercial",
                                  password="Comercial1w",
                                  query=query_funds)
    return funds


def get_full_portfolio_metrics(matrix, funds, fund_date, benchmark_date, inflation):
    '''
    En base a la cartera de los fondos y la matriz de varianza-covarianza, obtiene un dataframe con todos los portfolios
    con sus metricas de reisgo calculadas.
    '''
    portfolios = []
    # Para cada fondo obtenemos su portafolio activo con sus respectivas metricas de riesgo
    for i, fund in funds.iterrows():
        # Sacamos la informacion basica del fondo
        fund_id = fund["codigo_fdo"]
        benchmark_id = fund["benchmark_id"]
        alpha_seeker = fund["alpha_seeker"]
        # Portfolio del fondo sin metricas de riesgo
        fund_portfolio = get_portfolio(fund_date=fund_date,
                                       fund_id=fund_id,
                                       inflation=inflation)
        # Portfolio del benchmark sin metricas de riesgo
        benchmark_portfolio = get_portfolio_bmk(benchmark_date=benchmark_date,
                                                benchmark_id=benchmark_id)
        # Portfolio activo con metricas de riesgo
        portfolio = get_portfolio_metrics(fund_portfolio=fund_portfolio,
                                          benchmark_portfolio=benchmark_portfolio,
                                          fund_id=fund_id,
                                          matrix=matrix,
                                          benchmark_id=benchmark_id,
                                          alpha_seeker=alpha_seeker)
        portfolios.append(portfolio)
    portfolios = pd.concat(portfolios, ignore_index=True)
    return portfolios


def get_portfolio_metrics(fund_portfolio, benchmark_portfolio, fund_id, matrix, benchmark_id, alpha_seeker):
    '''
    En base a la cartera de cada fondo, su benchmark y la matriz de varianza-covarianza, 
    obtiene un dataframe con el portfolio activo junto sus metricas de riesgo calculadas.
    '''
    # Obtenemos el vector con los montos del portfolio agrupados por indice

    stock_pindex = fund_portfolio.groupby(by="Index_Id")["monto"].sum().reset_index().set_index(["Index_Id"]).reindex(index=matrix.index).fillna(0)
    
    # Transformamos el vector a uno de weights agrupado por indices
    w_pindex = stock_pindex/np.sum(stock_pindex)
    w_pindex.columns = ["weight_index"]

    # if fund_id=='MACRO 1.5':

    #     fs.print_full(fund_id)
    #     fs.print_full(fund_portfolio)
    #     fs.print_full(w_pindex)
    #     exit()

    # En caso de que tenga benchmark, obtenemos el vector w_b con la posicion del benchmark, tambien agrupado por indices
    if alpha_seeker == 1:
        w_bindex = benchmark_portfolio.groupby(by="Index_Id")["weight"].sum().reset_index().set_index(["Index_Id"]).reindex(index=matrix.index).fillna(0)
    # En caso contrario el vector de weights es un vector de ceros
    else:
        w_bindex = pd.DataFrame(index=w_pindex.index, columns=["weight"]).fillna(0)
    w_bindex.columns = ["weight_index"]
    # Obtenemos el vector de weight activos
    w_aindex = w_pindex - w_bindex
    
    # Mutiplicamos los weights por la matriz de varianza covarianza para obtener los mcr no normalizados
    w_marginal = matrix.dot(w_aindex)

    # Multiplicamos de nuevo por los weights para obtener la volatilidad o tracking error
    sigma = np.sqrt(w_aindex.T.dot(w_marginal))["weight_index"][0]

    # Ahora recomputamos el portfolio desagrupado para calcular las risk metrics
    portfolio = fund_portfolio.reset_index().set_index(["Index_Id"]).drop("index", 1)

    # Calculamos la contribucion marginal al riesgo normalizando por la volatilidad y concatenamos al portfolio
    mcr = ((w_marginal)*math.sqrt(360))/sigma
    mcr.columns = ["mcr"]
    

    portfolio = pd.merge(portfolio, mcr, how="left", left_index=True, right_index=True)
    portfolio = portfolio.reset_index().set_index(["codigo_ins"])
    
    # Concatenamos weight a cada instrumento y renombramos la columna del indice
    portfolio["weight"] = portfolio["monto"]/np.sum(portfolio["monto"])
    portfolio = portfolio.rename(columns = {"index": "Index_Id"})
    
    # Hacemos el mismo proceso para desagregar el portfolio del benchmark
    benchmark = benchmark_portfolio.reset_index().set_index(["Index_Id"]).drop("index", 1)
    benchmark = pd.merge(benchmark, mcr, how="left", left_index=True, right_index=True)
    benchmark = benchmark.reset_index().set_index(["codigo_ins"])
    if  benchmark.index.name != "Index_Id":
        benchmark = benchmark.rename(columns = {"index": "Index_Id"})

    

    
    active_portfolio = pd.merge(portfolio, benchmark, how="outer", left_index=True, right_index=True)
    active_portfolio["weight_x"].fillna(0.0, inplace=True)
    active_portfolio["weight_y"].fillna(0.0, inplace=True)

    # Concatenamos el active weight al portfolio
    active_portfolio["weight_active"] = active_portfolio["weight_x"] - active_portfolio["weight_y"]
    
    # Definimos las metricas a agregar a cada instrumento
    active_portfolio["ctr"] = None
    active_portfolio["ctd"] = None
    active_portfolio["cty"] = None
    #active_portfolio["index_id"] = None
    active_portfolio = active_portfolio.reset_index()
    
    
    # Por cada instrumento vamos completando los campos que no hicieron match en el join, por convencion trabajamos en el lado del fondo
    for i, instrument in active_portfolio.iterrows():
        #Vemos si el instrumento esta en el bmk
        if np.isnan(instrument["mcr_x"]):
            active_portfolio.set_value(i, "ctr", instrument["mcr_y"]*instrument["weight_active"])
            active_portfolio.set_value(i, "tipo_instrumento_x", instrument["tipo_instrumento_y"])
            active_portfolio.set_value(i, "moneda_x", instrument["moneda_y"])
            active_portfolio.set_value(i, "mcr_x", instrument["mcr_y"])
            active_portfolio.set_value(i, "duration_x", instrument["duration_y"])
            active_portfolio.set_value(i, "riesgo_x", instrument["riesgo_y"])
            active_portfolio.set_value(i, "sector_x", instrument["sector_y"])
            active_portfolio.set_value(i, "tasa_x", instrument["tasa_y"])
            active_portfolio.set_value(i, "riesgo_internacional_x", instrument["riesgo_internacional_y"])
            active_portfolio.set_value(i, "pais_emisor_x", instrument["pais_emisor_y"])
            active_portfolio.set_value(i, "nombre_emisor_x", instrument["nombre_emisor_y"])
            active_portfolio.set_value(i, "Index_Id_x", instrument["Index_Id_y"])
        else:
            active_portfolio.set_value(i, "ctr", instrument["mcr_x"]*instrument["weight_active"])
            active_portfolio.set_value(i, "ctd", instrument["duration_x"]*instrument["weight_x"])
            active_portfolio.set_value(i, "cty", instrument["tasa_x"]*instrument["weight_x"])

    # Finalmente recalculamos sigma agregado por si hubieron inconsistencias entre los mapeos, esto puede psar por cupones de bonos
    sigma_ag = np.sum(active_portfolio["ctr"])

    # Con el sigma nuevo podemos calcular el pcr exacto
    active_portfolio["pcr"] = active_portfolio["ctr"]/sigma_ag
    active_portfolio["codigo_fdo"] = fund_id
    active_portfolio["benchmark_id"] = benchmark_id

    # Ordenamos las columnas para el display
    active_portfolio = active_portfolio.rename(columns = {"Index_Id_x": "Index_Id"})
    active_portfolio = active_portfolio.reindex(columns = ["Index_Id", "benchmark_id","cantidad",
    "codigo_emi","codigo_fdo","codigo_ins","ctd","ctr","duration_x","duration_y",
    "fec_vtco","fecha_x","fecha_y", "index", "index_x","index_y","mcr_x","mcr_y",
    "moneda_x","moneda_y","monto","nombre_emisor_x","nombre_instrumento","nominal",
    "pais_emisor_x","pcr","precio","riesgo_x","riesgo_y","sector_x","tasa_x","tasa_y",
    "tipo_instrumento_x","tipo_instrumento_y","weight_active","weight_x","weight_y",
    "sector_y", "riesgo_internacional_x", "riesgo_internacional_y", "pais_emisor_y", "cty", "tipo_ra"])


    return active_portfolio


def get_historical_metrics(funds, dataset, fund_date, benchmark_date, inflation, days):
    '''
    Obtiene las metricas de riesgo agregadas en una serie de tiempo dado.
    Se deja fija la inflacion diaria porque no es una metrica dinamica
    en el analisis.
    '''
    # Definimos un dataframe para guardar los datos de las metricas historicamente
    serie = pd.DataFrame(columns=["Fecha", "Codigo_Fdo", "Slice", "Metric"])
    k = 0
    fund_date_iter = fund_date
    benchmark_date_iter = benchmark_date
    # Para cada fecha computamos una matriz de varianza covarianza
    for j in range(days):
        print("days left -> " + str(days - j))
        matrix = get_ewma_cov_matrix(data=dataset[j:], landa=0.94)
        # Para cada fondo computamos sus metricas
        for i, fund in funds.iterrows():
            fund_id = fund["codigo_fdo"]
            benchmark_id = fund["benchmark_id"]
            alpha_seeker = fund["alpha_seeker"]
            # Portfolio del fondo sin metricas de riesgo
            print(fund_date_iter)
            fund_portfolio_iter = get_portfolio(fund_date=fund_date_iter,
                                                fund_id=fund_id, 
                                                inflation=inflation)
            # Portfolio del benchmark sin metricas de riesgo
            benchmark_portfolio_iter = get_portfolio_bmk(benchmark_date=benchmark_date_iter,
                                                         benchmark_id=benchmark_id)
            try:
                # Portfolio activo con metricas de riesgo
                portfolio_iter = get_portfolio_metrics(fund_portfolio=fund_portfolio_iter,
                                                       benchmark_portfolio=benchmark_portfolio_iter,
                                                       fund_id=fund_id, matrix=matrix,
                                                       benchmark_id=benchmark_id,
                                                       alpha_seeker=alpha_seeker)
                te_clp = np.sum(portfolio_iter[portfolio_iter["moneda_x"] == "$"]["ctr"])
                te_clf = np.sum(portfolio_iter[portfolio_iter["moneda_x"] == "UF"]["ctr"])
                te_usd = np.sum(portfolio_iter[portfolio_iter["moneda_x"] == "US$"]["ctr"])
                te_eur = np.sum(portfolio_iter[portfolio_iter["moneda_x"] == "EU"]["ctr"])
                te_mxn = np.sum(portfolio_iter[portfolio_iter["moneda_x"] == "MX"]["ctr"])
                te_sol = np.sum(portfolio_iter[portfolio_iter["moneda_x"] == "SOL"]["ctr"])
                te_rea = np.sum(portfolio_iter[portfolio_iter["moneda_x"] == "REA"]["ctr"])
                te_chile = np.sum(portfolio_iter[portfolio_iter["pais_emisor_x"] == "CL"]["ctr"])
                te_mexico = np.sum(portfolio_iter[portfolio_iter["pais_emisor_x"] == "MX"]["ctr"])
                te_colombia = np.sum(portfolio_iter[portfolio_iter["pais_emisor_x"] == "CO"]["ctr"])
                te_peru = np.sum(portfolio_iter[portfolio_iter["pais_emisor_x"] == "PE"]["ctr"])
                te_brazil = np.sum(portfolio_iter[portfolio_iter["pais_emisor_x"] == "BR"]["ctr"])
                te_other = np.sum(portfolio_iter[(portfolio_iter["pais_emisor_x"] != "CL") & (portfolio_iter["pais_emisor_x"] != "MX") & (portfolio_iter["pais_emisor_x"] != "CO") & (portfolio_iter["pais_emisor_x"] != "PE") & (portfolio_iter["pais_emisor_x"] != "BR") ]["ctr"])
                dur = np.sum(portfolio_iter["ctd"])
                serie.loc[k] = [fund_date_iter, fund_id, "$", te_clp]
                serie.loc[k + 1] = [fund_date_iter, fund_id, "UF", te_clf]
                serie.loc[k + 2] = [fund_date_iter, fund_id, "US$", te_usd]
                serie.loc[k + 3] = [fund_date_iter, fund_id, "EU", te_eur]
                serie.loc[k + 4] = [fund_date_iter, fund_id, "MX", te_mxn]
                serie.loc[k + 5] = [fund_date_iter, fund_id, "SOL", te_sol]
                serie.loc[k + 6] = [fund_date_iter, fund_id, "REA", te_rea]
                serie.loc[k + 7] = [fund_date_iter, fund_id, "duration", dur]
                serie.loc[k + 8] = [fund_date_iter, fund_id, "chile", te_chile]
                serie.loc[k + 9] = [fund_date_iter, fund_id, "mexico", te_mexico]
                serie.loc[k + 10] = [fund_date_iter, fund_id, "colombia", te_colombia]
                serie.loc[k + 11] = [fund_date_iter, fund_id, "peru", te_peru]
                serie.loc[k + 12] = [fund_date_iter, fund_id, "brazil", te_brazil]
                serie.loc[k + 13] = [fund_date_iter, fund_id, "other", te_other]
                k += 14
            except:
                print("Error para " + fund_id + " en " + fund_date_iter)
        fund_date_iter = fs.get_prev_weekday(fund_date_iter)
        benchmark_date_iter = fs.get_prev_weekday(benchmark_date_iter)
    return serie