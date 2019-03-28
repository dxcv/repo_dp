"""
Created on Wed Dec 28 11:00:00 2016

@author: Fernando Suarez

compile view pyuic5 -x MainView.ui -o MainView.py
"""

import sys
sys.path.insert(0, '../../libreria/')
import libreria_fdo as fs
sys.path.insert(1, '../risk_library/')
from PyQt5 import QtCore, QtWidgets, QtGui
import risk as rk
import MainView as MainView
import numpy as np
import pandas as pd

# Esta variable es global y se utiliza para tener en memoria el portfolio por instrumento con toda su informacion 
portfolio_detailed = None


def insert_data_frame_into_table_widget(data_as_frame, table_widget):
    '''
    Inserta un dataframe en un table widget.
    '''
    table_widget.setSortingEnabled(False)
    table_widget.clearContents()
    table_widget.setColumnCount(len(data_as_frame.columns))
    table_widget.setRowCount(len(data_as_frame.index))
    table_widget.setHorizontalHeaderLabels(data_as_frame.columns)
    for i in range(len(data_as_frame.index)):
        for j in range(len(data_as_frame.columns)):
            item = QtWidgets.QTableWidgetItem()
            data = str(data_as_frame.iat[i,j])
            item.setData(QtCore.Qt.DisplayRole, data)
            table_widget.setItem(i, j, item)
    table_widget.setSortingEnabled(True)

def combination_changed():
    '''
    Evento asociado a un cambio de fecha o fondo. Cada vez que se gatilla 
    se carga un nuevo portfolio y se despliega el summary con sus metricas.
    '''
    load_portfolio()
    compute_summary()
    compute_metrics()

def compute_summary():
    '''
    Agrupa el portfolio por grandes clases de activos y lo 
    formatea para desplegar en pantalla. 
    '''
    global portfolio_detailed
    portfolio_diplay = format_portfolio_summary(portfolio = portfolio_detailed)
    insert_data_frame_into_table_widget(portfolio_diplay, ui.tableWidget_summary)
    header = ui.tableWidget_summary.horizontalHeader()
    for i in range(9):
        header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
    ui.tableWidget_summary.setHorizontalHeader(header)


def format_portfolio_summary(portfolio):  
    '''
    Agrupa y formatea el dataframe del portfolio por clase de activo 
    para el display en la interfaz. 
    '''
    portfolio_formated = portfolio[["instrument_type", "currency", "weight_port", "active_weight", "mkt_val", "ctd", "cty", "ctr", "pcr"]].groupby(by = ["instrument_type", "currency"], as_index = False).sum()
    portfolio_formated = portfolio_formated.round(4)
    portfolio_formated["weight_port"] = (portfolio_formated["weight_port"]*100).astype(str) + "%"
    portfolio_formated["active_weight"] = (portfolio_formated["active_weight"]*100).astype(str) + "%"
    portfolio_formated["cty"] = (portfolio_formated["cty"]*100).astype(str) + "%"
    portfolio_formated["pcr"] = (portfolio_formated["pcr"]*100).astype(str) + "%"
    portfolio_formated["ctr"] = (portfolio_formated["ctr"]*100).astype(str) + "%"
    portfolio_formated["mkt_val"].fillna(0.0)
    portfolio_formated["mkt_val"] = portfolio_formated["mkt_val"].apply(int)
    portfolio_formated["mkt_val"] = portfolio_formated["mkt_val"].apply(fs.format_separators)
    return portfolio_formated

