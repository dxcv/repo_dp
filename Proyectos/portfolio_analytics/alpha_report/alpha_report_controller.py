"""
Created on Thu Oct 06 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
sys.path.insert(1, '../risk_library/')
import risk as rk
import pandas as pd
import numpy as np
import math

def fetch_risk_free_rate(date):
    '''
    Descarga los fondos con su informacion basica en un dataframe.
    '''
    path = ".\\querys_alpha_report\\tpm.sql"
    query = fs.read_file(path=path)
    query = query.replace("autodate", date)
    val = fs.get_val_sql_user(server="Puyehue",
                              database="MesaInversiones",
                              username="usrConsultaComercial",
                              password="Comercial1w",
                              query=query)
    # Dividimos porue viene en base 100
    val = float(val / 100.0)
    return val


def fetch_funds():
    '''
    Descarga los fondos con su informacion basica en un dataframe.
    '''
    path = ".\\querys_alpha_report\\funds.sql"
    query = fs.read_file(path=path)
    funds = fs.get_frame_sql_user(server="Puyehue",
                                  database="MesaInversiones",
                                  username="usrConsultaComercial",
                                  password="Comercial1w",
                                  query=query)
    return funds


def fetch_nav_series(start_date, end_date):
     '''
     Descarga la serie con todos los nav historicos de los portfolios.
     '''
     path = ".\\querys_alpha_report\\navs.sql"
     query = fs.read_file(path).replace("autodate1", start_date).replace("autodate2", end_date)
     series = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query)
     series.set_index(["fecha", "codigo_fdo"], inplace=True)
     return series


def fetch_tac_series(start_date, end_date): 
    '''
    Retorna la serie con el tac historico de los portfolios.
    '''
    path = ".\\querys_alpha_report\\tacs.sql"
    query = fs.read_file(path).replace("autodate1", start_date).replace("autodate2", end_date)
    series = fs.get_frame_sql_user(server="Puyehue",
                                   database="MesaInversiones",
                                   username="usrConsultaComercial",
                                   password="Comercial1w",
                                   query=query)
    series.set_index(["fecha", "codigo_fdo"], inplace=True)
    return series


def fetch_benchmark_series(start_date, end_date):
     '''
     Descarga la serie con todos los nav historicos de los portfolios.
     '''
     path = ".\\querys_alpha_report\\benchmarks.sql"
     query = fs.read_file(path).replace("autodate1", start_date).replace("autodate2", end_date)
     series = fs.get_frame_sql_user(server="Puyehue",
                                    database="MesaInversiones",
                                    username="usrConsultaComercial",
                                    password="Comercial1w",
                                    query=query)
     series.set_index(["fecha", "benchmark_id"], inplace=True)
     return series


def compound_series(funds, nav_series, tac_series, benchmark_series): 
    '''
    Traspas todas las series a base 100 y les agrega el tac.
    Ademas pasamos la serie del nav a dias habiles y componemos
    el risk budget en el benchmark de los fondos de retorno absoluto
    '''
    nav_series_aux = []
    benchmark_series_aux = []
    # Por cada fondo obtenemos su serie sin tac en base 100
    # junto con la de su benchmark
    for i, fund in funds.iterrows():
        fund_id = fund["codigo_fdo"]
        benchmark_id = fund["benchmark_id"]
        alpha_seeker = fund["alpha_seeker"]
        risk_budget = fund["risk_budget"]
        # Obtenemos la serie del fondo, el tac acumulado y componemos en base 100
        nav_serie = nav_series[nav_series.index.get_level_values("codigo_fdo") == fund_id] 
        tac_serie = tac_series[tac_series.index.get_level_values("codigo_fdo") == fund_id]
        tac_serie = (tac_serie + 1).cumprod()
        nav_serie = nav_serie["valor_cuota_ajustado"] * tac_serie["tac"]
        nav_serie = normalize_serie(nav_serie, 100.0)
        # Obtenemos el benchmark y lo componemos en base 100
        benchmark_serie = benchmark_series[benchmark_series.index.get_level_values("benchmark_id") == benchmark_id]
        benchmark_serie = normalize_serie(benchmark_serie, 100.0)
        # Si el fondo es de retorno absoluto le componemos
        # su risk budget en la serie de su benchmark
        if alpha_seeker == 0:
            benchmark_serie = compound_risk_budget(benchmark_serie, risk_budget)
        nav_series_aux.append(nav_serie)
        benchmark_series_aux.append(benchmark_serie)
    nav_series = pd.concat(nav_series_aux)
    benchmark_series = pd.concat(benchmark_series_aux)
    # Notar que debemos dejar las series de tiempo como objetos series
    benchmark_series = benchmark_series["valor"]
    benchmark_series.name = "nav_benchmark"
    # Filtramos los nav por dias habiles
    nav_series = nav_series[nav_series.index.get_level_values("fecha").weekday <= 4]
    # Cambiamos nombre a la columna de valores
    nav_series.name = "nav_portfolio"
    return nav_series, benchmark_series


def normalize_serie(serie, base): 
    '''
    Traspasa una vector historico a una base dada.
    '''
    serie = serie.pct_change()
    serie = serie.fillna(0.0)
    serie = (serie + 1.0).cumprod()
    serie = serie * base
    return serie


def compound_risk_budget(serie, risk_budget): 
    '''
    Le suma a una serie su risk budget ajustado por fecha.
    '''
    days = len(serie)
    aux = pd.DataFrame(np.arange(days), index=serie.index)
    aux = (aux*risk_budget) / 365
    aux = aux * 100
    serie["valor"] = serie["valor"] + aux[0]
    return serie


def compute_risk_series(funds, dataset, end_date, period): 
    '''
    Calcula la serie de risk exposure los fondos.
    '''
    # Obtenemos la serie desagregada por moneda y pais
    series = rk.get_historical_metrics(funds=funds,
                                       dataset=dataset,
                                       fund_date=end_date,
                                       benchmark_date=end_date,
                                       inflation=3,
                                       days=period)
    # Filtramos por los cortes de moneda (podria ser tambien por pais)
    series = series[(series["Slice"]=="$")|(series["Slice"]=="UF")|(series["Slice"]=="US$")|(series["Slice"]=="MX")|(series["Slice"]=="EU")|(series["Slice"]=="REA")|(series["Slice"]=="SOL")]
    # Retornamos la serie como la suma de todas las monedas
    series.columns = ["fecha", "codigo_fdo", "slice", "metric"]
    series = series.groupby(by=["fecha", "codigo_fdo"])["metric"].sum()
    series.name = "risk"
    return series


def compute_cumulative_alpha_series(funds, nav_series, benchmark_series):
    '''
    Calcula la series de alpha acumulado entre los portfolios y los benchmarks.
    '''
    alpha_series = []
    # Por cada fondo calculamos su vector de alpha acumulado
    for i, fund in funds.iterrows():
        fund_id = fund["codigo_fdo"]
        benchmark_id = fund["benchmark_id"]
        # Obtenemos las series del nav y el benchmark
        nav_serie = nav_series[nav_series.index.get_level_values("codigo_fdo") == fund_id]
        # Como son series necesito guardar referencia al multiindex
        # para asignarselo al vector de alpha tras el calculo
        aux_index = nav_serie.index
        nav_serie.index = nav_serie.index.droplevel("codigo_fdo")
        benchmark_serie = benchmark_series[benchmark_series.index.get_level_values("benchmark_id") == benchmark_id]
        benchmark_serie.index = benchmark_serie.index.droplevel("benchmark_id")
        # Calculamos el alpha acumulado, dividimos por 100
        # ya que el vetor viene ne base 100
        alpha_serie = (nav_serie - benchmark_serie)/100
        alpha_serie.name = "cumulative_alpha"
        alpha_serie.index = aux_index
        alpha_series.append(alpha_serie)
    alpha_series = pd.concat(alpha_series)
    return alpha_series


def compute_risk_adjusted_metrics(funds, nav_series, benchmark_series, cumulative_alpha_series, risk_series, inception_date, end_date, risk_free_rate):
    '''
    Calcula las distintas metricas de retorno ajustado para cada fondo.
    '''
    # Obtenemos la cantidad de dias del periodo para traspasar
    # a base 252 todos los retornos y/o metricas
    days = len(fs.get_dates_between(inception_date, end_date))
    # Por cada fondo calculamos sus metircas y las agregamos al dataframe
    for i, fund in funds.iterrows():
        # Sacamos datos basicos del fondo
        fund_id = fund["codigo_fdo"]
        benchmark_id = fund["benchmark_id"]
        risk_budget = fund["risk_budget"]
        alpha_seeker = fund["alpha_seeker"]
        # Obtenemos las series pertinentes
        nav_serie = nav_series[nav_series.index.get_level_values("codigo_fdo") == fund_id] 
        nav_serie.index = nav_serie.index.droplevel("codigo_fdo")
        benchmark_serie = benchmark_series[benchmark_series.index.get_level_values("benchmark_id") == benchmark_id]
        benchmark_serie.index = benchmark_serie.index.droplevel("benchmark_id")
        cumulative_alpha_serie = cumulative_alpha_series[cumulative_alpha_series.index.get_level_values("codigo_fdo") == fund_id]
        cumulative_alpha_serie.index = cumulative_alpha_serie.index.droplevel("codigo_fdo")
        risk_serie = risk_series[risk_series.index.get_level_values("codigo_fdo") == fund_id]
        risk_serie.index = risk_serie.index.droplevel("codigo_fdo")        
        # Calculamos las metricas
        portfolio_cumulative_return = compute_total_return(nav_serie, end_date)
        benchmark_cumulative_return = compute_total_return(benchmark_serie, end_date)
        cumulative_alpha = portfolio_cumulative_return - benchmark_cumulative_return
        portfolio_expost_volatility = compute_expost_volatility(nav_serie)
        portfolio_anualized_return = portfolio_cumulative_return * (252/days)
        portfolio_sharpe_ratio = (portfolio_anualized_return - risk_free_rate) / portfolio_expost_volatility
        expost_tracking_error = compute_expost_tracking_error(nav_serie, benchmark_serie)
        anualized_cumulative_alpha = cumulative_alpha * (252/days)
        expost_info_ratio = anualized_cumulative_alpha / expost_tracking_error
        exante_tracking_error_spot = risk_serie.loc[end_date]
        exante_tracking_error_avg = risk_serie.mean()
        # Reanualizamos a 365 para calcular el ultimo ratio ya que 
        # el risk budget esta en base 365 chicos.
        anualized_cumulative_alpha = cumulative_alpha * (365/days)
        normalized_info_ratio = anualized_cumulative_alpha / risk_budget
        # Quitamos la composicion del budget de este ratio para retorno absoluto
        if alpha_seeker == 0:
        	benchmark_base_return = benchmark_cumulative_return - (days*risk_budget/365)
        	cumulative_base_alpha = portfolio_cumulative_return - benchmark_base_return
        	anualized_base_alpha = cumulative_base_alpha * (365/days)
        	normalized_info_ratio = anualized_base_alpha / risk_budget          
        # Seteamos las metricas
        funds.set_value(i, "portfolio_cumulative_return", portfolio_cumulative_return)
        funds.set_value(i, "benchmark_cumulative_return", benchmark_cumulative_return)
        funds.set_value(i, "cumulative_alpha", cumulative_alpha)
        funds.set_value(i, "portfolio_expost_volatility", portfolio_expost_volatility)
        funds.set_value(i, "portfolio_sharpe_ratio", portfolio_sharpe_ratio)
        funds.set_value(i, "expost_tracking_error", expost_tracking_error)
        funds.set_value(i, "expost_info_ratio", expost_info_ratio)
        funds.set_value(i, "exante_tracking_error_spot", exante_tracking_error_spot)
        funds.set_value(i, "exante_tracking_error_avg", exante_tracking_error_avg)
        funds.set_value(i, "normalized_info_ratio", normalized_info_ratio)
    return funds
    

def compute_total_return(serie, end_date):
    '''
    Calcula el retorno total acumulado en base a un vector de retorno acumulado.
    '''
    total_return = (serie.loc[end_date]-100) / 100
    return total_return


def compute_expost_volatility(portfolio_serie):
    '''
    Calcula la volatilidad ex post de un vector de retorno acumulado.
    '''
    portfolio_serie = portfolio_serie.pct_change()
    portfolio_serie = portfolio_serie.fillna(0.0)
    volatility = portfolio_serie.std() * math.sqrt(252)
    return volatility


def compute_expost_tracking_error(portfolio_serie, benchmark_serie):
    '''
    Calcula el tracking error ex post de dos vectores de retorno acumulado.
    '''
    portfolio_serie = portfolio_serie.pct_change()
    portfolio_serie = portfolio_serie.fillna(0.0)
    benchmark_serie = benchmark_serie.pct_change()
    benchmark_serie = benchmark_serie.fillna(0.0)
    active_serie = portfolio_serie - benchmark_serie
    tracking_error = active_serie.std() * math.sqrt(252)
    return tracking_error


def compute_extreme_series(funds, day_list): 
    '''
    Genera los vectores de avg y budget risk series.
    '''
    risk_budget_series = []
    risk_avg_series = []
    # Por cada fondo calculamos una serie con
    # el valor promedio de su exposure y otra
    # con el risk budget, para graicarlo en el reporte
    for i, fund in funds.iterrows():
        fund_id = fund["codigo_fdo"]
        risk_budget = fund["risk_budget"]
        risk_avg = fund["exante_tracking_error_avg"]
        # Construimos la serie del budget
        risk_budget_serie = pd.DataFrame(day_list, columns=["fecha"])
        risk_budget_serie["risk_budget"] = risk_budget
        risk_budget_serie["codigo_fdo"] = fund_id
        risk_budget_serie.set_index(["fecha", "codigo_fdo"], inplace=True)
        risk_budget_series.append(risk_budget_serie)
        # Construimos la serie del mean exposure
        risk_avg_serie = pd.DataFrame(day_list, columns=["fecha"])
        risk_avg_serie["risk_avg"] = risk_avg
        risk_avg_serie["codigo_fdo"] = fund_id
        risk_avg_serie.set_index(["fecha", "codigo_fdo"], inplace=True)
        risk_avg_series.append(risk_avg_serie)
    # Pasamos todo a series
    risk_budget_series = pd.concat(risk_budget_series)
    risk_budget_series = risk_budget_series["risk_budget"]
    risk_budget_series.name = "risk_budget"
    risk_avg_series = pd.concat(risk_avg_series)
    risk_avg_series = risk_avg_series["risk_avg"]
    risk_avg_series.name = "risk_avg"   
    return risk_budget_series, risk_avg_series
    

def format_funds(funds): 
    '''
    Formatea el dataframe de fondos para el display.
    '''
    funds.set_index(["codigo_fdo"], inplace=True)
    display_columns = ["benchmark_id", "nombre_benchmark",
                       "risk_budget", "portfolio_cumulative_return",
                       "benchmark_cumulative_return", "cumulative_alpha",
                       "portfolio_expost_volatility", "portfolio_sharpe_ratio",
                       "expost_tracking_error", "expost_info_ratio",
                       "exante_tracking_error_spot", "exante_tracking_error_avg",
                       "normalized_info_ratio", "alpha_seeker"]
    funds = funds[display_columns]
    return funds


def print_report_excel(funds, nav_series, benchmark_series, cumulative_alpha_series, risk_series, risk_budget_series, risk_avg_series, inception_date, end_date, risk_free_rate):
    '''
    Exporta el reporte a un pdf consolidado.
    '''
    # Abrimos el workbook con el template del informe
    wb = fs.open_workbook(path=".\\alpha_report.xlsx", screen_updating=True, visible=True)
    # Borramos la informacion anterior
    fs.clear_sheet_xl(wb=wb, sheet="funds")
    for i, fund in funds.iterrows():
        fund_id = fund.name
        benchmark_name = fund["nombre_benchmark"]
        alpha_seeker = fund["alpha_seeker"]
        risk_budget = str(fund["risk_budget"]*10000) + " bps"
        benchmark_name = fund["nombre_benchmark"]
        # Si es retorno absoluto le concatenamos el risk budget al nombre
        if alpha_seeker == 0:
            benchmark_name = benchmark_name + " + " + risk_budget
        funds.set_value(i, "nombre_benchmark", benchmark_name)
        fs.clear_sheet_xl(wb=wb, sheet=fund_id)
    # Insertamos los datos de los fondos
    fs.paste_val_xl(wb, "funds", 1, 1, funds)
    # Por cada fondo vamos a su sheet respectiva
    # e insertamos las series necesarias para el reporte
    for i, fund in funds.iterrows():
        fund_id = fund.name
        benchmark_id = fund["benchmark_id"]
        benchmark_name = fund["nombre_benchmark"]
        funds.set_value(i, "nombre_benchmark", benchmark_name)
        print("-> " + fund_id)
        # Obtenemos las series pertinentes
        nav_serie = nav_series[nav_series.index.get_level_values("codigo_fdo") == fund_id]
        benchmark_serie = benchmark_series[benchmark_series.index.get_level_values("benchmark_id") == benchmark_id]
        cumulative_alpha_serie = cumulative_alpha_series[cumulative_alpha_series.index.get_level_values("codigo_fdo") == fund_id]
        risk_serie = risk_series[risk_series.index.get_level_values("codigo_fdo") == fund_id]
        risk_budget_serie = risk_budget_series[risk_budget_series.index.get_level_values("codigo_fdo") == fund_id] 
        risk_avg_serie = risk_avg_series[risk_avg_series.index.get_level_values("codigo_fdo") == fund_id]
        # Insertamos las columnas de cada serie
        fs.paste_val_xl(wb, fund_id, 1, 1, "date")
        fs.paste_val_xl(wb, fund_id, 1, 2, fund_id)
        fs.paste_val_xl(wb, fund_id, 1, 3, benchmark_name)
        fs.paste_val_xl(wb, fund_id, 1, 4, "cumulative alpha")
        fs.paste_val_xl(wb, fund_id, 1, 5, "ex ante tracking error")
        fs.paste_val_xl(wb, fund_id, 1, 6, "risk budget")
        fs.paste_val_xl(wb, fund_id, 1, 7, "avg ex ante tracking error")
        # Insertamos las series por columna
        fs.paste_col_xl(wb, fund_id, 2, 1, np.array(nav_serie.index))
        fs.paste_col_xl(wb, fund_id, 2, 2, np.array(nav_serie))
        fs.paste_col_xl(wb, fund_id, 2, 3, np.array(benchmark_serie))
        fs.paste_col_xl(wb, fund_id, 2, 4, np.array(cumulative_alpha_serie))
        fs.paste_col_xl(wb, fund_id, 2, 5, np.array(risk_serie))
        fs.paste_col_xl(wb, fund_id, 2, 6, np.array(risk_budget_serie))
        fs.paste_col_xl(wb, fund_id, 2, 7, np.array(risk_avg_serie))
    # Exportamos a pdf
    path_pdf_alpha_seeker = fs.get_self_path() + "output_alpha_report\\alpha_seeker.pdf"
    path_pdf_absolute_return = fs.get_self_path() + "output_alpha_report\\absolute_return.pdf"
    fs.export_sheet_pdf(sheet_index=fs.get_sheet_index(wb, "report_alpha_seeker")-1, path_in=".", path_out=path_pdf_alpha_seeker)
    fs.export_sheet_pdf(sheet_index=fs.get_sheet_index(wb, "report_absolute_return")-1, path_in=".", path_out=path_pdf_absolute_return)
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)
    fs.merge_pdf(path=".\\output_alpha_report\\", output_name="alpha_report.pdf")
    fs.delete_file(path_pdf_alpha_seeker)
    fs.delete_file(path_pdf_absolute_return)
    
    # Guardamos backup
    name = "Alpha_Report_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    src = ".\\output_alpha_report\\alpha_report.pdf"
    dst = "L:\\Rates & FX\\fsb\\reporting\\alpha_report_backup\\" + name
    fs.copy_file(src, dst)


def send_mail_report(spot_date):
    '''
    Envia el mail a fernando suarez 1313. 
    '''
    print("sending mail ...", end="")
    subject = "Reporte de alpha"
    body = "Estimados, adjunto el reporte diario de alpha al " + spot_date +".\nSaludos"
    mail_list = ["fsuarez@credicorpcapital.com", "fsuarez1@uc.cl"]
    path = fs.get_self_path() + "output_alpha_report\\alpha_report.pdf"
    paths = [path]
    fs.send_mail_attach(subject=subject, body=body, mails=mail_list, attachment_paths=paths)
    fs.delete_file(path)


#  las fechas entre las que trabajaremos
pd.set_option("display.max_columns", 3)
pd.set_option("display.max_rows", 3)

# Fecha de cierre del reporte
spot_date = fs.get_ndays_from_today(0)
end_date = fs.get_prev_weekday(fs.get_prev_weekday(spot_date))

# Fijamos la fecha en la que empieza el dataset
# de la matriz de varianza covarianza
data_start_date = fs.get_ndays_from_date(365, end_date)

# Fijamos la fecha para la cual se tomara
# el ultimo dato para la matriz de varianza-covarianza
data_end_date = end_date

inception_date = fs.get_prev_weekday(fs.get_ndays_from_date(fs.get_current_days_year(fs.convert_string_to_date(spot_date))-2, spot_date))
# inception_date = "2017-04-26"

# Obtenemos la lista de dias de las series del reporte
day_list = fs.get_weekdays_dates_between(inception_date, end_date)

# Obtenemos la cantidad de dias habiles del periodo
period = len(day_list)

print("Generating alpha report for: ")
print("spot date: " + spot_date)
print("end date: " + end_date)
print("data start date: " + data_start_date)
print("inception date: " + inception_date)
print("period length: " + str(period))

# Obtenemos el dataset con toda la informacion historica
print("Fetching overnight risk free rate...")
risk_free_rate = fetch_risk_free_rate(end_date)

# Obtenemos el dataset con toda la informacion historica
print("Fetching historical dataset...")
dataset = rk.get_historical_dataset(data_start_date=data_start_date,
                                    data_end_date=data_end_date)

print("Fetching funds information...")
# Obtenemos la lista de los fondos con su informacion basica
# y obtenemos todos los portafolios activos con sus metricas de riesgo
funds = fetch_funds()

print("Fetching funds series...")
# Obtenemos las series de los nav con comision
nav_series = fetch_nav_series(inception_date, end_date)

print("Fetching tac series...")
# Obtenemos las series de los tacs
tac_series = fetch_tac_series(inception_date, end_date)

print("Fetching benchmark series...")
# Obtenemos las series de los benchmarks
benchmark_series = fetch_benchmark_series(inception_date, end_date)

print("Compounding series...")
# Componemos valores cuota sin comision
# y pasamos fondo y benchmark a base 100
# Para los retorno absoluto ajustamos el
# benchmark mas su risk budget
nav_series, benchmark_series = compound_series(funds, nav_series, tac_series, benchmark_series)

print("Computing alpha series...")
# Generamos las series de alpha acumulado
cumulative_alpha_series = compute_cumulative_alpha_series(funds, nav_series, benchmark_series)

print("Compouting risk metrics series...")
# Obtenemos las metricas de riesgo historicas
risk_series = compute_risk_series(funds, dataset, end_date, period)

print("Computing risk adjusted metrics...")
# Obtenemos las metricas de riesgo ajustadas
funds = compute_risk_adjusted_metrics(funds, nav_series, benchmark_series, cumulative_alpha_series, risk_series, inception_date, end_date, risk_free_rate)

print("Computing risk extreme series...")
# Obtenemos las series con los puntos extremos de budget
risk_budget_series, risk_avg_series = compute_extreme_series(funds, day_list)

print("Formatting funds...")
# Formateamos la informacion de los fondos
funds = format_funds(funds)

print("Printing report...")
# Imprimimos el reporte en excel
print_report_excel(funds, nav_series, benchmark_series, cumulative_alpha_series, risk_series, risk_budget_series, risk_avg_series, inception_date, end_date, risk_free_rate)

print("Sending report...")
# Enviamos el correo con el reporte
send_mail_report(spot_date=spot_date)
