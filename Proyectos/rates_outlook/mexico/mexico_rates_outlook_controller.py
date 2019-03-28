import sys
sys.path.insert(0, "../../libreria/")
import libreria_fdo as fs
sys.path.insert(1, "../library/")
import curve_tools as ct
import pandas as pd
import numpy as np
from scipy import optimize
from tia.bbg import v3api
import datetime as dt
import math
from workalendar.america import Mexico



def fetch_inputs():
    '''
    Lee el excel con los inputs del monitor.
    '''
    # Abrimos el excel de inputs
    wb = fs.open_workbook(".\\inputs.xlsx", True, True)
    # Obtenemos los paths de tom
    path_scenarios = fs.get_frame_xl(wb, "path_scenarios", 1, 1, [0])
    # Guardamos las fechas de rpm
    rpm_dates = path_scenarios[path_scenarios["rpm"] == 1]
    rpm_dates = rpm_dates.index
    path_scenarios =path_scenarios.drop("rpm", 1)
    path_scenarios = path_scenarios / 100
    # Guardamos los paths sin term premia para el reporte
    path_scenarios_display = path_scenarios
    # Obtenemos las probabilidades de ocurrencia para cada path
    path_distribution = fs.get_frame_xl(wb, "path_distribution", 1, 1, [0])
    # Obtenemos los term premia
    term_premia_cash = fs.get_frame_xl(wb, "term_premia_cash", 1, 1, [0])
    term_premia_cash = term_premia_cash / 100
    term_premia_swap = fs.get_frame_xl(wb, "term_premia_swap", 1, 1, [0])
    term_premia_swap = term_premia_swap / 100
    # Obtenemos los instrumentos nominales que vamos a valorizar
    curve_instruments_mxn = fs.get_frame_xl(wb, "curve_instruments_mxn", 1, 1, [0])
    # Obtenemos los instrumentos reales que vamos a valorizar
    curve_instruments_udi = fs.get_frame_xl(wb, "curve_instruments_udi", 1, 1, [0])
    # Obtenemos los instrumentos de la curva swap
    swap_instruments_mxn = fs.get_frame_xl(wb, "swap_instruments_mxn", 1, 1, [0])
   
    # Obtenemos parametros adicionales
    other_params = fs.get_frame_xl(wb, "other_params", 1, 1, [0])
    funding_rate = other_params.loc["funding_rate"]["data"]
    tpm_base = other_params.loc["tpm_base"]["data"]
    bonds_base = other_params.loc["bonds_base"]["data"]
    floating_rate_ticker = other_params.loc["floating_rate_ticker"]["data"]
    TIIE_ticker = other_params.loc["TIIE"]["data"]
    coupon_freq_swap = other_params.loc["coupon_freq_swap"]["data"]
    spread_tpm_TIIE = other_params.loc["spread_tpm_TIIE"]["data"]
    tpm_neutral_lower = other_params.loc["tpm_neutral_lower"]["data"]
    tpm_neutral_upper = other_params.loc["tpm_neutral_upper"]["data"]
    # Cerramos
    fs.close_excel(wb)

    
    return path_scenarios, path_distribution, term_premia_cash, term_premia_swap, curve_instruments_mxn, curve_instruments_udi, swap_instruments_mxn, funding_rate, tpm_base, bonds_base, floating_rate_ticker, TIIE_ticker, coupon_freq_swap, spread_tpm_TIIE, rpm_dates, tpm_neutral_lower, tpm_neutral_upper

def fetch_bbl_data(swap_instruments_mxn, TIIE_ticker, curve_instruments_mxn):
    '''
    Descarga los datos necesarios para el informe desde Bloomberg.
    '''
    # Definimos un terminal tia
    LocalTerminal = v3api.Terminal('localhost', 8194)

    curve_instruments_mxn= fetch_instruments_bbl(LocalTerminal, curve_instruments_mxn)
    fs.print_full(curve_instruments_mxn)


    # Obtenemos los flds para los instrumentos nominales swap
    swap_instruments_mxn = fetch_swap_instruments_bbl(LocalTerminal, swap_instruments_mxn)

    TIIE = get_TIIE(LocalTerminal, TIIE_ticker)
    tpm = get_tpm(LocalTerminal, floating_rate_ticker)

    

    cash_flow_tables = fetch_cash_flow_tables_bbl(LocalTerminal, curve_instruments_mxn)

    return curve_instruments_mxn, swap_instruments_mxn, TIIE, tpm, cash_flow_tables

