"""
Created on Mon Feb 15 09:36:51 2016

author: goldbena
"""

import datetime
import numpy as np
import pandas as pd
from tia.bbg import LocalTerminal
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from sklearn import cluster, covariance, manifold
import FXClas

 
class marketStructure(object):
    
    def __init__(self, assets = ['eurusd curncy', 'audusd curncy','cadusd curncy','jpyusd curncy','brlusd curncy']):
        self.assets = assets

    def downloadData(self,tw):
        self.tw = tw
        self.d = pd.datetools.BDay(-self.tw).apply(pd.datetime.now())
        self.m = pd.datetools.BMonthBegin(2).apply(pd.datetime.now())
        self.prices = LocalTerminal.get_historical(self.assets, ['PX_LAST'], start=self.d)
        self.names = LocalTerminal.get_reference_data(idx, ['SHORT_NAME'])
        return True
        
    def getReturns(self,prices, freq = 1):
        x = {}
        x['price'] = prices
        x['returns'] = (np.log(x['price']) - np.log(x['price'].shift(freq))).fillna(0).values
        x['pct_chg'] = (x['price'].pct_change()).fillna(0).values
        return x
        
    def learnGraphStructure(self):
        self.edge_model = covariance.GraphLassoCV()
        # standardize the time series: using correlations rather than covariance
        # is more efficient for structure recovery
#        data = self.getReturns(self.prices.as_frame())
        fx = FXClas.fxData()
        self._X = fx.getCurrencyBasketFromDB(currencies = None, periodicity = 'monthly', fxRisk = None)
#        self.X = data['returns']
        self._X /= self._X.std(axis=0)
        self.names = self._X.columns
        self.edge_model.fit(self._X.fillna(np.mean(self._X), inplace = True))
        
    def createClusters(self):
        # Cluster using affinity propagation
        _, self.labels = cluster.affinity_propagation(self.edge_model.covariance_)
        self.n_labels = self.labels.max()
        for i in range(self.n_labels + 1):
#            print('Cluster %i: %s' % ((i + 1), ', '.join(self.names.as_frame()['SHORT_NAME'][self.labels == i])))
            print('Cluster %i: %s' % ((i + 1), ', '.join(self.names[self.labels == i])))

    def generateVisualization(self):
        # Find a low-dimension embedding for visualization: find the best position of
        # the nodes (the stocks) on a 2D plane  
        # We use a dense eigen_solver to achieve reproducibility (arpack is
        # initiated with random vectors that we don't control). In addition, we
        # use a large number of neighbors to capture the large-scale structure.
        node_position_model = manifold.LocallyLinearEmbedding(
            n_components=2, eigen_solver='dense', n_neighbors=5)
        
        embedding = node_position_model.fit_transform(self._X.T).T 
        # Visualization
        plt.figure(1, facecolor='w', figsize=(10, 8))
        plt.clf()
        ax = plt.axes([0., 0., 1., 1.])
        plt.axis('off')
        
        # Display a graph of the partial correlations
        partial_correlations = self.edge_model.precision_.copy()
        d = 1 / np.sqrt(np.diag(partial_correlations))
        partial_correlations *= d
        partial_correlations *= d[:, np.newaxis]
        non_zero = (np.abs(np.triu(partial_correlations, k=1)) > 0.02)
        
        # Plot the nodes using the coordinates of our embedding
        plt.scatter(embedding[0], embedding[1], s=100 * d ** 2, c=self.labels,
                    cmap=plt.cm.rainbow)
        
        # Plot the edges
        start_idx, end_idx = np.where(non_zero)
        #a sequence of (*line0*, *line1*, *line2*), where::
        #            linen = (x0, y0), (x1, y1), ... (xm, ym)
        segments = [[embedding[:, start], embedding[:, stop]]
                    for start, stop in zip(start_idx, end_idx)]
        values = np.abs(partial_correlations[non_zero])
        lc = LineCollection(segments,
                            zorder=0, cmap=plt.cm.binary,
                            norm=plt.Normalize(0, .7 * values.max()))
        lc.set_array(values)
        lc.set_linewidths(15 * values)
        ax.add_collection(lc)
        
        # Add a label to each node. The challenge here is that we want to
        # position the labels to avoid overlap with other labels
        for index, (name, label, (x, y)) in enumerate(
#                zip(stx.names.as_frame()['SHORT_NAME'], self.labels, embedding.T)):
            zip(stx.names, self.labels, embedding.T)):
        
            dx = x - embedding[0]
            dx[index] = 1
            dy = y - embedding[1]
            dy[index] = 1
            this_dx = dx[np.argmin(np.abs(dy))]
            this_dy = dy[np.argmin(np.abs(dx))]
            if this_dx > 0:
                horizontalalignment = 'left'
                x = x + .002
            else:
                horizontalalignment = 'right'
                x = x - .002
            if this_dy > 0:
                verticalalignment = 'bottom'
                y = y + .002
            else:
                verticalalignment = 'top'
                y = y - .002
            plt.text(x, y, name, size=20,
                     horizontalalignment=horizontalalignment,
                     verticalalignment=verticalalignment)
#                     bbox=dict(facecolor='w',
#                               edgecolor=plt.cm.spectral(label / float(self.n_labels)),
#                               alpha=.6))
        
        plt.xlim(embedding[0].min() - .15 * embedding[0].ptp(),
                 embedding[0].max() + .10 * embedding[0].ptp(),)
        plt.ylim(embedding[1].min() - .03 * embedding[1].ptp(),
                 embedding[1].max() + .03 * embedding[1].ptp())
        
        plt.show()

if __name__ == '__main__':  

#    idx= ['BUSG Index','BUHY Index','BUSC Index','CRY Index',
#          'SPX Index','BGER Index','BERC Index','BEUH Index','DAX Index',
#          'BJPN Index','BJPY Index','NKY Index','BRIT Index','BGBP Index',
#          'BGBH Index','UKX Index','BAUS Index','BAUD Index','AS51 Index',
#          'BEMS Index','BIEM Index','BEAC Index','VEIEX US Equity','VIX Index']
#    idx = ['eurusd curncy', 'cadusd curncy', 'audusd curncy', 'gbpusd curncy',
#           'jpyusd curncy', 'dkkusd curncy', 'sekusd curncy', 'nokusd curncy',
#           'brlusd curncy', 'mxnusd curncy', 'clpusd curncy', 'copusd curncy',
#           'cnyusd curncy', 'myrusd curncy', 'krwusd curncy', 'sgdusd curncy',
#           'zarusd curncy', 'plnusd curncy', 'czkusd curncy', 'thbusd curncy',
#           'penusd curncy']
    idx = ['EURCLP curncy', 'CADCLP curncy', 'AUDCLP curncy', 'GBPCLP curncy',
           'JPYCLP curncy', 'DKKCLP curncy', 'SEKCLP curncy', 'NOKCLP curncy',
           'BRLCLP curncy', 'MXNCLP curncy', 'USDCLP curncy', 'COPCLP curncy',
           'CNYCLP curncy', 'MYRCLP curncy', 'KRWCLP curncy', 'SGDCLP curncy',
           'ZARCLP curncy', 'PLNCLP curncy', 'CZKCLP curncy', 'THBCLP curncy',
           'PENCLP curncy']
    stx = marketStructure(idx)
    stx.downloadData(500)
    stx.learnGraphStructure()
    stx.createClusters()
    stx.generateVisualization()