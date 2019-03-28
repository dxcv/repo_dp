"""
Created on Wed Jun 27 11:00:00 2017

@author: Fernando Suarez
"""

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
import matplotlib.pyplot as plt
import seaborn as sns


# Para desabilitar warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=FutureWarning)
pd.options.mode.chained_assignment = None 

def fetch_inputs():
    '''
    Lee el excel con los inputs del monitor.
    '''
    # Abrimos el excel de inputs
    wb = fs.open_workbook(".\\inputs.xlsx", True, True)
    # Obtenemos los paths de tom
    path_scenarios = fs.get_frame_xl(wb, "path_scenarios", 1, 1, [0])
    path_scenarios = path_scenarios / 100
    # Obtenemos las probabilidades de ocurrencia para cada path
    path_distribution = fs.get_frame_xl(wb, "path_distribution", 1, 1, [0])
    # Obtenemos los term premia
    term_premia = fs.get_frame_xl(wb, "term_premia", 1, 1, [0])
    term_premia = term_premia / 100
    # Obtenemos los instrumentos nominales que vamos a valorizar
    curve_instruments = fs.get_frame_xl(wb, "curve_instruments", 1, 1, [0])
    # Obtenemos datos adicionales
    other_params = fs.get_frame_xl(wb, "other", 1, 1, [0])
    tpm_base = other_params.loc["tpm_base"]["data"]
    bonds_base = other_params.loc["bonds_base"]["data"]
    tpm_ticker = other_params.loc["tpm_ticker"]["data"]
    zero_curve_ticker = other_params.loc["zero_curve_ticker"]["data"]
    tpm_neutral_lower = other_params.loc["tpm_neutral_lower"]["data"]
    tpm_neutral_upper = other_params.loc["tpm_neutral_upper"]["data"]
    funding_rate = other_params.loc["funding_rate"]["data"]
    # Cerramos
    fs.close_excel(wb)
    
    return path_scenarios, path_distribution, term_premia, curve_instruments, tpm_base, bonds_base, tpm_ticker, zero_curve_ticker, tpm_neutral_lower, tpm_neutral_upper, funding_rate
    
def fetch_bbl_data(curve_instruments, tpm_ticker, zero_curve_ticker):
    '''
    Descarga los datos necesarios para el informe desde Bloomberg.
    '''
    # Definimos un terminal tia
    LocalTerminal = v3api.Terminal('localhost', 8194)
    # Obtenemos los flds para los instrumentos nominales cash
    curve_instruments = fetch_instruments_bbl(LocalTerminal, curve_instruments)
    # Obtenemos las tablas de desarrollo de los bonos
    cash_flow_tables = fetch_cash_flow_tables_bbl(LocalTerminal, curve_instruments)

    #Obtenemos la tpm spot
    tpm_spot = fetch_tpm_spot(LocalTerminal, tpm_ticker)

    #Obtenemos la curva cero
    historical_zero_curve = fetch_zero_market_curve_bbl(LocalTerminal, zero_curve_ticker)

    return curve_instruments, cash_flow_tables, tpm_spot, historical_zero_curve

def fetch_tpm_spot(LocalTerminal, tpm_ticker):
    '''
    Obtiene la tpm spot.
    '''
    tpm_ticker = float(LocalTerminal.get_reference_data(tpm_ticker, "PX_LAST").as_frame()["PX_LAST"])
    tpm_ticker = tpm_ticker / 100
    return tpm_ticker   

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
    curve_instruments["local_id"] = "Sob " + curve_instruments["maturity_date"].astype(str).str[:-6]
    curve_instruments["breakeven"] = breakeven
    
    return curve_instruments


def fetch_cash_flow_tables_bbl(LocalTerminal, curve_instruments):
    '''
    Obtiene un dataframe con los cash flow de todos los bonos
    '''
    curve_tickers = curve_instruments.index
    cash_flow_tables = LocalTerminal.get_reference_data(curve_tickers, ['DES_CASH_FLOW'])
    cash_flow_tables = cash_flow_tables.as_frame()

    return cash_flow_tables