def fetch_cash_flow_tables_bbl(LocalTerminal, curve_instruments):
    '''
    Obtiene un dataframe con los cash flow de todos los bonos
    '''
    curve_tickers = curve_instruments.index
    cash_flow_tables = LocalTerminal.get_reference_data(curve_tickers, ['DES_CASH_FLOW'])
    cash_flow_tables = cash_flow_tables.as_frame()

    return cash_flow_tables

def get_TIIE(LocalTerminal, TIIE_ticker):


    TIIE = float(LocalTerminal.get_reference_data(TIIE_ticker, "PX_MID").as_frame()["PX_MID"])/100
    print("TIIE "+ str(TIIE)) 
    return TIIE

def get_tpm(LocalTerminal, floating_rate_ticker):

    tpm = float(LocalTerminal.get_reference_data(floating_rate_ticker, "PX_MID").as_frame()["PX_MID"])/100
    return tpm



def fetch_swap_instruments_bbl(LocalTerminal, swap_instruments_mxn):
    '''
    Completa el dataframe de instrumentos swap con la info de Bloomberg.
    '''
    cal = Mexico()
    instrument_types = swap_instruments_mxn["type"]
    instrument_tenors = swap_instruments_mxn["tenor"]
    instruments_implied_path = swap_instruments_mxn["implied"]
    
    tpm = swap_instruments_mxn.loc["MXONBR Index"]
    swap_instruments_mxn = swap_instruments_mxn[swap_instruments_mxn.index != "MXONBR Index"]
    swap_instruments_mxn = LocalTerminal.get_reference_data(swap_instruments_mxn.index, ["PX_LAST", "DAYS_TO_MTY_TDY"])
    swap_instruments_mxn = swap_instruments_mxn.as_frame()
    aux_dates = swap_instruments_mxn["DAYS_TO_MTY_TDY"] # REVISAR SI ESTA BIEN USAR ESTE
    #swap mxn empiezan T+1
    swap_instruments_mxn["start_date"] = cal.add_working_days(fs.convert_string_to_date(fs.get_ndays_from_today(0)),1)
   

    swap_instruments_mxn["DAYS_TO_MTY_TDY"] = pd.to_datetime(swap_instruments_mxn["start_date"]) + pd.to_timedelta(swap_instruments_mxn["DAYS_TO_MTY_TDY"], unit="D")
    swap_instruments_mxn.rename(columns={"PX_LAST": "yield", "DAYS_TO_MTY_TDY": "maturity_date"}, inplace=True)
    tpm["yield"] = float(LocalTerminal.get_reference_data("MXONBR Index", "PX_MID").as_frame()["PX_MID"])
    tpm["maturity_date"] = fs.convert_string_to_date(fs.get_ndays_from_today(-1))  

   
    swap_instruments_mxn.loc["MXONBR Index"] = tpm
    swap_instruments_mxn["yield"] = swap_instruments_mxn["yield"] / 100
    swap_instruments_mxn = swap_instruments_mxn.drop("start_date", 1)
    swap_instruments_mxn["maturity_date"] = pd.to_datetime(swap_instruments_mxn["maturity_date"])
    swap_instruments_mxn.sort_values(["maturity_date"], inplace=True)   
    swap_instruments_mxn["type"] = instrument_types   
    swap_instruments_mxn["tenor"] = instrument_tenors
    swap_instruments_mxn["implied"] = instruments_implied_path

    fs.print_full(swap_instruments_mxn)

  
    return swap_instruments_mxn

