"""
Created on Tue Feb 21 11:00:00 2017

@author: Fernando Suarez
"""

import sys
import pandas as pd
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
sys.path.insert(1, '../risk_library/')
import risk as rk


def get_scripts_status(spot_date, yesterday_date):
    '''
    Chequea scripts en base a una consulta a la base de datos.
    '''
    path = ".\\querys\\bug_checker_query.sql"
    query = fs.read_file(path=path)
    query = query.replace("autoyesterday", yesterday_date)
    query = query.replace("autotoday", spot_date)
    tests= fs.get_frame_sql_user(server="Puyehue",
    						     database="MesaInversiones",
    						     username="usrConsultaComercial",
    						     password="Comercial1w",
    						     query=query)
    return tests


def get_mapping_status(fund_date, benchmark_date):
    '''
    Chequea que todos los instrumentos en cartera de los fondos a reportar esten mapeados a un indice.
    '''
    # Obtenemos los fondos que se reporten en el informe de inversiones
    funds = rk.get_funds()
    # Dejamos dos variables de estado, una para los instrumentos de los fondos
    # y otro para los instrumentos en cartera de los benchmarks
    check_funds = 1
    check_benchmarks = 1
    total_unmaped_instruments_p = []
    total_unmaped_instruments_b = []
    # Ponemos una dummy inflation para utilizar la funcion que obtiene el portfolio
    inflation = 0.03
    # Para cada fondo obtenemos su portafolio y el de su benchmark
    for i, fund in funds.iterrows():
        # Sacamos la informacion basica del fondo
        fund_id = fund["codigo_fdo"]
        benchmark_id = fund["benchmark_id"]
        alpha_seeker = fund["alpha_seeker"]
        # Portfolio del fondo
        fund_portfolio = rk.get_portfolio(fund_date=fund_date,
                                          fund_id=fund_id,
                                          inflation=inflation)
        fund_portfolio = fund_portfolio.fillna(0)
        # Portfolio del benchmark
        benchmark_portfolio = rk.get_portfolio_bmk(benchmark_date=benchmark_date,
                                                   benchmark_id=benchmark_id)
        benchmark_portfolio = benchmark_portfolio.fillna(0)
        # Obtenemos los instrumentos no mapeados.
        # Por construccion son los que estab mapeados
        # al indice cero (a excepcion de FX CLP y cuotas de fondo)
        unmapped_fund_instruments = fund_portfolio[(fund_portfolio["Index_Id"] == 0) & (fund_portfolio["tipo_instrumento"] != "FX") & (fund_portfolio["tipo_instrumento"] != "FX Forward") & (fund_portfolio["tipo_instrumento"] != "Cuota de Fondo") & (fund_portfolio["tipo_instrumento"] != "Leverage")]
        unmapped_benchmark_instruments = benchmark_portfolio[(benchmark_portfolio["Index_Id"] == 0) & (benchmark_portfolio["tipo_instrumento"] != "FX") & (benchmark_portfolio["tipo_instrumento"] != "FX Forward") & (benchmark_portfolio["tipo_instrumento"] != "Cuota de Fondo")]
        total_unmaped_instruments_p.append(unmapped_fund_instruments)
        total_unmaped_instruments_b.append(unmapped_benchmark_instruments)
    # Consolidamos todos los instrumentos no mapeados
    total_unmaped_instruments_p = pd.concat(total_unmaped_instruments_p, ignore_index=True)
    total_unmaped_instruments_b = pd.concat(total_unmaped_instruments_b, ignore_index=True)
    # En caso de que existan instrumentos no mapeados levantamos un flag
    if not total_unmaped_instruments_p.empty:
    	check_funds = 0
    if not total_unmaped_instruments_b.empty:
    	check_benchmarks = 0
    # Retornamos los flags en un dataframe en conjunto con la lista de instrumentos
    map_status = pd.DataFrame([["08:30", "Mapping Fondos", check_funds], ["08:30", "Mapping Benchmarks", check_benchmarks]],columns = ["hora", "Script", "Checked"])
    total_unmaped_instruments_p["Codigo_Fdo/Benchmark_Id"] = total_unmaped_instruments_p["codigo_fdo"]
    total_unmaped_instruments_b["Codigo_Fdo/Benchmark_Id"] = total_unmaped_instruments_b["benchmark_id"]
    total_unmaped_instruments = pd.concat([total_unmaped_instruments_p[["codigo_emi", "codigo_ins", "Codigo_Fdo/Benchmark_Id"]], total_unmaped_instruments_b[["codigo_ins", "Codigo_Fdo/Benchmark_Id"]]], ignore_index=True)
    return map_status, total_unmaped_instruments



def send_mail_report(current_time, status, unmapped_fund_instruments):
    '''
    Envia el mail a fernando suarez 1313. 
    '''
    print("sending mail ...", end="")
    subject = "Reporte de Integridad Scripts-BDD"
    body = "Status de sistemas para las " + str(current_time) + ": \n" + str(status)  + "\n\n" + "Unmapped instruments: \n" + str(unmapped_fund_instruments)
    mail_list = ["fsuarez@credicorpcapital.com", "fsuarez1@uc.cl"]
    fs.send_mail(subject=subject, body=body, mails=mail_list)


# Cerramos posibles archivos Excel
fs.kill_excel()
print ("Checking if everything is ok, please wait ...")

# Fechas en que se verifica correctitud
spot_date = fs.get_ndays_from_today(0)
yesterday_date = fs.get_prev_weekday(spot_date)
prevyesterday_date = fs.get_prev_weekday(yesterday_date)
current_time = fs.get_current_time()

# Correctitud de scripts
scripts_status = get_scripts_status(spot_date, yesterday_date)

# Completitud del mapping
map_status, unmaped_instruments = get_mapping_status(yesterday_date, prevyesterday_date)

# Consolidamos todo
status = scripts_status.append(map_status).sort_values("hora").reset_index().drop("index", 1)
print("current status: ")
print(status)
print("")	
print("unmaped instruments: ")
print(unmaped_instruments)
print("")
print("Sending report...")
send_mail_report(current_time, status, unmaped_instruments)