def load_portfolio():
    '''
    Dados los inputs del usuario, obtiene el portfolio activo y lo carga en memoria. 
    '''
    global portfolio_detailed
    spot_date = str(ui.calendarWidget_fecha_spot.selectedDate().toPyDate())
    # Fijamos la fecha para la cual se tomara el vector de weights de los portafolios
    fund_date = fs.get_prev_weekday(spot_date)
    # Fijamos la fecha para la cual se tomara el vector de weights de los benchmarks
    benchmark_date = fs.get_prev_weekday(fund_date)
    # Fijamos la fecha para la cual se tomara el ultimo dato para la matriz de varianza-covarianza
    days_last_value = len(fs.get_weekdays_dates_between(spot_date, data_end_date)) - 1
    # Sacamos la inflacion
    inflation = rk.get_inflation(start_date=benchmark_date, end_date=fund_date)
    matrix = rk.get_ewma_cov_matrix(data=dataset[days_last_value:], landa=0.94)
    fund_id = str(ui.comboBox_codigo_fdo.currentText())
    benchmark_id = int(funds[funds["codigo_fdo"] == fund_id]["benchmark_id"])
    alpha_seeker = int(funds[funds["codigo_fdo"] == fund_id]["alpha_seeker"])
    fund_portfolio = rk.get_portfolio(fund_date=fund_date, fund_id=fund_id, inflation=inflation)
    benchmark_portfolio = rk.get_portfolio_bmk(benchmark_date=benchmark_date, benchmark_id=benchmark_id)
    try:
        portfolio = rk.get_portfolio_metrics(fund_portfolio=fund_portfolio,
                                             benchmark_portfolio=benchmark_portfolio,
                                             fund_id=fund_id, matrix=matrix,
                                             benchmark_id=benchmark_id,
                                             alpha_seeker=alpha_seeker) 
        portfolio = portfolio.reindex(columns=["codigo_emi","codigo_ins", "weight_x","weight_y","weight_active",
                                               "monto","nominal", "precio","duration_x","ctd", "cty", "ctr","mcr_x",
                                               "pcr", "tasa_x", "tipo_instrumento_x", "riesgo_x","fec_vtco","moneda_x",
                                               "nombre_emisor_x","nombre_instrumento", "pais_emisor_x","sector_x",
                                               "riesgo_internacional_x"])
        portfolio.rename(columns={"weight_x": "weight_port", "weight_y": "weight_bmk", 
        "duration_x": "duration", "mcr_x": "mcr", "tipo_instrumento_x": "instrument_type", "riesgo_x": "rating", 
        "moneda_x": "currency", "sector_x": "sector", "weight_active": "active_weight", "tasa_x": "yield", 
        "riesgo_internacional_x": "international_rating", "pais_emisor_x": "issuer_country", "nombre_emisor_x": "issuer_name", 
        "nombre_instrumento": "instrument_name", "fec_vtco": "maturity_date", "monto": "mkt_val"}, inplace=True)
        portfolio["ctr"] = portfolio["ctr"].astype(float)
        portfolio["pcr"] = portfolio["pcr"].astype(float)
        portfolio["mkt_val"] = portfolio["mkt_val"].astype(float)
        portfolio["ctd"] = portfolio["ctd"].astype(float)
        portfolio["cty"] = portfolio["cty"].astype(float)
        portfolio["yield"] = portfolio["yield"].astype(float)
        portfolio["days_to_maturity"] = (pd.to_datetime(portfolio["maturity_date"] ) - fs.convert_string_to_date(spot_date)).astype('timedelta64[D]')
    except:
        print("Error on " + fund_date)
    portfolio_detailed = portfolio


def compute_metrics():  
    '''
    Calcula el aum, tracking error y duracion del fondo para desplegar en la interfaz. 
    '''
    global portfolio_detailed
    portfolio_display = portfolio_detailed
    portfolio_display = portfolio_display.round(7)
    dur = str(np.sum(portfolio_display["ctd"]))
    dur = fs.truncate(f = dur, n = 3)
    te = np.sum(portfolio_display["ctr"])*100
    te = str(fs.truncate(f = te, n = 3)) + "%"
    aum = fs.format_separators(int(np.sum(portfolio_display["mkt_val"]))) + " $"
    yld = np.sum(portfolio_display["cty"])*100
    yld = str(fs.truncate(f = yld, n = 3)) + "%"
    ui.label_dur.setText(dur)
    ui.label_te.setText(te)
    ui.label_aum.setText(aum)
    ui.label_yield.setText(yld)


