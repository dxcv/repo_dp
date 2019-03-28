
import sys
import numpy as np
import xlwings as xw
import libreria_fdo as fs







print("hola")
wb = fs.open_workbook(".\\prueba.xlsx", True, True)
# Obtenemos los paths de tom
miframe = fs.get_frame_xl(wb, "numeros", 1, 1, [0])
miframe["cum"]=miframe["holav"].cumsum()
print(miframe)