# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 13:19:05 2016

@author: ngoldbergerr
"""

import sys
import os
from PyQt4 import QtCore, QtGui, uic
sys.path.append("L:\\Rates & FX\\Quant Analysis\\portfolioManager\\Portfolios")
#import numpy as np
from highway import portClas
#import portfolios as port
#import risk_factors as rf
import time
#from pylab import setp
from dbfunctions import *
import locale
import datetime as dt
import pandas as pd
locale.setlocale(locale.LC_NUMERIC, 'English')

#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT

### Utility Functions

#==============================================================================
# Extra functions used on updating and managing the GUI
#==============================================================================
def insertDataFrameIntoTableWidget(data_as_frame, table_widget):
    
    table_widget.setSortingEnabled(False)
    table_widget.clearContents()
    table_widget.setColumnCount(len(data_as_frame.columns))
    table_widget.setRowCount(len(data_as_frame.index))
    
    table_widget.setHorizontalHeaderLabels(data_as_frame.columns)
    
    for i in range(len(data_as_frame.index)):
        for j in range(len(data_as_frame.columns)):
            
            item = QtGui.QTableWidgetItem()
            
            data = data_as_frame.iat[i,j]
            
            if isinstance(data, float):
                data = round(data, 3)
            else:
                data = data
            
            item.setData(QtCore.Qt.DisplayRole, data)
            table_widget.setItem(i, j, item)
            
    table_widget.setSortingEnabled(True)
#            table_widget.setItem(i,j,QtGui.QTableWidgetItem(str(data)))

    
def autolabel(ax, rects, labels, vertical = True):
    #Función usada en plotExposures para agregar labels a las barras
    for num,rect in enumerate(rects):
        width = rect.get_width()
        label = round(labels[num],1)
        
        if vertical == True:
            if (label < 0):        # The bars aren't wide enough to print the ranking inside
                xloc = 0.1*width  # Shift the text to the left side of the right edge
                clr = (1,1,1)      # White on magenta
                align = 'right'
            else:
                xloc = 0.1*width  # Shift the text to the left side of the right edge
                clr = (1,1,1)      # White on magenta
                align = 'left'
            # Center the text vertically in the bar
            yloc = rect.get_y()+rect.get_height()/2.0
            ax.text(xloc,yloc,label,horizontalalignment=align,
                    verticalalignment='center', color=clr, weight='bold')
        else:
            if (label < 0):        # The bars aren't wide enough to print the ranking inside
                yloc = 0.8*label  # Shift the text to the left side of the right edge
                clr = (1,1,1)      # White on magenta
                align = 'top'
            else:
                yloc = 0.9*label  # Shift the text to the left side of the right edge
                clr = (1,1,1)      # White on magenta
                align = 'bottom'
            # Center the text vertically in the bar
            xloc = rect.get_x()+rect.get_width()/2.0
            ax.text(xloc,yloc,label,horizontalalignment='center',
                    verticalalignment=align, color=clr, weight='bold')
            
def getTableSelectionAsString(tableWidget):
        
    indexes = tableWidget.selectedIndexes()
    text = ''
    dataDict = {}
    colSeparator = '\t'
    rowSeparator = '\n'
    headers = {}
    
    for item in indexes:
        #Me add the row and column separators
        currentRow = item.row()
        currentColumn = item.column()
        
        if currentRow not in dataDict: 
            dataDict[currentRow] = []
            
        if currentColumn not in headers:
            headers[currentColumn] = tableWidget.horizontalHeaderItem(currentColumn).text()
            
        dataDict[currentRow].append(str(item.data()))
    
    rows = [colSeparator.join(headers.values())]
    
    for row in dataDict.values():
        rows.append(colSeparator.join(row))
        
    text = rowSeparator.join(rows)
    return text
        
class portfolioInsight(QtGui.QWidget):
    
    def __init__(self):
        super(portfolioInsight,self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\insiteLite.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\insiteLite.ui")
            
        uic.loadUi(pathname, self)
        
        self.initUI()
       
        self.show()
        
        
    def initUI(self):
        
        #Insertamos un splash screen para que se vea más bonito...
        splash_pix = QtGui.QPixmap('images\\splash_screen.png')
        splash=QtGui.QSplashScreen(splash_pix,QtCore.Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        splash.show()
        splash.showMessage('Portfolio Insight Lite 1.2', alignment = QtCore.Qt.AlignBottom, color = QtGui.QColor(0,162,232))
        self.setWidgetsPropertiesAndActions()
        time.sleep(3)
        splash.finish(self)
        
    def setWidgetsPropertiesAndActions(self):
        self._port = portClas()
        self.matrix = self._port.getPortFromDB()

        self.dateEdit.setDate(dt.datetime.today())
        self.updateAvailablePortfoliosList()

        self.pushButtonGO.clicked.connect(self.updatePortfolio)
        self.pushButtonIN.clicked.connect(self.openPortfolioDetails)
        
    def portfolioSelected(self):
        #Trigger when portfolio is selected from combo box list. 
        #It selects last available date for the portfolio, which updates information.
        if self.comboBoxPortfolio.currentIndex() == 0:
            self.dateEdit.setEnabled(False)
            return False
        
        self.dateEdit.setEnabled(True)
        portfolio_name = str(self.comboBoxPortfolio.currentText())
        last_date = self._portfolio.DBgetLastAvailableDate(portfolio_name)

        if not last_date:
            QtGui.QMessageBox.information(self, 'Warning', "No data found for portfolio (%s)."%portfolio_name)
            return False
            
        if last_date == self.dateEdit.date().toPyDate():
            self.updatePortfolio()
        else:
            self.dateEdit.setDate(last_date)
            
### Update widgets
#==============================================================================
# Functions for updating information on embedded widgets
#==============================================================================
    def updateAvailablePortfoliosList(self):        

        availablePorts = self._port.getAvailablePortfolios()
        self.comboBoxPortfolio.clear()
        self.comboBoxPortfolio.addItems([' '])
        self.comboBoxPortfolio.addItems(availablePorts)    

    def updatePortfolio(self):
        #Load portfolio from DB and populate tables
        port = str(self.comboBoxPortfolio.currentText())
        splash_pix = QtGui.QPixmap('images\\loading.png')
        splash=QtGui.QSplashScreen(splash_pix)
        splash.setMask(splash_pix.mask())
        splash.show()
        splash.showMessage('Loading portfolio, please wait...   ', alignment = QtCore.Qt.AlignRight, color = QtGui.QColor(0,162,232))

        self.textEdit1.setText(self.comboBoxPortfolio.currentText() + ' for date: ' + str(self.getDate()))

        if self.comboBoxPortfolio.currentIndex() == 0:
            splash.finish(self)
            return False, False

        try:
#            self.p1 = self._port.getPositionsMatrix(self.comboBoxPortfolio.currentText(), str(self.getDate()))
#            self.portfolio = self._port.getTrackingError(self.p1)
            con = self._port.openConnection()
            p_view = pd.read_sql(((("SELECT AssetClass, ROUND(MarketValue,2) AS MarketValue, ROUND(Weight,2) AS Weight, ROUND(CTD,2) AS CTD, ROUND(YTM,2) AS YTM, ROUND(Duration,2) AS Duration, ROUND(CTR,2) AS CTR, ROUND(PCTR,2) AS PCTR FROM HistoricalAttributes WHERE PortfolioName = 'AUTOPORT' and Date(date) = 'AUTODATE'").replace("AUTOPORT", port)).replace("AUTODATE",str(self.getDate()))),con)
            self.p_view = p_view[['AssetClass', 'MarketValue', 'Weight', 'CTR', 'PCTR', 'Duration', 'CTD', 'YTM']]
            pos = 0
            for asset in self.p_view['AssetClass']:
                if asset[0:3] == 'Dep':
                    self.p_view['AssetClass'][pos] = 'Deposito ' + asset[10:]
                pos += 1
            insertDataFrameIntoTableWidget(self.p_view, self.tableOne)
            disconnectDatabase(con)

            con = self._port.openConnection(path = 'L:\Rates & FX\Quant Analysis\portfolioManager\Portfolios\DB\\historicalPositions.db')
            fx_view = pd.read_sql(((("SELECT Currency, ROUND(MarketValue,2) AS MarketValue, ROUND(Weight,2) AS Weight, ROUND(CTD,2) AS CTD, ROUND(CTY,2) AS CTY, ROUND(CTR,2) AS CTR, ROUND(PCTR,2) AS PCTR FROM HistoricalPositions WHERE PortfolioName = 'AUTOPORT' and Date(date) = 'AUTODATE'").replace("AUTOPORT", port)).replace("AUTODATE",str(self.getDate()))),con)
            self.fx_view = fx_view[fx_view['Currency'].isin(['$','EUR','UF','USD'])].groupby(by='Currency').sum()
            self.fx_view['Currency'] = self.fx_view.index
            self.fx_view = self.fx_view[['Currency', 'Weight', 'CTR', 'PCTR', 'CTD', 'CTY']]
            
            insertDataFrameIntoTableWidget(self.fx_view, self.tableTwo)
            disconnectDatabase(con)

        except ValueError as error:
            QtGui.QMessageBox.information(self, 'Error', 'There was an error while retrieving portfolio for date (%s).\nError (%s)'%(self.getDate(), error))
            splash.finish(self)
            return False

        splash.finish(self)

### Open and Connect Widgets
#==============================================================================
# Functions for opening and connecting complementary widgets for portfolio managing
#============================================================================== 

    def openPortfolioDetails(self):
        
        self._portfolioDetails = portfolioDetails(parent = self)
        self._portfolioDetails.show()

### Get information from widgets
#==============================================================================
# Functions for getting information from widgets
#============================================================================== 
    def getDate(self):
        
        return self.dateEdit.date().toPyDate()
        
    def getPortfolioName(self):
        
        if self.comboBoxPortfolio.currentIndex() == 0:
            return False
            
        return str(self.comboBoxPortfolio.currentText())
    
    def getSelectedCurrency(self):
        
        rowIndex = self.tableExposures.currentRow()
        if rowIndex == -1:
            return False
            
        currency = str(self.tableExposures.item(rowIndex,0).text())
        return currency
            
    def getSelectedSecurity(self):
       
        rowIndex = self.tablePositions.currentRow()
        if rowIndex == -1:
            return False
        
        identifier = str(self.tablePositions.item(rowIndex,0).text())
        price = str(self.tablePositions.item(rowIndex,5).text())
        description = str(self.tablePositions.item(rowIndex,18).text())
        
        return identifier, price , description
        
        
class portfolioDetails(QtGui.QWidget):

    def __init__(self, parent = None):
        
        super(portfolioDetails, self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\inSide.ui")
        except NameError:
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\inSide.ui")
        
        self._parent = parent
        uic.loadUi(pathname, self)
        self.initUI()
        
    def initUI(self):
        
        self.setWidgetsPropertiesAndActions()
        
    def setWidgetsPropertiesAndActions(self):
        port = self._parent.comboBoxPortfolio.currentText()
        today = str(self._parent.getDate())
        self.textEdit.setText(port + ' for date: ' + today)
        self.tableInstruments.horizontalHeader().setStyleSheet("QHeaderView::section { background-color:rgb(48, 48, 48) }")
        self.tableInstruments.verticalHeader().hide()
        con = self._parent._port.openConnection(path = 'L:\Rates & FX\Quant Analysis\portfolioManager\Portfolios\DB\\historicalPositions.db')
        try:
            portfolio = pd.read_sql(((("SELECT ROUND(CTD,2) AS CTD, ROUND(CTY,2) AS CTY, Currency, Duration, InstrumentName, MarketValue, MaturityDate, Risk, Sector, ROUND(Weight*100,2) AS Weight, Link, ROUND(MCR,2) AS MCR, ROUND(CTR,2) AS CTR, ROUND(PCTR,2) AS PCTR FROM HistoricalPositions WHERE PortfolioName = 'AUTOPORT' and Date(date) = 'AUTODATE'").replace("AUTOPORT", port)).replace("AUTODATE",str(today))),con)
            portfolio.columns = ['CTD','CTY','Currency','Duration','Instrument Name','Market Value','Maturity Date','Risk','Sector','Weight','Link','MCR','CTR','PCTR']
            portfolio = portfolio[['Instrument Name','Link','Market Value','Weight','Duration','Currency','CTD','CTY','Maturity Date','Risk','Sector','MCR','CTR','PCTR']]
            pos = 0            
            for instrument in portfolio['Instrument Name']:
                if instrument[0:3] == 'Dep':
                    portfolio['Instrument Name'][pos] = 'Deposito ' + instrument[10:]
                pos += 1
            pd.options.display.float_format = '{:,.4f}'.format
            insertDataFrameIntoTableWidget(portfolio.fillna(0), self.tableInstruments)
#       try:
#            portfolio = self._parent.portfolio[['instrument_name','market_value','maturity_date','w','MCR','CTR','PCTR']]
#            portfolio.columns = ['Instrument Name','Market Value','Maturity Date','Weight','MCR','CTR','PCTR']
##            portfolio['Yield'] = [float(portfolio['Yield'][x]) for x in range(0,len(portfolio['Yield']))]
#            portfolio['Market Value'] = [float(portfolio['Market Value'][x]) for x in range(0,len(portfolio['Market Value']))]
##            portfolio['Nominal'] = [float(portfolio['Nominal'][x]) for x in range(0,len(portfolio['Nominal']))]
#            portfolio['Weight'] = portfolio['Weight']*100
#            pd.options.display.float_format = '{:,.4f}'.format
#            insertDataFrameIntoTableWidget(portfolio.fillna(0), self.tableInstruments)
        except ValueError as error:
            QtGui.QMessageBox.information(self, 'Error', 'There was an error while retrieving portfolio for date (%s).\nError (%s)'%(self.getDate(), error))
            return False
            
        return True
        
            
### Get information from widgets
#==============================================================================
# Functions for getting information from widgets
#============================================================================== 
                
    def getDataFromText(self):
        
        rowSeparator ='\n'        
        textPositions = str(self.textEditPositions.toPlainText())
        positionsTmp = textPositions.split(rowSeparator)
        positions = []
        
        for row in positionsTmp:
            if row:
                [identifier, nominal] = row.split('\t')
                positions.append((identifier, float(nominal)))
                
        return positions
        
    def getImportData(self):
        
        portfolio_name = str(self.comboBoxPortfolio.currentText())
        portfolio_type = str(self.comboBoxPortfolioType.currentText())
        date = self.dateEdit.date().toPyDate()
        try:
            positions = self.getDataFromText()
        except ValueError:
            QtGui.QMessageBox.information(self, 'Warning', "Import text could not be decoded to the required format. Row separator should by a line break (\\n) and column separator should be a tab (\\t)")
            return False
        
        return portfolio_name, portfolio_type, date, positions

### Event handlers definition
#==============================================================================
# Extra Functions for modifying event handlers con the GUI
#==============================================================================
    #Redefinimos algunos event handlers 
#    def closeEvent(self, event):        
#        if self._parent is not None:            
#            QtGui.QMessageBox.information(self, 'Information', "Portfolio list updated")            
#            self._parent.updateAvailablePortfoliosList()
            
class MySplashScreen(QtGui.QSplashScreen):
    def __init__(self, animation, flags):
        # run event dispatching in another thread
        super(MySplashScreen,self).__init__(QtGui.QPixmap(), flags)
        self.movie = QtGui.QMovie(animation)
        self.movie.frameChanged.connect(self.onNextFrame)
#        self.connect(self.movie, SIGNAL('frameChanged(int)'), SLOT('onNextFrame()'))
        self.movie.start()
   
    def onNextFrame(self):
        pixmap = self.movie.currentPixmap()
        self.setPixmap(pixmap)
        self.setMask(pixmap.mask())

                
def main():
    app = QtGui.QApplication(sys.argv)    
    QtGui.QApplication.setStyle('plastique')
    
    portInsight = portfolioInsight()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()