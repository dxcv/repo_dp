"""
Created on Mon 	Jan 23 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
sys.path.insert(1, '../yield_curve_library/')
import yield_curve as yc
import pandas as pd
import numpy as np
import math as math
import matplotlib.pyplot as plt


def get_portfolio_attribution(start_date, end_date, portfolio_start,  portfolio_end, usd_return, clf_return, eur_return, mxn_return, pen_return, rea_return, ars_return, parameters_clp_start, parameters_clp_end, parameters_clf_start, parameters_clf_end, tau_clp, tau2_clp, tau_clf, tau2_clf):
    '''
    Computa el performance attribution entre el portfolio inicial y final de un fondo.
    '''
    # Juntamos ambos porfolios en un dataframe que represente el performance attribution
    portfolio = pd.merge(portfolio_start, portfolio_end, how="outer", left_index=True, right_index=True, suffixes=("_start", "_end"))
    # Botamos los isntrumentos que no estaban en el dia inicial o en el final. 
    # Ademas, sacamos del analisis los bonos con duracion cero.
    portfolio = portfolio.dropna(subset=["tipo_instrumento_start", "tipo_instrumento_end"])
    portfolio = portfolio[(portfolio["tipo_instrumento_start"] == "Cuota de Fondo") | (portfolio["tipo_instrumento_start"] == "FX Forward") | (portfolio["duration_start"] != 0.0) & (portfolio["duration_end"] != 0.0)]
    # Calculamos los weights iniciales y finales del portfolio
    aum_start = np.sum(portfolio["monto_start"])
    portfolio["weight_start"] = portfolio["monto_start"] / aum_start
    aum_end = np.sum(portfolio["monto_end"])
    portfolio["weight_end"] = portfolio["monto_end"] / aum_end
    # Seteamos nuevas columnas para el attribution
    portfolio["empirical_return"] = None
    portfolio["carry_return"] = None
    portfolio["inflation_carry_return"] = None
    portfolio["level_return"] = None
    portfolio["slope_return"] = None
    portfolio["curvature_return"] = None
    portfolio["svensson_return"] = None
    portfolio["spread_return"] = None
    portfolio["fx_usd_return"] = None
    portfolio["fx_eur_return"] = None
    portfolio["fx_clf_return"] = None
    portfolio["fx_mx_return"] = None
    portfolio["fx_pen_return"] = None
    portfolio["fx_rea_return"] = None
    portfolio["fx_ars_return"] = None
    portfolio["residual_return"] = None
    portfolio["analytical_return"] = None
    # Por cada instrumento computamos su performance attribution
    for i, instrument in portfolio.iterrows():
        tipo_instrumento = instrument["tipo_instrumento_end"]
        currency =i[5]
        # Tenemos tres casos: si el attribution es posible calcularlo en base a su yield, si no utilizamos el precio, el ultimo caso son los forwards
        if (tipo_instrumento in ["Bono de Gobierno", "Bono Corporativo", "Deposito", "Factura", "Letra Hipotecaria"]) and (currency in ["$", "UF"]):
            empirical_return, carry_return, inflation_carry_return, level_return, slope_return, curvature_return, svensson_return, spread_return, fx_usd_return, fx_clf_return, fx_eur_return, fx_mx_return, fx_pen_return, fx_rea_return, fx_ars_return = get_bond_attribution_by_yield(start_date, end_date, instrument, clf_return, parameters_clp_start, parameters_clp_end, parameters_clf_start, parameters_clf_end, tau_clp, tau2_clp, tau_clf, tau2_clf)      
        elif (tipo_instrumento in ["Bono de Gobierno", "Bono Corporativo", "Deposito"] and currency != "$" and currency != "UF") or tipo_instrumento == "Cuota de Fondo":
            empirical_return, carry_return, inflation_carry_return, level_return, slope_return, curvature_return, svensson_return, spread_return, fx_usd_return, fx_clf_return, fx_eur_return, fx_mx_return, fx_pen_return, fx_rea_return, fx_ars_return = get_bond_attribution_by_price(instrument, usd_return, clf_return, eur_return, mxn_return, pen_return, rea_return, ars_return)
        elif tipo_instrumento == "FX Forward":
            empirical_return, carry_return, inflation_carry_return, level_return, slope_return, curvature_return, svensson_return, spread_return, fx_usd_return, fx_clf_return, fx_eur_return, fx_mx_return, fx_pen_return, fx_rea_return, fx_ars_return = get_fwd_attribution(instrument, usd_return, clf_return, eur_return, mxn_return, pen_return, rea_return, ars_return)
        # Agregamos las contribuciones al dataframe
        instrument["empirical_return"] = empirical_return
        instrument["carry_return"] = carry_return
        instrument["inflation_carry_return"] = inflation_carry_return
        instrument["level_return"] = level_return
        instrument["slope_return"] = slope_return
        instrument["curvature_return"] = curvature_return
        instrument["svensson_return"] = svensson_return
        instrument["spread_return"] = spread_return
        instrument["fx_usd_return"] = fx_usd_return
        instrument["fx_eur_return"] = fx_eur_return
        instrument["fx_clf_return"] = fx_clf_return
        instrument["fx_mx_return"] = fx_mx_return
        instrument["fx_pen_return"] = fx_pen_return
        instrument["fx_rea_return"] = fx_rea_return
        instrument["fx_ars_return"] = fx_ars_return
        portfolio.loc[i] = instrument

    # Calculamos el retorno total del analisis de cada instrumento junto con su valor residual
    portfolio["analytical_return"] = portfolio["carry_return"] + portfolio["inflation_carry_return"] + portfolio["level_return"] + portfolio["slope_return"] + portfolio["curvature_return"] + portfolio["svensson_return"] + portfolio["spread_return"] + portfolio["fx_usd_return"] + portfolio["fx_eur_return"] + portfolio["fx_clf_return"] + portfolio["fx_mx_return"] + portfolio["fx_pen_return"] + portfolio["fx_rea_return"] + portfolio["fx_ars_return"]
    portfolio["residual_return"] = portfolio["empirical_return"] - portfolio["analytical_return"]
    # Dejamos todo en basis points
    factors = ["empirical_return", "carry_return", "inflation_carry_return", "level_return", 
               "slope_return", "curvature_return", "svensson_return",
               "spread_return", "fx_usd_return", "fx_clf_return", "fx_eur_return", 
               "fx_mx_return", "fx_pen_return", "fx_rea_return", "fx_ars_return","residual_return", "analytical_return"]
    portfolio[factors] = portfolio[factors] * 10000 
    return portfolio


def get_bond_attribution_by_yield(start_date, end_date, instrument, clf_return, parameters_clp_start, parameters_clp_end, parameters_clf_start, parameters_clf_end, tau_clp, tau2_clp, tau_clf, tau2_clf):
    '''
    Computa el performance attribution de un instrumentos de renta fija en base a su yield.
    '''
    instrument_key = instrument.name

    price_start = float(instrument["precio_start"])
    price_end = float(instrument["precio_end"])
    # Obtenemos la informacion basica del instrumento
    tipo_instrumento = instrument["tipo_instrumento_end"]
    # Por defecto usamos el weight final del periodo (necesitamos que sume uno)
    weight = float(instrument["weight_end"])
    currency = instrument_key[5]
    yield_end = float(instrument["tasa_end"])
    yield_start = float(instrument["tasa_start"])
    # Usamos la yield promedio para calculo de carry
    yield_avg = (yield_end + yield_start) / 2
    duration_start = float(instrument["duration_start"])
    duration_end = float(instrument["duration_end"])
    # Usamos la duracion promedio para retorno de spread y curva
    duration_avg = float((duration_start + duration_end) / 2)
    # Asumimos que los tenors son iguales a las duraciones.
    # Esto es representativo en medida en que los bonos
    # tengan estructura de pago cero cupon
    tenor_start = np.array([duration_start])
    tenor_end = np.array([duration_end])
    # Seteamos todas las contribuciones en cero por defecto
    empirical_return = 0.0
    carry_return = 0.0
    inflation_carry_return = 0.0
    level_return = 0.0
    slope_return = 0.0
    curvature_return = 0.0
    svensson_return = 0.0
    spread_return = 0.0
    fx_usd_return = 0.0
    fx_eur_return = 0.0
    fx_clf_return = 0.0
    fx_mx_return = 0.0
    fx_pen_return = 0.0
    fx_rea_return = 0.0
    fx_ars_return = 0.0

    # Calculamos el retorno real del instrumento en base a su precio
    empirical_return = weight * ((price_end/price_start)-1)
    
    # Calculamos el carry contribution del instrumento.
    # El codigo comentado sirve para attribution DTD.
    # Notar que en el intervalo viernes-lunes se debe
    # agregar el carry del fin de semana
    
    # carry_return = weight * math.log(1 + (yield_avg/365)) * days
    
    
    if fs.convert_string_to_date(end_date).weekday() != 0:
        carry_return = weight * math.log(1 + (yield_avg/365))
    else:
        carry_return = weight * math.log(1 + (yield_avg/365)) * 3
    
    
    # Calculamos el carry por inflacion del instrumento.
    # Aca no es necesario el caso del fin de semana, ya
    # que el carry viene implicito en la uf de ambos dias.
    if currency == "UF":
        inflation_carry_return = weight * clf_return
    # Ahora calculamos la contribucion de la curva al
    # retorno. Para esto se modela la curva con
    # Nelson-Siegel-Svensson. Para obtener la tasa base
    # de los bonos nos ponemos en dos casos. Si es un bono
    # de gobierno usamos su tasa orginial. Si el instrumento
    # tiene algun grado de spread calculamos su base con
    # la curva modelada
    if tipo_instrumento == "Bono de Gobierno":
        base_yield_end = yield_end
        base_yield_start = yield_start
        if currency == "$":
            tau = tau_clp
            tau2 = tau_clp
        elif currency == "UF":
            tau = tau_clp
            tau2 = tau_clp
    else:
        if currency == "$":
            base_yield_start = yc.compute_yields(tenors=tenor_start, parameters=parameters_clp_start)[0]
            base_yield_end = yc.compute_yields(tenors=tenor_end, parameters=parameters_clp_end)[0]
            tau = tau_clp
            tau2 = tau_clp
        elif currency == "UF":
            base_yield_start = yc.compute_yields(tenors=tenor_start, parameters=parameters_clf_start)[0]
            base_yield_end = yc.compute_yields(tenors=tenor_end, parameters=parameters_clf_end)[0]
            tau = tau_clf
            tau2 = tau_clf
    # Calculamos la variacion de tasa y las exposiciones a los factores
    base_yield_change = base_yield_end - base_yield_start
    level_exposure = yc.level_exposure(tenors=tenor_start, tau=tau)
    slope_exposure = yc.slope_exposure(tenors=tenor_start, tau=tau)[0]
    curvature_exposure = yc.curvature_exposure(tenors=tenor_start, tau=tau)[0]
    svensson_exposure = yc.svensson_exposure(tenors=tenor_start, tau=tau2)[0]
    # Obtenemos los parametros de las distintas curvas
    if currency == "$":
        level_parameter_start = parameters_clp_start[1]
        level_parameter_end = parameters_clp_end[1]
        slope_parameter_start = parameters_clp_start[2]
        slope_parameter_end = parameters_clp_end[2]
        curvature_parameter_start = parameters_clp_start[3]
        curvature_parameter_end = parameters_clp_end[3]
        svensson_parameter_start = parameters_clp_start[4]
        svensson_parameter_end = parameters_clp_end[4]
    elif currency == "UF":
        level_parameter_start = parameters_clf_start[1]
        level_parameter_end = parameters_clf_end[1]
        slope_parameter_start = parameters_clf_start[2]
        slope_parameter_end = parameters_clf_end[2]
        curvature_parameter_start = parameters_clf_start[3]
        curvature_parameter_end = parameters_clf_end[3]
        svensson_parameter_start = parameters_clf_start[4]
        svensson_parameter_end = parameters_clf_end[4]
    # Calculamos la variacion de tasa por factor
    level_yield_chge = level_exposure * (level_parameter_end-level_parameter_start)
    slope_yield_chge = slope_exposure * (slope_parameter_end-slope_parameter_start)
    curvature_yield_chge = curvature_exposure * (curvature_parameter_end-curvature_parameter_start)
    svensson_yield_chge = svensson_exposure * (svensson_parameter_end-svensson_parameter_start)
    # Calculamos la variacion total de tasa agregada
    total_yield_chge = level_yield_chge + slope_yield_chge + curvature_yield_chge + svensson_yield_chge
    # Normalizamos los cambios de tasa por factor
    if total_yield_chge != 0.0:
        level_yield_chge_normalized = (level_yield_chge*base_yield_change) / total_yield_chge
        slope_yield_chge_normalized = (slope_yield_chge*base_yield_change) / total_yield_chge
        curvature_yield_chge_normalized = (curvature_yield_chge*base_yield_change) / total_yield_chge
        svensson_yield_chge_normalized = (svensson_yield_chge*base_yield_change) / total_yield_chge
    else:
        level_yield_chge_normalized = 0.0
        slope_yield_chge_normalized = 0.0
        curvature_yield_chge_normalized = 0.0
        svensson_yield_chge_normalized = 0.0
    # Finalmente calculamos la contribucion al retorno de cada factor
    level_return = -1 * duration_avg * level_yield_chge_normalized * weight
    slope_return = -1 * duration_avg * slope_yield_chge_normalized * weight
    curvature_return = -1 * duration_avg * curvature_yield_chge_normalized * weight
    svensson_return = -1 * duration_avg * svensson_yield_chge_normalized * weight
    # Calculamos la contribucion del movimiento de spread
    spread_change = (yield_end-base_yield_end) -   (yield_start-base_yield_start)
    spread_return = -1 * weight * duration_avg * spread_change
    return empirical_return, carry_return, inflation_carry_return, level_return, slope_return, curvature_return, svensson_return, spread_return, fx_usd_return, fx_clf_return, fx_eur_return, fx_mx_return, fx_pen_return, fx_rea_return, fx_ars_return


def get_bond_attribution_by_price(instrument, usd_return, clf_return, eur_return, mxn_return, pen_return, rea_return, ars_return):
    '''
    Computa el performance attribution de un bono en base a su precio.
    '''
    # Seteamos todas las contribuciones en cero por defecto
    empirical_return = 0.0
    carry_return = 0.0
    inflation_carry_return = 0.0
    level_return = 0.0
    slope_return = 0.0
    curvature_return = 0.0
    svensson_return = 0.0
    spread_return = 0.0
    fx_usd_return = 0.0
    fx_eur_return = 0.0
    fx_clf_return = 0.0
    fx_mx_return = 0.0
    fx_pen_return = 0.0
    fx_rea_return = 0.0
    fx_ars_return = 0.0

    instrument_key = instrument.name

    # Utilizamos el weight final por defecto
    weight = float(instrument["weight_end"])
    currency = instrument_key[5]
    # Obtenemos el precio del instrumento
    price_start = float(instrument["precio_start"])
    price_end = float(instrument["precio_end"])
    # Calculamos la contribucion al retorno del las fx,
    # notar que atribuimos a level todo y usamos dirty price
    # Como usamos dirty price hay que dividir por el fx return
    # en la descomposicion
    if currency == "US$":
        level_return = weight * (((price_end / price_start) - 1)/(1+usd_return))
        fx_usd_return = usd_return * weight
        empirical_return = level_return + fx_usd_return
    elif currency == "EU":
        level_return = weight * (((price_end / price_start) - 1)/(1+eur_return))
        fx_eur_return = eur_return * weight
        empirical_return = level_return + fx_eur_return
    elif currency == "UF":
        level_return = weight * (((price_end / price_start) - 1)/(1+clf_return))
        fx_clf_return = clf_return * weight
        empirical_return = level_return + fx_clf_return
    elif currency == "MX":
        level_return = weight * (((price_end / price_start) - 1)/(1+mxn_return))
        fx_mx_return = mxn_return * weight
        empirical_return = level_return + fx_mx_return
    elif currency == "SOL":
        level_return = weight * (((price_end / price_start) - 1)/(1+pen_return))
        fx_pen_return = pen_return * weight
        empirical_return = level_return + fx_pen_return
    elif currency == "REA":
        level_return = weight * (((price_end / price_start) - 1)/(1+rea_return))
        fx_rea_return = rea_return * weight
        empirical_return = level_return + fx_rea_return
    elif currency == "ARS":
        level_return = weight * (((price_end / price_start) - 1)/(1+ars_return))
        fx_ars_return = ars_return * weight
        empirical_return = level_return + fx_ars_return
    return empirical_return, carry_return, inflation_carry_return, level_return, slope_return, curvature_return, svensson_return, spread_return, fx_usd_return, fx_clf_return, fx_eur_return, fx_mx_return, fx_pen_return, fx_rea_return, fx_ars_return


def get_fwd_attribution(instrument, usd_return, clf_return, eur_return, mxn_return, pen_return, rea_return, ars_return):
    '''
    Computa el performance attribution de un fx forward.
    '''
    # Seteamos todas las contribuciones en cero por defecto
    empirical_return = 0.0
    carry_return = 0.0
    inflation_carry_return = 0.0
    level_return = 0.0
    slope_return = 0.0
    curvature_return = 0.0
    svensson_return = 0.0
    spread_return = 0.0
    fx_usd_return = 0.0
    fx_eur_return = 0.0
    fx_clf_return = 0.0
    fx_mx_return = 0.0
    fx_pen_return = 0.0
    fx_rea_return = 0.0
    fx_ars_return = 0.0

    instrument_key = instrument.name

    # Utilizamos el weight final por defecto
    weight = float(instrument["weight_end"])
    currency = instrument_key[5]
    # Calculamos la contribucion de los fwds
    if currency == "US$":
        fx_usd_return = weight * usd_return
        empirical_return = fx_usd_return
    elif currency == "EU":
        fx_eur_return = weight * eur_return
        empirical_return = fx_eur_return
    elif currency == "UF":
        fx_clf_return = weight * clf_return
        empirical_return = fx_clf_return
    elif currency == "MX":
        fx_mx_return = weight * mxn_return
        empirical_return = fx_mx_return
    elif currency == "SOL":
        fx_pen_return = weight * pen_return
        empirical_return = fx_pen_return
    elif currency == "REA":
        fx_rea_return = weight * rea_return
        empirical_return = fx_rea_return
    elif currency == "ARS":
        fx_ars_return = weight * ars_return
        empirical_return = fx_ars_return
    return empirical_return, carry_return, inflation_carry_return, level_return, slope_return, curvature_return, svensson_return, spread_return, fx_usd_return, fx_clf_return, fx_eur_return, fx_mx_return, fx_pen_return, fx_rea_return, fx_ars_return