def concat_tpm(curve_instruments, tpm_ticker, tpm_spot):
    '''
    Agrega la tpm al set de isntrumentos
    '''
    spot_date = fs.convert_string_to_date(fs.get_ndays_from_today(0))
    spot_date = pd.Timestamp(spot_date)
    curve_instruments.loc[tpm_ticker] = [tpm_ticker, tpm_spot, 1, 0.0, spot_date, tpm_ticker, 0, tpm_spot, tpm_spot, tpm_spot, tpm_spot, 0.0, 0.0]
    curve_instruments = curve_instruments.sort_values("days_to_maturity")
    
    return curve_instruments



def compute_display_matrix(curve_instruments):
    '''
    Construye un dataframe para mostrar los bonos en el reporte
    '''
    display_matrix = curve_instruments.reset_index()
    display_matrix.set_index(["maturity_date"], inplace=True)
    display_matrix = display_matrix[["instrument", "yield","expected", "delta",
                                      "dove", "central", "hawk",
                                      "fra", "yield_buffer_1M", "yield_buffer_3M", 
                                      "duration", "days_to_maturity"]]
    return display_matrix


def nelson_siegel_curve(curve_points):
    '''
    Dada lista de tenors, modela la curva y obtiene las tasas en los distintos tenors para una fecha indicada.
    '''
    tau = 2000
    tau2 = 0.8
    parameters = get_parameters(curve_points=curve_points, tau=tau, tau2=tau2)
        
    return parameters


def compute_yields(tenors, parameters):
    '''
    Calcula la curva utilziando nelson siegel, dados los parametros y los tenors. Retorna una lista con las yields dados los tenors pedidos.
    '''
    
    b0, b1, b2, b3 = parameters[1:5]
    tau = float(parameters[0])
    tau2 = float(parameters[5])
    yc = b0 * level_exposure(tenors, tau) + b1 * slope_exposure(tenors, tau) + b2 * curvature_exposure(tenors, tau) + b3 * svensson_exposure(tenors, tau2)


    return yc


def level_exposure(tenors, tau):
    '''
    Computa la exposicion o factor loading a nivel.
    '''
    return 1


def slope_exposure(tenors, tau):
    '''
    Computa la exposicion o factor loading a pendiente.
    '''
    return ((1 - np.exp(-tenors / tau)) / (tenors/tau))


def curvature_exposure(tenors, tau):
    '''
    Computa la exposicion o factor loading a curvatura.
    '''
    return ((((1 - np.exp(-tenors / tau)) / (tenors/tau)) - np.exp(-tenors / tau)))


def svensson_exposure(tenors, tau):
    '''
    Computa la exposicion o factor loading al factor de svensson.
    '''
    return ((((1 - np.exp(-tenors / tau)) / (tenors/tau)) - np.exp(-tenors / tau)))


def get_parameters(curve_points, tau, tau2):
    '''
    Dados los parametros.
    '''
    tenors = curve_points.index.values
    yields = curve_points["yield"].values
    x0 = np.array([0.1, 0.1, 0.1, 0.1])
    x0 = optimize.leastsq(nelson_siegel_residuals, x0, args = (tenors, yields, tau, tau2))
    return [tau] + x0[0].tolist() + [tau2]

def nelson_siegel_residuals(p, tenors, yields, tau, tau2):
    '''
    Calcula el error entre las tasas computadas sobre los parametros calculados y los empiricos.
    '''
    
    b0, b1, b2, b3 = p
    curve_yields = compute_yields(tenors, [tau, b0, b1, b2, b3, tau2])
    
    '''
    b0, b1, b2 = p
    curve_yields = compute_yields(tenors, [tau, b0, b1, b2])
    '''
    err = yields - curve_yields
    err = err.astype(float)
    return err


