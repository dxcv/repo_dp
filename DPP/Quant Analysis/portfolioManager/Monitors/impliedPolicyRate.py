# -*- coding: utf-8 -*-
"""
Created on Fri Aug 12 10:41:06 2016

@author: ngoldbergerr
"""

import sys
from tia.bbg import v3api
import pandas as pd
import xlrd
import os.path
import datetime as dt
import numpy as np

class impliedRate(object):

    def __init__(self, path = 'L:\\Rates & FX\\Quant Analysis\\portfolioManager\\Monitors\\'):
        self.XLpath = path

    def getLocalCurveInstrumentsFromBBG(self, country = 'CL'):
        countryDict = {'CL': 'YCSW0193 Index'}
        bbg_tickers = [countryDict['CL']]
        
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        try:
            response = LocalTerminal.get_reference_data(bbg_tickers, ['curve_tenor_rates'], ignore_security_error = 1, ignore_field_error = 1)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False
# 'DAYS_TO_MTY_TDY'
        curve_instruments = pd.DataFrame(response.as_frame()['curve_tenor_rates'].values[0])
        curve = pd.DataFrame(curve_instruments['Mid Yield'][1:6])
        curve.columns = ['Swap Rate']
#        curve.index = curve_instruments.Tenor[1:]
        curve.index = [(dt.datetime.today()+dt.timedelta(days=(LocalTerminal.get_reference_data(curve_instruments['Tenor Ticker'][j],['DAYS_TO_MTY_TDY'], ignore_security_error = 1, ignore_field_error = 1).as_frame()['DAYS_TO_MTY_TDY'][0]).astype(np.int32))) for j in range(1,len(curve)+1)]
        return curve

    def getMeetingDatesAndRates(self):
        wb = xlrd.open_workbook(os.path.join(self.XLpath,'impliedPolicyRate.xlsx'))
        sh = wb.sheet_by_index(0)
        dTPM= self.get_cell_range(sh,0,0,0,30)
        datesTPM = [xlrd.xldate.xldate_as_datetime(x[0].value, wb.datemode) for x in dTPM]
        tasa_camara = [self.getTPM('CL')]*len(dTPM)
        out = pd.DataFrame(tasa_camara, index=datesTPM)
        out.columns = ['Tasa Esperada']
        out['Days'] = 0
        out['Days'][1:] = [int((out.index[i] - out.index[i-1]).days) for i in range(1,len(out))]
        return out

    def getTPM(self, country = 'CL'):
        countryDict = {'CL': 'CHOVCHOV Index'}
        bbg_tickers = [countryDict['CL']]
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        response = LocalTerminal.get_reference_data(bbg_tickers, ['PX_LAST'], ignore_security_error = 1, ignore_field_error = 1)
        return response.as_frame().values[0][0]

    def get_cell_range(self,sheet, start_col, start_row, end_col, end_row):
        return [sheet.row_slice(row, start_colx=start_col, end_colx=end_col+1) for row in xrange(start_row, end_row+1)]       
        
if __name__ == '__main__':
    ir = impliedRate()
    camara = ir.getMeetingDatesAndRates()
    market = ir.getLocalCurveInstrumentsFromBBG()
    
    
    
    
    
    
    
    
    
    
    