def fetch_instruments_bbl(LocalTerminal, curve_instruments):
    '''
    Completa el dataframe de instrumentos con la info de Bloomberg.
    '''
    # Obtenemos los flds para los instrumentos nominales cash
    breakeven = curve_instruments["breakeven"]
    curve_instruments = LocalTerminal.get_reference_data(curve_instruments.index, ["SECURITY_DES", "YLD_YTM_MID", "DAYS_TO_MTY_TDY", "DUR_ADJ_MID"])
    curve_instruments = curve_instruments.as_frame()
    curve_instruments.rename(columns={"SECURITY_DES": "instrument", "YLD_YTM_MID": "yield", "DAYS_TO_MTY_TDY": "days_to_maturity", "DUR_ADJ_MID": "duration"}, inplace=True)
    curve_instruments["yield"] = curve_instruments["yield"] / 100
    curve_instruments["maturity_date"] = fs.convert_string_to_date(fs.get_ndays_from_today(0)) + pd.to_timedelta(curve_instruments["days_to_maturity"], unit="D")
    curve_instruments.sort_values(["days_to_maturity"], inplace=True)
    curve_instruments["local_id"] = "MBono " + curve_instruments["maturity_date"].astype(str).str[:-6]
    curve_instruments["breakeven"] = breakeven

    return curve_instruments


def compute_zero_swap_curve(swap_instruments_mxn, coupon_freq_swap, TIIE, tpm, spread_tpm_TIIE):
		
        cal = Mexico()
        start_date_swap= cal.add_working_days(fs.convert_string_to_date(fs.get_ndays_from_today(0)),1)
        start_date_curve = fs.convert_string_to_date(fs.get_ndays_from_today(0))
        TIIE_date = start_date_swap + pd.to_timedelta(28, unit="D")
        

		#se separan los instrumentos sobre los cuales se sacara la TPM implicita
        swap_instruments_mxn_implied = swap_instruments_mxn.loc[swap_instruments_mxn["implied"]==1.0]
		
		# Creamos el dataframe que tendra ala curva tras el bootstraping
        bootstraped_curve = pd.DataFrame(columns=["zero_yld"])
        end_date_curve = swap_instruments_mxn_implied["maturity_date"][-1]
        #print("tpm "+str(tpm) + "  spread "+ str(spread_tpm_TIIE) )
        ancla = tpm + spread_tpm_TIIE
        bootstraped_curve.loc[start_date_curve] = ancla
        bootstraped_curve.loc[TIIE_date] = TIIE
        print(bootstraped_curve)

        coupon_period = coupon_freq_swap/360

        n_known_coupons = 1
        prev_zero_yld = TIIE


		
        for ticker, fields in swap_instruments_mxn_implied.iterrows():
			
			#print(ticker)
            maturity_date = fields["maturity_date"]
            n_coupons = int((maturity_date - pd.to_datetime(start_date_swap)).days/coupon_freq_swap)
            coupon_yld = fields["yield"]
            fixed_coupon = coupon_yld * coupon_period
			#print(str(coupon_yld) + "|"+str(fixed_coupon)+"|"+str(n_coupons))
            known_cash_flow = compute_known_cash_flow(bootstraped_curve, n_known_coupons, fixed_coupon, start_date_swap, TIIE, coupon_period)
			#print("TIIE "+ str(TIIE)) 
			#print("known "+ str(known_cash_flow)) 
            x0 = TIIE
            zero_yld = optimize.newton(bootstrapping_error, x0, args=(known_cash_flow, fixed_coupon, prev_zero_yld, n_coupons, n_known_coupons, coupon_period))
            #print("n_coupons "+str(n_coupons)+ "  zero_yld "+ str(zero_yld))
            bootstraped_curve.loc[maturity_date] = zero_yld
            curve_dates = fs.get_dates_between(start_date_curve, maturity_date)
            bootstraped_curve = bootstraped_curve.reindex(curve_dates)
            bootstraped_curve = bootstraped_curve.interpolate(method="linear")
	
            prev_zero_yld = zero_yld
            n_known_coupons = n_coupons


        return bootstraped_curve 