def fetch_zero_market_curve_bbl(LocalTerminal, zero_curve_ticker):
    '''
    Obtiene la curva zero historica de bloomberg
    '''
    date_inic = fs.get_ndays_from_today(1500)
    date_end = fs.get_ndays_from_today(1)
    curve_members = LocalTerminal.get_reference_data(zero_curve_ticker, ["CURVE_MEMBERS"])
    curve_members = curve_members.as_frame().loc["YCGT0520 Index"]["CURVE_MEMBERS"]["Curve Members"]
    curve_members = ["PRRRONUS Index"] + curve_members.tolist()
    curves_dataset = LocalTerminal.get_historical(curve_members,
                                                 ["PX_LAST"],
                                                 ignore_security_error=1,
                                                 ignore_field_error=1,
                                                 start=date_inic,
                                                 end=date_end,
                                                 max_data_points=10000000,
                                                 non_trading_day_fill_method="PREVIOUS_VALUE",
                                                 non_trading_day_fill_option="ALL_CALENDAR_DAYS")
    curves_dataset = curves_dataset.as_frame()
    curves_dataset = curves_dataset[curve_members]
    curves_dataset.columns = curves_dataset.columns.droplevel(level=1)
    curves_dataset = curves_dataset.sort_index(ascending=False)
    curves_dataset = curves_dataset / 100


    for ticker in curves_dataset.columns:
        if ticker == "PRRRONUS Index":
            curves_dataset.rename(columns={"PRRRONUS Index": 1}, inplace=True) 
        elif ticker == "CUSOS108 Index":
            curves_dataset.rename(columns={"CUSOS108 Index": 10890}, inplace=True) 
        elif ticker == "CUSO0 Index":
            curves_dataset.rename(columns={"CUSO0 Index": 30}, inplace=True) 
        else:
            days = ticker[4:-6]
            curves_dataset.rename(columns={ticker: int(days)}, inplace=True) 


    return curves_dataset



def compute_spot_zero_curve(historical_zero_curve):
    '''
    Arma una curva diaria spot
    '''
    curve = historical_zero_curve.loc[historical_zero_curve.index[0]] 
    curve = curve.to_frame(name="yield")
    curve.index.name = "tenor_days"

    # Calibramos una nelson siegel svensson
    parameters = nelson_siegel_curve(curve) 

    tenors = curve.index[-1]
    tenors = np.arange(tenors) + 1
    curve = compute_yields(tenors=tenors, parameters=parameters)
    
    curve = pd.DataFrame(curve, index=tenors, columns=["yield"])
    curve.index.name = "tenor"

    return curve

def compute_historical_term_premia(historical_zero_curve, tpm_neutral_lower, tpm_neutral_upper):
    '''
    Calcula la evolucion del premio por plazo.
    '''
    historical_term_premia_5y = pd.DataFrame(columns=["term_premia"], index=historical_zero_curve.index)
    historical_term_premia_10y = pd.DataFrame(columns=["term_premia"], index=historical_zero_curve.index)
    historical_term_premia_20y = pd.DataFrame(columns=["term_premia"], index=historical_zero_curve.index)
    tpm_neutral = (tpm_neutral_lower+tpm_neutral_upper) / 2

    for t, yields in historical_zero_curve.iterrows():
        curve = yields.to_frame(name="yield")
        curve.index.name = "tenor_days"
        # Calibramos una nelson siegel svensson
        parameters = nelson_siegel_curve(curve)
        tenors = np.array([1799, 1800, 3599, 3600, 7199, 7200])
        curve = compute_yields(tenors, parameters)
        fwd_rate_5y = (((1.0+curve[1])**tenors[1])/((1.0+curve[0]
            )**tenors[0])) - 1.0
        fwd_rate_10y = (((1.0+curve[3])**tenors[3])/((1.0+curve[2])**tenors[2])) - 1.0
        fwd_rate_20y = (((1.0+curve[5])**tenors[5])/((1.0+curve[4])**tenors[4])) - 1.0
        term_premia_5y = (fwd_rate_5y - tpm_neutral)*10000
        term_premia_10y = (fwd_rate_10y - tpm_neutral)*10000
        term_premia_20y = (fwd_rate_20y - tpm_neutral)*10000
        historical_term_premia_5y.loc[t, "term_premia"] = term_premia_5y
        historical_term_premia_10y.loc[t, "term_premia"] = term_premia_10y
        historical_term_premia_20y.loc[t, "term_premia"] = term_premia_20y

    historical_term_premia_5y["average"] = historical_term_premia_5y["term_premia"].mean()
    historical_term_premia_10y["average"] = historical_term_premia_10y["term_premia"].mean()
    historical_term_premia_20y["average"] = historical_term_premia_20y["term_premia"].mean()
    
    return historical_term_premia_5y, historical_term_premia_10y, historical_term_premia_20y


