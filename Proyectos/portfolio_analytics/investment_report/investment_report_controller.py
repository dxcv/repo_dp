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


def print_report_pdf(portfolios, funds, fund_date, serie_historica):
    '''
    Exporta el reporte a un pdf consolidado.
    '''
    # Abrimos el workbook con el template del informe
    wb = fs.open_workbook(path=".\\investment_report.xlsx", screen_updating=True, visible=False)
    # Borramos la informacion anterior
    fs.clear_table_xl(wb=wb, sheet="Historical", row=1, column=1)
    fs.clear_sheet_xl(wb=wb, sheet="Dataset")
    fs.paste_val_xl(wb=wb, sheet="Historical", row=1, column=1, value=serie_historica)
    fs.paste_val_xl(wb=wb, sheet="Dataset", row=1, column=1, value=portfolios)
    fs.paste_val_xl(wb=wb, sheet="Historical", row=2, column=8, value=fund_date)
    # Imprimimos la hoja de resumen
    print("printing -> summary")
    fs.export_sheet_pdf(sheet_index=fs.get_sheet_index(wb, "Resumen")-1, path_in=".", path_out=fs.get_self_path()+"output\\aperture.pdf")
    # Imprimimos cada fondo
    for i, fund in funds.iterrows():
        fund_id = fund["codigo_fdo"]
        display_portfolio = fund["display_portfolio"]
        print("printing -> " + fund_id)
        fs.paste_val_xl(wb=wb, sheet=display_portfolio, row=11, column=4, value=fund_id)
        fs.paste_val_xl(wb=wb, sheet="Historical", row=2, column=7, value=fund_id)
        path_pdf = fs.get_self_path() + "output\\" + display_portfolio + "_" + fund_id + ".pdf"
        fs.export_sheet_pdf(sheet_index=fs.get_sheet_index(wb, display_portfolio)-1, path_in=".", path_out=path_pdf)
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)
    fs.merge_pdf(path=".\\output\\", output_name="investment_report.pdf")
    for i, fund in funds.iterrows():
        fund_id = fund["codigo_fdo"]
        display_portfolio = fund["display_portfolio"]
        fs.delete_file(".\\output\\" + display_portfolio + "_" + fund_id + ".pdf")
    fs.delete_file(".\\output\\aperture.pdf")

    # Guardamos backup
    name = "Investment_Report_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    src = ".\\output\\investment_report.pdf"
    dst = "L:\\Rates & FX\\fsb\\reporting\\investment_report_backup\\" + name
    fs.copy_file(src, dst)

def send_mail_report(spot_date):
    '''
    Envia el mail a fernando suarez 1313. 
    '''
    print("sending mail ...", end="")
    subject = "Reporte de inversiones"
    body = "Estimados, adjunto el reporte diario de inversiones al " + spot_date +".\nSaludos"
    mail_list = ["fsuarez@credicorpcapital.com", "fsuarez1@uc.cl"]
    path = fs.get_self_path() + "output\\investment_report.pdf"
    paths = [path]
    fs.send_mail_attach(subject=subject,
                        body=body,
                        mails=mail_list,
                        attachment_paths=paths)
    fs.delete_file(path)


# Cerramos posibles instancias de Excel abiertas
fs.kill_excel()

#  las fechas entre las que trabajaremos
pd.set_option("display.max_columns", 3)
pd.set_option("display.max_rows", 3)

# dia_fin = "2016-09-30"
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

print("starting...")
# Obtenemos el dataset con toda la informacion historica
print("fetching historical dataset...")
dataset = rk.get_historical_dataset(data_start_date=data_start_date,
                                    data_end_date=data_end_date)
# Contruimos una matriz de varianza-covarianza
# exponentially weighted en base al dataset
print("computing exponentially weighted covariance matrix...")
matrix = rk.get_ewma_cov_matrix(data=dataset, landa=0.94)

# Obtenemos la lista de los fondos con su informacion basica
# y obtenemos todos los portafolios activos con sus metricas de riesgo
print("computing ex ante volatility...")
funds = rk.get_funds()
funds = funds[(funds["codigo_fdo"] == "DEUDA CORP")|(funds["codigo_fdo"] == "SPREADCORP")]


portfolios = rk.get_full_portfolio_metrics(matrix=matrix,
                                           funds=funds,
                                           fund_date=fund_date,
                                           benchmark_date=benchmark_date,
                                           inflation=inflation)

# fs.print_full(portfolios.groupby(by="codigo_fdo")["cty"].sum()*100) para ver yields

# Obtenemos tambien el agregado historico de las metricas
# para los ultimos 20 dias habiles para fondos que lo requieran
funds_hist = funds[(funds["display_portfolio"] == "retorno absoluto") | (funds["display_portfolio"] == "credito") | (funds["display_portfolio"] == "renta variable") | (funds["display_portfolio"] == "credito latam")]
print(funds_hist)
print(fund_date)
serie = rk.get_historical_metrics(funds=funds_hist,
                                  dataset=dataset,
                                  fund_date=fund_date,
                                  benchmark_date=benchmark_date,
                                  inflation=inflation,
                                  days=20)

# Construimos el reporte en un pdf consolidado
print("constructing report...")
print_report_pdf(portfolios=portfolios,
                 funds=funds,
                 fund_date=fund_date,
                 serie_historica=serie)

# Enviamos el correo con el reporte
send_mail_report(spot_date=spot_date)
