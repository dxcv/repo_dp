# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 14:07:40 2016

@author: ngoldbergerr
"""

import pandas
import numpy as np
import bloomberg as bbg
import statsmodels.tsa.api as sm
import datetime as dt

b = bbg.bloomberg()

# Analizando el comportamiento entre los puntos de la curva
#ratesData = b.getHistDataFromBloomberg(['PES02 Index','PES05 Index','PES07 Index','PES10 Index'], init = dt.datetime(2013,12,20), end = dt.datetime(2016,12,20))

#data = ratesData.diff().dropna()

#model = sm.VAR(data)

#results = model.fit(1)
#results.summary()
#results.plot()
#results.plot_acorr()
#model.select_order(15)
#results = model.fit(maxlags=15, ic='aic')
#lag_order = results.k_ar
#results.forecast(data.values[-lag_order:], 5)
#
#irf = results.irf(5)
#irf.plot(orth=False)
#irf.plot(response='PES10 Index')
#irf.plot_cum_effects(orth=False)
#
#results.test_causality('PES10 Index', ['PES05 Index', 'PES07 Index','PES02 Index'], kind='f')
#
#var = sm.DynamicVAR(data, lag_order=2, window_type='expanding')
#var.coefs
#var.forecast(2)
#var.plot_forecast(2)

# Analizando el impacto de la TPM sobre la curva

tpmRatesData = b.getHistDataFromBloomberg(['CHOVCHOV Index','PES02 Index','PES05 Index','PES07 Index','PES10 Index'], init = dt.datetime(2006,12,20), end = dt.datetime(2016,12,20), freq = 'MONTHLY')

data = tpmRatesData.diff().dropna()

model = sm.VAR(data)
results = model.fit(1)
results.summary()
irf = results.irf(10)
irf.plot(impulse='CHOVCHOV Index')
irf.plot_cum_effects(orth=False)
irf.plot_cum_effects(impulse='CHOVCHOV Index')
results.test_causality('PES10 Index', ['CHOVCHOV Index'], kind='f')