def print_monitor(display_matrix, path_scenarios_display, term_premia, path_distribution, market_zero_curve,
                  tpm_neutral_lower,tpm_neutral_upper, funding_rate, fras_cash, historical_term_premia_5y,
                  historical_term_premia_10y, historical_term_premia_20y, cary_30, cary_90, cary_180, cary_360):
    '''
    Construye el display para el monitor
    '''
    wb = fs.open_workbook("outputs_peru.xlsx", True, True)
    fs.clear_sheet_xl(wb, "instruments")
    fs.clear_sheet_xl(wb, "paths")
    fs.clear_sheet_xl(wb, "term_premia")
    fs.clear_sheet_xl(wb, "path_distribution")
    fs.clear_sheet_xl(wb, "market_zero_curve")
    fs.clear_sheet_xl(wb, "tpm_neutral")
    fs.clear_sheet_xl(wb, "funding_rate")
    fs.clear_sheet_xl(wb, "fras_cash")
    fs.clear_sheet_xl(wb, "historical_term_premia_5y")
    fs.clear_sheet_xl(wb, "historical_term_premia_10y")
    fs.clear_sheet_xl(wb, "historical_term_premia_20y")
    fs.clear_sheet_xl(wb, "cary_30")
    fs.clear_sheet_xl(wb, "cary_90")
    fs.clear_sheet_xl(wb, "cary_180")
    fs.clear_sheet_xl(wb, "cary_360")
    fs.paste_val_xl(wb, "instruments", 1, 1, display_matrix)
    fs.paste_val_xl(wb, "paths", 1, 1, path_scenarios_display)
    fs.paste_val_xl(wb, "term_premia", 1, 1, term_premia)
    fs.paste_val_xl(wb, "path_distribution", 1, 1, path_distribution)
    fs.paste_val_xl(wb, "market_zero_curve", 1, 1, market_zero_curve)
    fs.paste_val_xl(wb, "tpm_neutral", 1, 1, tpm_neutral_lower)
    fs.paste_val_xl(wb, "tpm_neutral", 2, 1, tpm_neutral_upper)
    fs.paste_val_xl(wb, "funding_rate", 1, 1, funding_rate)
    fs.paste_val_xl(wb, "fras_cash", 1, 1, fras_cash)
    fs.paste_val_xl(wb, "historical_term_premia_5y", 1, 1, historical_term_premia_5y)
    fs.paste_val_xl(wb, "historical_term_premia_10y", 1, 1, historical_term_premia_10y)
    fs.paste_val_xl(wb, "historical_term_premia_20y", 1, 1, historical_term_premia_20y)
    fs.paste_val_xl(wb, "cary_30", 1, 1, cary_30)
    fs.paste_val_xl(wb, "cary_90", 1, 1, cary_90)
    fs.paste_val_xl(wb, "cary_180", 1, 1, cary_180)
    fs.paste_val_xl(wb, "cary_360", 1, 1, cary_360)


    path_pdf = fs.get_self_path()
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p1")-1, ".", path_pdf + "1.pdf")
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p2")-1, ".", path_pdf + "2.pdf")
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p3")-1, ".", path_pdf + "3.pdf")
    name = "Peru_Rates_Outlook_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    fs.merge_pdf(".", name)
    fs.delete_file(path_pdf + "1.pdf")
    fs.delete_file(path_pdf + "2.pdf")
    fs.delete_file(path_pdf + "3.pdf")
    fs.save_workbook(wb)
    fs.close_excel(wb)
    src = name
    dst = "L:\\Rates & FX\\fsb\\reporting\\rates_outlook_backup\\" + name
    fs.copy_file(src, dst)
    fs.delete_file(path_pdf+ name)
    fs.open_file(dst)



