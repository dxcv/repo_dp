# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 17:59:50 2016

@author: ngoldbergerr
"""

import sys
#import pandas as pd
import numpy as np
import datetime as dt
#from tia.bbg import LocalTerminal
from tia.bbg import v3api

class bloomberg(object):
    
    def __init__(self):
        self.x = 0


    def getHistDataFromBloomberg(self, tickers, init = None, end = None, freq = 'DAILY'):
        if not init:
            init = dt.datetime.today()-dt.timedelta(weeks=52)
            dt.datetime.today()-dt.timedelta(days=1)
            
        LocalTerminal = v3api.Terminal('localhost', 8194)        
        try:
            response = LocalTerminal.get_historical(tickers, ['PX_LAST'], ignore_security_error=1, ignore_field_error=1, start = init, end = end, period = freq)
        except:
            print("Unexpected error:", sys.exc_info()[0])   
            return False

        bloombergData = response.as_frame()
        bloombergData.columns = bloombergData.columns.levels[0]
        
        return bloombergData
    
    def getDataFromBloomberg(self,tickers,fields):
        
        LocalTerminal = v3api.Terminal('localhost', 8194)  
        response = LocalTerminal.get_reference_data(tickers, fields, ignore_security_error = 1, ignore_field_error = 1)
#            return response.as_frame()
            
        bloombergData = response.as_frame()
        bloombergData.columns = bloombergData.columns.levels[0]        
        return bloombergData
    
if __name__ == '__main__':
    b = bloomberg()
    spx = b.getHistDataFromBloomberg('SPX Index')