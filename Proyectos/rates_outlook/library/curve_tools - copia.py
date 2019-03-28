"""
Created on Wed Jul 05 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, "../../libreria/")
sys.path.insert(0, "../../indice_camara/")

import libreria_fdo as fs
import pandas as pd
import numpy as np
from scipy import optimize
from tia.bbg import v3api
import datetime as dt
import math
from scipy.ndimage.interpolation import shift
import dateutil.relativedelta as rd
import calculo_indice_camara

def compute_expected_path(path_scenarios, path_distribution):
    '''
    Calcula el path de TPM esperado en base a la distribucion.
    '''
    path_scenarios["expected"] = 0.0
    for scenario, data in path_distribution.iterrows():
        probability = float(data["probability"])
        path_scenarios["expected"] += probability * path_scenarios[scenario]
    return path_scenarios


def sum_term_premia(path_scenarios, term_premia):
    '''
    Le suma el term_premia a los path de TPM.
    '''
    start_date = path_scenarios.index[0]
    term_premia = term_premia.reset_index()
    
    term_premia["tenor"] = pd.to_timedelta(term_premia["tenor"], unit='D') + fs.convert_string_to_date(fs.get_ndays_from_today(0))
    term_premia.set_index(["tenor"], inplace=True)
    path_scenarios = pd.merge(path_scenarios, term_premia, how="outer", left_index=True, right_index=True)
    path_scenarios = path_scenarios.interpolate(method="linear")
    premia = path_scenarios["premia"]
    path_scenarios = path_scenarios.drop("premia", 1)
    scenarios = path_scenarios.columns
    for scenario in scenarios:
    	path_scenarios[scenario] += premia
    return path_scenarios


def compound_spot_curve(forward_curve, method, tpm_base, bonds_base):
    '''
    Compone una curva spot en base a una curva forward.
    '''
    #print(forward_curve)
    forward_dates = forward_curve.index
    start_date = forward_dates[0]
    end_date = forward_dates[-1]
    one_year_date =  start_date + dt.timedelta(365)
    spot_dates = fs.get_dates_between(start_date, end_date)
    spot_curve = forward_curve.reindex(spot_dates)
    
    # dejamos la forward constante en los primeros 365 dias
    # el resto interpolamos entre fechas dada la baja 
    # granularidad.
    spot_curve_short = spot_curve[spot_curve.index<=one_year_date]
    spot_curve_short = spot_curve_short.fillna(method="ffill")
    spot_curve_long = spot_curve[spot_curve.index>one_year_date]
    spot_curve_long = spot_curve_long.interpolate()
    spot_curve = pd.concat([spot_curve_short, spot_curve_long])

    

    # como empieza en nan hay que interpolar de nuevo
    spot_curve = spot_curve.interpolate()
    
    spot_curve = spot_curve.to_frame(name="yield")
    spot_curve["days"] = np.arange(len(spot_curve.index)) + 1
    spot_curve["yield"]  = (1.0 + (spot_curve["yield"]/tpm_base))
    
    spot_curve["yield"] = spot_curve["yield"].cumprod()


    if method == "compounded":
        spot_curve["yield"] = ((spot_curve["yield"])**(bonds_base/spot_curve["days"])) - 1.0
    elif method == "linear":
        spot_curve["yield"] = ((spot_curve["yield"]-1.0)*(bonds_base/spot_curve["days"]))
    spot_curve = spot_curve["yield"]    
    spot_curve.name = forward_curve.name
    return spot_curve


def compute_spot_curves(path_scenarios, method, tpm_base, bonds_base):
    '''
    Calcula las curvas zero y las almacena en un dataframe.
    '''
    scenarios = path_scenarios.columns
    zero_curves = []
    for scenario in scenarios:
        path = path_scenarios[scenario]
        zero_curve = compound_spot_curve(path, method, tpm_base, bonds_base)
        zero_curves.append(zero_curve)
    zero_curves = pd.concat(zero_curves, axis=1)
    return zero_curves


def dcf(rates, cash_flows, tenors, outstanding):
    '''
    Calcula el precio dado los flujos, tasas, tenors y el outstanding
    '''

    pv = (cash_flows / (1+rates)**tenors).sum(axis=0)
    price = (pv/outstanding) * 100
    return price


def dcf_error(rate, cash_flows, tenors, outstanding, target_price):
    '''
    Es la funcion que calcula el error entre una valorizacion
    de una iteracion y el precio real del activo.
    '''
    price_iteration = dcf(rate, cash_flows, tenors, outstanding)
    error = price_iteration - target_price
    return error



def compute_zero_swap_curves(swap_instruments_clp, swap_instruments_clf, long_end_date, method, bonds_base, tpm_base):
    '''
    Calcula las curvas swap.
    '''
    zero_swap_curve_clp = compute_zero_swap_curve(swap_instruments_clp, long_end_date, method, bonds_base, tpm_base)
    zero_swap_curve_clf = compute_zero_swap_curve(swap_instruments_clf, long_end_date, method, bonds_base, tpm_base)
    
    return zero_swap_curve_clp, zero_swap_curve_clf
    

def compute_zero_swap_curve(swap_instruments, long_end_date, method, bonds_base=360, tpm_base=360):
    '''
    Calcula la curva swap zero cupon en base a la curva swap spot.
    '''

    # Creamos el dataframe que tendra ala curva tras el bootstraping
    bootstraped_curve = pd.DataFrame(columns=["zero_yld"])
    
    # Obtenemos las fechas para marcar los tenors de cada instrumento
    maturity_dates = np.array(swap_instruments["maturity_date"])
    
    # Fijamos las fecha en las que calibraremos la curva
    start_date = maturity_dates[0]
    end_date = maturity_dates[-1]
    
    # Obtenemos la lista con todas las fecha que iran en la curva
    curve_dates = fs.get_dates_between(start_date, end_date)

    # Separamos los instrumentos que son cero cupon
    swaps_zero = swap_instruments[swap_instruments["type"] == "zero"]
 
    # Calculamos la parte corta de la curva cero
    bootstraped_curve = compute_short_zero_swap_curve(swaps_zero, bootstraped_curve, curve_dates, start_date, method, tpm_base)
    
    # Separamos los intrumentos bullet de la curva
    swaps_bullet = swap_instruments[swap_instruments["type"] == "bullet"]

    # Calculamos la curva zero completa
    bootstraped_curve = compute_long_zero_swap_curve(bootstraped_curve, swaps_bullet, swaps_zero, curve_dates, start_date, tpm_base)
    
    # Pasamos a base 365 para valorizar chicos
    bootstraped_curve["zero_yld"] = ((1.0+bootstraped_curve["zero_yld"])**(bonds_base/tpm_base)) - 1.0
    
    # Agregamos lo que falta para valorizar el ultimo bono
    start_date = bootstraped_curve.index[0]
    complete_curve_dates = fs.get_dates_between(start_date, long_end_date)
    bootstraped_curve = bootstraped_curve.reindex(complete_curve_dates)
    bootstraped_curve = bootstraped_curve.interpolate(method="pchip")

    # La dejamos como serie
    bootstraped_curve = bootstraped_curve["zero_yld"]
    
    return bootstraped_curve


def compute_short_zero_swap_curve(swaps_zero, bootstraped_curve, curve_dates, start_date, method, tpm_base):
    '''
    Calcula la parte corta de la curva swap zero cupon.
    '''
    # primero pasamos todo a compuesto
   
    tenors = swaps_zero["maturity_date"] - start_date
    swaps_zero["tenor"] = tenors.dt.days + 1
    
    if method == "compounded":
        swaps_zero["yield"] =  ((1.0+((swaps_zero["yield"]*swaps_zero["tenor"])/tpm_base))**(tpm_base/swaps_zero["tenor"])) - 1.0
    swaps_zero = swaps_zero.drop("tenor", 1)
    # Todos los intrumentos se agregan a la curva
    for ticker, instrument in swaps_zero.iterrows():
        yld = instrument["yield"]
        maturity_date = instrument["maturity_date"]
        bootstraped_curve.loc[maturity_date] = yld
    # Agregamos todas las fechas restantes e interpos
    # linealmente entre cada intervalo
       
    bootstraped_curve = bootstraped_curve.reindex(curve_dates)
    bootstraped_curve = bootstraped_curve.interpolate(method="linear")
    
    last_zero_swaps_date = swaps_zero["maturity_date"][-1]
    bootstraped_curve = bootstraped_curve[bootstraped_curve.index <= last_zero_swaps_date]

    return bootstraped_curve


def compute_long_zero_swap_curve(bootstraped_curve, swaps_bullet, swaps_zero, curve_dates, start_date, tpm_base):
    '''
    Calcula la parte corta de la curva swap zero cupon.
    '''
    # Obtenemos la fecha y el tenor del ultimo cupon
    # cero para iniciar el bootstrapping
    prev_coupon_date = swaps_zero["maturity_date"][-1]
    prev_tenor =  len(fs.get_dates_between(start_date, prev_coupon_date))
    prev_tenor = (prev_tenor / tpm_base)

    # Obtenemos la cantidad de dias hasta que empieza
    # el bootstrapping expresado todo en anios
    last_zero_swaps_date = swaps_zero["maturity_date"][-1]
    periods_to_bullets = len(fs.get_dates_between(start_date, last_zero_swaps_date))
    periods_to_bullets = periods_to_bullets / tpm_base

    # En base a esto obtenemos la cantidad de cupones
    # que se descuentan a tasa cero
    n_coupons_zero = int(periods_to_bullets*2)
    
    # Luego, por cada instrumento bullet calculamos
    # su tasa cero y la agregamos de manera iterativa
    # a la curva cero bootstrapeada
    for ticker, instrument in swaps_bullet.iterrows():
        # Obtenemos la info basica del swap
        maturity_date = instrument["maturity_date"]
        yld = instrument["yield"]
        coupon = yld / 2
        tenor = len(fs.get_dates_between(start_date, maturity_date))
        tenor = tenor / tpm_base
        n_coupons_total = int(tenor*2)
        n_coupons_bullet = n_coupons_total - n_coupons_zero
        
        # Calculamos el valor presente de los
        # cupones que ya tienen una tasa cero
        # calculada en la curva swap
        short_cash_flow = compute_short_cash_flow(bootstraped_curve, n_coupons_zero, coupon, start_date)
        
        
        # Aca hacemos el bootstrapping de los cupones que no tienen
        # tasa cero calculada. Necesitamos dar como parametro la tasa
        # cero cupon del ultimo cupon para que haga el promedio
        # entre la puntas al optimizar.
        prev_zero_yld = float(bootstraped_curve.loc[prev_coupon_date]["zero_yld"])
        x0 = 0.025
        zero_yld = optimize.newton(bootstrapping_error, x0, args=(short_cash_flow, coupon, prev_zero_yld, prev_tenor, tenor, n_coupons_bullet))
        
        # Agregamos la tasa calculada a la curva cero
        bootstraped_curve.loc[maturity_date] = zero_yld
    
        # dejamos todo listo para el proximo chicos
        # hacemos interpol
        curve_dates = fs.get_dates_between(start_date, maturity_date)
        bootstraped_curve = bootstraped_curve.reindex(curve_dates)
        bootstraped_curve = bootstraped_curve.interpolate(method="linear")
    
        n_coupons_zero += n_coupons_bullet
        prev_coupon_date = maturity_date
        prev_tenor = tenor + 0.5
    return bootstraped_curve

def compute_short_cash_flow(bootstraped_curve, n_coupons_zero, coupon, start_date):
    '''
    Calcula el valor presente de los cupones que no necesitan
    bootstraping.
    '''
    short_cash_flow = 0.0
    # por cada cupon lo descontamos a su tasa
    # correspondiente de la curva cero
    for i in range(n_coupons_zero):
        coupon_tenor = (i+1) * 0.5
        coupon_date = start_date + np.timedelta64(int(coupon_tenor*365), 'D')
        discount_rate = float(bootstraped_curve.loc[coupon_date]["zero_yld"])
        coupon_dcf = coupon / ((1+discount_rate)**coupon_tenor)
        short_cash_flow += coupon_dcf
    return short_cash_flow


def bootstrapping_error(rate, short_cash_flow, coupon, prev_zero_yld, prev_tenor, tenor, n_coupons_bullet):
    '''
    Calcula el error para cada iteracion del calculo de la zero yield.
    '''
    
    # Tenemos tres casos, el primero es cuando
    # es el primer bono bullet y no tenemos ningun
    # cupon con tasa desconocida ademas del ultimo
    if n_coupons_bullet == 1:
        prev_cash_flow = 0.0
    # El segundo caso es cuando tenemos exactamente dos
    # cupones con cupon desconocido ahi tomamos el promedio del
    # ultimo cupon y el ultimo (incognita)
    elif n_coupons_bullet == 2:
        prev_cash_flow = coupon / ((1.0+((prev_zero_yld+rate)/2.0))**prev_tenor)
    # el tercer caso es la gneeralizacion del segundo y
    # sirve para los tenors 15 y 20y. El segundo caso
    # se pudo considerar aca pero en el minuto lo hice
    # asi por simplicidad. Suerte a las futuras generaciones chicos.
    else:
        prev_cash_flow = 0.0
        # por cada cupon calculamos su valor presente
        for t in range(n_coupons_bullet):
            prev_cash_flow += coupon / ((1.0+((prev_zero_yld+rate)/2.0))**prev_tenor)
            prev_tenor += 0.5
    # finalmente sumamos el ultimo cupon
    cash_flow = (coupon+1.0) / ((1.0+rate)**tenor)
    # calculamos el dcf y vemos el error en base 1
    long_cash_flow = prev_cash_flow + cash_flow
    total_cash_flow = short_cash_flow + long_cash_flow
    error = 1.0 - total_cash_flow
    return error


def compute_valuation(curve_instruments, cash_flow_tables, zero_curves_cash, zero_curve_swap=None):
    '''
    Calcula los fair value de todos los instrumentos en la curva
    y los agrega al dataframe de instrumentos.
    '''
    # Primero dejamos los tenors de las curvas en dias

    #print(zero_curves_cash)
    #exit()
    zero_curves_cash["tenors"] = np.arange(len(zero_curves_cash.index)) / 365
    tenors = zero_curves_cash["tenors"]
    zero_curves_cash = zero_curves_cash.drop("tenors", 1)
    zero_curves_scenarios = zero_curves_cash.columns
    # Dejamos las columnas listas para setear los fair value
    for scenario in zero_curves_scenarios:
        curve_instruments[scenario] = None
    
    if zero_curve_swap is not None:
    	curve_instruments["swap_equivalent"] = None

    # Por cada instrumentos valorizamos
    for ticker, instrument in curve_instruments.iterrows():
        
        cash_flow_table = cash_flow_tables.loc[ticker]["DES_CASH_FLOW"]
        cash_flow_table.set_index(["Payment Date"], inplace=True)
        coupon_cash_flow = cash_flow_table["Coupon Amount"]
        principal_cash_flow = cash_flow_table["Principal Amount"]
        outstanding = principal_cash_flow.sum()
        total_cash_flow = coupon_cash_flow + principal_cash_flow
        # por cada curva cash zero lo valorizamos
        for scenario in zero_curves_scenarios:
           curve = zero_curves_cash[scenario]
           valuation_price = dcf(curve, total_cash_flow, tenors, outstanding)
            # fijamos punto de partida para la optimizacion en la tpm actual
           x0 = 0.025
           valuation_yield = optimize.newton(dcf_error, x0, args=(total_cash_flow, tenors, outstanding, valuation_price))
           curve_instruments.set_value(ticker, scenario, valuation_yield)
           
        # valorizamos tambien en la swap equivalent
        if zero_curve_swap is not None:
            valuation_price = dcf(zero_curve_swap, total_cash_flow, tenors, outstanding)
            x0 = 0.025
            valuation_yield = optimize.newton(dcf_error, x0, args=(total_cash_flow, tenors, outstanding, valuation_price))
            curve_instruments.set_value(ticker, "swap_equivalent", valuation_yield)
            
    return curve_instruments


def compute_yield_buffer(curve_instruments, funding_rate, clf_serie=None):
    '''
    Calcula el colchon de tasa de los bonos. Notar que en inflation-linked bonds
    tenemos que sumarle las expectativas implicitas en el vector de cpi.}
    '''
    if clf_serie is None:
        curve_instruments["yield_buffer_1M"] = ((curve_instruments["yield"]/12) - funding_rate) / curve_instruments["duration"]
        curve_instruments["yield_buffer_3M"] = (3*((curve_instruments["yield"]/12) - funding_rate)) / curve_instruments["duration"]
    else:
        spot_date = clf_serie.index[0]
        carry_1m_date = spot_date + dt.timedelta(30)
        carry_3m_date = spot_date + dt.timedelta(90)
        clf_spot = clf_serie.loc[spot_date]
        clf_1m = clf_serie.loc[carry_1m_date]
        clf_3m = clf_serie.loc[carry_3m_date]
        inflation_carry_1m = (clf_1m/clf_spot) - 1.0
        inflation_carry_3m = (clf_3m/clf_spot) - 1.0
        curve_instruments["yield_buffer_1M"] = ((curve_instruments["yield"]/12) + inflation_carry_1m - funding_rate) / curve_instruments["duration"]
        curve_instruments["yield_buffer_3M"] = ((3*(curve_instruments["yield"]/12) + inflation_carry_3m - 3*funding_rate)) / curve_instruments["duration"]
    return curve_instruments



def compute_fras(curve_instruments, fra_limit):
    '''
    Calcula el fra entre los bonos a yield de mercado
    '''
    days_to_maturity = curve_instruments["duration"]
    shift_days_to_maturity = days_to_maturity.shift(1).fillna(0.0)  
    delta_days = days_to_maturity-shift_days_to_maturity
    yld = curve_instruments["yield"]
    shift_yld = yld.shift(1).fillna(1.0)
    curve_instruments["fra"] = ((yld+1)**(days_to_maturity/(delta_days)))/((shift_yld+1)**(shift_days_to_maturity/(delta_days))) - 1.0
    curve_instruments.loc[((curve_instruments["fra"]>fra_limit)|(curve_instruments["fra"]<-1*fra_limit)), "fra"] = None
    return curve_instruments


def compute_swap_spread(curve_instruments):
    '''
    Calcula el spread entre los bonos valorizados el valuation
    por expectativas y el swap equivalent.
    '''
    curve_instruments["swap_spread"] = curve_instruments["swap_equivalent"] - curve_instruments["yield"]
    return curve_instruments


def compute_delta_value(curve_instruments):
    '''
    Calcula la diferencia entre el fair value y el mercado.
    '''
    curve_instruments["delta"] = curve_instruments["yield"] - curve_instruments["expected"]
    return curve_instruments


def compute_expected_inflation(path_distribution):
    '''
    Calcula la inflacion esperada.
    '''
    for tenor in path_distribution.columns[1:]:
        probabilities = path_distribution[path_distribution.index != "expected"]["probability"]
        inflations = path_distribution[path_distribution.index != "expected"][tenor]
        expected_inflation = probabilities.dot(inflations)
        path_distribution.set_value("expected", tenor, expected_inflation)
    return path_distribution


def compute_zero_curves_clf(zero_curves_clp, inflation_forwards, path_distribution):
    '''
    Calcula las curvas zero y las almacena en un dataframe.
    '''
    zero_curves_clf = []
    # path_distribution = path_distribution[path_distribution.index == "expected"]
    for scenario, data in path_distribution.iterrows():
        inflation_1y = data["inflation_1y"]
        inflation_2y = data["inflation_2y"]
        inflation_equilibrium = data["inflation_equilibrium"]
        zero_curve_clp = zero_curves_clp[scenario]
        zero_curve_clf = compound_inflation_curve(zero_curve_clp, inflation_forwards, path_distribution, inflation_1y, inflation_2y, inflation_equilibrium)
        zero_curve_clf.name = scenario
        zero_curves_clf.append(zero_curve_clf)
    zero_curves_clf = pd.concat(zero_curves_clf, axis=1)
    return zero_curves_clf


def compute_swap_simulation_curves(path_simulation_scenarios, method, tpm_base, swap_instruments):
    '''
    Dada una coleccion de paths de tpm calcula distitnas curvas swap, en base a los instrumentos swap existentes.
    '''
    swap_maturity_dates = swap_instruments["maturity_date"]
    zero_simulation_curves = compute_spot_curves(path_simulation_scenarios, "linear", tpm_base, tpm_base)
    swap_simulation_curves = pd.DataFrame(index=swap_maturity_dates, columns=path_simulation_scenarios.columns)
    # Para cada instrumento obtenemos el cupon swap equivalente en cada escenario
    for scenario in zero_simulation_curves.columns:
        zero_curve = zero_simulation_curves[scenario]
        zero_curve.name = "zero_rate"
        for i, instrument in swap_instruments.iterrows():
            ticker = i
            maturity_date = instrument["maturity_date"]
            cash_flow_type = instrument["type"]
            coupon = compute_swap_coupon(zero_curve, maturity_date, cash_flow_type, tpm_base)
            swap_simulation_curves.loc[maturity_date][scenario] = coupon
    # Agregamos los tenors para hacer loc mas facil
    tenors = swap_instruments.reindex().set_index(["maturity_date"])["tenor"]
    market_rates = swap_instruments.reindex().set_index(["maturity_date"])["yield"]
    slope_simulation = swap_instruments.reindex().set_index(["maturity_date"])["slope_simulation"]
    swap_simulation_curves["tenor"] = tenors
    swap_simulation_curves["market"] = market_rates
    swap_simulation_curves["slope_simulation"] = slope_simulation
    swap_simulation_curves = swap_simulation_curves.reset_index()
    swap_simulation_curves.set_index(["tenor"], inplace=True)
    return swap_simulation_curves


def compute_swap_coupon(zero_curve, maturity_date, cash_flow_type, tpm_base):
    '''
    Calcula el cupon equivalente de un instrumento en base a la curva
    cero de expectativas de path de politica monetaria.
    '''
    # Sacamos la tasa zero para el ultimo cupon

    z_T = zero_curve.loc[maturity_date]
    spot_date = zero_curve.index[0]
    days_to_maturity = len(zero_curve[zero_curve.index <= maturity_date].index)
    coupon = None
    # Si el bono es cero, entonces la tasa es el cupon
    if cash_flow_type == "zero":
        coupon = z_T
    # Si es bullet entregamos el cupon calculado
    # en base a la estructura de pagos del bono
    elif cash_flow_type == "bullet":
        payment_dates = []
        payment_date = spot_date
        n_coupons = int(days_to_maturity/180)
        # Por cada tenor del cupon calculamos su fecha
        for t in range(1,n_coupons):
            payment_date += dt.timedelta(180)
            payment_dates.append(payment_date)
        # pasamos a datetimeindex
        payment_dates.append(maturity_date)
        payment_dates = pd.DatetimeIndex(payment_dates)
        zero_rates = zero_curve.reindex(payment_dates)
        zero_rates = pd.DataFrame(zero_rates, index=zero_rates.index)
        zero_rates["days"] = zero_rates.index - spot_date
        zero_rates["days"] = zero_rates["days"].dt.days
        T = zero_rates.loc[maturity_date]["days"]
        coupon = (2*T*z_T) / ((tpm_base+(T*z_T))*tpm_base*((1/(tpm_base + (zero_rates["days"]*zero_rates["zero_rate"]))).sum()))
        
    return coupon


def compute_simulation(curves, floating_rate=None, slope=None):
    '''
    Calcula los fras o pendientes de las combinaciones de tenors posibles.
    '''
    simulation_curves = curves[curves["slope_simulation"] == 1]
    scenarios = simulation_curves.drop(
        "maturity_date", 1).drop("slope_simulation", 1).columns
    simulation = pd.DataFrame(columns=scenarios)
    tenors_used = []
    for tenor1, rates1 in simulation_curves.iterrows():
        for tenor2, rates2 in simulation_curves.iterrows():
            if tenor1 != tenor2 and tenor2 not in tenors_used:
                aux_id = tenor1 + "-" + tenor2
                for scenario in scenarios:
                    long_rate = rates2[scenario]
                    long_time = int(tenor2[:-1])
                    short_rate = rates1[scenario]
                    short_time = int(tenor1[:-1])
                    if slope is True:
                        aux = long_rate - short_rate
                    else:
                        aux = ((((1+long_rate)**(long_time))/((1+short_rate)** (short_time))) ** (1/(long_time-short_time)))-1
                    simulation.loc[aux_id, scenario] = aux
                # LLenamos la columna del carry
                short_market_rate = rates1["market"]
                long_market_rate = rates2["market"]
                short_tenor = tenor1.replace("Y", "")
                short_tenor = int(short_tenor)
                long_tenor = tenor2.replace("Y", "")
                long_tenor = int(long_tenor)
                # normalizamos el tenor corto para que los dv01 sean iguales
                if slope is True:
                    tenor_ratio = long_tenor / short_tenor
                    simulation.loc[aux_id, "carry"] = (
                        long_market_rate - floating_rate) + (tenor_ratio*(floating_rate-short_market_rate))
                else:
                    simulation.loc[aux_id, "carry"] = (
                        long_market_rate-short_market_rate)
                tenors_used.append(tenor1)
    return simulation


def compute_simulation_carry(curves, floating_rate):
    '''
    Calcula el carry del market y lo agrega al dataframe del nivel.
    '''
    # Calculamos el carry
    curves["carry"] = curves["market"] - floating_rate

    return curves

def compute_simulation_delta(simulation):
    '''
    Calcula la diferencia entre las inclinaciones o los fras de los escenarios y el market.
    '''
    for scenario in simulation.columns:
        if scenario not in ["market", "carry", "maturity_date", "slope_simulation"]:
            simulation[scenario + "_delta"] = simulation["market"] - simulation[scenario]
    # Dejamos las columnas en orden
    columns = simulation.columns.tolist()
    columns.remove("market")
    columns.remove("carry")
    columns = ["market", "carry"] + columns
    simulation = simulation[columns]
    return simulation


def compound_inflation_curve(zero_curve_clp, clf_serie, path_distribution, inflation_1y, inflation_2y, inflation_equilibrium):
    '''
    Compone una curva de inflacion en base a una curva nominal y los forwards de inflacion.
    '''
    
    spot_date = clf_serie.index[0]
    one_year_date =  spot_date + dt.timedelta(365)
    two_year_date = one_year_date + dt.timedelta(365)
    last_fwd_date = clf_serie.index[-1]

    # Calculo de 0-1y de inflacion
    # Obtenemos la curva hasta 1y
    clf_1y = clf_serie.loc[one_year_date]
    clf_spot = clf_serie.loc[spot_date]
    implied_inflation_1y = clf_1y / clf_spot - 1
    # Obtenemos la diferencia de expectativas que sumaremos a 1y
    # y lo pasamos a daily
    

    market_diff_1y = ((1.0+inflation_1y)/(1.0+implied_inflation_1y)) - 1.0
    market_diff_1y = ((1.0+market_diff_1y)**(1/365)) - 1.0

    

    # Calculo de 1y-1.5y de inflacion
    # Obtenemos la curva hasta 24m
    clf_2y = clf_serie.loc[last_fwd_date]
    implied_inflation_2y = clf_2y / clf_1y - 1.0
    # Obtenemos la diferencia de expectativas que sumaremos a 1y
    # y lo pasamos a daily
    market_diff_2y = ((1.0+inflation_2y)/(1.0+implied_inflation_2y)) - 1.0
    market_diff_2y = ((1.0+market_diff_2y)**(1/365)) - 1.0


    inflation_returns = clf_serie.pct_change()
    #print(clf_serie)
    inflation_returns = inflation_returns.fillna(method="bfill")
    inflation_returns[inflation_returns.index<=one_year_date] += market_diff_1y
    inflation_returns[inflation_returns.index>one_year_date] += market_diff_2y

    # Ahora debemos agregar la inflacion de equilibrio diaria
    inflation_equilibrium_d =  (1.0+(inflation_equilibrium))**(1/365) - 1.0
    equilibrium_date = last_fwd_date + dt.timedelta(1)
    inflation_returns = inflation_returns.set_value(equilibrium_date, inflation_equilibrium_d)
    inflation_returns = inflation_returns.reindex(zero_curve_clp.index)
    inflation_returns = inflation_returns.fillna(method="ffill")
    
    # Ahora armamos la curva cero en uf, debemos descomponer con la zero en pesos
    inflation_returns += 1.0
    inflation_returns = inflation_returns.cumprod()
    #print(inflation_returns)
    tenor_days = np.arange(len(inflation_returns.index)) + 1
    #print(tenor_days)
    inflation_rate = inflation_returns**(365/tenor_days) - 1.0
    #print(inflation_rate)
    zero_curve_clf = ((zero_curve_clp+1.0) / (inflation_rate+1.0)) - 1.0
    #print(inflation_rate)
    #print(zero_curve_clp)
    
    return zero_curve_clf


def compute_implied_term_premia(market_zero_curve, tpm_neutral_lower, tpm_neutral_upper):
    '''
    Calcula el term premio implicito en la curva cero.
    '''
    market_zero_curve["implied_term_premia_lower"] = market_zero_curve["forward_rate"] - tpm_neutral_lower
    market_zero_curve["implied_term_premia_upper"] = market_zero_curve["forward_rate"] - tpm_neutral_upper
    market_zero_curve["implied_term_premia_mid"] = (market_zero_curve["implied_term_premia_lower"]+market_zero_curve["implied_term_premia_upper"]) / 2
    
    return market_zero_curve


def compute_zero_implied_tpm(market_zero_curve):
    '''
    Construye el display para el monitor
    '''
    # Armamos las columnas desfasadas de yield
    market_zero_curve.rename(columns={"yield": "yield_t2"},inplace=True)
    market_zero_curve["yield_t1"] = market_zero_curve["yield_t2"].shift(1)
    market_zero_curve["yield_t1"] = market_zero_curve["yield_t1"].fillna(method="bfill")
    # Calculamos la forward instantanea
    market_zero_curve["forward_rate"] = (((1.0+market_zero_curve["yield_t2"])**(market_zero_curve.index)) / ((1.0+market_zero_curve["yield_t1"])**(market_zero_curve.index - 1))) - 1.0
    market_zero_curve = market_zero_curve.replace(np.inf, np.nan)
    market_zero_curve = market_zero_curve.fillna(method="ffill")

    # Calculamos moving averagep ara el error
    market_zero_curve["forward_rate_discrete"] = market_zero_curve["forward_rate"]
    market_zero_curve["forward_rate"] = market_zero_curve["forward_rate"].rolling(window=60).mean()
    market_zero_curve["forward_rate"] = market_zero_curve["forward_rate"].fillna(market_zero_curve["forward_rate_discrete"])
    market_zero_curve = market_zero_curve.drop("forward_rate_discrete", 1)
    # Obtenemos la tpm iplicita
    market_zero_curve["implied_tpm"] = market_zero_curve["forward_rate"].apply(lambda x: fs.custom_round(x, base=0.0025))
    market_zero_curve["tenor_date"] = fs.convert_string_to_date(fs.get_ndays_from_today(0))
    market_zero_curve["tenor_date"] = pd.to_datetime(market_zero_curve["tenor_date"]) + pd.to_timedelta(market_zero_curve.index, unit="D")
    market_zero_curve.set_index(["tenor_date"], inplace=True)
    market_zero_curve.rename(columns={"yield_t1": "zero_curve"},inplace=True)
    
    return market_zero_curve


def compute_inflation_paths(clf_serie, cpi_serie):
    '''
    Calcula la serie de inflacion yoy en base a un vector de uf esperada
    y el cpi efectivo.
    '''
    spot_date = fs.convert_string_to_date(fs.get_ndays_from_today(0))
    spot_date = pd.Timestamp(spot_date)
    # Construimos un vector de cpi con la historia
    # y el forecast en base a los forwards
    
    cpi_serie = compute_cpi_forecast(clf_serie, cpi_serie, spot_date)
    #print(cpi_serie)
    # Obtenemos la fecha de 12 mas, hasta ahi llega nuestro forecast
    yoy_date = spot_date + dt.timedelta(730)
    
    # Calculamos inflacion anual del cpi
    yoy_inflation = cpi_serie.pct_change(periods=365)
    
    
    yoy_inflation = yoy_inflation.dropna()
    yoy_inflation = yoy_inflation[yoy_inflation.index <= yoy_date]
    
    # Dejamos todo al 9 del mes
    
    yoy_inflation = yoy_inflation.groupby(pd.TimeGrouper('M')).nth(-1)
    
    #yoy_inflation = yoy_inflation.shift(-1)

    # Ahora calculamos a inflacion mensual de cpi
    mom_inflation = cpi_serie.groupby(pd.TimeGrouper('M')).nth(-1)   
    mom_inflation = mom_inflation.pct_change()
    # mom_inflation = mom_inflation.shift(1)
    mom_inflation = mom_inflation.dropna()

    
    # Separamos en realized y forecast
    yoy_inflation = pd.DataFrame(yoy_inflation, columns=["realized_yoy"], index=yoy_inflation.index)
    mom_inflation = pd.DataFrame(mom_inflation, columns=["realized_mom"], index=mom_inflation.index)

    inflation_paths = pd.merge(yoy_inflation,
                               mom_inflation,
                               how="inner",
                               left_index=True,
                               right_index=True,
                               suffixes=("_y", "_m"))
    # Obtenemos el siguiente 0
    date = spot_date
    while True:
        day = date.timetuple()[2]
        if day == 9:
            prev_nine = date
            break
        date -= dt.timedelta(1)

    inflation_paths["expected_yoy"] = inflation_paths["realized_yoy"]
    inflation_paths["expected_mom"] = inflation_paths["realized_mom"]
    inflation_paths.loc[inflation_paths.index > prev_nine, "realized_yoy"] = 0.0
    inflation_paths.loc[inflation_paths.index <= prev_nine, "expected_yoy"] = 0.0
    inflation_paths.loc[inflation_paths.index > prev_nine, "realized_mom"] = 0.0
    inflation_paths.loc[inflation_paths.index <= prev_nine, "expected_mom"] = 0.0

    #print(inflation_paths)
    
    return inflation_paths

def compute_cpi_forecast(clf_serie, cpi_serie, spot_date):
    '''
    Calcula el forecast de ipc y se lo concatena a la historia.
    '''
    # Para cada fecha de la proyeccion de uf buscamos el siguiente 9
    # poner 1: para el dia de la inflacion ves tu ?
    for date in clf_serie.index:
        # Obetnemos el dia de la fecha
        day = date.timetuple()[2]
        if day == 9:
            next_nine = date
            break

    #Obtenemos la cantidad de dias para el proximo nueve
    days_to_next_nine = next_nine - spot_date
    days_to_next_nine = days_to_next_nine.days #TENGO QUE ARREGLAR ESTO, HAY QUE PEGAR LA CTDAD DE DIAS AL PROXIMO 9 EN DIAS DE PUBLICACION


    # Corremos nuestra proyeccion de uf en esa cantidad de dias
    # ya que la inflacion entre los proximos nueves es la inflacion vigente hoy
    #print(clf_serie)
    shifted_clf_serie = clf_serie.shift(-1*days_to_next_nine)
    #print(shifted_clf_serie)

    shifted_clf_serie = shifted_clf_serie.dropna()
    
    # Obtenemos la base del ultimo cpi
    cpi_base = cpi_serie[-1]
    #print(cpi_serie)


    # Cambiamos de base
    shifted_clf_serie = 1.0 + shifted_clf_serie.pct_change()
    shifted_clf_serie = shifted_clf_serie.fillna(1.0)
    shifted_clf_serie = shifted_clf_serie.cumprod()
    shifted_clf_serie = shifted_clf_serie * cpi_base
    #print(shifted_clf_serie)
    

    # Ahora movemos el indice hasta el proximo dia post cpi
    cpi_date = cpi_serie.index[-1]
    post_cpi_date = cpi_date + dt.timedelta(1)
    #print(post_cpi_date)
    days_to_spot = spot_date - post_cpi_date
    days_to_spot = days_to_spot.days + 1
    #print(days_to_spot)
    shifted_clf_serie = shifted_clf_serie.shift(-1*days_to_spot, freq='D')
    #print("ahora")
    #print(shifted_clf_serie)

    shifted_clf_serie = shifted_clf_serie[1:]

    # Juntamos ambas series
    cpi_serie = pd.concat([cpi_serie, shifted_clf_serie])
    #print(cpi_serie)


    return cpi_serie


def compute_swap_implied_path(rpm_dates, path_scenarios_display, swap_instruments_clp, tpm_base, long_end_date, method, second_order):
    '''
    Calcula el path implicito en una curva swap.
    '''
    # Fijamos los parametros de la optimizacion
    spot_date = rpm_dates[0]
    swap_instruments_bullet = swap_instruments_clp[swap_instruments_clp["type"] == "bullet"]
    first_bullet_ticker = swap_instruments_bullet.index[0]
    first_bullet_rate = swap_instruments_bullet.loc[first_bullet_ticker]["yield"]
    first_bullet_date = swap_instruments_bullet.loc[first_bullet_ticker]["maturity_date"]
    instruments = swap_instruments_clp[swap_instruments_clp["maturity_date"] <= first_bullet_date]

    instruments = compute_linear_bootstraping(instruments, first_bullet_ticker, first_bullet_date, first_bullet_rate, tpm_base)

    dates = [date for date in rpm_dates]
    swap_instruments_dates = instruments["maturity_date"]


    swap_curve_market = instruments[["maturity_date", "yield"]]
    swap_curve_market.set_index(["maturity_date"], inplace=True)
    swap_curve_market.rename(columns={"yield": "market"}, inplace=True)

    


    tpm_spot = swap_curve_market.loc[swap_curve_market.index[0]]
    tpm_spot = float(tpm_spot)

    #swap_curve_market = swap_curve_market.drop(swap_curve_market.index[0])

    rpm = len(rpm_dates)

    # Fijamos el punto inicial de la optimizacion como nuestro path de tasas central
    central_path = path_scenarios_display["central"]
    central_path = central_path.reindex(rpm_dates)
    spot_tpm = central_path.loc[spot_date]
    # sacamos el nivel para ver recortes
    central_path -= spot_tpm
    #x0 = np.array(central_path)
    x0 = np.zeros(rpm)
    b_ = [(-0.0025,0.0025) for i in range(rpm)]
    c_ = build_constrains(x0, second_order)

   
    # Buscamos la tasa implicita
    implied_delta = optimize.minimize(compute_composition_error,
                                      x0,
                                      args=(dates, swap_curve_market, tpm_base, tpm_spot),
                                      constraints=c_,
                                      bounds=b_,
                                      method="SLSQP",
                                      tol=0.00000001,
                                      options={"maxiter": 100000000})
    implied_delta = implied_delta.x
    estimated_curve, implied_path = compound_tpm_delta(implied_delta,
                                                       dates,
                                                       swap_curve_market,
                                                       tpm_base,
                                                       tpm_spot)
    implied_path["delta_tpm"] = implied_delta
    swap_implied_path = pd.merge(implied_path,
                                 estimated_curve,
                                 how="outer",
                                 left_index=True,
                                 right_index=True)   
    swap_implied_path = pd.merge(swap_implied_path,
                                 swap_curve_market,
                                 how="outer",
                                 left_index=True,
                                 right_index=True) 
    swap_implied_path["implied_path"] = swap_implied_path["implied_path"].fillna(method="ffill")


    return swap_implied_path

def compute_linear_bootstraping(instruments, first_bullet_ticker, first_bullet_date, first_bullet_rate, tpm_base):
    '''
    Hace bootsraping para tasas lineales hasta el primer bullet (inclusive).
    '''
    # tenor = len(fs.get_dates_between(start_date, maturity_date))

    # Primero necesitamos una curva cero  a partir de los bonos
    # que son cero, para valorizar los cupones del bono 2y
    swap_instruments_zero = instruments[instruments["type"] == "zero"]

    # Creamos el dataframe que tendra ala curva tras el bootstraping
    bootstraped_curve = pd.DataFrame(columns=["zero_yld"])
    
    # Obtenemos las fechas para marcar los tenors de cada instrumento
    maturity_dates = np.array(swap_instruments_zero["maturity_date"])
    
    # Fijamos las fecha en las que calibraremos la curva
    start_date = maturity_dates[0]
    end_date = maturity_dates[-1]
    
    # Obtenemos la lista con todas las fecha que iran en la curva
    curve_dates = fs.get_dates_between(start_date, end_date)
 
    # Calculamos la parte corta de la curva cero
    zero_curve = compute_short_zero_swap_curve(swap_instruments_zero, bootstraped_curve, curve_dates, start_date, "linear", tpm_base)

    # Ahora calculamos el dcf lineal de los cupones del bono excepto el ultimo
    coupon = first_bullet_rate / 2
    short_dcf = 0
    for i in range(3):
        coupon_tenor = (i+1) * 0.5
        coupon_date = start_date + np.timedelta64(int(coupon_tenor*365), 'D')
        discount_rate = float(zero_curve.loc[coupon_date]["zero_yld"])
        coupon_dcf = coupon / (1+(discount_rate*coupon_tenor))
        short_dcf += coupon_dcf

    zero_rate_2y = (((1.0+coupon)/(1.0-short_dcf)) -1.0) * 0.5
    instruments.loc[first_bullet_ticker, "yield"] = zero_rate_2y

    return instruments

def build_constrains(x0, second_order):
    '''
    Construye las restricciones para la optimizacion
    del calculo de tpm implicida en la swap
    '''
    # forzamos a que no cambie de tasa en t0 (no es rpm)
    cons = [{"type": "eq", "fun": lambda x: x[0]}] 
    # No puede bajar (subir) si la reunion pasada subio (bajo)
    for i in range(len(x0)-1):
        cons.append({"type": "ineq", "fun": lambda x, i: x[i]*x[i+1]*1000000, "args": [i]})
    # No puede bajar (subir) si la reunion antepasada subio (bajo)
    if second_order:
        for i in range(len(x0)-2):
            cons.append({"type": "ineq", "fun": lambda x, i: x[i]*x[i+2]*1000000, "args": [i]})

    return cons

def compute_composition_error(delta_tpm, dates, swap_curve, tpm_base, tpm_spot):
    '''
    Calcula el error entre la swap estimada y la swap spot.
    '''
    # Obtenemos la curva swap estimada
    estimated_curve, tpm_path = compound_tpm_delta(delta_tpm,
                                                   dates,
                                                   swap_curve,
                                                   tpm_base,
                                                   tpm_spot)


    # Calculamos la diferencia cuadratica entre
    # la curva estimada y la swap de mercado
    
    market_diff = pd.merge(swap_curve,
                           estimated_curve,
                           how="left",
                           left_index=True,
                           right_index=True)
    
    market_diff["error"] = market_diff["market"] - market_diff["estimated"]

    
    error = market_diff["error"]
    error = error**2
    error = error.sum()
    return error*10000


def compound_tpm_delta(delta_tpm, dates, swap_curve_market, tpm_base, tpm_spot):
    '''
    Compone una curva swap en base a la tpm spot y un path de hikes/cuts de tpm.
    Necesitamos la curva de mercado para dejar exactamente los mismos tenors
    '''
    # Primero armamos el path de tpm

    tpm_path = pd.DataFrame(dates, columns=["dates"])
    cum_delta_tpm = delta_tpm.cumsum()
    tpm_path["tpm"] = tpm_spot
    tpm_path["tpm"] += cum_delta_tpm
    tpm_path.set_index(["dates"], inplace=True)
    tpm_path = tpm_path["tpm"]
    # Luego componemos la curva
    estimated_curve = compound_spot_curve(tpm_path, "linear", tpm_base, tpm_base)
    estimated_curve = estimated_curve.to_frame(name="estimated")
    estimated_curve = estimated_curve.reindex(swap_curve_market.index)
    
    # Retorma, el path para poder graficarlo despues
    tpm_path = tpm_path.to_frame(name="implied_path")

    return estimated_curve, tpm_path

def sum_swap_spread(swap_implied_path, curve_instruments, tpm_ticker):
    '''
    Sumamos el spread repo contra ibr
    '''
    tpm = curve_instruments.loc[tpm_ticker, "yield"]
    repo_index = swap_implied_path.loc[swap_implied_path.index[0], "implied_path"]
    spread = tpm- repo_index
    swap_implied_path["implied_path"] += spread

    return swap_implied_path


def get_cum_path(tpm_implied_path):
    '''
    Consolida path de tpm en resumen
    '''
    spot_date = pd.Timestamp(fs.convert_string_to_date(fs.get_ndays_from_today(0)))
    date_12m = spot_date+rd.relativedelta(years=+1)
    first_eoy = dt.datetime(spot_date.year,12,31)
    second_eoy = first_eoy+rd.relativedelta(years=+1)
    third_eoy = second_eoy+rd.relativedelta(years=+1)


    deltaTPM_first_year = tpm_implied_path.loc[tpm_implied_path.index<=first_eoy,'delta_tpm'].sum()
    deltaTPM_second_year = tpm_implied_path.loc[(tpm_implied_path.index > first_eoy) & (tpm_implied_path.index<=second_eoy),'delta_tpm'].sum()
    deltaTPM_third_year = tpm_implied_path.loc[(tpm_implied_path.index > second_eoy) & (tpm_implied_path.index<=third_eoy),'delta_tpm'].sum()
    deltaTPM_12m=tpm_implied_path.loc[tpm_implied_path.index<=date_12m,'delta_tpm'].sum()

    consolid_tpm_info = pd.DataFrame(columns=['delta_tpm', 'end_date'])
    consolid_tpm_info.index.name = 'Year'
    consolid_tpm_info.loc[first_eoy.year] = [deltaTPM_first_year, first_eoy]
    consolid_tpm_info.loc[second_eoy.year] = [deltaTPM_second_year, second_eoy]
    consolid_tpm_info.loc[third_eoy.year] = [deltaTPM_third_year, third_eoy]
    consolid_tpm_info.loc['12M'] = [deltaTPM_12m,date_12m]


    return consolid_tpm_info

def compute_zero_implied_path_by_rpm(market_zero_curve, rpm_dates, floating_rate):
    '''
    Consolida path de tpm en resumen
    '''
    spot_date = pd.Timestamp(fs.convert_string_to_date(fs.get_ndays_from_today(0)))
    zero_implied_discrete_path = pd.DataFrame(columns=["forward_rate"])
    zero_implied_discrete_path.index.name = "date"
    zero_implied_discrete_path.loc[spot_date] = floating_rate
    df_aux = market_zero_curve["forward_rate"].to_frame(name="forward_rate")
    df_aux = df_aux[df_aux.index.isin(rpm_dates)]
    zero_implied_discrete_path = zero_implied_discrete_path.append(df_aux)
    zero_implied_discrete_path["delta_tpm"] = zero_implied_discrete_path["forward_rate"]-zero_implied_discrete_path["forward_rate"].shift(1)
    zero_implied_discrete_path["delta_tpm_cum_zero"]=zero_implied_discrete_path["delta_tpm"].cumsum()
    zero_implied_discrete_path = zero_implied_discrete_path.replace(np.nan, 0)


    return zero_implied_discrete_path

def compute_swap_implied_path_by_rpm(swap_implied_path, rpm_dates):
    '''
    Consolida path de tpm en resumen
    '''
    swap_implied_path_rpm = swap_implied_path[swap_implied_path.index.isin(rpm_dates)]
    del swap_implied_path_rpm['estimated']
    del swap_implied_path_rpm['market']

    return swap_implied_path_rpm

def join_zero_swap_paths_by_rpm(swap_implied_path_rpm, zero_implied_path_rpm):
    '''
    Hace el join entre las dos trayectorias implicitas de las curvas.
    '''
    joined_frame = pd.merge( swap_implied_path_rpm, zero_implied_path_rpm, how='inner', left_index=True, right_index=True, suffixes=('_swap','_zero'))

    return joined_frame

def compute_cash_fras(curve_instruments):
    '''
    Creamos un dataframe con los fra de los bonos del benchamark
    '''
    data = curve_instruments
    data = data.fillna(0.0)
    data.set_index(['local_id'], inplace=True)
    benchmark = data['breakeven'] != 0
    data = data[benchmark]
    instruments = data.index.tolist()
    dic_fra = {}
    for instrument in instruments:
        list_fra = compute_cash_fra(instrument, instruments, data)
        dic_fra[instrument] = pd.Series(list_fra, index=instruments)
    data = pd.DataFrame(dic_fra)
    return data[instruments]

def compute_cash_fra(instrument, instruments, data):
    '''
    Obtenemos la lista con los fra para un instrumento con todos los otros
    '''
    list_fra = []
    for i in instruments:
        fra = compute_bond_fra(data.loc[instrument], data.loc[i])
        list_fra.append(fra)
    return list_fra


def compute_cash_fra_bei(fra_clp, fra_clf):
    '''
    Retorna los BEI en los FRA de bonos.
    '''

    clp = fra_clp.reset_index()
    clf = fra_clf.reset_index()
    clp.columns = range(0, len(clp.columns))
    clf.columns = range(0, len(clf.columns))
    clp_ids = clp[0]
    clf_ids = clf[0]
    ids = clp_ids + "-" + clf_ids
    clp = clp.drop(0, 1)
    clf = clf.drop(0, 1)
    bei = ((1+clp)/(1+clf)) - 1
    bei["bei"] = ids
    bei.set_index(["bei"], inplace=True)
    bei.columns = ids


    return bei


def compute_bond_fra(instrument1, instrument2):
    '''
    Obtenemos los entre dos bonos
    '''
    days_to_maturity1 = instrument1['duration']
    days_to_maturity2 = instrument2['duration']
    yld1 = instrument1['yield']
    yld2 = instrument2['yield']
    if days_to_maturity1 > days_to_maturity2:
        fra = ((((1+yld1)**(days_to_maturity1))/((1+yld2)**(days_to_maturity2)))
               ** (1/(days_to_maturity1-days_to_maturity2)))-1
    elif days_to_maturity1 < days_to_maturity2:
        fra = ((((1+yld2)**(days_to_maturity2))/((1+yld1)**(days_to_maturity1)))
               ** (1/(days_to_maturity2-days_to_maturity1)))-1
    else:
        fra = None
    return fra

def compute_historical_term_premia(historical_zero_rates, tenor, tpm_neutral_lower, tpm_neutral_upper):
    '''
    Calcula el term premia historico en base a las tasas cero cupon.
    '''
    tpm_neutral = (tpm_neutral_lower+tpm_neutral_upper) / 2
    t_1 = tenor*360
    t_0 = t_1 - 30
    term_premia = pd.DataFrame()
    term_premia["z_t1"] = historical_zero_rates[historical_zero_rates["tenor"] == t_1]["yield"]
    term_premia["z_t0"] = historical_zero_rates[historical_zero_rates["tenor"] == t_0]["yield"]
    term_premia["fwd"] = (((1.0 + term_premia["z_t1"])**(t_1/30))/((1.0 + term_premia["z_t0"])**(t_0/30))) - 1.0
    term_premia["term_premia"] = (term_premia["fwd"] - tpm_neutral) * 10000
    term_premia["average"] = term_premia["term_premia"].mean()
    term_premia = term_premia[["term_premia", "average"]]

    return term_premia


def compute_historical_breakeven_forward(historical_zero_rates_cash_clp, historical_zero_rates_cash_clf, tenor):
    '''
    Calcula la serie historica de los breakeven forward en la cero cupon. 
    '''
    breakevens = pd.DataFrame()
    t_0 = tenor*360
    t_1 = t_0 + 360
    breakevens["clp_t1"] = historical_zero_rates_cash_clp[historical_zero_rates_cash_clp["tenor"] == t_1]["yield"]
    breakevens["clp_t0"] = historical_zero_rates_cash_clp[historical_zero_rates_cash_clp["tenor"] == t_0]["yield"]
    breakevens["clf_t1"] = historical_zero_rates_cash_clf[historical_zero_rates_cash_clf["tenor"] == t_1]["yield"]
    breakevens["clf_t0"] = historical_zero_rates_cash_clf[historical_zero_rates_cash_clf["tenor"] == t_0]["yield"]
    if tenor != 0:
        breakevens["fwd_clp"] = (((1.0 + breakevens["clp_t1"])**(t_1/360))/((1.0 + breakevens["clp_t0"])**(t_0/360))) - 1.0
        breakevens["fwd_clf"] = (((1.0 + breakevens["clf_t1"])**(t_1/360))/((1.0 + breakevens["clf_t0"])**(t_0/360))) - 1.0
        breakevens["breakeven"] = ((1+breakevens["fwd_clp"])/(1+breakevens["fwd_clf"])) - 1.0
    else:
        breakevens["breakeven"] = ((1+breakevens["clp_t1"])/(1+breakevens["clf_t1"])) - 1.0
    breakevens["average"] = breakevens["breakeven"].mean()
    breakevens = breakevens[["breakeven", "average"]]

    return breakevens



def compute_carry_roll(curve, horizon):
    '''
    Calcula el carry and roll de una curva. 
    '''
    tenors = [360, 720, 1080, 1800, 3600, 7200]
    cary = curve.copy()
    cary.rename(columns={"yield": "spot"},inplace=True)
    cary["fwd"] = cary["spot"].shift(-horizon)
    cary = cary.dropna()
    cary["fwd"] = (((1+cary["fwd"])**((cary.index+horizon)/cary.index))/((1+cary.loc[1, "fwd"])**(horizon/cary.index)))- 1
    cary["fwd_shift"] = cary["fwd"].shift(horizon)
    cary["spot_shift"] = cary["spot"].shift(horizon)
    cary["carry"] = cary["fwd_shift"] - cary["spot"]
    cary["total"] = cary["fwd_shift"] - cary["spot_shift"]
    cary["roll"] = cary["total"] - cary["carry"]
    cary = cary[cary.index.isin(tenors)]
    cary = cary[["spot", "fwd_shift", "carry", "roll", "total"]]
    cary[["carry", "roll", "total"]] = cary[["carry", "roll", "total"]]*10000
    cary[["spot", "fwd_shift"]] = cary[["spot", "fwd_shift"]]*100

    ''' para upfront
    cary["carry"] = cary["carry"]*((cary.index-(horizon/2))/365)
    cary["roll"] = cary["roll"]*((cary.index-(horizon/2))/365)
    cary["total"] = cary["total"]*((cary.index-(horizon/2))/365)
    '''

    cary.rename(columns={"fwd_shift": "forward"},inplace=True)
    cary = cary.reset_index()
    cary["tenor"] = cary["tenor"]/360    
    cary["tenor"] = cary["tenor"].astype(int)
    cary["tenor"] = cary["tenor"].astype(str) + "Y"
    cary.set_index(["tenor"], inplace=True)

    return cary

def compute_sinteticos_swaps(date, path_scenarios, swap_instruments_clp):
    
    #print(path_scenarios)
    indice_camara = calculo_indice_camara.indice_camara(date,path_scenarios)
    swap_instruments_clp.rename(columns={'maturity_date':'Fecha'}, inplace=True)
    swap_instruments_clp.reset_index(inplace=True)
    swap_instruments_clp.set_index('Fecha', inplace=True)
    #sinteticos_swaps = swap_instruments_clp.join(indice_camara, how='inner')
    sinteticos_swaps = pd.merge_asof(swap_instruments_clp,indice_camara)
    #print(sinteticos_swaps)




