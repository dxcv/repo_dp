"""
Created on Wed Mar 08 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
sys.path.insert(1, '../risk_library/')
import risk as rk
import pandas as pd
import numpy as np

def get_fx(spot_date, fx_id):
    '''
    Retorna el retorno entre dos fechas para una moneda, dado el id del fx.
    '''
    path = ".\\querys_portfolio_simulator\\" + fx_id + ".sql"
    query = fs.read_file(path=path).replace("autodate", spot_date)
    fx = fs.get_val_sql_user(server="Puyehue",
                             database="MesaInversiones",
                             username="usrConsultaComercial",
                             password="Comercial1w",
                             query=query)
    return fx


def print_report_pdf(portfolio, fund, fund_date):
    '''
    Exporta el reporte a un pdf consolidado.
    '''
    # Abrimos el workbook con el template del informe
    wb = fs.open_workbook(path="..\\investment_report\\InvestmentReport.xlsx", screen_updating=True, visible=False)
    # Borramos la informacion anterior
    fs.clear_table_xl(wb=wb, sheet="Historical", row=1, column=1)
    fs.clear_sheet_xl(wb=wb, sheet="Dataset")
    fs.paste_val_xl(wb=wb, sheet="Dataset", row=1, column=1, value=portfolio)
    fs.paste_val_xl(wb=wb, sheet="Historical", row=2, column=8, value=fund_date)
    # Imprimimos cael reporte para el fondo en cuestion
    fund_id = fund["codigo_fdo"]
    display_portfolio = fund["display_portfolio"]
    print("printing -> " + fund_id)
    fs.paste_val_xl(wb=wb, sheet=display_portfolio, row=11, column=4, value=fund_id)
    path_pdf = fs.get_self_path() + "output_portfolio_simulator\\" + display_portfolio + "_" + fund_id + ".pdf"
    fs.export_sheet_pdf(sheet_index=fs.get_sheet_index(wb, display_portfolio)-1, path_in=".", path_out=path_pdf)
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)


def get_fake_positions():
    '''
    Extrae los instrumentos a simular desde el doucmento JSON.
    '''
    positions_raw = fs.read_file(path=".\\positions.json")
    positions = fs.convert_json_to_dict(positions_raw)
    instruments = positions["instruments"]
    fund_id = positions["fund_id"]
    return fund_id, instruments


def get_portfolio_simulation(fund_portfolio, instruments, fund_date, usd, clf, eur, mxn, brl):
    '''
    Agrega al portfolio los nuevos instrumentos mas la fluctuacion de caja.
    '''
    # Fijamos las columnas del portfolio obtenido de la bdd
    instrument_columns = ["fecha", "codigo_fdo", "codigo_emi", "codigo_ins", "tipo_instrumento",
                          "moneda", "monto", "nominal", "cantidad", "precio", "duration", "tasa",
                          "riesgo", "nombre_emisor", "nombre_instrumento", "fec_vtco",
                          "pais_emisor", "Index_Id", "sector", "riesgo_internacional"]
    total_cost = 0.0
    # Por cada instrumento actualizamos el portfolio
    for instrument in instruments:
        codigo_ins = instrument["codigo_ins"]
        instruments_list = fund_portfolio["codigo_ins"].tolist()
        # Caso en que el instrumento ya existia en cartera
        if codigo_ins in instruments_list:
        	fund_portfolio, monto = update_portfolio(fund_portfolio, instrument, fund_date, usd, clf, eur, mxn, brl)
        # Caso cuando es un instrumento nuevo
        else:
            instrument_df, monto = get_instrument_df(instrument, instrument_columns, fund_date, usd, clf, eur, mxn, brl)
            # Aca tenemos que agregar el instrumento nuevo al portfolio
            fund_portfolio = pd.concat([fund_portfolio, instrument_df], ignore_index=True)
        total_cost += monto
    # Finalmente agregamos la caja con la misma notacion que en el mapping
    cashflow_df = get_cashflow_df(fund_id=fund_id,
                                  fund_date=fund_date,
                                  total_cost=total_cost,
                                  instrument_columns=instrument_columns)
    fund_portfolio = pd.concat([fund_portfolio, cashflow_df], ignore_index=True)
    return fund_portfolio


def update_portfolio(fund_portfolio, instrument, fund_date, usd, clf, eur, mxn, brl):
    '''
    Actualiza una posicion del portfolio.
    '''
    # Obtenemos los datos del instrumento a actualizar
    cantidad_new = instrument["cantidad"]
    cantidad_start = fund_portfolio[fund_portfolio["codigo_ins"] == instrument["codigo_ins"]]["cantidad"].iloc[0]
    tipo_instrumento = fund_portfolio[fund_portfolio["codigo_ins"] == instrument["codigo_ins"]]["tipo_instrumento"].iloc[0]
    moneda = fund_portfolio[fund_portfolio["codigo_ins"] == instrument["codigo_ins"]]["moneda"].iloc[0]
    monto_start = fund_portfolio[fund_portfolio["codigo_ins"] == instrument["codigo_ins"]]["monto"].iloc[0]
    cantidad = cantidad_start + cantidad_new
    precio = instrument["precio"]
    # Los instrumentos de renta fija tienen su precio en base 100,
    # por lo que debemos normalizarla
    if tipo_instrumento != "Accion":
        precio = precio/100
    # Calculamos el monto nuevo en base a los distintos tipos de cambio
    if moneda == "$":
        monto =  cantidad * precio
    elif moneda == "UF":
        monto = clf * cantidad * precio
    elif moneda == "US$":
        monto = usd * cantidad * precio
    elif moneda == "EU":
        monto = eur * cantidad * precio
    elif moneda == "MX":
        monto = mxn * cantidad * precio
    elif moneda == "REA":
        monto = brl * cantidad * precio
    # Agregamos los nuevos valores al portfolio
    fund_portfolio.loc[fund_portfolio["codigo_ins"] == instrument["codigo_ins"],"monto"] = monto
    fund_portfolio.loc[fund_portfolio["codigo_ins"] == instrument["codigo_ins"], "cantidad"] = cantidad
    fund_portfolio.loc[fund_portfolio["codigo_ins"] == instrument["codigo_ins"], "precio"] = precio
    monto_flow = monto - monto_start
    return fund_portfolio, monto_flow



def get_instrument_df(instrument, instrument_columns, fund_date, usd, clf, eur, mxn, brl):
    '''
    Retorna el instrumento nuevo en un dataframe.
    '''
    # Obtenemos los datos del intrumento nuevo
    fecha = fund_date
    codigo_fdo = fund_id
    codigo_emi = instrument["codigo_emi"]
    codigo_ins = instrument["codigo_ins"]
    tipo_instrumento = instrument["tipo_instrumento"]
    moneda = instrument["moneda"]
    cantidad = instrument["cantidad"]
    nominal = cantidad
    precio = instrument["precio"]
    # Los instrumentos de renta fija tienen su precio en base 100,
    # por lo que debemos normalizarla
    if tipo_instrumento != "Accion":
    	precio = precio/100
    tipo_instrumento = instrument["tipo_instrumento"]
    # Calculamos el monto nuevo en base a los distintos tipos de cambio
    if moneda == "$":
        monto =  cantidad * precio
    elif moneda == "UF":
        monto = clf * cantidad * precio
    elif moneda == "US$":
        monto = usd * cantidad * precio
    elif moneda == "EU":
        monto = eur * cantidad * precio
    elif moneda == "MX":
        monto = mxn * cantidad * precio
    elif moneda == "REA":
        monto = brl * cantidad * precio
    duration = instrument["duration"]
    tasa = instrument["tasa"] / 100
    riesgo = instrument["riesgo"]
    nombre_emisor = codigo_emi
    nombre_instrumento = codigo_ins
    fec_vcto = instrument["fec_vcto"]
    pais_emisor = instrument["pais_emisor"]
    index_id = instrument["Index_Id"]
    sector = instrument["sector"]
    riesgo_internacional = instrument["riesgo_internacional"]
    instrument_array = [[fecha, codigo_fdo, codigo_emi, codigo_ins,
                         tipo_instrumento, moneda, monto, nominal,
                         cantidad, precio, duration, tasa, riesgo,
                         nombre_emisor, nombre_instrumento, fec_vcto,
                         pais_emisor, index_id, sector, riesgo_internacional]]
    # Le damos formato de dataframe y calculamos el monto total
    instrument_df = pd.DataFrame(data=instrument_array, columns=instrument_columns)
    monto = instrument_df["monto"].iloc[0]
    return instrument_df, monto


def get_cashflow_df(fund_id, fund_date, total_cost, instrument_columns):
    '''
    Retorna flujo de caja obtenido tras la simulacion en un dataframe.
    '''
    fecha = fec_vcto = fund_date
    codigo_fdo = fund_id
    codigo_emi = "CAJA " + fund_id
    codigo_ins = "CAJA $ FAKE"
    tipo_instrumento = "FX"
    monto = -1 * total_cost
    nominal = cantidad = monto
    precio = 1
    duration = tasa = 0.0
    riesgo = riesgo_internacional = pais_emisor = "N/A"
    moneda = "$"
    nombre_emisor =  sector = "Caja"
    nombre_instrumento = "Caja Fake"
    index_id = 0
    instrument_array = [[fecha, codigo_fdo, codigo_emi, codigo_ins,
                         tipo_instrumento, moneda, monto, nominal,
                         cantidad, precio, duration, tasa, riesgo,
                         nombre_emisor, nombre_instrumento, fec_vcto,
                         pais_emisor, index_id, sector, riesgo_internacional]]
    instrument_df = pd.DataFrame(data=instrument_array, columns=instrument_columns)
    return instrument_df


def get_fund(fund_id):
    '''
    Obtiene la informaicon basica del fondo en cuestion.
    '''
    funds = rk.get_funds()
    funds["codigo_fdo_aux"] = funds["codigo_fdo"]
    fund = funds.set_index(["codigo_fdo_aux"]).loc[fund_id]
    return fund

spot_date = fs.get_ndays_from_today(0)

# Fijamos la fecha en la que empieza el dataset
# de la matriz de varianza covarianza
data_start_date = fs.get_ndays_from_date(365, spot_date)

# Fijamos la fecha para la cual se tomara
# el vector de weights de los portafolios
fund_date = fs.get_prev_weekday(spot_date)

# Fijamos la fecha para la cual se tomara
# el vector de weights de los benchmarks
benchmark_date = fs.get_prev_weekday(fund_date)

# Fijamos la fecha para la cual se tomara
# el ultimo dato para la matriz de varianza-covarianza
data_end_date = benchmark_date

# Obtenemos la inflacion para calcular yield de bonos reajustables
inflation = rk.get_inflation(start_date=benchmark_date, end_date=fund_date)

# Obtenemos las distintas FX
usd = get_fx(fund_date, "usd")
clf = get_fx(fund_date, "clf")
eur = get_fx(fund_date, "eur")
mxn = get_fx(fund_date, "mxn")
brl = get_fx(fund_date, "brl")

print("Generating investment report for: ")
print("spot date: " + spot_date)
print("data start date: " + data_start_date)
print("portfolio date: " + fund_date)
print("benchmark date: " + benchmark_date)
print("inflation: " + str(inflation))


# Obtenemos el codigo del fondo y las posiciones a simular
fund_id, instruments = get_fake_positions()


# Obtenemos el dataset con toda la informacion historica
print("Fetching historical dataset...")
dataset = rk.get_historical_dataset(data_start_date=data_start_date,
                                    data_end_date=data_end_date)

# Contruimos una matriz de varianza-covarianza
# exponentially weighted en base al dataset
print("Computing exponentially weighted covariance matrix...")
matrix = rk.get_ewma_cov_matrix(data=dataset, landa=0.94)


# Obtenemos el fondo de la base de datos
fund = get_fund(fund_id)
benchmark_id = fund["benchmark_id"]
alpha_seeker = fund["alpha_seeker"]


# Obtenemos el portfolio del fondo sin metricas de riesgo
fund_portfolio = rk.get_portfolio(fund_date=fund_date,
                                  fund_id=fund_id,
                                  inflation=inflation)

# Portfolio del benchmark sin metricas de riesgo
benchmark_portfolio = rk.get_portfolio_bmk(benchmark_date=benchmark_date,
                                           benchmark_id=benchmark_id)



# Insertamos los nuevos instrumentos al portfolio
fund_portfolio = get_portfolio_simulation(fund_portfolio=fund_portfolio,
	                                instruments=instruments,
	                                fund_date=fund_date,
	                                usd=usd,
	                                clf=clf,
	                                eur=eur,
	                                mxn=mxn,
	                                brl=brl)

# Portfolio activo con metricas de riesgo
active_portfolio = rk.get_portfolio_metrics(fund_portfolio=fund_portfolio,
                                            benchmark_portfolio=benchmark_portfolio,
                                            fund_id=fund_id,
                                            matrix=matrix,
                                            benchmark_id=benchmark_id,
                                            alpha_seeker=alpha_seeker)

# Construimos el reporte en un pdf consolidado
print("Constructing report...")
print_report_pdf(portfolio=active_portfolio,
                 fund=fund,
                 fund_date=fund_date)