def bootstrapping_error(rate, prev_cash_flow, fixed_coupon, prev_zero_yld, n_coupons_total, n_known_coupons, coupon_period):
   
    n_unknown_coupons = n_coupons_total - n_known_coupons 
    #print("n_known_coupons "+ str(n_known_coupons))
    #print("prev_zero_yld "+str(prev_zero_yld))
    interpolation_slope = (rate - prev_zero_yld)/n_unknown_coupons
    #print("interpolation_slope "+str(interpolation_slope))
    
    tenor  = (n_known_coupons+1) * coupon_period



    for j in range(1,n_unknown_coupons):
    		
    		dcf_rate = prev_zero_yld + interpolation_slope * j 
    		coupon_dcf = fixed_coupon / (1.0+ dcf_rate * tenor)
    		#print("tenor "+str(tenor) + "tasa " + str(dcf_rate) + "coupon_dcf "+str(coupon_dcf))
    		prev_cash_flow += coupon_dcf
    		tenor = tenor +  coupon_period 
    		
    # finalmente sumamos el ultimo cupon
    last_coupon =  (1.0 + fixed_coupon) / (1.0+rate*tenor)
    #print("last_coupon "+str(last_coupon) + "tenor "+str(tenor))
    cash_flow = prev_cash_flow + last_coupon
    #print("cash_flow "+ str(cash_flow))
    error = 1.0 -cash_flow

    return error

def compute_known_cash_flow(bootstraped_curve, n_known_coupons, fixed_coupon, start_date_swap, TIIE, coupon_period):
    
   # el primer cupon flotante siempre es conocido
    known_cash_flow = fixed_coupon/(1+TIIE*coupon_period)
   
   # por cada cupon lo descontamos a su tasa 
    for i in range(1,n_known_coupons):

        coupon_tenor = (i+1) * coupon_period
        coupon_date = start_date_swap + pd.to_timedelta(int(coupon_tenor*360), unit='D')
        discount_rate = float(bootstraped_curve.loc[coupon_date]["zero_yld"])
        coupon_dcf = fixed_coupon / (1+discount_rate*coupon_tenor)
        known_cash_flow += coupon_dcf

    return known_cash_flow


