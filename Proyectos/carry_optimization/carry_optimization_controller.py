"""
Created on Tue Mar 14 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from numpy.linalg import solve


wb = fs.open_workbook("tasasiif.xlsx", True, True)
caps = fs.get_table_xl(wb, "Input", 2, 2)[0][1:]
schema = fs.get_table_xl(wb, "Input", 1, 2)[0]
raw_table = fs.get_table_xl(wb, "Input", 3, 2)
fs.close_excel(wb)
dataset = pd.DataFrame(raw_table, columns=schema)
dataset.set_index(["duration"], inplace=True)
print(dataset)
A_eq = []
A_ub = []
b_eq = [1.0]
b_ub = []
c = []
dur_eq = []
for i, data in dataset.iterrows():
	for bank in schema[1:]:
		A_eq.append(1.0)
		dur_eq.append(i)
		c.append(float(data[bank]))


col_ind = 0
for cap in caps:
	cap_eq = [0.0] * (len(caps) * len(raw_table))
	row_ind = 0
	for i, data in dataset.iterrows():
		cap_eq[row_ind*len(caps) + col_ind] = 1
		row_ind += 1
	col_ind += 1
	A_ub.append(cap_eq)
	b_ub.append(cap)




A_ub.append(dur_eq)
b_ub.append(90)

A_eq = np.array([A_eq])
b_eq = np.array(b_eq)
A_ub = np.array(A_ub)
b_ub = np.array(b_ub)
c = np.array(c)

res = linprog(-c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=(0, None))
print('Optimal value:', res.fun, '\nX:', res.x)


ncol = len(schema[1:])
result = []
for i in range(len(res.x)):
	if(i*ncol == 260):
		break
	res_row = []
	for j in range(ncol):
		res_row.append(res.x[(i*ncol)+j])
	result.append(res_row)


result = pd.DataFrame(data= result, columns=schema[1:])


wb = fs.open_workbook("tasasiif.xlsx", True, True)
fs.clear_sheet_xl(wb, "Output")
fs.paste_val_xl(wb, "Output", 1, 1, result)