def compute_details():
    '''
    Formatea  y despliega el detalle del portafolio. 
    '''
    global portfolio_detailed
    portfolio_diplay = portfolio_detailed
    portfolio_diplay = format_portfolio_detailed(portfolio = portfolio_diplay)
    insert_data_frame_into_table_widget(portfolio_diplay, ui.tableWidget_summary)
    header = ui.tableWidget_summary.horizontalHeader()
    for i in range(24):
        header.setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
    header.setDefaultSectionSize(150)
    ui.tableWidget_summary.setHorizontalHeader(header)

def format_portfolio_detailed(portfolio):  
    '''
    Formatea el dataframe del portfolio detallado para el display en la interfaz. 
    '''
    portfolio_formated = portfolio
    portfolio_formated.sort_values(["maturity_date"], inplace=True, ascending=[True])
    portfolio_formated = portfolio_formated.round(4)
    portfolio_formated["weight_port"] = (portfolio_formated["weight_port"]*100).astype(str) + "%"
    portfolio_formated["weight_bmk"] = (portfolio_formated["weight_bmk"]*100).astype(str) + "%"
    portfolio_formated["mcr"] = (portfolio_formated["mcr"]).astype(str) + "%"
    portfolio_formated["active_weight"] = (portfolio_formated["active_weight"]*100).astype(str) + "%"
    portfolio_formated["cty"] = (portfolio_formated["cty"]*100).astype(str) + "%"
    portfolio_formated["pcr"] = (portfolio_formated["pcr"]*100).astype(str) + "%"
    portfolio_formated["ctr"] = (portfolio_formated["ctr"]*100).astype(str) + "%"
    portfolio_formated["mkt_val"] = portfolio_formated["mkt_val"].fillna(0.0)
    portfolio_formated["mkt_val"] = portfolio_formated["mkt_val"].apply(int)
    portfolio_formated["mkt_val"] = portfolio_formated["mkt_val"].apply(fs.format_separators)
    portfolio_formated["yield"] = (portfolio_formated["yield"]*100).astype(str) + "%"
    return portfolio_formated

def export_portfolio_excel():
    '''
    Exporta el portfolio a excel. 
    '''
    global portfolio_detailed
    file_path = fs.get_file_path_ui(default_name="portfolio.xlsx", extension=".xlsx")
    wb = fs.create_workbook()
    fs.paste_val_xl(wb=wb, sheet="Hoja1", row=1, column=1,value=portfolio_detailed)
    fs.save_workbook(wb, path=file_path)
    fs.close_workbook(wb=wb)

# Fijamos la fecha en la que empieza el dataset de la matriz de varianza covarianza
data_start_date = "2016-01-01"
data_end_date = fs.get_ndays_from_today(0)

# Obtenemos el dataset con toda la informacion historica
dataset = rk.get_historical_dataset(data_start_date=data_start_date,
                                    data_end_date= data_end_date)

# Seteamos la interfaz
app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ui = MainView.Ui_MainWindow()
ui.setupUi(MainWindow)
# Agregamos los fondos a la combobox
funds = rk.get_funds()
ui.comboBox_codigo_fdo.addItems(funds["codigo_fdo"])
# Mapeamos los eventos correspondientes
ui.comboBox_codigo_fdo.currentIndexChanged[str].connect(combination_changed)
ui.calendarWidget_fecha_spot.selectionChanged.connect(combination_changed)
ui.pushButton_detailed.clicked.connect(compute_details)
ui.pushButton_summary.clicked.connect(compute_summary)
ui.pushButton_excel.clicked.connect(export_portfolio_excel)
# Llamada inicial para poblar tabla
load_portfolio()
compute_summary()
compute_metrics()
# Desplegamos la ventana principal
stylesheet = "::section{Background-color:rgb(75, 75, 75);}"
ui.tableWidget_summary.horizontalHeader().setStyleSheet(stylesheet)
ui.tableWidget_summary.verticalHeader().setStyleSheet(stylesheet)
# MainWindow.showMaximized()
MainWindow.show()
MainWindow.activateWindow()
sys.exit(app.exec_())