def compute_swap_implied_path(rpm_dates, path_scenarios_display, swap_instruments_mxn, zero_swap_curve, TIIE, tpm_base, tpm, spread_tpm_TIIE, second_order=False):
    '''
    Calcula el path implicito en una curva swap.
    '''
    # Fijamos los parametros de la optimizacion
    spot_date = rpm_dates[0]
    cal = Mexico()
    start_date_swap= cal.add_working_days(fs.convert_string_to_date(fs.get_ndays_from_today(0)),1)
    TIIE_date = pd.Timestamp(start_date_swap + pd.to_timedelta(28, unit="D"))
    aux_date = pd.Timestamp(start_date_swap + pd.to_timedelta(28*19, unit="D"))

    swap_curve_market = pd.DataFrame(columns=["zero_yld"])
    swap_curve_market.loc[TIIE_date] = TIIE
    swap_curve_market.loc[aux_date] =  zero_swap_curve.loc[aux_date]["zero_yld"]
    
    swap_instruments_mxn_maturities = swap_instruments_mxn[swap_instruments_mxn["implied"] == 1.0]["maturity_date"]
    swap_curve_market =swap_curve_market.append(zero_swap_curve[zero_swap_curve.index.isin(swap_instruments_mxn_maturities)])
    swap_curve_market.rename(columns={"zero_yld": "market"}, inplace=True)

    swap_curve_market = swap_curve_market.sort_index(ascending=True)
    
    dates = [date for date in rpm_dates]
   
    tpm_spot = tpm + spread_tpm_TIIE #esto es TPM + premio
    tpm_spot = float(tpm_spot)

    rpm = len(rpm_dates)
  

    # Fijamos el punto inicial de la optimizacion como nuestro path de tasas central
    central_path = path_scenarios["central"]
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

    estimated_curve, implied_path = ct.compound_tpm_delta(implied_delta,
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


def compute_composition_error(delta_tpm, dates, swap_curve, tpm_base, tpm_spot):
    '''
    Calcula el error entre la swap estimada y la swap spot.
    '''
    # Obtenemos la curva swap estimada
    estimated_curve, tpm_path = ct.compound_tpm_delta(delta_tpm,
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
        for i in range(11,len(x0)-2):
                cons.append({"type": "ineq", "fun": lambda x, i: x[i]*x[i+2]*1000000, "args": [i]})

    return cons

def compute_display_matrix(curve_instruments):
    '''
    Construye un dataframe para mostrar los bonos en el reporte
    '''
    display_matrix = curve_instruments.reset_index()
    display_matrix.set_index(["maturity_date"], inplace=True)
    display_matrix = display_matrix[["instrument", "yield","expected", "delta",
                                      "dove", "central", "hawk",
                                      "fra","duration", "days_to_maturity"]]
    return display_matrix


def print_monitor(display_matrix, path_scenarios_display, path_distribution, swap_implied_path, zero_swap_curve, fras_cash):
    '''
    Construye el display para el monitor
    '''
    wb = fs.open_workbook("outputs_mexico.xlsx", True, True)   
    
    
    fs.clear_sheet_xl(wb, "instruments")
    fs.clear_sheet_xl(wb, "swap_implied_path")
    fs.clear_sheet_xl(wb, "market_zero_curve")
    fs.clear_sheet_xl(wb, "path_distribution")
    fs.clear_sheet_xl(wb, "fras_cash")
    fs.clear_sheet_xl(wb, "paths")
    

    fs.paste_val_xl(wb, "instruments", 1, 1, display_matrix)
    fs.paste_val_xl(wb, "swap_implied_path", 1, 1, swap_implied_path)
    fs.paste_val_xl(wb, "market_zero_curve", 1, 1, zero_swap_curve) 
    fs.paste_val_xl(wb, "path_distribution", 1, 1, path_distribution)
    fs.paste_val_xl(wb, "fras_cash", 1, 1, fras_cash)
    fs.paste_val_xl(wb, "paths", 1, 1, path_scenarios_display)

    fs.save_workbook(wb)
    

print("fetching manual inputs...")
path_scenarios, path_distribution, term_premia_cash, term_premia_swap, curve_instruments_mxn, curve_instruments_udi, swap_instruments_mxn, funding_rate, tpm_base, bonds_base, floating_rate_ticker, TIIE_ticker, coupon_freq_swap, spread_tpm_TIIE, rpm_dates, tpm_neutral_lower, tpm_neutral_upper = fetch_inputs()

print("fetching bloomberg data...")
curve_instruments_mxn, swap_instruments_mxn, TIIE, tpm, cash_flow_tables = fetch_bbl_data(swap_instruments_mxn, TIIE_ticker, curve_instruments_mxn)

print("computing historical term premia...")

print("computing zero coupon curve...")

print("computing bonds carry and roll...")

# Guardamos los paths sin term premia para el reporte
path_scenarios_display = path_scenarios

# Calculamos el path de TPM esperado
print("computing expected monetary policy path...")
path_scenarios = ct.compute_expected_path(path_scenarios, path_distribution)

print("computing zero swap..")
zero_swap_curve = compute_zero_swap_curve(swap_instruments_mxn, coupon_freq_swap, TIIE, tpm, spread_tpm_TIIE)

print("computing swap implied path..")
swap_implied_path = compute_swap_implied_path(rpm_dates, path_scenarios, swap_instruments_mxn, zero_swap_curve, TIIE, tpm_base, tpm, spread_tpm_TIIE, True)

print("computing cash zero curve implied path...")


print("compounding term premia...")

print("computing zero cash curves...")
zero_curve_mxn = ct.compute_spot_curves(path_scenarios, "compounded_mxn", tpm_base, bonds_base)

print("computing valuations...")
curve_instruments_mxn = ct.compute_valuation(curve_instruments_mxn, cash_flow_tables, zero_curve_mxn, None, True)

print("computing fras...")
curve_instruments_mxn = ct.compute_fras(curve_instruments_mxn, 0.1)

print("computing market difference...")
# Calculamos los deltas
curve_instruments_mxn = ct.compute_delta_value(curve_instruments_mxn)

print("computing display...")
# Armamos un dataframe para el display
display_matrix = compute_display_matrix(curve_instruments_mxn)

# Construimos la matriz de fras para los instrumentos
fras_cash = ct.compute_cash_fras(curve_instruments_mxn)

print_monitor(display_matrix, path_scenarios_display, path_distribution, swap_implied_path, zero_swap_curve, fras_cash)










