"""
Created on Thu May 18 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=FutureWarning)

def fetch_dataset(start_date, end_date, dataset_name):
    '''
     Baja un dataset de la base de datos.
     '''
    path = ".\\querys\\" + dataset_name + ".sql"
    query = fs.read_file(path)
    query = query.replace("autodate1", start_date)
    query = query.replace("autodate2", end_date)
    series = fs.get_frame_sql_user(server="Puyehue",
                                   database="MesaInversiones",
                                   username="usrConsultaComercial",
                                   password="Comercial1w",
                                   query=query)
    series.set_index(["fecha"], inplace=True)
    return series


def compute_implied(swap_curve, fwd_curve):
    '''
    Computa el fair value de la curva swap en la moneda del fx forward.
     '''
    implied_curve = ((1+swap_curve)/(1+fwd_curve)) -1
    return implied_curve


def compute_delta(swap_curve, implied_curve):
    '''
    Computa la diferencia entre el valuation de un bono y su precio efectivo.
    '''
    delta = swap_curve - implied_curve
    return delta


def compute_avg(delta_curve):
    '''
    Calcula el promedio historico de las diferencias.
    '''
    days = delta_curve.index
    delta_avg_aux = delta_curve.mean()
    delta_avg_aux = pd.DataFrame([delta_avg_aux.values], columns=delta_avg_aux.index.values)
    delta_avg = pd.DataFrame(columns=delta_avg_aux.columns, index = days)
    delta_avg = delta_avg.fillna(delta_avg_aux.loc[0])
    return delta_avg


def compute_fras_matrix(curve):
    '''
    Computa la matris de fras dada una curva.
    '''
    tenors = curve.index.values
    matrix = np.zeros((len(tenors), len(tenors)))
    matrix = pd.DataFrame(matrix, columns = tenors, index=tenors)
    for t1 in tenors:
        for t2 in tenors:
            if t1 < t2:
                y_t1 = curve[t1]
                y_t2 = curve[t2]
                t1_val = float(t1)
                t2_val = float(t2)
                fra = ((1+y_t2)**(t2_val/(t2_val-t1_val)))/((1+y_t1)**(t1_val/(t2_val-t1_val))) - 1
                matrix.loc[t1][t2] = fra
    return matrix


def compute_fras_metrics(implied_curve):
    '''
    Calcula matriz con la media historica y desviacion estandar
    de la matrices de fras.
    '''
    fras_cube = {}
    for date in implied_curve.index:
        date = fs.convert_date_to_string(date)
        curve = implied_curve.loc[date]
        fras_matrix = compute_fras_matrix(curve)
        fras_cube[date] = fras_matrix
    fras_cube = pd.Panel(fras_cube)
    mean_fras_matrix = fras_cube.mean(axis=0)
    std_fras_matrix  = fras_cube.std(axis=0)
    return mean_fras_matrix, std_fras_matrix


def compute_diff_fras(fras_matrix_swap , fras_matrix_implied):
    '''
    Devulve una matriz con las diferencias entre los fras de las curvas swap y spot 
    '''
    tenors=fras_matrix_implied.columns.tolist()
    diff_fras_matrix=pd.DataFrame(index=tenors, columns= tenors)
    for t in tenors:
        diff_fras_matrix[t]=(fras_matrix_implied[t]-fras_matrix_swap[t])
    return diff_fras_matrix



def compute_diff_fras_metrics(implied_curve, usd_curve):
    '''
    Calcula matriz con la media historica y desviacion estandar
    de la matrices de diferencias de fras.
    '''
    fras_cube = {}
    for date in implied_curve.index:
        date = fs.convert_date_to_string(date)
        curve_implied = implied_curve.loc[date]
        curve_swap = usd_curve.loc[date]
        fras_matrix_implied = compute_fras_matrix(curve_implied)
        fras_matrix_swap = compute_fras_matrix( curve_swap)
        diff_fras_matrix=compute_diff_fras(fras_matrix_swap, fras_matrix_implied)
        fras_cube[date] = diff_fras_matrix
    fras_cube = pd.Panel(fras_cube)
    mean_fras_matrix = fras_cube.mean(axis=0)
    std_fras_matrix  = fras_cube.std(axis=0)
    return mean_fras_matrix, std_fras_matrix


def compute_gain_loss(n_tenors, short_tenor, long_tenor, unavailable_days, days_dataset, bid_dataset, ask_dataset):
    '''
    Calcula la serie del backtest dado los tenors a comprar y vender.
    '''
    dates = days_dataset.index[:-unavailable_days]
    date_epoch = start_date
    gain_loss = []
    for date_epoch in dates:
        date_epoch = fs.convert_date_to_string(date_epoch)
        days_to_settlement = int(days_dataset.loc[date_epoch][long_tenor])
        settlement_date = fs.convert_date_to_string(fs.convert_string_to_date(date_epoch) + dt.timedelta(days=days_to_settlement))
        roll_sum = 0.0
        date_tenor = date_epoch
        bids = []
        days_roll_counter = 0
        for tenor in range(n_tenors):
            bid = bid_dataset.loc[date_tenor][short_tenor]
            days_roll = int(days_dataset.loc[date_tenor][short_tenor])
            roll_sum += bid
            date_tenor = fs.convert_date_to_string(fs.convert_string_to_date(date_tenor) + dt.timedelta(days=days_roll))
            bids.append(bid)
            if tenor == n_tenors - 2:
                days_roll = int(days_dataset.loc[date_tenor][short_tenor])
                days_roll_effective = len(fs.get_dates_between(date_tenor, settlement_date))
                bid = bid_dataset.loc[date_tenor][short_tenor]
                bid_effective = (bid/days_roll) * days_roll_effective
                roll_sum += bid_effective
                bids.append(bid_effective)
                days_roll_counter = days_roll
                break
        long_ask = ask_dataset.loc[date_epoch][long_tenor]
        epoch_gain = roll_sum - long_ask
        gain_loss.append(epoch_gain)
    gain_loss = pd.DataFrame(data=gain_loss, columns=["gain_loss"])
    gain_loss.index = dates
    return gain_loss

def print_report_pdf(end_date, fwd_curve, clp_curve, usd_curve, implied_curve, delta_curve, delta_avg, fras_matrix_spot, mean_fras_matrix, std_fras_matrix, diff_fras_matrix_spot, mean_diff_fras_matrix,std_diff_fras_matrix,fras_matrix_swap, gain_loss_1M1Y, gain_loss_3M1Y):
    '''
    Exporta el reporte a un pdf consolidado.
    '''
    # Abrimos el workbook con el template del informe
    wb = fs.open_workbook(path=".\\fwd_monitor.xlsx",
                          screen_updating=True,
                          visible=True)
    # Borramos datos anteriores
    fs.clear_sheet_xl(wb=wb, sheet="data")
    fs.clear_sheet_xl(wb=wb, sheet="forward")
    fs.clear_sheet_xl(wb=wb, sheet="clp")
    fs.clear_sheet_xl(wb=wb, sheet="usd")
    fs.clear_sheet_xl(wb=wb, sheet="implied")
    fs.clear_sheet_xl(wb=wb, sheet="delta")
    fs.clear_sheet_xl(wb=wb, sheet="avg")
    fs.clear_sheet_xl(wb=wb, sheet="fras_spot")
    fs.clear_sheet_xl(wb=wb, sheet="fras_mean")
    fs.clear_sheet_xl(wb=wb, sheet="fras_std")
    fs.clear_sheet_xl(wb=wb, sheet="diff_fras_spot")
    fs.clear_sheet_xl(wb=wb, sheet="diff_fras_mean")
    fs.clear_sheet_xl(wb=wb, sheet="diff_fras_std")
    fs.clear_sheet_xl(wb=wb, sheet="fras_swap_spot")
    fs.clear_sheet_xl(wb=wb, sheet="gain_loss_1M1Y")
    fs.clear_sheet_xl(wb=wb, sheet="gain_loss_3M1Y")
    # Insertamos nueva data
    fs.paste_val_xl(wb, "data", 1, 1, end_date)
    fs.paste_val_xl(wb, "forward", 1, 1, fwd_curve)
    fs.paste_val_xl(wb, "clp", 1, 1, clp_curve)
    fs.paste_val_xl(wb, "usd", 1, 1, usd_curve)
    fs.paste_val_xl(wb, "implied", 1, 1, implied_curve)
    fs.paste_val_xl(wb, "delta", 1, 1, delta_curve)
    fs.paste_val_xl(wb, "avg", 1, 1, delta_avg)
    fs.paste_val_xl(wb, "fras_spot", 1, 1, fras_matrix_spot)
    fs.paste_val_xl(wb, "fras_mean", 1, 1, mean_fras_matrix)
    fs.paste_val_xl(wb, "fras_std", 1, 1, std_fras_matrix)
    fs.paste_val_xl(wb, "diff_fras_spot", 1, 1, diff_fras_matrix_spot)
    fs.paste_val_xl(wb, "diff_fras_mean", 1, 1, mean_diff_fras_matrix)
    fs.paste_val_xl(wb, "diff_fras_std", 1, 1, std_diff_fras_matrix)
    fs.paste_val_xl(wb, "fras_swap_spot", 1, 1, fras_matrix_swap)
    fs.paste_val_xl(wb, "gain_loss_1M1Y", 1, 1, gain_loss_1M1Y)
    fs.paste_val_xl(wb, "gain_loss_3M1Y", 1, 1, gain_loss_3M1Y)
    # Exportamos a pdf
    path_pdf_1 = fs.get_self_path() + "output\\usd_fwd_monitor_1.pdf"
    path_pdf_2 = fs.get_self_path() + "output\\usd_fwd_monitor_2.pdf"
    fs.export_sheet_pdf(sheet_index=fs.get_sheet_index(wb, "monitor_1")-1,
                        path_in=".",
                        path_out=path_pdf_1)
    fs.export_sheet_pdf(sheet_index=fs.get_sheet_index(wb, "monitor_2")-1,
                        path_in=".",
                        path_out=path_pdf_2)
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)
    fs.merge_pdf(path=".\\output\\", output_name="usd_fwd_monitor.pdf")
    fs.delete_file(path_pdf_1)
    fs.delete_file(path_pdf_2)

    # Guardamos backup
    name = "NDF_Monitor_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    src = ".\\output\\usd_fwd_monitor.pdf"
    dst = "L:\\Rates & FX\\fsb\\reporting\\ndf_report_backup\\" + name
    fs.copy_file(src, dst)


def send_mail_report(spot_date):
    '''
    Envia el mail a fernando suarez 1313.
    '''
    subject = "Forward Points Monitor"
    body = "Estimados, adjunto el monitor de puntos forward " + spot_date + ".\nSaludos"
    mail_list = ["fsuarez@credicorpcapital.com", "fsuarez1@uc.cl"]
    path = fs.get_self_path() + "output\\usd_fwd_monitor.pdf"
    paths = [path]
    fs.send_mail_attach(subject=subject,
                        body=body,
                        mails=mail_list,
                        attachment_paths=paths)
    fs.delete_file(path)



# Cerramos posibles instancias de Excel
fs.kill_excel()

print("Starting...")
# Obtenemos las fechas en las que trabaJa
spot_date = fs.get_ndays_from_today(2)
end_date = fs.get_prev_weekday(spot_date)
# end_date = spot_date
#end_date= '2017-12-27'
start_date = "2013-05-16"

print("Fetching curves...")
# Obtenemos las curvas historicas
fwd_curve = fetch_dataset(start_date, end_date, "fwd")
clp_curve = fetch_dataset(start_date, end_date, "clp")
usd_curve = fetch_dataset(start_date, end_date, "usd")
days_dataset = fetch_dataset(start_date, end_date, "days")
bid_dataset = fetch_dataset(start_date, end_date, "bid")
ask_dataset = fetch_dataset(start_date, end_date, "ask")

print("Computing implied curve...")
# Valorizamos la curva swap en fx
implied_curve = compute_implied(clp_curve, fwd_curve)

# Calculamos la diferencia historica entre la curva swap y el valuation
delta_curve = compute_delta(usd_curve, implied_curve)

# Calculamos la media historica de la diferencia swap-valuation
delta_avg = compute_avg(delta_curve)

# Obtenemos la curva del valuation spot
spot_implied_curve = implied_curve.loc[end_date]
fras_matrix_spot = compute_fras_matrix(spot_implied_curve)

# Obtenemos la media y la std dev del cubo de fras historico
mean_fras_matrix, std_fras_matrix = compute_fras_metrics(implied_curve)

# Obtenemos los fras para la curva swap
spot_swap_curve = usd_curve.loc[end_date]
fras_matrix_swap= compute_fras_matrix(spot_swap_curve)


# Calculamos la matriz de con la diferencia entre los fras spot
diff_fras_matrix_spot=compute_diff_fras(fras_matrix_swap, fras_matrix_spot)


# Obtenemos la media y la std de la diferencia entre los fras historicos 
mean_diff_fras_matrix, std_diff_fras_matrix = compute_diff_fras_metrics(implied_curve, usd_curve)


print("Computing long short strategies backtest...")
# Obtenemos el gain-loss de las estrategias long short forward
# Primero definimos los inputs de cada estrategia.
# Por defecto elegimos una ventana de 258 dias maximo
# para una estrategia de 1Y.
n_tenors_1M1Y = 12
short_tenor_1M1Y = "1M"
long_tenor_1M1Y = "12M"
unavailable_days_1M1Y = 258
n_tenors_3M1Y = 4
short_tenor_3M1Y = "3M"
long_tenor_3M1Y = "12M"
unavailable_days_3M1Y = 258


# Ejecutamos el backtesting de las estrategias
gain_loss_1M1Y = compute_gain_loss(n_tenors_1M1Y,
                                   short_tenor_1M1Y,
                                   long_tenor_1M1Y,
                                   unavailable_days_1M1Y,
                                   days_dataset,
                                   bid_dataset,
                                   ask_dataset)


gain_loss_3M1Y = compute_gain_loss(n_tenors_3M1Y,
                                   short_tenor_3M1Y,
                                   long_tenor_3M1Y,
                                   unavailable_days_3M1Y,
                                   days_dataset,
                                   bid_dataset,
                                   ask_dataset)

# Para graficar lass estrategias
# fs.plot_curves(gain_loss_1M1Y["gain_loss"], gain_loss_3M1Y["gain_loss"], gain_loss_1M1Y.index)


print("Printing report...")
# Imprimimos el reporte en exceo
print_report_pdf(end_date,
                 fwd_curve,
                 clp_curve,
                 usd_curve,
                 implied_curve,
                 delta_curve,
                 delta_avg,
                 fras_matrix_spot,
                 mean_fras_matrix,
                 std_fras_matrix,
                 diff_fras_matrix_spot,
                 mean_diff_fras_matrix,
                 std_diff_fras_matrix,
                 fras_matrix_swap,
                 gain_loss_1M1Y,
                 gain_loss_3M1Y
                 )

#print("Sending report...")
# Enviamos el correo
send_mail_report(spot_date)

