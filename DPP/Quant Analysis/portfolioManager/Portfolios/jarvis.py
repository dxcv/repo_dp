# -*- coding: utf-8 -*-
"""
Created on Mon Sep 05 19:18:04 2016

@author: ngoldbergerr
"""

from highway import portClas

port = portClas()

view, portfolio = port.getBasicView('MACRO 1.5')
port.uploadPortfolioAttributesToDB(view,'MACRO 1.5')

view, portfolio = port.getBasicView('MACRO CLP3')
port.uploadPortfolioAttributesToDB(view,'MACRO CLP3')

view, portfolio = port.getBasicView('IMT E-PLUS')
port.uploadPortfolioAttributesToDB(view,'IMT E-PLUS')

view, portfolio = port.getBasicView('RENTA')
port.uploadPortfolioAttributesToDB(view,'RENTA')