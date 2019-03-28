# -*- coding: utf-8 -*-
"""
Created on Tue Apr 05 11:31:38 2016

author: goldbena
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tia.bbg import LocalTerminal
from matplotlib import rc
rc('mathtext', default='regular')
from sklearn.decomposition import PCA


class fragility(object):

    def __init__(self, idx = ['eurusd curncy', 'audusd curncy','cadusd curncy','jpyusd curncy','brlusd curncy']):
        self.idx = idx
        
    def downloadData(self,tw):
        self.tw = tw
        self.d = pd.datetools.BDay(-self.tw).apply(pd.datetime.now())
        self.m = pd.datetools.BMonthBegin(-2).apply(pd.datetime.now())
        self.response = LocalTerminal.get_historical(self.idx, ['px_last'], start=self.d)

    def getReturns(self,prices, freq = 1):
        x = {}
        x['price'] = prices
        x['returns'] = (np.log(x['price']) - np.log(x['price'].shift(freq))).fillna(0)
        x['pct_chg'] = (x['price'].pct_change()).fillna(0)
        return x
    
    def getAbsorptionRatio(self, x, nFactors):
        self.pca = PCA()
        self.pca.fit_transform(x.fillna(0))
#        self.components = pd.DataFrame(self.pca.components_.T, index = x.columns)
        variance = pd.DataFrame(self.pca.explained_variance_ratio_)
#        return components, variance
        return np.sum(variance[0][0:nFactors])

    def graph(self,data):
        t = [pd.datetools.BDay(-i).apply(pd.datetime.now()) for i in range(len(data))]
        t.reverse()
        fig, ax1 = plt.subplots(1,1,figsize=(10,6))
        ax1.plot(t,data, color = [0.90625,0.48828125,0.1171875])   
        ax1.set_xlabel('Fechas', fontsize = 14)
        ax1.set_ylabel('Ratio de Absorcion', fontsize = 14)
        ax1.set_title('Fragilidad Mercado Global', fontsize = 16)
        ax1.xaxis.set_tick_params(labelsize=12)
        ax1.yaxis.set_tick_params(labelsize=12)
        fig.autofmt_xdate(rotation=0, ha= 'center')
        fig.tight_layout()

    def computeFragilityAndPlot(self,nFactors, freq):
        df = self.getReturns(self.response.as_frame(),freq)
        self.nFactors = nFactors 
        self.fragilityRollingData = self.getRollingFragilityData(df,nFactors)
        self.graph(self.fragilityRollingData)
        return self.fragilityRollingData
        
    def getRollingFragilityData(self, df, nFactors, rollingWindow = 251):
        data = []
        for i in range(0,len(df['returns'])-rollingWindow):
            try:
                data.append(self.getAbsorptionRatio(df['returns'][0+i:rollingWindow+i],nFactors))   
            except:
                print('There was an error while trying to compute the fragility')
                pass
        return data

if __name__ == '__main__':  
    idx= ['BUSG Index','BUHY Index','BUSC Index','BNDX Index','CRY Index',
          'SPX Index','BGER Index','BERC Index','BEUH Index','DAX Index',
          'BJPN Index','BJPY Index','NKY Index','BRIT Index','BGBP Index',
          'BGBH Index','UKX Index','BAUS Index','BAUD Index','AS51 Index',
          'BEMS Index','BIEM Index','BEAC Index','VEIEX US Equity']
#    idx = ['RIAMIU30 Index','RIAMIIA1 Index','RIAMI130 Index','RIAMI270 Index',
#    'RIAMIT2Y Index','RIAMIU15 Index','RIAMI160 Index','RIAMI11Y Index','RIAMIU1Y Index',
#    'RIAMIU12 Index','RIAMI120 Index','RIAMIU60 Index','RIAMI150 Index','RIAMIU90 Index',
#    'RIAMIU18 Index','RIAMI107 Index','RIAMIU07 Index','RIAMI180 Index','RIAMIU27 Index',
#    'RIAMI190 Index','RIAM1275 Index','RIAM1259 Index','RIAM1280 Index','RIAM1284 Index',
#    'RIAM1289 Index','RIAM1266 Index','RIAM1290 Index','RIAM1265 Index','RIAM1279 Index',
#    'RIAM1282 Index','RIAM1273 Index','RIAM1293 Index','RIAM1281 Index','RIAM1294 Index',
#    'RIAM1260 Index','RIAM1263 Index','RIAM1278 Index','RIAM1262 Index','RIAM1261 Index',
#    'RIAM1283 Index','RIAM1274 Index','RIAM1296 Index','RIAM1295 Index','RIAM1287 Index',
#    'RIAM1292 Index','RIAM1297 Index','RIAM1291 Index','RIAM1286 Index','RIAM1298 Index',
#    'RIAM1276 Index','RIAM1264 Index','RIAMBU04 Index','RIAMBU03 Index','RIAMBP04 Index',
#    'RIAMBU10 Index','RIAMBU20 Index','RIAMBP20 Index','RIAMBU30 Index','RIAMBU05 Index',
#    'RIAMBP03 Index','RIAMBP05 Index','RIAMBP30 Index','RIAMBU02 Index','RIAMBP10 Index',
#    'RIAMBP02 Index','RIAMBU07 Index','RIAMBP07 Index','RIAM0AC7 Index','RIAMBBB8 Index',
#    'RIAMBBB2 Index','RIAM0AC2 Index','RIAMBBB5 Index','RIAM0AC5 Index','RIAM0AC8 Index',
#    'RIAM0AC3 Index','RIAMBBB7 Index','RIAMBBB3 Index']
#    idx = ['LUATTRUU Index','LD08TRUU Index','LUACTRUU Index','LUMSTRUU Index','LBEATREU Index',
#           'LAPCTRJU Index','LF98TRUU Index','LP01TREU Index','EMUSTRUU  Index','SPX Index',
#           'DAX Index','SHSZ300 Index']
#    idx = ['AUDUSD Curncy', 'BRLUSD Curncy', 'CADUSD Curncy', 'CHFUSD Curncy', 'CLPUSD Curncy', 
#           'CNHUSD Curncy', 'COPUSD Curncy', 'DKKUSD Curncy', 'EURUSD Curncy', 'GBPUSD Curncy', 
#           'JPYUSD Curncy', 'KRWUSD Curncy', 'MXNUSD Curncy', 'NOKUSD Curncy', 'NZDUSD Curncy', 
#           'PLNUSD Curncy', 'SEKUSD Curncy', 'PENUSD Curncy', 'ZARUSD Curncy', 'TRYUSD Curncy']
    frag = fragility(idx)
    frag.downloadData(1000)
    rollData = frag.computeFragilityAndPlot(2,1)