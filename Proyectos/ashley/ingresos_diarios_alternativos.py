"""
Created on Wed Nov 22 11:00:00 2017

@author: Ashley Mac Gregor
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import datetime as dt





def get_patrimonio_diario(path, fec_inicio, fec_hoy):
    '''
    Lee el query de patrimonio diario de alternativos, y lo transforma en dataframe
    '''

    patrimonio_query = fs.read_file(path=path)
    patrimonio_query = patrimonio_query.replace("autodate1", fec_hoy)
    patrimonio_query = patrimonio_query.replace("autodate", fec_inicio)
    patrimonio_diario_alternativos = fs.get_frame_sql_user(server="Puyehue",
                                           database="MesaInversiones",
                                           username="usrConsultaComercial",
                                           password="Comercial1w",
                                           query=patrimonio_query)
    return patrimonio_diario_alternativos




fec_inicio = str(dt.datetime.strptime(fs.get_ndays_from_today(365), '%Y-%m-%d'))
fec_hoy = str(dt.datetime.strptime(fs.get_ndays_from_today(0), '%Y-%m-%d'))
path = ".\\input reporte gestion alternativos\\patrimonio_alternativos.sql"

print(get_patrimonio_diario(path, fec_inicio, fec_hoy))

