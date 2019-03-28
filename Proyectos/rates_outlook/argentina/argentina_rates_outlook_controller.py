"""
Created on Fri Oct 13 11:00:00 2017

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, "../../libreria/")
import libreria_fdo as fs
sys.path.insert(1, "../library/")
import curve_tools as ct
import pandas as pd
import numpy as np
from scipy import optimize
from tia.bbg import v3api
import datetime as dt
# Para desabilitar warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=FutureWarning)
pd.options.mode.chained_assignment = None 


wb = fs.open_workbook(".\\inputs.xlsx", True, True)
curve_members = fs.get_frame_xl(wb, "lebacs", 1, 1, [0])

curve = curve_members[["yield", "tenor_days"]]
curve.set_index(["tenor_days"], inplace=True)
curve = curve.sort_index()
days = curve.index[-1]
days = np.arange(days) + 1
curve = curve.reindex(days)
curve = curve.interpolate(method="pchip")
curve = ct.compute_zero_implied_tpm(curve)
print(curve)
fs.plot_curves([curve["implied_tpm"], curve["zero_curve"], curve["forward_rate"]])