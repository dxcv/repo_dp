"""
Created on Wed May 31 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, "../../libreria/")
import libreria_fdo as fs
sys.path.insert(1, "../library/")
import curve_tools as ct
sys.path.insert(2, "./breakeven_model/")
import breakeven_model as bm
sys.path.insert(3, "./term_premia_model/")
import term_premia as tp
sys.path.insert(4, "./spread_model/")
import spread_model as sp
import pandas as pd
import numpy as np
from scipy import optimize
from tia.bbg import v3api
import datetime as dt
import math
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
    curve_instruments_clp = fs.get_frame_xl(wb, "curve_instruments_clp", 1, 1, [0])
    # Obtenemos los instrumentos reales que vamos a valorizar
    curve_instruments_clf = fs.get_frame_xl(wb, "curve_instruments_clf", 1, 1, [0])
    # Obtenemos los instrumentos de la curva swap
    swap_instruments_clp = fs.get_frame_xl(wb, "swap_instruments_clp", 1, 1, [0])
    swap_instruments_clf = fs.get_frame_xl(wb, "swap_instruments_clf", 1, 1, [0])
    # Obtenemos los forwards de inflacion
    inflation_forwards = fs.get_frame_xl(wb, "inflation_forwards", 1, 1, [0])
    # Obtenemos los paths de tpm para las simulaciones
    path_simulation_scenarios = fs.get_frame_xl(wb, "path_simulation_scenarios", 1, 1, [0])
    path_simulation_scenarios = path_simulation_scenarios / 100
    # Guardamos los paths de simulacion sin term premia para el reporte
    path_simulation_scenarios_display = path_simulation_scenarios
    # Obtenemos parametros adicionales
    breakeven_params = fs.get_frame_xl(wb, "breakeven_model", 1, 1, [0])
    train_breakeven_model = breakeven_params.loc["trainning"]["data"]
    # Obtenemos parametros adicionales
    other_params = fs.get_frame_xl(wb, "other_params", 1, 1, [0])
    funding_rate = other_params.loc["funding_rate"]["data"]
    tpm_base = other_params.loc["tpm_base"]["data"]
    bonds_base = other_params.loc["bonds_base"]["data"]
    floating_rate_ticker = other_params.loc["floating_rate_ticker"]["data"]
    cpi_ticker = other_params.loc["cpi_ticker"]["data"]
    tpm_neutral_lower = other_params.loc["tpm_neutral_lower"]["data"]
    tpm_neutral_upper = other_params.loc["tpm_neutral_upper"]["data"]
    # Cerramos
    fs.close_excel(wb)

    
    return path_scenarios, path_distribution, term_premia_cash, term_premia_swap, curve_instruments_clp, curve_instruments_clf, swap_instruments_clp, swap_instruments_clf, inflation_forwards, funding_rate, tpm_base, bonds_base, path_scenarios_display, path_simulation_scenarios, path_simulation_scenarios_display, floating_rate_ticker, cpi_ticker, rpm_dates, tpm_neutral_lower, tpm_neutral_upper, breakeven_params, train_breakeven_model

    
def fetch_bbl_data(curve_instruments_clp, curve_instruments_clf, swap_instruments_clp, swap_instruments_clf, inflation_forwards, floating_rate_ticker, cpi_ticker, train_breakeven_model):
    '''
    Descarga los datos necesarios para el informe desde Bloomberg.
    '''
    # Definimos un terminal tia
    LocalTerminal = v3api.Terminal('localhost', 8194)

    # Obtenemos los flds para los instrumentos nominales cash clp
    curve_instruments_clp = fetch_instruments_bbl(LocalTerminal, curve_instruments_clp)

    # Obtenemos los flds para los instrumentos nominales cash en uf
    curve_instruments_clf= fetch_instruments_bbl(LocalTerminal, curve_instruments_clf)

    # Obtenemos las tablas de desarrollo de los bonos nominals
    cash_flow_tables_clp = fetch_cash_flow_tables_bbl(LocalTerminal, curve_instruments_clp)

    # Obtenemos las tablas de desarrollo de los bonos en uf
    cash_flow_tables_clf = fetch_cash_flow_tables_bbl(LocalTerminal, curve_instruments_clf)

    # Obtenemos los flds para los instrumentos nominales swap
    swap_instruments_clp, swap_instruments_clf = fetch_swap_instruments_bbl(LocalTerminal, swap_instruments_clp, swap_instruments_clf)

    # Obtenemos la serie de uf
    clf_serie = fetch_clf_serie(LocalTerminal, inflation_forwards)
    print(clf_serie)
    

    # Obtenemos la tasa floatante para la swap
    floating_rate = fetch_floating_rate(LocalTerminal, floating_rate_ticker)

    # Obtenemos la serie del ipc
    cpi_serie = fetch_cpi(LocalTerminal, cpi_ticker)

    # Descargamos los datos para calcular el modelo de breakeven
    clf_spot_dataset_forecast, clf_fwd_dataset_forecast = fetch_breakeven_model_inputs_bbl(LocalTerminal, inflation_forwards, swap_instruments_clp, swap_instruments_clf, 1)

    # Descargamos los datos para calcular el modelo de term premia
    term_premia_dataset = fetch_term_premia_model_inputs_bbl(LocalTerminal)

    # Descargamos los datos para entrenar el modelo de breakeven
    if train_breakeven_model is True:
    	clf_spot_dataset_training, clf_fwd_dataset_training = fetch_model_inputs_bbl(LocalTerminal, inflation_forwards, swap_instruments_clp, swap_instruments_clf, 2100)
    else:
    	clf_spot_dataset_training, clf_fwd_dataset_training = None, None

    return curve_instruments_clp, curve_instruments_clf, cash_flow_tables_clp, cash_flow_tables_clf, swap_instruments_clp, swap_instruments_clf, clf_serie, floating_rate, cpi_serie, clf_spot_dataset_training, clf_fwd_dataset_training, clf_spot_dataset_forecast, clf_fwd_dataset_forecast, term_premia_dataset


def fetch_market_zero_curve(inflation_linked=False):
    '''
    Descarga la curva cero de riskamerica desde la base de datos.
    '''
    query = "select tenor, yield from {}"
    if inflation_linked:
        table_name = "real_zero_curve_uf_spot"
    else:
        table_name = "nominal_zero_curve_clp_spot"
    query = query.format(table_name)
    market_zero_curve = fs.get_frame_sql_user(server="Puyehue",
                                              database="MesaInversiones",
                                              username="usrConsultaComercial",
                                              password="Comercial1w",
                                              query=query)
    market_zero_curve.set_index(["tenor"], inplace=True)
    market_zero_curve = market_zero_curve / 100
    
    return market_zero_curve


def fetch_historical_zero_rates(curve_name, rolling_days):
    '''
    Descarga las tasas cero cupon historicas para distintos tenors.
    '''
    start_date = fs.get_ndays_from_today(rolling_days)
    query = "select date, tenor, yield from zhis_ra_curves where curve_name = '{}' and tenor in (360, 1080, 1800, 3600, 7200, 1799, 3599, 7199, 1440, 2160, 3960, 7560, 720, 1770, 3570, 7170) and date >= '{}' order by date desc"
    query = query.format(curve_name, start_date)
    historical_zero_rates = fs.get_frame_sql_user(server="Puyehue",
                                                  database="MesaInversiones",
                                                  username="usrConsultaComercial",
                                                  password="Comercial1w",
                                                  query=query)
    historical_zero_rates.set_index(["date"], inplace=True)
    historical_zero_rates["yield"] = historical_zero_rates["yield"] / 100

    return historical_zero_rates

def fetch_instruments_bbl(LocalTerminal, curve_instruments):
    '''
    Completa el dataframe de instrumentos con la info de Bloomberg.
    '''
    # Obtenemos los flds para los instrumentos nominales cash
    breakeven = curve_instruments["breakeven"]
    
    curve_instruments = LocalTerminal.get_reference_data(curve_instruments.index, ["SECURITY_DES", "ID_MDM_MISC_DOMES", "YLD_CNV_LAST", "DAYS_TO_MTY_TDY", "DUR_MID"])
    curve_instruments = curve_instruments.as_frame()
    bval_tickers = curve_instruments.index.str.replace("@TLR1", "@BVAL")
    curve_instruments_bval = LocalTerminal.get_reference_data(bval_tickers, ["SECURITY_DES", "ID_MDM_MISC_DOMES", "YLD_CNV_LAST", "DAYS_TO_MTY_TDY", "DUR_MID"])
    curve_instruments_bval = curve_instruments_bval.as_frame()
    curve_instruments_bval = curve_instruments_bval.reset_index()
    curve_instruments_bval["index"] = curve_instruments_bval["index"].str.replace("@BVAL", "@TLR1")
    curve_instruments_bval.set_index(["index"], inplace=True)
    curve_instruments["DUR_MID"] = curve_instruments["DUR_MID"].fillna(curve_instruments_bval["DUR_MID"])
    curve_instruments["YLD_CNV_LAST"] = curve_instruments["YLD_CNV_LAST"].fillna(curve_instruments_bval["YLD_CNV_LAST"])
    curve_instruments.rename(columns={"SECURITY_DES": "instrument", "YLD_CNV_LAST": "yield", "DAYS_TO_MTY_TDY": "days_to_maturity", "ID_MDM_MISC_DOMES": "local_id", "DUR_MID": "duration"}, inplace=True)
    curve_instruments["yield"] = curve_instruments["yield"] / 100
    curve_instruments.sort_values(["days_to_maturity"], inplace=True)
    curve_instruments["maturity_date"] = fs.convert_string_to_date(fs.get_ndays_from_today(0)) + pd.to_timedelta(curve_instruments["days_to_maturity"], unit="D")
    curve_instruments["breakeven"] = breakeven
    
    return curve_instruments

def fetch_cash_flow_tables_bbl(LocalTerminal, curve_instruments_clp):
    '''
    Obtiene un dataframe con los cash flow de todos los bonos
    '''
    curve_tickers = curve_instruments_clp.index
    cash_flow_tables = LocalTerminal.get_reference_data(curve_tickers, ['DES_CASH_FLOW'])
    cash_flow_tables = cash_flow_tables.as_frame()
    
    return cash_flow_tables

def fetch_swap_instruments_bbl(LocalTerminal, swap_instruments_clp, swap_instruments_clf):
    '''
    Completa el dataframe de instrumentos swap con la info de Bloomberg.
    '''
    instrument_types = swap_instruments_clp["type"]
    instrument_tenors = swap_instruments_clp["tenor"]
    instrument_slope_simulation = swap_instruments_clp["slope_simulation"]
    tpm = swap_instruments_clp.loc["CHOVCHOV Index"]
    swap_instruments_clp = swap_instruments_clp[swap_instruments_clp.index != "CHOVCHOV Index"]
    swap_instruments_clp = LocalTerminal.get_reference_data(swap_instruments_clp.index, ["PX_LAST", "DAYS_TO_MTY_TDY"])
    swap_instruments_clp = swap_instruments_clp.as_frame()
    aux_dates = swap_instruments_clp["DAYS_TO_MTY_TDY"] # porque clf no los tiene
    swap_instruments_clp["today"] = fs.convert_string_to_date(fs.get_ndays_from_today(0))
    #for ticker, swap in swap_instruments_clp.iterrows():
    #    swap_instruments_clp.set_value(ticker, "DAYS_TO_MTY_TDY", swap_instruments_clp.loc[ticker]["today"] + dt.timedelta(days=swap_instruments_clp.loc[ticker]["DAYS_TO_MTY_TDY"]))    
    swap_instruments_clp["DAYS_TO_MTY_TDY"] = pd.to_datetime(swap_instruments_clp["today"]) + pd.to_timedelta(swap_instruments_clp["DAYS_TO_MTY_TDY"], unit="D")
    swap_instruments_clp.rename(columns={"PX_LAST": "yield", "DAYS_TO_MTY_TDY": "maturity_date"}, inplace=True)
    tpm["yield"] = float(LocalTerminal.get_reference_data("CHOVCHOV Index", "PX_MID").as_frame()["PX_MID"])
    tpm["maturity_date"] = fs.convert_string_to_date(fs.get_ndays_from_today(-1))  # no se si funcionara es para sumar un dia jajaja
    
    swap_instruments_clp.loc["CHOVCHOV Index"] = tpm
    swap_instruments_clp["yield"] = swap_instruments_clp["yield"] / 100
    swap_instruments_clp = swap_instruments_clp.drop("today", 1)
    swap_instruments_clp["maturity_date"] = pd.to_datetime(swap_instruments_clp["maturity_date"])
    swap_instruments_clp.sort_values(["maturity_date"], inplace=True)   
    swap_instruments_clp["type"] = instrument_types   
    swap_instruments_clp["tenor"] = instrument_tenors
    swap_instruments_clp["slope_simulation"] = instrument_slope_simulation.astype(int)

    instrument_types = swap_instruments_clf["type"]
    instrument_tenors = swap_instruments_clf["tenor"]
    instrument_slope_simulation = swap_instruments_clf["slope_simulation"]
    tpm_real = swap_instruments_clf.loc["CLICREAL Index"]
    swap_instruments_clf = swap_instruments_clf[swap_instruments_clf.index != "CLICREAL Index"]
    swap_instruments_clf = LocalTerminal.get_reference_data(swap_instruments_clf.index, ["PX_LAST", "DAYS_TO_MTY_TDY"])
    swap_instruments_clf = swap_instruments_clf.as_frame()
    for ticker, data in swap_instruments_clf.iterrows():
        ticker_aux = ticker.replace("CHSWC", "CHSWP")
        days = aux_dates.loc[ticker_aux]
        swap_instruments_clf.set_value(ticker, "DAYS_TO_MTY_TDY", days)

    swap_instruments_clf["today"] = fs.convert_string_to_date(fs.get_ndays_from_today(0))
    #for ticker, swap in swap_instruments_clp.iterrows():
    #    swap_instruments_clp.set_value(ticker, "DAYS_TO_MTY_TDY", swap_instruments_clp.loc[ticker]["today"] + dt.timedelta(days=swap_instruments_clp.loc[ticker]["DAYS_TO_MTY_TDY"]))    
    swap_instruments_clf["DAYS_TO_MTY_TDY"] = pd.to_datetime(swap_instruments_clf["today"]) + pd.to_timedelta(swap_instruments_clf["DAYS_TO_MTY_TDY"], unit="D")
    swap_instruments_clf.rename(columns={"PX_LAST": "yield", "DAYS_TO_MTY_TDY": "maturity_date"}, inplace=True)

    inflation_spot = float(LocalTerminal.get_reference_data("CNPINSMO Index", "PX_LAST").as_frame()["PX_LAST"])
    inflation_spot = inflation_spot / 100
    tpm = tpm["yield"] / 100
    tpm_real["yield"] = 100 * (((1.0+tpm)/((1.0+inflation_spot)**12))-1.0)
    tpm_real["maturity_date"] = fs.convert_string_to_date(fs.get_ndays_from_today(-1))  # no se si funcionara es para sumar un dia jajaja
    swap_instruments_clf.loc["CLICREAL Index"] = tpm_real
    swap_instruments_clf["yield"] = swap_instruments_clf["yield"] / 100
    swap_instruments_clf = swap_instruments_clf.drop("today", 1)
    swap_instruments_clf["maturity_date"] = pd.to_datetime(swap_instruments_clf["maturity_date"])
    swap_instruments_clf.sort_values(["maturity_date"], inplace=True)   
    swap_instruments_clf["type"] = instrument_types
    swap_instruments_clf["tenor"] = instrument_tenors
    swap_instruments_clf["slope_simulation"] = instrument_slope_simulation.astype(int)
    return swap_instruments_clp, swap_instruments_clf

def fetch_breakeven_model_inputs_bbl(LocalTerminal, inflation_forwards, swap_instruments_clp, swap_instruments_clf, dataset_len):
    '''
    Descarga los datos para el modelo de breakeven desde Bloomberg.
    '''
    # Obtenemos fecha importantes
    date_inic_str = fs.get_ndays_from_today(dataset_len)
    date_end_str = fs.get_ndays_from_today(0)
    date_inic = fs.convert_string_to_date(date_inic_str)
    date_end = fs.convert_string_to_date(date_end_str)
    date_next_mth = fs.get_ndays_from_today(-31)
    dates_next_mth = fs.get_dates_between(date_end_str, date_next_mth)
    
    # Obtenemos la fecha del proximo nueve
    for date in dates_next_mth:
        # Obetnemos el dia de la fecha
        day = date.timetuple()[2]
        if day == 9:
            next_nine = date
            break

    # Armamso los dataframes de input
    forwards = inflation_forwards.reset_index()
    tenors = forwards["tenor"]
    tickers = forwards["ticker"]

    swaps_clp = swap_instruments_clp.reset_index()
    swaps_clp = swaps_clp[swaps_clp["tenor"].isin(["2Y", "5Y"])]["index"]
    swaps_clf = swap_instruments_clf.reset_index()
    swaps_clf = swaps_clf[swaps_clf["tenor"].isin(["2Y", "5Y"])]["index"]
    
    tickers = tickers.unique()
    clf_ticker =tickers[0]
    tickers = np.delete(tickers, 0, 0)
    tickers = np.append(tickers, clf_ticker)  

    tickers = np.append(tickers, swaps_clp)    
    tickers = np.append(tickers, swaps_clf)  

    tenors = tenors[2:]
    tenors_aux = pd.Series(["UF", "P2", "P5", "C2", "C5"])
    tenors = tenors.append(tenors_aux)

    # Descargamos de bloomberg las series
    dataset_fwd = LocalTerminal.get_historical(tickers,
                                              ["PX_LAST"],
                                              currency="CLP",
                                              ignore_security_error=1,
                                              ignore_field_error=1,
                                              start=date_inic,
                                              end=next_nine,
                                              max_data_points=10000000,
                                              non_trading_day_fill_method="PREVIOUS_VALUE",
                                              non_trading_day_fill_option="ALL_CALENDAR_DAYS")
    dataset_fwd = dataset_fwd.as_frame()
    dataset_fwd = dataset_fwd[tickers]
    dataset_fwd.columns = dataset_fwd.columns.droplevel(level=1)
    dataset_fwd = dataset_fwd.sort_index(ascending=False)
    dataset_spot = dataset_fwd["CHUF Index"]
    dataset_spot = dataset_spot.to_frame(name="CHUF Index")    
    dataset_fwd = dataset_fwd[dataset_fwd.index<=pd.Timestamp(date_end)]
    if dataset_len == 1:
    	dataset_spot = dataset_spot[dataset_spot.index==pd.Timestamp(next_nine)]
    	dataset_fwd = dataset_fwd[dataset_fwd.index==pd.Timestamp(date_end)]

    return dataset_spot, dataset_fwd


def fetch_term_premia_model_inputs_bbl(LocalTerminal):
    '''
    Descarga los datos para el modelo de term premia desde Bloomberg.
    '''
    # Obtenemos fecha importantes
    date_inic_str = fs.get_ndays_from_today(29)
    date_end_str = fs.get_ndays_from_today(0)
    date_inic = fs.convert_string_to_date(date_inic_str)
    date_end = fs.convert_string_to_date(date_end_str)
    tickers = ["CCHIL1U5 CBIN Curncy", "RIAMPDU7 Index", "CHSWP5 BGN Curncy", "CHSWC5 BGN Curncy", "USDCLPV1M BGN Curncy"]
    # Descargamos de bloomberg las series
    dataset = LocalTerminal.get_historical(tickers,
                                           ["PX_LAST"],
                                           currency="CLP",
                                           ignore_security_error=1,
                                           ignore_field_error=1,
                                           start=date_inic,
                                           end=date_end,
                                           max_data_points=10000000,
                                           non_trading_day_fill_method="PREVIOUS_VALUE",
                                           non_trading_day_fill_option="ALL_CALENDAR_DAYS")
    dataset = dataset.as_frame()
    dataset = dataset[tickers]
    dataset.columns = dataset.columns.droplevel(level=1)
     
    dataset["RIAMPDU7_Stdev"] = dataset["RIAMPDU7 Index"].rolling(center=False,window=30).std()
    dataset["Breakeven_5"]=((100 + dataset["CHSWP5 BGN Curncy"]) / (100 + dataset["CHSWC5 BGN Curncy"])) - 1
    dataset["Breakeven_Stdev"] = dataset["Breakeven_5"].rolling(center=False,window=30).std()
    for column in ["RIAMPDU7 Index", "CHSWP5 BGN Curncy", "CHSWC5 BGN Curncy", "Breakeven_5"]:
        dataset.drop(column, axis=1, inplace=True)
    dataset=dataset.dropna(axis=0)

    return dataset

def fetch_clf_serie(LocalTerminal, inflation_forwards):
    '''
    Completa el dataframe de forwards de inflacion con la info de Bloomberg.
    '''
    # Nececitamos un vector de uf, para esto nos separamos en 3 casos
    # uf spot, la ultima uf conocida y la uf transada en los forwards
    
    # Empezamos con la spot
    clf_spot = inflation_forwards.loc["spot"]
    spot_date = fs.convert_string_to_date(fs.get_ndays_from_today(0))
    spot_date = pd.Timestamp(spot_date)
    clf_spot_ticker = clf_spot["ticker"] 
    clf_spot_data = LocalTerminal.get_historical(clf_spot_ticker ,
                                                 "PX_LAST",
                                                  start=spot_date,
                                                  end=spot_date)
    clf_spot_data = clf_spot_data.as_frame()
    clf_spot = clf_spot_data[clf_spot_ticker]["PX_LAST"]
    clf_spot = float(clf_spot)
    # Ahora obtenemos la ultima uf conocida
    clf_eom = inflation_forwards.loc["eom"]
    clf_eom_ticker = clf_eom["ticker"]
    clf_eom_data = LocalTerminal.get_reference_data(clf_eom_ticker, ["PX_LAST", "LAST_UPDATE_DT"])
    clf_eom_data = clf_eom_data.as_frame()
    # Aprovechamos de sacar la fecha de esta uf  
    settlement_eom = clf_eom_data.loc[clf_eom_ticker]["LAST_UPDATE_DT"]   
    clf_eom = clf_eom_data.loc[clf_eom_ticker]["PX_LAST"]

    # Finalmente tomamos las expectativas del mercado
    inflation_forwards = inflation_forwards[(inflation_forwards.index != "spot")&(inflation_forwards.index != "eom")]
    inflation_forwards.set_index(["ticker"], inplace=True)
    inflation_forwards_data = LocalTerminal.get_reference_data(inflation_forwards.index, ["SETTLE_DT", "PX_LAST"])
    inflation_forwards_data = inflation_forwards_data.as_frame()

    inflation_forwards["settlement"] = inflation_forwards_data["SETTLE_DT"]
    inflation_forwards["clf"] = inflation_forwards_data["PX_LAST"]
    
    # Ya con los valores, procedemos a construir un vector de uf
    # primero que nada necesitamos las fechas en que son validas
    # las ufs y ponerlas en una lista

    # la uf actual es valida para hoy
    settlement_spot = spot_date

    # la ultima uf conocida ya la teniamos (igualdad por buena practica)
    settlement_eom = settlement_eom

    # Ahora armamos nuestro vector de uf futuro

    clf_serie = inflation_forwards.set_index(["settlement"])
    clf_serie.loc[settlement_spot] = clf_spot
    clf_serie.loc[settlement_eom] = clf_eom
    clf_serie = clf_serie.sort_index()

    # fs.print_full(clf_serie)
    # exit()

    

    last_forward_date = clf_serie.index[-1]
    clf_dates = fs.get_dates_between(spot_date, last_forward_date)
    clf_serie = clf_serie.reindex(clf_dates)
    clf_serie = clf_serie.interpolate()
    clf_serie = clf_serie["clf"]

    return clf_serie


def fetch_floating_rate(LocalTerminal, floating_rate_ticker):
    '''
    Descarga el indice camara de bloomberg y calcula la tasa anualizada spot.
    '''
    floating_rate = float(LocalTerminal.get_reference_data(floating_rate_ticker, "PX_LAST").as_frame()["PX_LAST"])
    floating_rate = floating_rate / 100
    return floating_rate


def fetch_cpi(LocalTerminal, cpi_ticker):
    '''
    Descarga el icp, entonces te fijas.
    '''
    spot_date = fs.convert_string_to_date(fs.get_ndays_from_today(0))
    spot_date = pd.Timestamp(spot_date)
    yesterday_date = spot_date - dt.timedelta(1)
    yoy_date = yesterday_date - dt.timedelta(730)
    cpi_data = LocalTerminal.get_historical(cpi_ticker ,
                                            "PX_LAST",
                                             start=yoy_date,
                                             end=yesterday_date)
    cpi_data = cpi_data.as_frame()
    cpi_serie = cpi_data[cpi_ticker]["PX_LAST"]

    # Ahora armamos una serie diaria
    start_date = cpi_serie.index[0]
    end_date = cpi_serie.index[-1]
    cpi_dates = fs.get_dates_between(start_date, end_date)
    cpi_serie = cpi_serie.reindex(cpi_dates)
    cpi_serie = cpi_serie.interpolate()

    return cpi_serie


def compute_breakevens(curve_instruments_clp, curve_instruments_clf):
    '''
    Construye los breakevens
    '''
    breakevens_clp = curve_instruments_clp[curve_instruments_clp["breakeven"].notnull()]
    breakevens_clf = curve_instruments_clf[curve_instruments_clf["breakeven"].notnull()]
    breakevens_clp.set_index(["breakeven"], inplace=True)
    breakevens_clf.set_index(["breakeven"], inplace=True)
    breakevens = breakevens_clp[["local_id", "yield", "expected", "dove", "central", "hawk"]]
    breakevens["local_id_clf"] = breakevens_clf["local_id"]
    breakevens[["yield", "expected", "dove", "central", "hawk"]] = ((1.0 + breakevens_clp[["yield", "expected", "dove", "central", "hawk"]])/(1.0 + breakevens_clf[["yield", "expected", "dove", "central", "hawk"]])) - 1.0
    breakevens["local_id_clf"] =  breakevens["local_id_clf"].apply(lambda x: x[:-7] + x[6:])
    breakevens["local_id"] =  breakevens["local_id"].apply(lambda x: x[:-7] + x[6:])
    breakevens["local_id"] =  breakevens["local_id"] + "/" + breakevens["local_id_clf"]
    breakevens.rename(columns={"yield": "market"}, inplace=True)
    breakevens = breakevens.drop("local_id_clf", 1)
    breakevens["delta"] = breakevens["market"] - breakevens["expected"] 
    breakevens = breakevens[["local_id", "expected", "market", "delta", "dove", "central", "hawk"]]

    return breakevens

def compute_display_matrix(curve_instruments):
    '''
    Construye un dataframe para mostrar los bonos en el reporte
    '''
    display_matrix = curve_instruments.reset_index()
    display_matrix.set_index(["maturity_date"], inplace=True)
    display_matrix = display_matrix[["local_id", "expected", "yield", "delta", "dove", "central", "hawk",
                                     "swap_equivalent", "swap_spread", "yield_buffer_1M", "yield_buffer_3M" ,
                                     "duration", "days_to_maturity", "instrument", "breakeven"]]
    display_matrix = display_matrix.fillna(0.0)
    display_matrix = display_matrix.replace(np.inf, 0.0)
    display_matrix = display_matrix.replace(-1*np.inf, 0.0)

    return display_matrix


def print_monitor(display_matrix_clp, display_matrix_clf, path_scenarios_display, term_premia_cash, term_premia_swap, path_distribution,
                  path_simulation_scenarios_display, swap_simulation_curves, slope_simulation, market_zero_curve,
                  funding_rate, yoy_inflation, swap_implied_path, tpm_neutral_lower, tpm_neutral_upper, breakevens,
                  swap_cum_path, zero_cum_path, implied_paths_rpm, breakeven_model_2y, breakeven_model_5y, fras_cash_clp,
                  fras_cash_clf, fra_simulation, term_premia_model, expected_spread_diff, expected_returns, historical_term_premia_5y_cash,
                  historical_term_premia_10y_cash, historical_term_premia_20y_cash, historical_term_premia_5y_swap,
                  historical_term_premia_10y_swap, historical_term_premia_20y_swap, historical_breakeven_cash_spot,
                  historical_breakeven_cash_1y, historical_breakeven_cash_3y, historical_breakeven_cash_5y, historical_breakeven_cash_10y, historical_breakeven_cash_20y,
                  cary_clp_90, cary_clp_180, cary_clp_360, cary_clf_90, cary_clf_180, cary_clf_360, fras_cash_bei):
    '''
    Construye el display para el monitor
    '''
    wb = fs.open_workbook("outputs.xlsx", True, True)
    fs.clear_sheet_xl(wb, "instruments_clp")
    fs.clear_sheet_xl(wb, "instruments_clf")
    fs.clear_sheet_xl(wb, "paths")
    fs.clear_sheet_xl(wb, "term_premia_cash")
    fs.clear_sheet_xl(wb, "term_premia_swap")
    fs.clear_sheet_xl(wb, "path_distribution")
    fs.clear_sheet_xl(wb, "paths_simulation")
    fs.clear_sheet_xl(wb, "swap_simulation_curves")
    fs.clear_sheet_xl(wb, "slope_simulation")
    fs.clear_sheet_xl(wb, "market_zero_curve")
    fs.clear_sheet_xl(wb, "funding_rate")
    fs.clear_sheet_xl(wb, "yoy_inflation")
    fs.clear_sheet_xl(wb, "swap_implied_path")
    fs.clear_sheet_xl(wb, "implied_path_rpm")
    fs.clear_sheet_xl(wb, "tpm_neutral")
    fs.clear_sheet_xl(wb, "breakevens")
    fs.clear_sheet_xl(wb, "swap_cum_path")
    fs.clear_sheet_xl(wb, "zero_cum_path")
    fs.clear_sheet_xl(wb, "breakeven_model_2y")
    fs.clear_sheet_xl(wb, "breakeven_model_5y")
    fs.clear_sheet_xl(wb, "fras_cash_clp")
    fs.clear_sheet_xl(wb, "fras_cash_clf")
    fs.clear_sheet_xl(wb, "fra_simulation")
    fs.clear_sheet_xl(wb, "term_premia_model")
    fs.clear_sheet_xl(wb, "expected_spread_diff")
    fs.clear_sheet_xl(wb, "expected_returns")
    fs.clear_sheet_xl(wb, "historical_term_premia_5y_cash")
    fs.clear_sheet_xl(wb, "historical_term_premia_10y_cash")
    fs.clear_sheet_xl(wb, "historical_term_premia_20y_cash")
    fs.clear_sheet_xl(wb, "historical_term_premia_5y_swap")
    fs.clear_sheet_xl(wb, "historical_term_premia_10y_swap")
    fs.clear_sheet_xl(wb, "historical_term_premia_20y_swap")
    fs.clear_sheet_xl(wb, "historical_breakeven_cash_spot")
    fs.clear_sheet_xl(wb, "historical_breakeven_cash_1y")
    fs.clear_sheet_xl(wb, "historical_breakeven_cash_3y")
    fs.clear_sheet_xl(wb, "historical_breakeven_cash_5y")
    fs.clear_sheet_xl(wb, "historical_breakeven_cash_10y")
    fs.clear_sheet_xl(wb, "historical_breakeven_cash_20y")
    fs.clear_sheet_xl(wb, "cary_clp_90")
    fs.clear_sheet_xl(wb, "cary_clp_180")
    fs.clear_sheet_xl(wb, "cary_clp_360")
    fs.clear_sheet_xl(wb, "cary_clf_90")
    fs.clear_sheet_xl(wb, "cary_clf_180")
    fs.clear_sheet_xl(wb, "cary_clf_360")
    fs.clear_sheet_xl(wb, "fras_cash_bei")
    fs.paste_val_xl(wb, "instruments_clp", 1, 1, display_matrix_clp)
    fs.paste_val_xl(wb, "instruments_clf", 1, 1, display_matrix_clf)
    fs.paste_val_xl(wb, "paths", 1, 1, path_scenarios_display)
    fs.paste_val_xl(wb, "term_premia_cash", 1, 1, term_premia_cash)
    fs.paste_val_xl(wb, "term_premia_swap", 1, 1, term_premia_swap)
    fs.paste_val_xl(wb, "path_distribution", 1, 1, path_distribution)
    fs.paste_val_xl(wb, "paths_simulation", 1, 1, path_simulation_scenarios_display)
    fs.paste_val_xl(wb, "slope_simulation", 1, 1, slope_simulation)
    fs.paste_val_xl(wb, "swap_simulation_curves", 1, 1, swap_simulation_curves)
    fs.paste_val_xl(wb, "market_zero_curve", 1, 1, market_zero_curve)
    fs.paste_val_xl(wb, "funding_rate", 1, 1, funding_rate)
    fs.paste_val_xl(wb, "yoy_inflation", 1, 1, yoy_inflation)
    fs.paste_val_xl(wb, "swap_implied_path", 1, 1, swap_implied_path)
    fs.paste_val_xl(wb, "implied_path_rpm", 1, 1, implied_paths_rpm)
    fs.paste_val_xl(wb, "tpm_neutral", 1, 1, tpm_neutral_lower)
    fs.paste_val_xl(wb, "tpm_neutral", 2, 1, tpm_neutral_upper)
    fs.paste_val_xl(wb, "breakevens", 1, 1, breakevens)
    fs.paste_val_xl(wb, "swap_cum_path", 1, 1, swap_cum_path)
    fs.paste_val_xl(wb, "zero_cum_path", 1, 1, zero_cum_path)
    fs.paste_val_xl(wb, "breakeven_model_2y", 1, 1, breakeven_model_2y)
    fs.paste_val_xl(wb, "breakeven_model_5y", 1, 1, breakeven_model_5y)
    fs.paste_val_xl(wb, "fras_cash_clp", 1, 1, fras_cash_clp)
    fs.paste_val_xl(wb, "fras_cash_clf", 1, 1, fras_cash_clf)
    fs.paste_val_xl(wb, "fra_simulation", 1, 1, fra_simulation)
    fs.paste_val_xl(wb, "term_premia_model", 1, 1, term_premia_model)
    fs.paste_val_xl(wb, "expected_spread_diff", 1, 1, expected_spread_diff)
    fs.paste_val_xl(wb, "expected_returns", 1, 1, expected_returns)
    fs.paste_val_xl(wb, "historical_term_premia_5y_cash", 1, 1, historical_term_premia_5y_cash)
    fs.paste_val_xl(wb, "historical_term_premia_10y_cash", 1, 1, historical_term_premia_10y_cash)
    fs.paste_val_xl(wb, "historical_term_premia_20y_cash", 1, 1, historical_term_premia_20y_cash)
    fs.paste_val_xl(wb, "historical_term_premia_5y_swap", 1, 1, historical_term_premia_5y_swap)
    fs.paste_val_xl(wb, "historical_term_premia_10y_swap", 1, 1, historical_term_premia_10y_swap)
    fs.paste_val_xl(wb, "historical_term_premia_20y_swap", 1, 1, historical_term_premia_20y_swap)
    fs.paste_val_xl(wb, "historical_breakeven_cash_spot", 1, 1, historical_breakeven_cash_spot)
    fs.paste_val_xl(wb, "historical_breakeven_cash_1y", 1, 1, historical_breakeven_cash_1y)
    fs.paste_val_xl(wb, "historical_breakeven_cash_3y", 1, 1, historical_breakeven_cash_3y)
    fs.paste_val_xl(wb, "historical_breakeven_cash_5y", 1, 1, historical_breakeven_cash_5y)
    fs.paste_val_xl(wb, "historical_breakeven_cash_10y", 1, 1, historical_breakeven_cash_10y)
    fs.paste_val_xl(wb, "historical_breakeven_cash_20y", 1, 1, historical_breakeven_cash_20y)
    fs.paste_val_xl(wb, "cary_clp_90", 1, 1, cary_clp_90)
    fs.paste_val_xl(wb, "cary_clp_180", 1, 1, cary_clp_180)
    fs.paste_val_xl(wb, "cary_clp_360", 1, 1, cary_clp_360)
    fs.paste_val_xl(wb, "cary_clf_90", 1, 1, cary_clf_90)
    fs.paste_val_xl(wb, "cary_clf_180", 1, 1, cary_clf_180)
    fs.paste_val_xl(wb, "cary_clf_360", 1, 1, cary_clf_360)
    fs.paste_val_xl(wb, "fras_cash_bei", 1, 1, fras_cash_bei)


    path_pdf = fs.get_self_path()
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p1")-1, ".", path_pdf + "1.pdf")
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p2")-1, ".", path_pdf+ "2.pdf")
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p3")-1, ".", path_pdf+ "3.pdf")
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p4")-1, ".", path_pdf+ "4.pdf")
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p5")-1, ".", path_pdf+ "5.pdf")
    fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p6")-1, ".", path_pdf+ "6.pdf")
    #fs.export_sheet_pdf(fs.get_sheet_index(wb, "display_p7")-1, ".", path_pdf+ "7.pdf")
    name = "Chile_Rates_Outlook_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    fs.merge_pdf(".", name)
    fs.save_workbook(wb)
    fs.close_excel(wb)
    src = name
    dst = "L:\\Rates & FX\\fsb\\reporting\\rates_outlook_backup\\" + name
    fs.copy_file(src, dst)
    fs.delete_file(path_pdf + "1.pdf")
    fs.delete_file(path_pdf+ "2.pdf")
    fs.delete_file(path_pdf+ "3.pdf")
    fs.delete_file(path_pdf+ "4.pdf")
    fs.delete_file(path_pdf+ "5.pdf")
    fs.delete_file(path_pdf+ "6.pdf")
    #fs.delete_file(path_pdf+ "7.pdf")
    fs.delete_file(path_pdf+ name)
    fs.open_file(dst)


# Descargamos los inputs del excel, entonces te fijas chicos
print("fetching manual inputs...")
path_scenarios, path_distribution, term_premia_cash, term_premia_swap, curve_instruments_clp, curve_instruments_clf, swap_instruments_clp, swap_instruments_clf, inflation_forwards, funding_rate, tpm_base, bonds_base, path_scenarios_display, path_simulation_scenarios, path_simulation_scenarios_display, floating_rate_ticker, cpi_ticker, rpm_dates, tpm_neutral_lower, tpm_neutral_upper, breakeven_params, train_breakeven_model = fetch_inputs()

# Descargamos los datos de Bloomberg
print("fetching bloomberg data...")
curve_instruments_clp, curve_instruments_clf, cash_flow_tables_clp, cash_flow_tables_clf, swap_instruments_clp, swap_instruments_clf, clf_serie, floating_rate, cpi_serie, clf_spot_dataset_training, clf_fwd_dataset_training, clf_spot_dataset_forecast, clf_fwd_dataset_forecast, term_premia_dataset = fetch_bbl_data(curve_instruments_clp, curve_instruments_clf, swap_instruments_clp, swap_instruments_clf, inflation_forwards, floating_rate_ticker, cpi_ticker, train_breakeven_model)

# print("computing sinteticos swaps")
#sinteticos_swaps = ct.compute_sinteticos_swaps(fs.get_ndays_from_today(0), path_scenarios, swap_instruments_clp)

# Descargamos las curvas cero historics de riskamerica
print("fetching historical zero curves...")
historical_zero_rates_cash_clp = fetch_historical_zero_rates("Gob CERO Pesos" ,1000)
historical_zero_rates_swap_clp = fetch_historical_zero_rates("Swap CLP/Camara" ,1000)
historical_zero_rates_cash_clf = fetch_historical_zero_rates("Gob CERO UF" ,1000)

print("computing historical forward breakevens serie...")
historical_breakeven_cash_spot = ct.compute_historical_breakeven_forward(historical_zero_rates_cash_clp, historical_zero_rates_cash_clf, 0)
historical_breakeven_cash_1y = ct.compute_historical_breakeven_forward(historical_zero_rates_cash_clp, historical_zero_rates_cash_clf, 1)
historical_breakeven_cash_3y = ct.compute_historical_breakeven_forward(historical_zero_rates_cash_clp, historical_zero_rates_cash_clf, 3)
historical_breakeven_cash_5y = ct.compute_historical_breakeven_forward(historical_zero_rates_cash_clp, historical_zero_rates_cash_clf, 5)
historical_breakeven_cash_10y = ct.compute_historical_breakeven_forward(historical_zero_rates_cash_clp, historical_zero_rates_cash_clf, 10)
historical_breakeven_cash_20y = ct.compute_historical_breakeven_forward(historical_zero_rates_cash_clp, historical_zero_rates_cash_clf, 20)

# Descargamos las tasas cero historicas y calculamos las series de term premia historicas de los bonos
print("computing historical term premia bonds serie...")
historical_term_premia_5y_cash = ct.compute_historical_term_premia(historical_zero_rates_cash_clp, 5, tpm_neutral_lower, tpm_neutral_upper)
historical_term_premia_10y_cash = ct.compute_historical_term_premia(historical_zero_rates_cash_clp, 10, tpm_neutral_lower, tpm_neutral_upper)
historical_term_premia_20y_cash = ct.compute_historical_term_premia(historical_zero_rates_cash_clp, 20, tpm_neutral_lower, tpm_neutral_upper)

# Descargamos las tasas cero historicas y calculamos las series de term premia historicas de la swap
print("computing historical term premia swaps serie...")
historical_term_premia_5y_swap = ct.compute_historical_term_premia(historical_zero_rates_swap_clp, 5, tpm_neutral_lower, tpm_neutral_upper)
historical_term_premia_10y_swap = ct.compute_historical_term_premia(historical_zero_rates_swap_clp, 10, tpm_neutral_lower, tpm_neutral_upper)
historical_term_premia_20y_swap = ct.compute_historical_term_premia(historical_zero_rates_swap_clp, 20, tpm_neutral_lower, tpm_neutral_upper)

# Corremos el modelo de term premia
print("computing term premia model...")
term_premia_model = tp.compute_term_premia_model(term_premia_dataset)
# Corremos el modelo de breakeven
print("computing breakeven model...")
breakeven_model_2y = bm.compute_breakeven_model(breakeven_params, clf_spot_dataset_training, clf_fwd_dataset_training, clf_spot_dataset_forecast, clf_fwd_dataset_forecast, 2)
breakeven_model_5y = bm.compute_breakeven_model(breakeven_params, clf_spot_dataset_training, clf_fwd_dataset_training, clf_spot_dataset_forecast, clf_fwd_dataset_forecast, 5)

print("computing yoy inflation serie...")
# Calculamos los paths de inflacion yoy
yoy_inflation = ct.compute_inflation_paths(clf_serie, cpi_serie)

# Descargamos las curvas cero de riskamerica desde la base de datos
print("fetching zero market curves...")
market_zero_curve_clp = fetch_market_zero_curve(inflation_linked=False)
market_zero_curve_clf = fetch_market_zero_curve(inflation_linked=True)

# Calculamos carry and roll 
print("computing bonds carry and roll...")
cary_clp_90 = ct.compute_carry_roll(market_zero_curve_clp, 90)
cary_clp_180 = ct.compute_carry_roll(market_zero_curve_clp, 180)
cary_clp_360 = ct.compute_carry_roll(market_zero_curve_clp, 360)
cary_clf_90 = ct.compute_carry_roll(market_zero_curve_clf, 90)
cary_clf_180 = ct.compute_carry_roll(market_zero_curve_clf, 180)
cary_clf_360 = ct.compute_carry_roll(market_zero_curve_clf, 360)

# Calculamos el path de tpm esperado en la curva cash
print("computing expected monetary policy path...")
path_scenarios = ct.compute_expected_path(path_scenarios, path_distribution)

# Le agregamos el term premia a los distintos paths
print("compounding term premia...")
path_scenarios = ct.sum_term_premia(path_scenarios, term_premia_cash)

# Le agregamos el term premia a los distintos paths de la simulacion
print("compounding term premia simulation...")
path_simulation_scenarios = ct.sum_term_premia(path_simulation_scenarios, term_premia_swap)

# Obtenemos las curvas cero    
print("computing zero cash curves...")
zero_curves_clp = ct.compute_spot_curves(path_scenarios, "compounded", tpm_base, bonds_base)


print("computing expected inflation...")
path_distribution = ct.compute_expected_inflation(path_distribution)

print("computing inflation curves...")
zero_curves_clf = ct.compute_zero_curves_clf(zero_curves_clp, clf_serie, path_distribution)

# Obtenemos la ultiam fecha necesaria para valorizar un bono
long_end_date = zero_curves_clp.index[-1]

# Calculamos las curvas zero swap equivalent
print("computing zero swap curves...")
zero_swap_curve_clp, zero_swap_curve_clf = ct.compute_zero_swap_curves(swap_instruments_clp, swap_instruments_clf, long_end_date, "compounded", bonds_base, tpm_base)

# Calculamos los retornos esperados de los distintos buckets de activos
print("computing expected spread compression and returns...")
expected_returns, expected_spread_diff = sp.compute_df_spread(days=90,
                                                              params=['tipo', 'moneda', 'Bucket_Duration', 'rating'],
                                                              clp_mkt=market_zero_curve_clp,
                                                              clf_mkt=market_zero_curve_clf,
                                                              clp_exp=zero_curves_clp,
                                                              clf_exp=zero_curves_clf,
                                                              swap_clp=zero_swap_curve_clp,
                                                              swap_clf=zero_swap_curve_clf,
                                                              df_inflacion=clf_serie)

# Calculamos el path de tpm implicito en la curva swap

print("computing swap curve implied path...")
swap_implied_path = ct.compute_swap_implied_path(rpm_dates, path_scenarios_display, swap_instruments_clp, tpm_base, long_end_date, "linear", False)
swap_implied_path_rpm = ct.compute_swap_implied_path_by_rpm(swap_implied_path, rpm_dates)
 
swap_cum_path = ct.get_cum_path(swap_implied_path_rpm)


print("computing zero curve implied path...")
market_zero_curve_clp = ct.compute_zero_implied_tpm(market_zero_curve_clp)


print("computing zero curve implied term premia...")
market_zero_curve_clp = ct.compute_implied_term_premia(market_zero_curve_clp, tpm_neutral_lower, tpm_neutral_upper)

# Calculamos las tasas consolidadas
print("computing consolitaded tpm...")
zero_implied_path_rpm = ct.compute_zero_implied_path_by_rpm(market_zero_curve_clp, rpm_dates, floating_rate)
zero_cum_path = ct.get_cum_path(zero_implied_path_rpm)

implied_paths_rpm = ct.join_zero_swap_paths_by_rpm(swap_implied_path_rpm, zero_implied_path_rpm)

# Calculamos el valuation de los instrumentos nominales
print("computing nominal valuations...")
curve_instruments_clp = ct.compute_valuation(curve_instruments_clp, cash_flow_tables_clp, zero_curves_clp, zero_swap_curve_clp)


# Calculamos el valuation de los instrumentos en uf
print("computing inflation linked valuations...")
curve_instruments_clf = ct.compute_valuation(curve_instruments_clf, cash_flow_tables_clf, zero_curves_clf, zero_swap_curve_clf)



# Calculamos el colchon de tasa de los instrumentos nominales
print("computing nominal yield buffers...")
curve_instruments_clp = ct.compute_yield_buffer(curve_instruments_clp, funding_rate)

# Calculamos el colchon de tasa de los instrumentos nominales
print("computing inflation-linked yield buffers...")
curve_instruments_clf = ct.compute_yield_buffer(curve_instruments_clf, funding_rate, clf_serie)

print("computing swap spreads...")
# Calculamos los swap spreads
curve_instruments_clp = ct.compute_swap_spread(curve_instruments_clp)
curve_instruments_clf = ct.compute_swap_spread(curve_instruments_clf)

print("computing market difference...")
# Calculamos los deltas
curve_instruments_clp = ct.compute_delta_value(curve_instruments_clp)
curve_instruments_clf = ct.compute_delta_value(curve_instruments_clf)


print("computing inflation breakevens...")
# Calculamos los breakevens de inflacion
breakevens = compute_breakevens(curve_instruments_clp, curve_instruments_clf)

print("computing swap simulation curves...")
# Calculamos las curvas swaps simuladas

swap_simulation_curves = ct.compute_swap_simulation_curves(path_simulation_scenarios, "linear", tpm_base, swap_instruments_clp)

print("computing simulation slopes...")
#Calculamos las inclinaciones de las curvas swap simuladas
slope_simulation = ct.compute_simulation(swap_simulation_curves, floating_rate=floating_rate, slope=True)

print("computing simulation slopes market difference...")
# Calculamos las diferencias de inclinacion entre los escenarios y el mercado
slope_simulation = ct.compute_simulation_delta(slope_simulation)

print("computing simulation fras...")
#Calculamos las inclinaciones de las curvas swap simuladas
fra_simulation = ct.compute_simulation(swap_simulation_curves)

print("computing simulation fras market difference...")
# Calculamos las diferencias de inclinacion entre los escenarios y el mercado
fra_simulation = ct.compute_simulation_delta(fra_simulation)

# Calculamos el carry y delta de entrar en trade de nivel de las simulaciones
swap_simulation_curves = ct.compute_simulation_carry(swap_simulation_curves, floating_rate)
swap_simulation_curves = ct.compute_simulation_delta(swap_simulation_curves)

print("computing display...")
# Armamos dataframes para el display
display_matrix_clp = compute_display_matrix(curve_instruments_clp)
display_matrix_clf = compute_display_matrix(curve_instruments_clf)

print("computing cash fras...")
# Calculamos las matrices de fra para los bonos
fras_cash_clp = ct.compute_cash_fras(curve_instruments_clp)
fras_cash_clf = ct.compute_cash_fras(curve_instruments_clf)
fras_cash_bei = ct.compute_cash_fra_bei(fras_cash_clp, fras_cash_clf)



print("printing monitor...")
# Imprimimos el monitor en excel

print_monitor(display_matrix_clp,
              display_matrix_clf,
              path_scenarios_display,
              term_premia_cash,
              term_premia_swap,
              path_distribution,
              path_simulation_scenarios_display,
              swap_simulation_curves,
              slope_simulation,
              market_zero_curve_clp,
              funding_rate,
              yoy_inflation,
              swap_implied_path,
              tpm_neutral_lower,
              tpm_neutral_upper,
              breakevens,
              swap_cum_path,
              zero_cum_path,
              implied_paths_rpm,
              breakeven_model_2y,
              breakeven_model_5y,
              fras_cash_clp,
              fras_cash_clf,
              fra_simulation,
              term_premia_model,
              expected_spread_diff,
              expected_returns,
              historical_term_premia_5y_cash,
              historical_term_premia_10y_cash,
              historical_term_premia_20y_cash,
              historical_term_premia_5y_swap,
              historical_term_premia_10y_swap,
              historical_term_premia_20y_swap,
              historical_breakeven_cash_spot,
              historical_breakeven_cash_1y,
              historical_breakeven_cash_3y,
              historical_breakeven_cash_5y,
              historical_breakeven_cash_10y,
              historical_breakeven_cash_20y,
              cary_clp_90,
              cary_clp_180,
              cary_clp_360,
              cary_clf_90,
              cary_clf_180,
              cary_clf_360,
              fras_cash_bei
              )
