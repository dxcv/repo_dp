"""
Created on Mon 	Jan 23 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
sys.path.insert(1, '../yield_curve_library/')
import yield_curve as yc
sys.path.insert(2, '../performance_attribution_library/')
import performance_attribution as pa
import pandas as pd
import numpy as np
from math import log

# Para desabilitar warnings
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=FutureWarning)
pd.options.mode.chained_assignment = None 



def get_fx_serie(start_date, end_date, fx_id):
    '''
    Retorna la serie de precio de un determinado fx.
    '''
    path = ".\\querys_performance_attribution_report\\" + fx_id + ".sql"
    query = fs.read_file(path=path).replace("autodate1", start_date).replace("autodate2", end_date)
    serie = fs.get_frame_sql_user(server="Puyehue",
                                  database="MesaInversiones",
                                  username="usrConsultaComercial",
                                  password="Comercial1w",
                                  query=query)
    serie.set_index(["fecha"], inplace=True)
    return serie


def get_fx_return(start_date, end_date, fx_serie):
    '''
    Retorna el retorno entre dos fechas para una moneda, dada la serie del fx.
    '''
    fx_start = float(fx_serie.loc[fs.convert_string_to_date(start_date)])
    fx_end = float(fx_serie.loc[fs.convert_string_to_date(end_date)])
    ret_fx = (fx_end/fx_start) - 1
    return ret_fx


def get_funds():
    '''
    Retorna los fondos junto con su informacion basica.
    '''
    path = ".\\querys_performance_attribution_report\\fondos.sql"
    query = fs.read_file(path=path)
    funds = fs.get_frame_sql_user(server="Puyehue",
    						      database="MesaInversiones",
    						      username="usrConsultaComercial",
    						      password="Comercial1w",
    					          query=query)
    return funds
 

def compute_funds_attribution(funds, start_date, end_date, performance_columns, usd_return, clf_return, eur_return, mxn_return, pen_return, rea_return, ars_return, parameters_clp_start, parameters_clp_end, parameters_clf_start, parameters_clf_end, tau_clp, tau2_clp, tau_clf, tau2_clf, historical_analytical_return):
    '''
    Computa el performance attribution para todos los fondos y los retorna en un dataframe.
    '''
    portfolios = []
    # Iteramos para cada fondo computando el performance attribution de su portfolio
    for i, fund in funds.iterrows():
        # Obtenemos la informacion basica del fondo
        fund_id = fund["codigo_fdo"]
        print("computing -> " + fund_id)
        # Obtenemos los portfolios para el inicio y el fin del periodo de computo
        portfolio_start = get_portfolio(fund_id=fund_id, date=start_date)
        portfolio_end = get_portfolio(fund_id=fund_id, date=end_date)
        # Computamos el performance attribution entre ambos periodos
        portfolio_attribution = pa.get_portfolio_attribution(start_date=start_date,
                                                             end_date=end_date,
                                                             portfolio_start=portfolio_start,
                                                             portfolio_end=portfolio_end,
                                                             usd_return=usd_return,
                                                             clf_return=clf_return,
                                                             eur_return=eur_return,
                                                             mxn_return=mxn_return,
                                                             pen_return=pen_return,
                                                             rea_return=rea_return,
                                                             ars_return=ars_return,
                                                             parameters_clp_start=parameters_clp_start,
                                                             parameters_clp_end=parameters_clp_end,
                                                             parameters_clf_start=parameters_clf_start,
                                                             parameters_clf_end=parameters_clf_end,
                                                             tau_clp=tau_clp,
                                                             tau2_clp=tau2_clp,
                                                             tau_clf=tau_clf,
                                                             tau2_clf=tau2_clf)
        period_return = float(np.sum(portfolio_attribution["empirical_return"]))/10000
        kappa_t = log(period_return+1) / period_return
        portfolio_attribution[performance_columns] = portfolio_attribution[performance_columns] * kappa_t
        

        historical_analytical_return.set_value((end_date, fund_id), "retorno", period_return)


        # Agregamos el portfolio del fondo a la lista de portfolios
        portfolios.append(portfolio_attribution)
    # Concatenamos los portfolios en un dataframe
    portfolios = pd.concat(portfolios, ignore_index=False)
    return portfolios, historical_analytical_return


def get_portfolio(fund_id, date):
    '''
    Obtiene la cartera de un fondo desde la base de datos
    con llave codigo emisor, codigo instrumento, fecha de vencimiento
    y fecha de operacion.
    '''
    path = ".\\querys_performance_attribution_report\\portfolio.sql"
    query_fondos = fs.read_file(path=path).replace("autofund", fund_id).replace("autodate", date)
    portfolio = fs.get_frame_sql_user(server="Puyehue",
                                      database="MesaInversiones",
                                      username="usrConsultaComercial",
                                      password="Comercial1w",
                                      query=query_fondos)
    # Indexamos en codigo emisor, codigo instrumento, fecha de operacion y fecha de vencimiento. Es necesario por la notacion de los forwards.
    # tambien necesitamos la moneda porque las cueotas que se desagregan de fondos en otra moneda recursiva pueden generar problemas.
    portfolio.index = pd.MultiIndex.from_arrays(portfolio[["codigo_fdo", "codigo_emi", "codigo_ins", "fec_op", "fec_vcto", "moneda"]].values.T, names=["codigo_fdo", "codigo_emi", "codigo_ins", "fec_op", "fec_vcto", "moneda"])
    portfolio = portfolio.drop("codigo_fdo", 1).drop("codigo_emi", 1).drop("codigo_ins", 1).drop("fec_vcto", 1).drop("fec_op", 1).drop("moneda", 1)
    return portfolio


def get_parameters_series(start_date, end_date, tau_clp, tau2_clp, tau_clf, tau2_clf):
    '''
    Calibra las curvas clp y clf para dos fechas, dados los tau.
    '''
    yields_serie_clp = yc.get_historical_dataset(start_date, end_date, "clp")
    yields_serie_clf = yc.get_historical_dataset(start_date, end_date, "clf")

    parameters_columns = ["tau", "level", "slope", "curvature", "svensson", "tau2"]
    parameters_serie_clp = pd.DataFrame(columns=parameters_columns, index = ["fecha"])
    parameters_serie_clp = parameters_serie_clp.dropna()
    for i, yields in yields_serie_clp.iterrows():
        parameters = yc.get_parameters(yields_serie_clp[yields_serie_clp.index == i], tau_clp, tau2_clp)
        parameters_serie_clp.loc[i] = parameters


    parameters_serie_clf = pd.DataFrame(columns=parameters_columns, index = ["fecha"])
    parameters_serie_clf = parameters_serie_clf.dropna()
    for i, yields in yields_serie_clf.iterrows():
        parameters = yc.get_parameters(yields_serie_clf[yields_serie_clf.index == i], tau_clf, tau2_clf)
        parameters_serie_clf.loc[i] = parameters

    return parameters_serie_clp, parameters_serie_clf


def get_curves(start_date, end_date, parameters_serie_clp, parameters_serie_clf):
    '''
    Calibra las curvas clp y clf para dos fechas, dados los tau.
    '''
    # Calibramos las distintas curvas
    parameters_clp_start = parameters_serie_clp.loc[start_date]
    parameters_clp_end = parameters_serie_clp.loc[end_date]
    parameters_clf_start = parameters_serie_clf.loc[start_date]
    parameters_clf_end = parameters_serie_clf.loc[end_date]
    return parameters_clp_start, parameters_clp_end, parameters_clf_start, parameters_clf_end



def get_navs_serie(start_date, end_date):
     '''
     Computa la serie con todos los nav historicos de los portfolios.
     '''
     path_nav = ".\\querys_performance_attribution_report\\nav.sql"
     query = fs.read_file(path=path_nav).replace("autodate1", start_date).replace("autodate2", end_date)
     serie = fs.get_frame_sql_user(server="Puyehue",
                                   database="MesaInversiones",
                                   username="usrConsultaComercial",
                                   password="Comercial1w",
                                   query=query)
     serie.index = pd.MultiIndex.from_arrays(serie[["fecha", "codigo_fdo"]].values.T, names=["fecha", "codigo_fdo"])
     serie = serie.drop("fecha", 1).drop("codigo_fdo", 1)
     return serie


def get_nav_return(fund_id, start_date, end_date, navs_serie, tac_serie):
     '''
     Computa la rentabilidad sin tac de un fondo entre dos fechas.
     '''
     # Obtenemos el valor cuota inicial
     nav_start = float(navs_serie.loc[start_date, fund_id])
     # Obtenemos el valor cuota final
     nav_end = float(navs_serie.loc[end_date, fund_id])
     # Obtenemos el tac final
     tac = get_total_tac(start_date, end_date, tac_serie, fund_id)
     # Calculamos el retorno
     nav_return = float(nav_end/nav_start) + float(tac) - 1
     return nav_return


def get_tac_serie(start_date, end_date): 
    '''
    Retorna el tac total entre dos fechas
    '''
    path_tac = ".\\querys_performance_attribution_report\\tac.sql"
    query_tacs = fs.read_file(path_tac).replace("autodate1", start_date).replace("autodate2", end_date)
    serie = fs.get_frame_sql_user(server="Puyehue",
                                  database="MesaInversiones",
                                  username="usrConsultaComercial",
                                  password="Comercial1w",
                                  query=query_tacs)
    serie.set_index(["fecha", "codigo_fdo"], inplace=True)
    return serie


def get_total_tac(start_date, end_date, tac_serie, fund_id): 
    '''
    Retorna el tac total entre dos fechas
    '''
    tacs = tac_serie[(tac_serie.index.get_level_values("codigo_fdo") == fund_id)&(tac_serie.index.get_level_values("fecha") >= start_date)&(tac_serie.index.get_level_values("fecha") <= end_date)]
    total_tac = float((tacs +1).cumprod()["tac"].loc[end_date]) - 1
    return total_tac


def compute_advanced_funds_attribution(funds, start_date_iter, end_date_iter, start_date, end_date, mtd_days, usd, clf, eur, mxn, pen, rea, ars, parameters_serie_clp, parameters_serie_clf, tau_clp, tau2_clp, tau_clf, tau2_clf):
    '''
    Calcula el performance attribution entre dos fechas no necesariamente
    contiguas. Para esto se realizan n attribuciones las cuales se suavizan
    para consolidarlas en una suma para el periodo total.
    '''

    # Fijamos las columnascon las que trabaja
    # el dataframe para el performance attribution
    # entre dos fechas. Ademas, fijamos las columnas
    # que representan la descomposicion del retorno y
    # las columnas finales que utilizamos para el display.
    portfolio_columns = ["tipo_instrumento_start",
                         "monto_start", "duration_start", "tasa_start",
                         "precio_start", "riesgo_start", 
                         "tipo_instrumento_end", "monto_end", "duration_end",
                         "tasa_end", "precio_end", "riesgo_end", "weight_start",
                         "weight_end", "carry_return", "inflation_carry_return",
                         "level_return", "slope_return", "curvature_return",
                         "svensson_return", "spread_return", "fx_usd_return",
                         "fx_eur_return", "fx_clf_return", "fx_mx_return",
                         "fx_pen_return", "fx_rea_return", "fx_ars_return", "empirical_return",
                         "residual_return", "analytical_return"]

    performance_columns = ["carry_return", "inflation_carry_return",
                           "level_return", "slope_return", "curvature_return",
                           "svensson_return", "spread_return", "fx_usd_return",
                           "fx_eur_return", "fx_clf_return", "fx_mx_return",
                           "fx_pen_return", "fx_rea_return", "fx_ars_return", "empirical_return",
                           "residual_return", "analytical_return"]

    display_columns = ["weight_end",  "tipo_instrumento_end",
                       "duration_end", "riesgo_end", "weight_end",
                       "carry_return", "inflation_carry_return",
                       "level_return", "slope_return", "curvature_return",
                       "svensson_return", "spread_return", "fx_usd_return",
                       "fx_eur_return", "fx_clf_return", "fx_mx_return",
                       "empirical_return", "residual_return", "analytical_return"
                       , "fx_pen_return", "fx_rea_return", "fx_ars_return"]
    
    # Definimos el dataframe que representa la atribucion
    # entre dos fechas. Notar que la llave es por fondo
    funds_attribution = pd.DataFrame(columns=portfolio_columns)
    funds_attribution.index = pd.MultiIndex(levels=[[], [], [], [], [], []],
                                            labels=[[], [], [], [], [], []],
                                            names=["codigo_fdo", "codigo_emi", "codigo_ins", "fec_op", "fec_vcto", "moneda"])

    # Definimos un dataframe para los retornos historicos
    # de los fondos. Notar que necesitamos esto para generar
    # el factor de suavizacion kappa despues del computo total.

    historical_analytical_return = pd.DataFrame(columns=["fecha", "codigo_fdo", "retorno"])
    historical_analytical_return.set_index(["fecha", "codigo_fdo"], inplace=True)

    # Por cada dia computamos su atribucion y la sumamos al acumulado
    for t in range(mtd_days):
        # Primero obtenemos los parametros necesarios para calibrar las curvas reales y nominales
        parameters_clp_start, parameters_clp_end, parameters_clf_start, parameters_clf_end = get_curves(start_date=start_date_iter,
                                                                                                        end_date=end_date_iter,
                                                                                                        parameters_serie_clp=parameters_serie_clp,
                                                                                                        parameters_serie_clf=parameters_serie_clf)
        # Obtenemos el retorno del tipo de cambio
        usd_return = get_fx_return(start_date_iter, end_date_iter, usd)
        clf_return = get_fx_return(start_date_iter, end_date_iter, clf)
        eur_return = get_fx_return(start_date_iter, end_date_iter, eur)
        mxn_return = get_fx_return(start_date_iter, end_date_iter, mxn)
        pen_return = get_fx_return(start_date_iter, end_date_iter, pen)
        rea_return = get_fx_return(start_date_iter, end_date_iter, rea)
        ars_return = get_fx_return(start_date_iter, end_date_iter, ars)

        print("period " + str(mtd_days-t) + ": " + start_date_iter + " - " + end_date_iter)

        # Opcional por si se quieren graficar las curvas
        # yc.plot_curves([parameters_clp_start, parameters_clp_end, parameters_clf_start, parameters_clf_end])

        # Calcula mos el performance attribution de todos los fondos entre dos fechas
        funds_attribution_t, historical_analytical_return = compute_funds_attribution(funds=funds,
                                                                                      start_date=start_date_iter,
                                                                                      end_date=end_date_iter,
                                                                                      performance_columns=performance_columns,
                                                                                      usd_return=usd_return,
                                                                                      clf_return=clf_return,
                                                                                      eur_return=eur_return,
                                                                                      mxn_return=mxn_return,
                                                                                      pen_return=pen_return,
                                                                                      rea_return=rea_return,
                                                                                      ars_return=ars_return,
                                                                                      parameters_clp_start=parameters_clp_start,
                                                                                      parameters_clp_end=parameters_clp_end,
                                                                                      parameters_clf_start=parameters_clf_start,
                                                                                      parameters_clf_end=parameters_clf_end, 
                                                                                      tau_clp=tau_clp, 
                                                                                      tau2_clp=tau2_clp,
                                                                                      tau_clf=tau_clf, 
                                                                                      tau2_clf=tau2_clf,
                                                                                      historical_analytical_return=historical_analytical_return)
        # Hacemos el join con el dataframe del retorno acumulado para agregar
        # la performance de los instrumentos. Notar que los sufijos c y t 
        # representan la cartera acumulada y la del periodo respectivamente
        funds_attribution = pd.merge(funds_attribution, funds_attribution_t, how="outer", left_index=True, right_index=True, suffixes=("_c", "_t"))
        
        # Agregamos columnas nuevas donde ira el resultado acumulado para la proxima iteracion
        for col in funds_attribution_t.columns:
            funds_attribution[col] = None


        # Por cada periodo acumulamos el retorno del periodo anterior
        # tenemos tres casos dependiendo del instrumento
        for i, instrument in funds_attribution.iterrows():
            # Si el instrumento no estaba en el acumulado, es que es un intrumento nuevo (dejamos su retorno)
            if np.isnan(instrument["weight_start_c"]):
                funds_attribution.set_value(i, "tipo_instrumento_start", instrument["tipo_instrumento_start_t"])
                funds_attribution.set_value(i, "monto_start", instrument["monto_start_t"])
                funds_attribution.set_value(i, "duration_start", instrument["duration_start_t"])
                funds_attribution.set_value(i, "tasa_start", instrument["tasa_start_t"])
                funds_attribution.set_value(i, "precio_start", instrument["precio_start_t"])
                funds_attribution.set_value(i, "riesgo_start", instrument["riesgo_start_t"])
                funds_attribution.set_value(i, "tipo_instrumento_end", instrument["tipo_instrumento_end_t"])
                funds_attribution.set_value(i, "monto_end", instrument["monto_end_t"])
                funds_attribution.set_value(i, "duration_end", instrument["duration_end_t"])
                funds_attribution.set_value(i, "tasa_end", instrument["tasa_end_t"])
                funds_attribution.set_value(i, "precio_end", instrument["precio_end_t"])
                funds_attribution.set_value(i, "riesgo_end", instrument["riesgo_end_t"])
                funds_attribution.set_value(i, "weight_start", instrument["weight_start_t"])
                funds_attribution.set_value(i, "weight_end", instrument["weight_end_t"])
                funds_attribution.set_value(i, "carry_return", instrument["carry_return_t"])
                funds_attribution.set_value(i, "inflation_carry_return", instrument["inflation_carry_return_t"])
                funds_attribution.set_value(i, "level_return", instrument["level_return_t"])
                funds_attribution.set_value(i, "slope_return", instrument["slope_return_t"])
                funds_attribution.set_value(i, "curvature_return", instrument["curvature_return_t"])
                funds_attribution.set_value(i, "svensson_return", instrument["svensson_return_t"])
                funds_attribution.set_value(i, "spread_return", instrument["spread_return_t"])
                funds_attribution.set_value(i, "fx_usd_return", instrument["fx_usd_return_t"])
                funds_attribution.set_value(i, "fx_eur_return", instrument["fx_eur_return_t"])
                funds_attribution.set_value(i, "fx_clf_return", instrument["fx_clf_return_t"])
                funds_attribution.set_value(i, "fx_mx_return", instrument["fx_mx_return_t"])
                funds_attribution.set_value(i, "fx_pen_return", instrument["fx_pen_return_t"])
                funds_attribution.set_value(i, "fx_rea_return", instrument["fx_rea_return_t"])
                funds_attribution.set_value(i, "fx_ars_return", instrument["fx_ars_return_t"])
                funds_attribution.set_value(i, "empirical_return", instrument["empirical_return_t"])
                funds_attribution.set_value(i, "residual_return", instrument["residual_return_t"])
                funds_attribution.set_value(i, "analytical_return", instrument["analytical_return_t"])
            # Si el instrumento no esta en la atribucion t, es que es un intrumentoque se vendio (dejamos su retorno acumulado)
            elif np.isnan(instrument["weight_start_t"]):
                funds_attribution.set_value(i, "tipo_instrumento_start", instrument["tipo_instrumento_start_c"])
                funds_attribution.set_value(i, "monto_start", instrument["monto_start_c"])
                funds_attribution.set_value(i, "duration_start", instrument["duration_start_c"])
                funds_attribution.set_value(i, "tasa_start", instrument["tasa_start_c"])
                funds_attribution.set_value(i, "precio_start", instrument["precio_start_c"])
                funds_attribution.set_value(i, "riesgo_start", instrument["riesgo_start_c"])
                funds_attribution.set_value(i, "tipo_instrumento_end", instrument["tipo_instrumento_end_c"])
                funds_attribution.set_value(i, "monto_end", instrument["monto_end_c"])
                funds_attribution.set_value(i, "duration_end", instrument["duration_end_c"])
                funds_attribution.set_value(i, "tasa_end", instrument["tasa_end_c"])
                funds_attribution.set_value(i, "precio_end", instrument["precio_end_c"])
                funds_attribution.set_value(i, "riesgo_end", instrument["riesgo_end_c"])
                funds_attribution.set_value(i, "weight_start", instrument["weight_start_c"])
                funds_attribution.set_value(i, "weight_end", instrument["weight_end_c"])
                funds_attribution.set_value(i, "carry_return", instrument["carry_return_c"])
                funds_attribution.set_value(i, "inflation_carry_return", instrument["inflation_carry_return_c"])
                funds_attribution.set_value(i, "level_return", instrument["level_return_c"])
                funds_attribution.set_value(i, "slope_return", instrument["slope_return_c"])
                funds_attribution.set_value(i, "curvature_return", instrument["curvature_return_c"])
                funds_attribution.set_value(i, "svensson_return", instrument["svensson_return_c"])
                funds_attribution.set_value(i, "spread_return", instrument["spread_return_c"])
                funds_attribution.set_value(i, "fx_usd_return", instrument["fx_usd_return_c"])
                funds_attribution.set_value(i, "fx_eur_return", instrument["fx_eur_return_c"])
                funds_attribution.set_value(i, "fx_clf_return", instrument["fx_clf_return_c"])
                funds_attribution.set_value(i, "fx_mx_return", instrument["fx_mx_return_c"])
                funds_attribution.set_value(i, "fx_pen_return", instrument["fx_pen_return_c"])
                funds_attribution.set_value(i, "fx_rea_return", instrument["fx_rea_return_c"])
                funds_attribution.set_value(i, "fx_ars_return", instrument["fx_ars_return_c"])
                funds_attribution.set_value(i, "empirical_return", instrument["empirical_return_c"])
                funds_attribution.set_value(i, "residual_return", instrument["residual_return_c"])
                funds_attribution.set_value(i, "analytical_return", instrument["analytical_return_c"])          
            # Si el instrumento esta en ambos periodos, sumamos todos sus retornos en el acumulado
            else:
                funds_attribution.set_value(i, "tipo_instrumento_start", instrument["tipo_instrumento_start_t"])
                funds_attribution.set_value(i, "monto_start", instrument["monto_start_t"])
                funds_attribution.set_value(i, "duration_start", instrument["duration_start_t"])
                funds_attribution.set_value(i, "tasa_start", instrument["tasa_start_t"])
                funds_attribution.set_value(i, "precio_start", instrument["precio_start_t"])
                funds_attribution.set_value(i, "riesgo_start", instrument["riesgo_start_t"])
                funds_attribution.set_value(i, "tipo_instrumento_end", instrument["tipo_instrumento_end_t"])
                funds_attribution.set_value(i, "monto_end", instrument["monto_end_t"])
                funds_attribution.set_value(i, "duration_end", instrument["duration_end_t"])
                funds_attribution.set_value(i, "tasa_end", instrument["tasa_end_t"])
                funds_attribution.set_value(i, "precio_end", instrument["precio_end_t"])
                funds_attribution.set_value(i, "riesgo_end", instrument["riesgo_end_t"])
                funds_attribution.set_value(i, "weight_start", instrument["weight_start_t"])
                funds_attribution.set_value(i, "weight_end", instrument["weight_end_t"])
                funds_attribution.set_value(i, "carry_return", instrument["carry_return_t"] + instrument["carry_return_c"])
                funds_attribution.set_value(i, "inflation_carry_return", instrument["inflation_carry_return_t"] + instrument["inflation_carry_return_c"])
                funds_attribution.set_value(i, "level_return", instrument["level_return_t"] + instrument["level_return_c"])
                funds_attribution.set_value(i, "slope_return", instrument["slope_return_t"] + instrument["slope_return_c"])
                funds_attribution.set_value(i, "curvature_return", instrument["curvature_return_t"] + instrument["curvature_return_c"])
                funds_attribution.set_value(i, "svensson_return", instrument["svensson_return_t"] + instrument["svensson_return_c"])
                funds_attribution.set_value(i, "spread_return", instrument["spread_return_t"] + instrument["spread_return_c"])
                funds_attribution.set_value(i, "fx_usd_return", instrument["fx_usd_return_t"] + instrument["fx_usd_return_c"])
                funds_attribution.set_value(i, "fx_eur_return", instrument["fx_eur_return_t"] + instrument["fx_eur_return_c"])
                funds_attribution.set_value(i, "fx_clf_return", instrument["fx_clf_return_t"] + instrument["fx_clf_return_c"])
                funds_attribution.set_value(i, "fx_mx_return", instrument["fx_mx_return_t"] + instrument["fx_mx_return_c"])
                funds_attribution.set_value(i, "fx_pen_return", instrument["fx_pen_return_t"] + instrument["fx_pen_return_c"])
                funds_attribution.set_value(i, "fx_rea_return", instrument["fx_rea_return_t"] + instrument["fx_rea_return_c"])
                funds_attribution.set_value(i, "fx_ars_return", instrument["fx_ars_return_t"] + instrument["fx_ars_return_c"])
                funds_attribution.set_value(i, "empirical_return", instrument["empirical_return_t"] + instrument["empirical_return_c"])
                funds_attribution.set_value(i, "residual_return", instrument["residual_return_t"] + instrument["residual_return_c"])
                funds_attribution.set_value(i, "analytical_return", instrument["analytical_return_t"] + instrument["analytical_return_c"])

        # Dejamos las columnas del acumulado total
        funds_attribution = funds_attribution[funds_attribution_t.columns]
        
        # Actualizamos las fechas para el siguiente periodo
        end_date_iter = start_date_iter
        start_date_iter = fs.get_prev_weekday(end_date_iter)
    
    # Ahora calculamos el kappa total del periodo para cada fondo
    historical_analytical_return.sort_index(level="fecha", inplace=True, ascending=False)
    funds["kappa"] = None
    funds["nav_return"] = None
    for i, fund in funds.iterrows():
        fund_id = fund["codigo_fdo"]
        # Obtenemos el retorno analitico total acumulado hasta el final del periodo
        fund_analytical_return_serie = historical_analytical_return[(historical_analytical_return.index.get_level_values("codigo_fdo") == fund_id)]["retorno"]
        fund_total_return = (fund_analytical_return_serie+1).cumprod().loc[end_date, fund_id] - 1
        # Calculamos el kappa para el periodo (smoothness factor)
        fund_kappa = log(fund_total_return+1) / fund_total_return 
        funds.set_value(i, "kappa", fund_kappa)
        # Calculamos el retorno empirico para ver el valor residual en el reporte
        nav_return = get_nav_return(fund_id, bottom_date, end_date, navs_serie, tac_serie)
        nav_return = nav_return * 10000
        funds.set_value(i, "nav_return", nav_return)

    # Finalmente hacemos un join del portfolio con la info de 
    # los fondos para dividir cadaportfolio con su kappa respectivo
    funds.set_index(["codigo_fdo"], inplace=True)
    funds_attribution = pd.merge(funds_attribution, funds, how="left", left_index=True, right_index=True)
    funds_attribution[performance_columns] = funds_attribution[performance_columns].divide(funds_attribution["kappa"], axis=0) 
    funds_attribution = funds_attribution[display_columns]

    return funds_attribution, funds


def print_report_pdf(funds, funds_attribution, start_date, end_date):
    '''
    Exporta el reporte a un pdf consolidado. 
    '''
    # Abrimos el workbook
    wb = fs.open_workbook(path="AttributionReport.xlsx", screen_updating=True, visible=True)
    # Borramos la informacion pasada
    fs.clear_table_xl(wb=wb,sheet="Historical",row=2,column=1)
    fs.clear_sheet_xl(wb=wb, sheet="Dataset")
    fs.clear_sheet_xl(wb=wb, sheet="Funds")
    # Insertamos la data en el excel
    fs.paste_val_xl(wb=wb, sheet="Historical", row=2, column=1, value=start_date)
    fs.paste_val_xl(wb=wb, sheet="Historical", row=2, column=2, value=end_date)
    fs.paste_val_xl(wb=wb, sheet="Dataset", row=1, column=1, value=funds_attribution)
    fs.paste_val_xl(wb=wb, sheet="Funds", row=1, column=1, value=funds)
    # Por cada fondo imprimimos su reporte
    for i, fund in funds.iterrows():
        fund_id = i
        print("printing -> " + fund_id)
        fs.paste_val_xl(wb=wb, sheet="Report", row=9, column=2, value=fund_id)
        path_pdf = fs.get_self_path() + "output_performance_attribution_report\\" + str(i) +  fund_id + ".pdf"
        fs.export_sheet_pdf(sheet_index=fs.get_sheet_index(wb, "Report") - 1,
                            path_in=".",
                            path_out=path_pdf)
    # Guardamos y cerramos el excel
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)
    # Consolidamos todos los documentos en uno y luego los borr amos
    fs.merge_pdf(path=".\\output_performance_attribution_report\\", output_name="performance_attribution_report.pdf")
    for i, fund in funds.iterrows():
        fund_id = i
        fs.delete_file(".\\output_performance_attribution_report\\" + str(i) + fund_id + ".pdf")
    
    name = "Performance_Attribution_Report_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    src = ".\\output_performance_attribution_report\\performance_attribution_report.pdf"
    dst = "L:\\Rates & FX\\fsb\\reporting\\performance_attribution_report_backup\\" + name
    fs.copy_file(src, dst)

def send_mail_report(spot_date):
    '''
    Envia el mail a fernando suarez 1313 y borra el pdf.
    '''
    print("sending mail ...", end="")
    subject = "Reporte de performance attribution"
    body = "Estimados, adjunto el reporte diario de performance attribution al " + spot_date +".\nSaludos"
    mail_list = ["fsuarez@credicorpcapital.com", "fsuarez1@uc.cl"]
    path = fs.get_self_path() + "output_performance_attribution_report\\performance_attribution_report.pdf"
    paths = [path]
    fs.send_mail_attach(subject=subject, body=body, mails=mail_list, attachment_paths=paths)
    fs.delete_file(path)


print("starting....")
# Cerramos posibles instancias de Excel abiertas
# fs.kill_excel()

# Fijamos las fechas en que trabajaremos
spot_date = fs.get_ndays_from_today(0)
end_date = fs.get_prev_weekday(spot_date)
start_date = fs.get_prev_weekday(end_date)
mtd_days = fs.get_current_weekdays_year(fs.convert_string_to_date(end_date)) - 1
bottom_date = fs.get_nweekdays_from_date(mtd_days, end_date)
start_date_iter = start_date
end_date_iter = end_date


# Fijamos los tau que utilizamos para modelar la curva
tau_clp = 4.5
tau2_clp = 10

tau_clf = 0.05
tau2_clf = 15

# Obtenemos los fondos con su informacion basica
funds = get_funds()
# Descargamos las distintas series que necesitamos
# para construir el performance attribution. Se 
# descargan para ahorrar llamadas al servidor.
navs_serie = get_navs_serie(bottom_date, end_date)
tac_serie = get_tac_serie(bottom_date, end_date)
usd = get_fx_serie(bottom_date, end_date, "usd")
clf = get_fx_serie(bottom_date, end_date, "clf")
eur = get_fx_serie(bottom_date, end_date, "eur")
mxn = get_fx_serie(bottom_date, end_date, "mxn")
pen = get_fx_serie(bottom_date, end_date, "pen")
rea = get_fx_serie(bottom_date, end_date, "rea")
ars = get_fx_serie(bottom_date, end_date, "ars")
parameters_serie_clp, parameters_serie_clf = get_parameters_series(bottom_date, end_date, tau_clp, tau2_clp, tau_clf, tau2_clf)

# Computamos el performance attribution de todos los fondos
# para todo el periodo acumuldo desde bottom date. Esto se hace
# calculando la attribucion dtd y luego sumandolas ponderadas 
# por un factor de smoothness (kappa).
funds_attribution, funds = compute_advanced_funds_attribution(funds=funds,
                                                              start_date_iter=start_date_iter,
                                                              end_date_iter=end_date_iter,
                                                              start_date=start_date,
                                                              end_date=end_date,
                                                              mtd_days=mtd_days,
                                                              usd=usd,
                                                              clf=clf,
                                                              eur=eur,
                                                              mxn=mxn,
                                                              pen=pen,
                                                              rea=rea,
                                                              ars=ars,
                                                              parameters_serie_clp=parameters_serie_clp,
                                                              parameters_serie_clf=parameters_serie_clf,
                                                              tau_clp=tau_clp,
                                                              tau2_clp=tau2_clp,
                                                              tau_clf=tau_clf,
                                                              tau2_clf=tau2_clf)

# Imprimimos el reporte en la plantilla
print_report_pdf(funds, funds_attribution, bottom_date, end_date)

# Se envia el correo con el reporte
send_mail_report(spot_date)