print("fetching manual inputs...") 
path_scenarios, path_distribution, term_premia, curve_instruments, tpm_base, bonds_base, tpm_ticker, zero_curve_ticker, tpm_neutral_lower, tpm_neutral_upper, funding_rate = fetch_inputs()

# Descargamos los datos de Bloomberg
print("fetching bloomberg data...")
curve_instruments, cash_flow_tables, tpm_spot, historical_zero_curve = fetch_bbl_data(curve_instruments, tpm_ticker, zero_curve_ticker)


# Calculamos el term premia historico
print("computing historical term premia...")
historical_term_premia_5y, historical_term_premia_10y, historical_term_premia_20y = compute_historical_term_premia(historical_zero_curve, tpm_neutral_lower, tpm_neutral_upper)

# Calibramos la curva cero cupon 
print("computing zero coupon curve...")
market_zero_curve = compute_spot_zero_curve(historical_zero_curve)

# Calculamos carry and roll 
print("computing bonds carry and roll...")
cary_30 = ct.compute_carry_roll(market_zero_curve, 30)
cary_90 = ct.compute_carry_roll(market_zero_curve, 90)
cary_180 = ct.compute_carry_roll(market_zero_curve, 180)
cary_360 = ct.compute_carry_roll(market_zero_curve, 360)


# Calculamos la tpm implicita en la cash cero cupon
print("computing zero curve implied path...")
market_zero_curve = ct.compute_zero_implied_tpm(market_zero_curve)

# Calculamos el term premia implicito en la cash cero cupon
print("computing zero curve implied term premia...")
market_zero_curve = ct.compute_implied_term_premia(market_zero_curve, tpm_neutral_lower, tpm_neutral_upper)

# Guardamos los paths sin term premia para el reporte
path_scenarios_display = path_scenarios

# Calculamos el path de TPM esperado
print("computing expected monetary policy path...")
path_scenarios = ct.compute_expected_path(path_scenarios, path_distribution)

# Le agregamos el term premia a los distintos paths
print("compounding term premia...")
path_scenarios = ct.sum_term_premia(path_scenarios, term_premia)

# Obtenemos las curvas cero
print("computing zero cash curves...")
zero_curves = ct.compute_spot_curves(path_scenarios, "compounded", tpm_base, bonds_base)

# Calculamos el valuation de los instrumentos
print("computing valuations...")
curve_instruments = ct.compute_valuation(curve_instruments, cash_flow_tables, zero_curves)

# Calculamos el colchon de tasa de los instrumentos
print("computing nominal yield buffers...")
curve_instruments = ct.compute_yield_buffer(curve_instruments, funding_rate)

# Agregamos la repo a los instrumentos
print("Joining tpm...")
curve_instruments = concat_tpm(curve_instruments, tpm_ticker, tpm_spot)

print("computing fras...")
# Calculamos los fras
curve_instruments = ct.compute_fras(curve_instruments, 0.1)

print("computing market difference...")
# Calculamos los deltas
curve_instruments = ct.compute_delta_value(curve_instruments)

print("computing display...")
# Armamos un dataframe para el display
display_matrix = compute_display_matrix(curve_instruments)

# Construimos la matriz de fras para los instrumentos
fras_cash = ct.compute_cash_fras(curve_instruments)

# Imprimimos el informe
print_monitor(display_matrix,
              path_scenarios_display,
              term_premia,
              path_distribution,
              market_zero_curve,
              tpm_neutral_lower,
              tpm_neutral_upper, 
              funding_rate,
              fras_cash,
              historical_term_premia_5y,
              historical_term_premia_10y,
              historical_term_premia_20y,
              cary_30,
              cary_90,
              cary_180,
              cary_360)
