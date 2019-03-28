import sys
sys.path.insert(0, '../portfolio_analytics/utiles')
sys.path.insert(0, "../libreria")

import libreria_fdo as fs
import utiles as utiles
import pandas as pd
import numpy as np
import datetime as dt
from win32com import client
import win32com.client
import vencimientos
import trades
import carry
import gobierno_mtm

funds = utiles.get_FI_funds()
rf_portfolio = utiles.get_updated_RFI(funds)
iif_portolio = utiles.get_updated_IIF(funds)
print(iif_portolio)
exit()
today = fs.get_ndays_from_today(2)
weight_min = 0
fondos, df_vencimientos_forwards, rf, fwd, df_forwards_expirations = vencimientos.get_vencimientos(today, weight_min)
fs.print_full(fondos)
fs.print_full(df_vencimientos_forwards)
fs.print_full(rf)
fs.print_full(fwd)
fs.print_full(df_forwards_expirations)
df_iif_trades = trades.iif(today)
print(df_iif_trades)
irf_trades = trades.irf(today)
print(irf_trades)
carry = carry.get_funds_carry(today)
govt_mtm = gobierno_mtm.get_govt_rates(today)
print(govt_mtm)

wb = fs.open_workbook("reporte_diario.xlsx", True, True)
fs.clear_sheet_xl(wb, "summary")
fs.paste_val_xl(wb, "summary", 3, 2, rf[1])
fs.paste_val_xl(wb, "summary", 3, 7, fwd[1])
fs.paste_val_xl(wb, "summary", 3, 15, carry)
fs.paste_val_xl(wb, "summary", 3, 23, df_iif_trades)
fs.paste_val_xl(wb, "summary", 3, 28, irf_trades)
fs.paste_val_xl(wb, "summary", 3, 35, govt_mtm)












