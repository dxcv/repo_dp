# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 12:53:11 2016

@author: mvillalon / goldbena
"""

import sys
import os
from PyQt4 import QtCore, QtGui, uic
sys.path.append("L:\Rates & FX\Quant Analysis\portfolioManager")
import numpy as np
import portfolios as port
import risk_factors as rf
import time
from pylab import setp
import locale
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
                data = str(data)
            
            item.setData(QtCore.Qt.DisplayRole, data)
            table_widget.setItem(i, j, item)
            
    table_widget.setSortingEnabled(True)
#            table_widget.setItem(i,j,QtGui.QTableWidgetItem(str(data)))
            
    
def autolabel(ax, rects, labels, vertical = True):                              # Modified on Version 1.1 to work with bar and barh ###############
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
        
class portfolioManager(QtGui.QWidget):
    
    def __init__(self):
        super(portfolioManager,self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\portfolioManager.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\portfolioManager.ui")
            
        uic.loadUi(pathname, self)
        
        self.initUI()
       
        self.show()
        
        
    def initUI(self):
        
        #Insertamos un splash screen para que se vea más bonito...
        splash_pix = QtGui.QPixmap('images\\splash_screen.png')
        splash=QtGui.QSplashScreen(splash_pix,QtCore.Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        splash.show()
        splash.showMessage('Risk and Asset Manager for Bank Operations (RAMBO)\nPowered by QuantTeam', alignment = QtCore.Qt.AlignBottom, color = QtCore.Qt.green)
        self.setWidgetsPropertiesAndActions()
        time.sleep(6)
        splash.finish(self)
        
    def setWidgetsPropertiesAndActions(self):
        
        self._portfolio = port.portfolio()
        self._portfolioExposures = port.pd.DataFrame()
        self._portfolioPositions = port.pd.DataFrame()

        self.tablePositions.horizontalHeader().setStyleSheet("QHeaderView::section { background-color:rgb(48, 48, 48) }")
        self.tablePositions.verticalHeader().hide()
        
        self.splitter_3.setSizes([10, 2000])
        self.splitter_2.setSizes([200, 200])
        
        self.tableExposures.horizontalHeader().setStyleSheet("QHeaderView::section { background-color:rgb(48, 48, 48) }")
        self.tableExposures.verticalHeader().hide()
        
        self.dateEdit.setDate(port.dt.today())
        self.updateAvailablePortfoliosList()
        self.dateEdit.dateChanged.connect(self.updatePortfolio)
        
        self.comboBoxPortfolio.activated[str].connect(self.portfolioSelected)
        
        self.tableExposures.clicked.connect(self.updateCurrencyWidgets)
        
        self.initiatePlot()
        
        self.checkBoxDuration.stateChanged.connect(self.updateCurrencyPlotLabel)
        self.checkBoxFX.stateChanged.connect(self.updateCurrencyPlotLabel)
        self.checkBoxSpread.stateChanged.connect(self.updateCurrencyPlotLabel)
        self.checkBoxKRD.stateChanged.connect(self.updateCurrencyPlotLabel)
        
        self.radioButtonNominal.toggled.connect(self.updatePortfolio)
        self.radioButtonLinker.toggled.connect(self.updatePortfolio)
        self.radioButtonAllAssets.toggled.connect(self.updatePortfolio)
        
        self.pushButtonUpdate.clicked.connect(self.updatePortfolio)
        
        self.splitter.setStretchFactor(1, 10)
        
        self.pushButtonTrade.clicked.connect(self.openTrades) 
        self.pushButtonImport.clicked.connect(self.openImportPortfolio)
        
        self.pushButtonTE.clicked.connect(self.showTE)
        
    def initiatePlot(self):
        
        factor=0.19
        mainColor=(factor,factor,factor)
        self._fig = self.mplwidgetExposures.figure
        self._figCurrency = self.mplwidgetCurrencyExposures.figure             # Added on Version 1.1 ##################
        self._figOAD = self.mplwidgetOADExposures.figure                       # Added on Version 1.1 ##################
        
        self._fig.set_facecolor(mainColor)
        self._figCurrency.set_facecolor(mainColor)                             # Added on Version 1.1 ##################
        self._figOAD.set_facecolor(mainColor)                                  # Added on Version 1.1 ##################
        
        self._plot = self._fig.add_subplot(111, axisbg = mainColor)
        self._plotCurrencies = self._figCurrency.add_subplot(111, axisbg = mainColor) # Added on Version 1.1 ###########
        self._plotOAD = self._figOAD.add_subplot(111, axisbg = mainColor)             # Added on Version 1.1 ###########
         
        self._plot.tick_params(axis='x',colors='white')
        self._plot.tick_params(axis='y',colors='white')
        
        self._plotCurrencies.tick_params(axis='x',colors='white')              # Added on Version 1.1 ##################
        self._plotCurrencies.tick_params(axis='y',colors='white')              # Added on Version 1.1 ##################
        
        self._plotOAD.tick_params(axis='x',colors='white')                     # Added on Version 1.1 ##################
        self._plotOAD.tick_params(axis='y',colors='white')                     # Added on Version 1.1 ##################
        
        self._plot.hold(False)
        self._plotCurrencies.hold(False)                                       # Added on Version 1.1 ##################
        self._plotOAD.hold(False)                                              # Added on Version 1.1 ##################
        
        #Reseteamos los axes disponibles  
        for axes in self._fig.get_axes():
            
            axes.get_xaxis().set_ticks([])
            axes.get_yaxis().set_ticks([])
            
        for axes in self._figCurrency.get_axes():                              # Added on Version 1.1 ##################
            
            axes.get_xaxis().set_ticks([])                                     # Added on Version 1.1 ##################
            axes.get_yaxis().set_ticks([])                                     # Added on Version 1.1 ##################

        for axes in self._figOAD.get_axes():                                   # Added on Version 1.1 ##################
            
            axes.get_xaxis().set_ticks([])                                     # Added on Version 1.1 ##################
            axes.get_yaxis().set_ticks([])                                     # Added on Version 1.1 ##################
        
        self.mplwidgetExposures.draw()
        self.mplwidgetCurrencyExposures.draw()                                 # Added on Version 1.1 ##################
        self.mplwidgetOADExposures.draw()                                      # Added on Version 1.1 ##################
        
        
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
        
        availablePorts = self._portfolio.DBgetAvailablePortfolios()
        self.comboBoxPortfolio.clear()
        self.comboBoxPortfolio.addItems([''] + availablePorts)
    
    def updatePortfolio(self):
        #Load portfolio from DB and populate tables
        splash_pix = QtGui.QPixmap('images\\thumbs_up.jpg')
        splash=QtGui.QSplashScreen(splash_pix,QtCore.Qt.WindowStaysOnTopHint)
#        splash = MySplashScreen('images\\loading.gif', QtCore.Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        splash.show()
        splash.showMessage('Loading portfolio, please wait...', alignment = QtCore.Qt.AlignRight, color = QtCore.Qt.green)
#        QtGui.QApplication.processEvents()
            
        if self.comboBoxPortfolio.currentIndex() == 0:
            splash.finish(self)
            return False, False
        
        try:
            self._portfolioExposures, self._portfolioPositions = self.loadPortfolio()
        except ValueError as error:
            QtGui.QMessageBox.information(self, 'Error', 'There was an error while retrieving portfolio for date (%s).\nError (%s)'%(self.getDate(), error))
            splash.finish(self)
            return False
        
        if self._portfolioExposures.empty:
            splash.finish(self)
            QtGui.QMessageBox.information(self, 'Warning', 'Nothing updated. No active positions available. Check that portfolio and benchmark are loaded for date (%s)'%self.getDate())
            return False
            
        if self._portfolioPositions.empty:
            splash.finish(self)
            QtGui.QMessageBox.information(self, 'Warning', 'Nothing updated. No portfolio positions available. Check that portfolio and benchmark are loaded for date (%s)'%self.getDate())            
            return False
            
        if self.isNominal():
            self._portfolioExposures = self._portfolioExposures[self._portfolioExposures['INFLATION'] != 'Y']
            self._portfolioPositions = self._portfolioPositions[self._portfolioPositions['INFLATION'] != 'Y']
        elif self.isBoth():                                                    
            self._portfolioExposures = self._portfolioExposures                
            self._portfolioPositions = self._portfolioPositions                
        else:
            self._portfolioExposures = self._portfolioExposures[self._portfolioExposures['INFLATION'] == 'Y']
            self._portfolioPositions = self._portfolioPositions[self._portfolioPositions['INFLATION'] == 'Y']
        
        self._exposureByCurrency = self._portfolioExposures.groupby(['CURRENCY'], as_index = False).agg(lambda x: x.sum())
        self.updateTableExposure(self._exposureByCurrency)
        self.updateCurrencyWidgets()
        
        splash.finish(self)
        
    def updateTableExposure(self, exposureAsFrame):
        
#        self.tableExposures.setRowCount(0)
        columns = ['CURRENCY','WEIGHT (%)','YIELD','CONVEXITY','DURATION','SPREAD','DTS']
        exposureAsFrame['WEIGHT (%)'] = exposureAsFrame['WEIGHT']*100
        insertDataFrameIntoTableWidget(exposureAsFrame[columns], self.tableExposures)
        self.updateCurrencyExposurePlot()                                     
        self.updateOADExposurePlot()                                          
        
    def updateCurrencyWidgets(self):
        
        currency = self.getSelectedCurrency()
        self.updateTablePositions(currency)
        self.updateCurrencyPlot(currency)
        
    def updateTablePositions(self, currency):
        
        if not currency:
            self.tablePositions.setRowCount(0)
            return False        
        
        positionsOnCurrency = self._portfolioPositions[self._portfolioPositions['CURRENCY'] == currency]
        positionsOnCurrency.is_copy = False #La siguiente asignación arroja un falso positivo. Lo que lo silencio con esto
        
        positionsOnCurrency.loc[:, 'IDENTIFIER'] = positionsOnCurrency.index
        positionsOnCurrency['WEIGHT (%)'] = positionsOnCurrency['WEIGHT']*100
        positionsOnCurrency = positionsOnCurrency[['IDENTIFIER', 'WEIGHT (%)'] + positionsOnCurrency.columns[:-2].tolist()]
        
        positionsOnCurrency['NOMINAL'] = positionsOnCurrency['NOMINAL'].apply(lambda x: locale.format('%.2f', x, True))
        positionsOnCurrency['MARKET_VALUE_LOCAL'] = positionsOnCurrency['MARKET_VALUE_LOCAL'].apply(lambda x: locale.format('%.2f', x, True))
        positionsOnCurrency['MARKET_VALUE_USD'] = positionsOnCurrency['MARKET_VALUE_USD'].apply(lambda x: locale.format('%.2f', x, True))
        
        
        insertDataFrameIntoTableWidget(positionsOnCurrency, self.tablePositions)
        
    def updateCurrencyPlot(self, currency):
        
        #Función que se encarga de graficar las posiciones activas
            
        fig = self._fig
        ax = self._plot
        
        if not currency:
            ax.clear()
            self.mplwidgetExposures.draw()
            return False
            
        width = 0.7 #Ancho de las barras
        riskExposure = self._exposureByCurrency[self._exposureByCurrency['CURRENCY'] == currency].reset_index()
        
        
        riskFactorsNames = []
        riskFactorsValues = []
        
        if self.checkBoxFX.isChecked():
            riskFactorsNames.extend(['FX'])
            riskFactorsValues.append(riskExposure['WEIGHT'][0])
        
        if self.checkBoxDuration.isChecked():
            riskFactorsNames.extend(['duration'])
            riskFactorsValues.append(riskExposure['DURATION'][0])
        
        if self.checkBoxSpread.isChecked():
            riskFactorsNames.extend(['DTS'])
            riskFactorsValues.append(riskExposure['DTS'][0])
        
        if self.checkBoxKRD.isChecked():
            krdNames=['KRD 0.5','KRD 1.0','KRD 2.0','KRD 3.0','KRD 5.0','KRD 7.0','KRD 10.0','KRD 20.0','KRD 30.0']
            riskFactorsNames.extend(krdNames)
            riskFactorsValues.extend(riskExposure['KRD'][0]['Duration'].values.tolist())
        
        if not riskFactorsNames:
            ax.clear()
            self.mplwidgetExposures.draw()
            return False
            
        #Datos a graficar en las barras horizontales
        x=np.arange(len(riskFactorsNames)) #índice de cada posición activa
        y=riskFactorsValues #Valor de las exposiciones activas 
       
        rects=ax.barh(x,y,height=width, color=(0,0.5,0.7), edgecolor=(0,0.5,0.7))
                    
        ax.set_yticks(x + width/2)
        setp(ax, yticklabels=riskFactorsNames)
        
        ax.set_xticks([min(y),max(y)])
        setp(ax, xticklabels=[round(min(y),0),round(max(y),1)])
        
        autolabel(ax,rects,riskFactorsValues)
  
        fig.tight_layout()    
                 
        self.mplwidgetExposures.draw()

# Added on Version 1.1 #################################################################################################################################################

    def updateCurrencyExposurePlot(self):
        
        exposureAsFrame = self._portfolioExposures.groupby(['CURRENCY'], as_index = False).agg(lambda x: x.sum())
        #Función que se encarga de graficar las posiciones activas
            
        fig = self._figCurrency
        ax = self._plotCurrencies
            
        width = 0.7 #Ancho de las barras
        
        columns = ['CURRENCY','WEIGHT (%)']
        exposureAsFrame['WEIGHT (%)'] = exposureAsFrame['WEIGHT']*100
                 
        currencyExposure = exposureAsFrame[columns] 
        
        #Datos a graficar en las barras verticales
        x = np.arange(len(currencyExposure)) #índice de cada posición activa
        y = currencyExposure['WEIGHT (%)'] #Valor de las exposiciones activas 
       
        rects=ax.bar(x, y, width = width, color=(0,0.5,0.7), edgecolor=(0,0.5,0.7))
                    
        ax.set_xticks(x + width/2)
        setp(ax, xticklabels=currencyExposure['CURRENCY'])
        
        ax.set_yticks([min(y),max(y)])
        setp(ax, yticklabels=[round(min(y),0),round(max(y),1)])
        
        autolabel(ax,rects,currencyExposure['WEIGHT (%)'], vertical = False)
  
        fig.tight_layout()
        
        self.mplwidgetCurrencyExposures.draw()
        
    
    def updateOADExposurePlot(self):
        
        exposureAsFrame = self._portfolioExposures.groupby(['CURRENCY'], as_index = False).agg(lambda x: x.sum())
        #Función que se encarga de graficar las posiciones activas
            
        fig = self._figOAD
        ax = self._plotOAD
            
        width = 0.7 #Ancho de las barras
        
        columns = ['CURRENCY','DURATION']
                 
        currencyExposure = exposureAsFrame[columns] 
        
        #Datos a graficar en las barras verticales
        x = np.arange(len(currencyExposure)) #índice de cada posición activa
        y = currencyExposure['DURATION'] #Valor de las exposiciones activas 
       
        rects=ax.bar(x, y, width = width, color=(0,0.5,0.7), edgecolor=(0,0.5,0.7))
                    
        ax.set_xticks(x + width/2)
        setp(ax, xticklabels=currencyExposure['CURRENCY'])
        
        ax.set_yticks([min(y),max(y)])
        setp(ax, yticklabels=[round(min(y),0),round(max(y),1)])
        
        autolabel(ax,rects,currencyExposure['DURATION'], vertical = False)
  
        fig.tight_layout()    
                 
        self.mplwidgetOADExposures.draw()

#######################################################################################################################################################################
            
    def updateCurrencyPlotLabel(self):
        #Function called on label checkbox for the plot
        currency = self.getSelectedCurrency()
        self.updateCurrencyPlot(currency)
        
    def updatePortfolioFromTradesWidget(self):
        #Special function created for managing how the portfolio will be updated when updatePortfolio is signaled from trades widget.
        self.updatePortfolio()

### Open and Connect Widgets
#==============================================================================
# Functions for opening and connecting complementary widgets for portfolio managing
#============================================================================== 
    
    def openTrades(self):
        
        portfolio_name = self.getPortfolioName()
        date = self.getDate()
        
        if not portfolio_name:
            QtGui.QMessageBox.information(self, 'Warning', "Please select a portfolio first.")
            return False
            
        self._trades = trades(portfolio_name, date, parent = self)
        
        #Connections between trades and portofolioManager widgets:
        self._trades.pushButtonUpdatePortfolio.clicked.connect(self.updatePortfolioFromTradesWidget)
        self.tablePositions.clicked.connect(self._trades.updateIsinFromTablePositions)
        
        
        self._trades.show()
        
    def openImportPortfolio(self):
        
        self._importPortfolio = importPortfolio(parent = self)
        self._importPortfolio.show()
        
    def showTE(self):
        
#        self._progress = QtGui.QProgressDialog("Hold...hold...", "Cancel", 0, 0, self)
#        self._progress.setWindowTitle('Please wait...')
#        self._progress.setWindowModality(QtCore.Qt.WindowModal)
#        self._progress.canceled.connect(self._progress.close)
#        self._progress.show()
        
        self._riskFactor = rf.risk_factor()
        
        returnCov = self._riskFactor.getCovarianceMatrix()
        portfolio_name = self.getPortfolioName()
        date = self.getDate()
        portfolio = self._riskFactor.DBgetPortfolioExposure(portfolio_name = portfolio_name, date = date)
        
        TEMarg = self._riskFactor.dot(returnCov, portfolio.transpose())
        TE = (self._riskFactor.dot(portfolio, TEMarg)*252)**0.5*100
        
        QtGui.QMessageBox.information(self, 'Message', 
        """TE for portfolio (%s) on date (%s) is:
        %s bps"""%(portfolio_name, date, round(TE.values[0][0],3)))
        
### Use and/or get information from objects
#==============================================================================
# Functions for getting information to be used on widgets
#==============================================================================    
    
    def loadPortfolio(self):        
            
        date = self.getDate()
        portfolio_name = self.getPortfolioName()
        exposureAsFrame = self._portfolio.getActiveRiskContribution(portfolio_name, date = date)
        positionsAsFrame = self._portfolio.DBgetPortfolioProperties(portfolio_name, date = date)
        return exposureAsFrame, positionsAsFrame

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
        
    def isNominal(self):
        
        if self.radioButtonNominal.isChecked():
            return True
        elif self.radioButtonLinker.isChecked():
            return False

    def isBoth(self):                                                                       # Added on Version 1.1 ##############################################################
        
        if self.radioButtonAllAssets.isChecked():
            return True
        elif self.radioButtonLinker.isChecked() or self.radioButtonNominal.isChecked():
            return False
            
    def getSelectedSecurity(self):
       
        rowIndex = self.tablePositions.currentRow()
        if rowIndex == -1:
            return False
        
        identifier = str(self.tablePositions.item(rowIndex,0).text())
        price = str(self.tablePositions.item(rowIndex,5).text())
        description = str(self.tablePositions.item(rowIndex,18).text())
        
        return identifier, price , description
        
    def getTableSelectionAsString(self, tableWidget):
        
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
        
### Event handlers definition
#==============================================================================
# Extra Functions for modifying event handlers con the GUI
#==============================================================================       
    #Redefinimos algunos event handlers 
#    def closeEvent(self, event):
#        reply=QtGui.QMessageBox.question(self,'Message',
#                                         "Sure you want to quit?...",QtGui.QMessageBox.Yes |
#                                         QtGui.QMessageBox.No, QtGui.QMessageBox.No)
#        if reply == QtGui.QMessageBox.Yes:
#            event.accept()
#        else:
#            event.ignore()
            
    def keyPressEvent(self, e):     
        if e.key() == QtCore.Qt.Key_Escape: 
            
            self.close()
            
        if e.key() == QtCore.Qt.Key_C and e.modifiers() == QtCore.Qt.ControlModifier:
            
            if self.tablePositions.hasFocus():
                text = self.getTableSelectionAsString(self.tablePositions)
                
            if self.tableExposures.hasFocus():
                text = self.getTableSelectionAsString(self.tableExposures)
                
            QtGui.QApplication.clipboard().setText(text)
            
    
            
class trades(QtGui.QWidget):
    
    def __init__(self, portfolio_name, date, parent = None):
        
        super(trades,self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\trades.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\trades.ui")
        
        self._portfolioName = portfolio_name
        self._date = date
        
        self._parent = parent
        
        uic.loadUi(pathname, self)
        self.initUI()
        
    def initUI(self):   
        
        self.setWidgetsPropertiesAndActions()
        
    def setWidgetsPropertiesAndActions(self):
        
        self._portfolio = port.portfolio()
        self._FX = None
        self._tradeBuffer = []
        
        self.labelWidgetDescription.setText('Trade Manager for portfolio (%s) on date (%s)'%(self._portfolioName, self._date))
        
        self.pushButtonBuy.clicked.connect(self.updateBondTradeBuffer)
        self.pushButtonSell.clicked.connect(self.updateBondTradeBuffer)
        
        self.pushButtonResetBuffer.clicked.connect(self.updateResetBuffer)
        self.pushButtonSimulate.clicked.connect(self.updateSimulate)
        
        self.pushButtonResetSimulated.clicked.connect(self.updateResetSimulated)
        self.pushButtonCommitSimulated.clicked.connect(self.updateCommitTrades)
        
        self.pushButtonFX.clicked.connect(self.openFX)
        self.pushButtonFXForward.clicked.connect(self.openFXForward)
        self.pushButtonDepo.clicked.connect(self.openDepo)
        self.pushButtonPrice.clicked.connect(self.openPrice)
        self.pushBuyFromBMK.clicked.connect(self.openBenchmark)
        
        self.updateSimulate()
        

### Update widgets
#==============================================================================
# Functions for updating information on embedded widgets
#==============================================================================
    def updateCommitTrades(self):
        
        simulated_trades_as_frame = self.commitTrades()
        insertDataFrameIntoTableWidget(simulated_trades_as_frame, self.tableTradesSimulated)
        
    def updateResetSimulated(self):
        
        self.resetSimulatedTrades()      
        self.tableTradesSimulated.setRowCount(0)
        
        self.pushButtonUpdatePortfolio.click()
        
    def updateSimulate(self):
        
        simulated_trades_as_frame = self.simulateTrades()        
        insertDataFrameIntoTableWidget(simulated_trades_as_frame, self.tableTradesSimulated)
        
        self.updateUnpricedPositions()
        
        #We update portfolio manager widgets
        self.pushButtonUpdatePortfolio.click()
        
    def updateUnpricedPositions(self):
        
        unpricedPositions = self.checkUnpricedPositions()
        
        if not unpricedPositions:
            self.checkBoxUnpricedPositions.setChecked(False)
        else:
            self.checkBoxUnpricedPositions.setChecked(True)
        
    def updateBondTradeBuffer(self):
        
        trade = self.getSecurityTradeData()
        if not trade:
            return False
            
        self._tradeBuffer.append(trade)
        trade_buffer_as_frame = port.pd.DataFrame(self._tradeBuffer)
        insertDataFrameIntoTableWidget(trade_buffer_as_frame, self.tableTradesBuffer)
    
    def updateExternalTradeBuffer(self, externalTradeBuffer):
        #This function is called from the connection with children widget
            
        self._tradeBuffer.extend(externalTradeBuffer)  
        trade_buffer_as_frame = port.pd.DataFrame(self._tradeBuffer)
        insertDataFrameIntoTableWidget(trade_buffer_as_frame, self.tableTradesBuffer)
    
            
    def updateResetBuffer(self):
        
        self._tradeBuffer = []
        self.tableTradesBuffer.setRowCount(0)
        
    def updateIsinFromTablePositions(self):

        if self._parent is None:
            return False
                    
        identifier, price, description = self._parent.getSelectedSecurity()
        
        if description in ('BOND'):
            
            self.lineEditIsin.setText(identifier)
            self.lineEditPrice.setText(price)
            
        return False
        
    def updateIsinFromTableBmkInstruments(self):

        if self._parent is None:
            return False
                    
        identifier, price, description = self._benchmark.getSelectedSecurityFromBmk()
        
        if description in ('CASH', 'TIME DEPOSIT', 'COMMERCIAL PAPER'):
            return False
        
        self.lineEditIsin.setText(identifier)
        self.lineEditPrice.setText(price)        
        
### Open and Connect Widgets
#==============================================================================
# Functions for opening and connecting complementary widgets for portfolio managing
#============================================================================== 
    def openFX(self):
                
        self._FX = FX(parent = self)
        self._FX.show()
        
    def openFXForward(self):
                
        self._FXForward = FXForward(parent = self)
        self._FXForward.show()
    
    def openDepo(self):
        
        self._depo = depo(parent = self)
        self._depo.show()
        
    def openPrice(self):
        
        self._price = price(self._portfolioName, self._date, self._parent)
        self._price.tableWidget.itemChanged.connect(self.updateUnpricedPositions)
        
        self._price.show()

    def openBenchmark(self):
        
        self._benchmark = benchmark(parent = self)
        self._benchmark.tableBmkInstruments.clicked.connect(self._parent._trades.updateIsinFromTableBmkInstruments)
        self._benchmark.show()
        
### Use and/or get information from objects
#==============================================================================
# Functions for getting information to be used on widgets
#==============================================================================
    def simulateTrades(self):
        
        if self._tradeBuffer:
            self._portfolio.TradeAndUpdatePortfolio(self._portfolioName, self._tradeBuffer, date = self._date)
            
        simulated_trades_as_frame = self._portfolio.DBgetSimulatedTrades(self._portfolioName, date = self._date)
        self.updateResetBuffer()
        
        return simulated_trades_as_frame
    
    def resetSimulatedTrades(self):
        
        identifiers = self.getIdentifiersFromSimulatedTable()
        self._portfolio.DeleteSimulatedAndUpdatePortfolio(self._portfolioName, date = self._date, identifiers = identifiers)        
        #We check if trades where deleted
        simulated_trades_as_frame = self._portfolio.DBgetSimulatedTrades(self._portfolioName, date = self._date)
        return simulated_trades_as_frame
    
    def commitTrades(self):
        
        identifiers = self.getIdentifiersFromSimulatedTable()
        self._portfolio.DBcommitTrades(self._portfolioName, date = self._date, identifiers = identifiers)
        
        simulated_trades_as_frame = self._portfolio.DBgetSimulatedTrades(self._portfolioName, date = self._date)
        return simulated_trades_as_frame
    
    def checkUnpricedPositions(self):
        
        checkUnpricedPositions = self._portfolio.DBcheckUnpricedPositions(self._portfolioName, date = self._date, DBtype = 'portfolios')
        return checkUnpricedPositions
        
### Get information from widgets
#==============================================================================
# Functions for getting information from widgets
#============================================================================== 
    def getSecurityTradeData(self):
        
        identifier = str(self.lineEditIsin.text())        
        if not identifier:
            return False
            
        price = float(self.lineEditPrice.text())
        if not isinstance(price, float):
            return False
        
        if str(self.sender().objectName()) == 'pushButtonBuy':
            amount=self.spinBoxTradeAmount.value()
        elif str(self.sender().objectName()) == 'pushButtonSell':
            amount=-self.spinBoxTradeAmount.value()
        if not amount:
            return False    
                
        trade = {'identifier': identifier, 
                    'price': price, 
                    'nominal': amount,
                    'trade_description': 'bond',
                    'portfolio_name': self._portfolioName,
                    'trade_type': 'SIMULATED'}
            
        return trade
     
    def getIdentifiersFromSimulatedTable(self):
     
        identifiers = [str(self.tableTradesSimulated.item(i, 2).text()) for i in range(0, self.tableTradesSimulated.rowCount())]
        return identifiers
        
### Event handlers definition
#==============================================================================
# Extra Functions for modifying event handlers con the GUI
#==============================================================================           
    def keyPressEvent(self, e):     
        if e.key() == QtCore.Qt.Key_Escape: 
            
            self.close()
            
        if e.key() == QtCore.Qt.Key_C and e.modifiers() == QtCore.Qt.ControlModifier:
            
            if self.tableTradesBuffer.hasFocus():
                text = getTableSelectionAsString(self.tableTradesBuffer)
                
            if self.tableTradesSimulated.hasFocus():
                text = getTableSelectionAsString(self.tableTradesSimulated)
                
            QtGui.QApplication.clipboard().setText(text)
            
class FXForward(QtGui.QWidget):
    
    def __init__(self, parent = None):
        
        super(FXForward,self).__init__()
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\FXForward.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\FXForward.ui") 
            
        self._parent = parent
        
        uic.loadUi(pathname, self)
        self.initUI()
        
    def initUI(self):
        
        self.setWidgetsPropertiesAndActions()
        
    def setWidgetsPropertiesAndActions(self):
        
        self._tradeBuffer = []
        self._currencies = self.getFXIdentifiers()        
        self._availableIssuers = self._parent._portfolio.DBgetAvailableIssuers(commercial_paper = False, time_deposits = False, fx_forward = True)[['IDENTIFIER','NAME']].to_dict('index').values()
        
        issuerName = [depo['NAME'] for depo in self._availableIssuers]
       
        self.comboBoxIssuer.addItems(issuerName)
        
        self.comboBoxBUY.addItems([''] + self._currencies['CURRENCY'].tolist())
        self.comboBoxSELL.addItems([''] + self._currencies['CURRENCY'].tolist())
        
        self.comboBoxBUY.activated[str].connect(self.updateRate)
        self.comboBoxSELL.activated[str].connect(self.updateRate)
        self.checkBoxInvert.stateChanged.connect(self.updateRate)
        self.lineEditRate.editingFinished.connect(self.updateIsinStr)
        self.comboBoxIssuer.activated[str].connect(self.updateIsinStr)
        
        self.dateEdit.setDate(self._parent._date)
        self.editAmount.setText('0')
        
        self.dateEdit.dateChanged.connect(self.updateRate)
        
        self.pushButtonAddToBuffer.clicked.connect(self.updateParentTradeBuffer)


### Update widgets
#==============================================================================
# Functions for updating information on embedded widgets
#==============================================================================
        
    def updateParentTradeBuffer(self):
        
        FXTradeBuffer = [self.getFXTradeInformation()]
        self._parent.updateExternalTradeBuffer(FXTradeBuffer)
        
        
    def updateRate(self):
        
        buyCurrency=""
        sellCurrency="" 
        rateStr = ""
        rate = ''
        #Agregar acá in filtro de settlement date
        maturity = self.getDate()
        
        if self.comboBoxBUY.currentIndex() > 0 and self.comboBoxSELL.currentIndex() > 0:
            buyCurrency = str(self.comboBoxBUY.currentText())
            buyCurrencyInfo = self._currencies[self._currencies['CURRENCY'] == buyCurrency]
            buyRateUSD = self.getFXForwardStrike(buyCurrencyInfo[['FORWARD_CURVE', 'CURRENCY', 'FX_USD_SPOT']], maturity)
            
            sellCurrency = str(self.comboBoxSELL.currentText())
            sellCurrencyInfo = self._currencies[self._currencies['CURRENCY'] == sellCurrency]
            sellRateUSD = self.getFXForwardStrike(sellCurrencyInfo[['FORWARD_CURVE', 'CURRENCY', 'FX_USD_SPOT']], maturity)
        
            if self.checkBoxInvert.isChecked():
                rateStr = sellCurrency+"/"+buyCurrency 
                rate = str(sellRateUSD/buyRateUSD)
            else:
                rateStr = buyCurrency+"/"+sellCurrency        
                rate = str(buyRateUSD/sellRateUSD)
            
        self.labelRate.setText(rateStr)
        self.lineEditRate.setText(rate)
        
        self.updateIsinStr()
    
    def updateIsinStr(self):
        
        if self.comboBoxBUY.currentIndex() > 0 and self.comboBoxSELL.currentIndex() > 0:
            issuer = self._availableIssuers[self.comboBoxIssuer.currentIndex()]['IDENTIFIER']
            buyCurrency = str(self.comboBoxBUY.currentText())
            sellCurrency = str(self.comboBoxSELL.currentText())
            date = self.getDate().strftime('%Y%m%d')
            
            if self.checkBoxInvert.isChecked():
                price = 1/float(self.lineEditRate.text())
            else:
                price = float(self.lineEditRate.text())
                
            isinStr = 'FXFW' + str(buyCurrency) + str(sellCurrency) + date + str(issuer) + '_' + str(price)
            self.lineEditIsin.setText(isinStr)
        
### Use and/or get information from objects
#==============================================================================
# Functions for getting information to be used on widgets
#==============================================================================    
    def getFXIdentifiers(self):
       
       date = self._parent._date
       portfolio_name = self._parent._portfolioName
       currency_names = self._parent._portfolio.DBgetAvailableCurrencies(portfolio_name = portfolio_name, DBtype = 'All', date = date)
       currencies = self._parent._portfolio.getFXForwardInformation(currency_names, pricing_date = date)
       
       return currencies
       
    def getFXForwardStrike(self, fx_info, maturity):
        
       forward_strike = self._parent._portfolio.getFXForwardMarketStrike(fx_info, maturity)['STRIKE_USD'].values[0]
       return forward_strike

### Get information from widgets
#==============================================================================
# Functions for getting information from widgets
#============================================================================== 
    def getFXTradeInformation(self):
        
        identifier = str(self.lineEditIsin.text())
        amount = float(self.editAmount.text())
        settlement_date = self.dateEdit.date().toPyDate()
        
#        if self.checkBoxInvert.isChecked():
#            price = 1/float(self.lineEditRate.text())
#        else:
#            price = float(self.lineEditRate.text())
        
        
        trade = {'identifier': identifier,
                'nominal': amount,
                'trade_description': 'FX FORWARD',
                'portfolio_name': self._parent._portfolioName,
                'trade_type': 'SIMULATED',
                'settlement_date': settlement_date}
                
        return trade
        
    def getDate(self):

        return self.dateEdit.date().toPyDate()
        

        
class FX(QtGui.QWidget):
    
    def __init__(self, parent = None):
        
        super(FX,self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\FX.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\FX.ui")        
        
        self._parent = parent
        
        uic.loadUi(pathname, self)
        self.initUI()
        
    def initUI(self):
        
        self.setWidgetsPropertiesAndActions()
        
    def setWidgetsPropertiesAndActions(self):
        
        self._tradeBuffer = []
        self._availableCurrencies = None
        availableCurrencies = self.getFXIdentifiers()
        
        self.comboBoxBUY.addItems([''] + availableCurrencies)
        self.comboBoxSELL.addItems([''] + availableCurrencies)
        
        self.comboBoxBUY.activated[str].connect(self.updateRate)
        self.comboBoxSELL.activated[str].connect(self.updateRate)
        self.checkBoxInvert.stateChanged.connect(self.updateRate)
        
        self.dateEdit.setDate(self._parent._date)
        self.editAmount.setText('0')
        
        self.pushButtonAddToBuffer.clicked.connect(self.updateParentTradeBuffer)

### Update widgets
#==============================================================================
# Functions for updating information on embedded widgets
#==============================================================================
    def updateParentTradeBuffer(self):
        
        FXTradeBuffer = [self.getFXTradeInformation()]
        self._parent.updateExternalTradeBuffer(FXTradeBuffer)
        
    def updateRate(self):
        
        buyCurrency=""
        sellCurrency="" 
        rateStr = ""
        rate = ''
        
        if self.comboBoxBUY.currentIndex() > 0 and self.comboBoxSELL.currentIndex() > 0:
            buyCurrency = str(self.comboBoxBUY.currentText())            
            buyRateUSD = self._currencies['USDFX'][buyCurrency]
            
            sellCurrency = str(self.comboBoxSELL.currentText())
            sellRateUSD = self._currencies['USDFX'][sellCurrency] 
        
            if self.checkBoxInvert.isChecked():
                rateStr = sellCurrency+"/"+buyCurrency 
                rate = str(sellRateUSD/buyRateUSD)
            else:
                rateStr = buyCurrency+"/"+sellCurrency        
                rate = str(buyRateUSD/sellRateUSD)
            
        self.labelRate.setText(rateStr)
        self.lineEditRate.setText(rate)
        
        
### Use and/or get information from objects
#==============================================================================
# Functions for getting information to be used on widgets
#==============================================================================    
    def getFXIdentifiers(self):
       
       date = self._parent._date
       portfolio_name = self._parent._portfolioName
       currency_names = self._parent._portfolio.DBgetAvailableCurrencies(portfolio_name = portfolio_name, DBtype = 'All', date = date)
       self._currencies = self._parent._portfolio.DBgetAllAvailableSecurities(identifiers = currency_names)
       return currency_names

### Get information from widgets
#==============================================================================
# Functions for getting information from widgets
#============================================================================== 
    def getFXTradeInformation(self):
        
        identifier = str(self.comboBoxBUY.currentText())
        currency_pay = str(self.comboBoxSELL.currentText())
        amount = float(self.editAmount.text())
        settlement_date = self.dateEdit.date().toPyDate()
        
        if self.checkBoxInvert.isChecked():
            price = 1/float(self.lineEditRate.text())
        else:
            price = float(self.lineEditRate.text())
        
        
        trade = {'identifier': identifier, 
                'price': price, 
                'nominal': amount,
                'trade_description': 'FX',
                'portfolio_name': self._parent._portfolioName,
                'trade_type': 'SIMULATED',
                'currency_pay': currency_pay,
                'settlement_date': settlement_date}
                
        return trade
        
class depo(QtGui.QWidget):
    
    def __init__(self, parent = None):
        
        super(depo,self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\Depo.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\Depo.ui")
        
        self._parent = parent
        
        uic.loadUi(pathname, self)
        self.initUI()
        
    def initUI(self):     
        
        self._tradeBuffer = []
        self._availableCurrencies = None
        self.setWidgetsPropertiesAndActions()
        
    def setWidgetsPropertiesAndActions(self):
        
        self._currencies = self.getFXIdentifiers()
        self._availableIssuers = self._parent._portfolio.DBgetAvailableIssuers()[['IDENTIFIER','NAME']].to_dict('index').values()
        self._depoType = [{'NAME':'TIME DEPOSIT', 'IDENTIFIER':'DEPO'},{'NAME':'COMMERCIAL PAPER', 'IDENTIFIER':'COMP'}]
        self._accrualType = [{'NAME':'Act/365', 'IDENTIFIER':'A1'}]
        
        issuerName = [depo['NAME'] for depo in self._availableIssuers]
        depoName = [depo['NAME'] for depo in self._depoType]
        accrualName = [depo['NAME'] for depo in self._accrualType]
        
        self.comboBoxType.addItems(depoName)
        self.comboBoxIssuer.addItems(issuerName)
        self.comboBoxCurrency.addItems(self._currencies)
        self.comboBoxAccrual.addItems(accrualName)
        self.dateEdit.setDate(self._parent._date)
        
        self.comboBoxType.activated[str].connect(self.updateIsinStr)
        self.comboBoxIssuer.activated[str].connect(self.updateIsinStr)
        self.comboBoxCurrency.activated[str].connect(self.updateIsinStr)
        self.comboBoxAccrual.activated[str].connect(self.updateIsinStr)
        self.dateEdit.dateChanged.connect(self.updateIsinStr)
        self.lineEditRate.editingFinished.connect(self.updateIsinStr)
        
        self.updateIsinStr()
        
        self.pushButtonAddToBuffer.clicked.connect(self.updateParentTradeBuffer)
        
### Update widgets
#==============================================================================
# Functions for updating information on embedded widgets
#==============================================================================
    def updateParentTradeBuffer(self):
        
        depoTradeBuffer = [self.getDepoTradeInformation()]
        self._parent.updateExternalTradeBuffer(depoTradeBuffer)
        
    def updateIsinStr(self):
        depoType = self._depoType[self.comboBoxType.currentIndex()]['IDENTIFIER']
        issuer = self._availableIssuers[self.comboBoxIssuer.currentIndex()]['IDENTIFIER']
        currency = str(self.comboBoxCurrency.currentText())
        accrual = self._accrualType[self.comboBoxAccrual.currentIndex()]['IDENTIFIER']
        rate = str(self.lineEditRate.text())
        date = self.getDate().strftime('%Y%m%d')
        
        isinStr = str(depoType) + str(currency) + date + str(accrual) + str(issuer) + '_' + str(rate)
        self.lineEditIsin.setText(isinStr)
        self.updateDepoPrice()
     
    def updateDepoPrice(self):
        
        depoIsin = str(self.lineEditIsin.text())
        
        price = self._parent._portfolio.getDepositTradeProperties(depoIsin, 0)
        self.lineEditPrice.setText('')
        self.lineEditPrice.setText(str(price[0]))
        
### Use and/or get information from objects
#==============================================================================
# Functions for getting information to be used on widgets
#==============================================================================    
    def getFXIdentifiers(self):
       date = self._parent._date
       portfolio_name = self._parent._portfolioName
       self._currencies = self._parent._portfolio.DBgetAvailableCurrencies(portfolio_name = portfolio_name, DBtype = 'All', date = date)       
       return self._currencies
      
### Get information from widgets
#==============================================================================
# Functions for getting information from widgets
#============================================================================== 
    def getDate(self):
        
        return self.dateEdit.date().toPyDate()
        
    def getDepoTradeInformation(self):
        
        identifier = str(self.lineEditIsin.text())
        amount = float(self.lineEditAmount.text())
        trade_description = str(self.comboBoxType.currentText())
            
        trade = {'identifier': identifier,
                'nominal': amount,
                'trade_description': trade_description,
                'portfolio_name': self._parent._portfolioName,
                'trade_type': 'SIMULATED'}
                
        return trade

class benchmark(QtGui.QWidget):
    
    def __init__(self, parent = None):
        
        super(benchmark,self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\benchmark.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\benchmark.ui")
        
        self._parent = parent
        
        uic.loadUi(pathname, self)
        self.initUI()
        
    def initUI(self):
        
        self._tradeBuffer = []
        self._availableCurrencies = None
        self.setWidgetsPropertiesAndActions()
        
    def setWidgetsPropertiesAndActions(self):
        
        self.tableBmkInstruments.horizontalHeader().setStyleSheet("QHeaderView::section { background-color:rgb(48, 48, 48) }")
        self.tableBmkInstruments.verticalHeader().hide()
        
        availableCurrencies = self.updateAvailableCurrencyList()
        self.updateTableBmkInstruments()
        self.comboBoxFX.addItems([''] + availableCurrencies)
        self.comboBoxFX.activated.connect(self.updateTableBmkInstruments)
                
### Update widgets
#==============================================================================
# Functions for updating information on embedded widgets
#==============================================================================

    def updateTableBmkInstruments(self):
        
        benchmarkAsFrame = self.loadBenchmark()
        currency = self.getSelectedCurrency()

        if not currency:
            benchmarkAsFrame['IDENTIFIER'] = benchmarkAsFrame.index
            columns = ['IDENTIFIER','CURRENCY','TICKER','ISSUER','PRICE','INFLATION','DURATION','DESCRIPTION']
            insertDataFrameIntoTableWidget(benchmarkAsFrame[columns], self.tableBmkInstruments)
        else:
            benchmarkAsFrame['IDENTIFIER'] = benchmarkAsFrame.index
            columns = ['IDENTIFIER','CURRENCY','TICKER','ISSUER','PRICE','INFLATION','DURATION','DESCRIPTION']
            dataBenchmark = benchmarkAsFrame[columns]
            insertDataFrameIntoTableWidget(dataBenchmark[dataBenchmark['CURRENCY'] == currency], self.tableBmkInstruments)
        
    def updateIsinFromTablePositions(self):

        if self._parent is None:
            return False
                    
        identifier, price, description = self._parent.getSelectedSecurity()
        
        if description in ('CASH', 'TIME DEPOSIT', 'COMMERCIAL PAPER'):
            return False
        
        self.lineEditIsin.setText(identifier)
        self.lineEditPrice.setText(price)
        
    def updateAvailableCurrencyList(self):        
        date = self._parent._date
        portfolio_name = self._parent._portfolioName
        self._bmkCurrencies = self._parent._portfolio.DBgetAvailableCurrencies(portfolio_name = portfolio_name, DBtype = 'BMK', date = date)
        
        return self._bmkCurrencies
        
### Use and/or get information from objects
#==============================================================================
# Functions for getting information to be used on widgets
#==============================================================================    

    def loadBenchmark(self):

        date = self._parent._date
        portfolio_name = self._parent._portfolioName
        benchmarkAsFrame = self._parent._portfolio.DBgetSecurities(portfolio_name, date = date, DBtype = 'BMK')
        return benchmarkAsFrame
              
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

    def getSelectedSecurityFromBmk(self):
       
        rowIndex = self.tableBmkInstruments.currentRow()
        if rowIndex == -1:
            return False
        
        identifier = str(self.tableBmkInstruments.item(rowIndex,0).text())
        price = str(self.tableBmkInstruments.item(rowIndex,4).text())
        description = str(self.tableBmkInstruments.item(rowIndex,7).text())
        
        return identifier, price , description

    def getSelectedCurrency(self):
        currency = str(self.comboBoxFX.currentText())
        
        return currency

class price(QtGui.QWidget):
    
    def __init__(self, portfolio_name, date, parent = None):
        
        super(price,self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\price.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\price.ui")
        
        self._portfolioName = portfolio_name
        self._date = date
        self._parent = parent
        
        uic.loadUi(pathname, self)
        self.initUI()
        
    def initUI(self):  
        
        self.setWidgetsPropertiesAndActions()
        
    def setWidgetsPropertiesAndActions(self):    

        self._portfolio = port.portfolio()
        
        self.labelWidgetDescription.setText('Price positions for portfolio (%s) on date (%s)'%(self._portfolioName, self._date))
        
        self.pushButtonUpdateUnpriced.clicked.connect(self.updateUnpricedPositions)
        self.pushButtonPriceSecurities.clicked.connect(self.updateInsertAndPrice)
        
        self.pushButtonPricePortfolio.clicked.connect(self.updatePricePortfolio)
        self.pushButtonPriceBMK.clicked.connect(self.updatePriceBMK)
        
        self.updateUnpricedPositions()
        
### Update widgets
#==============================================================================
# Functions for updating information on embedded widgets
#==============================================================================
    def updateUnpricedPositions(self):
        
        self._query_with_identifiers = self.getUnpricedPositions()
        query_with_identifiers_as_frame = port.pd.DataFrame(self._query_with_identifiers, columns = ('BBG_QUERY','IDENTIFIER'))
        
        insertDataFrameIntoTableWidget(query_with_identifiers_as_frame, self.tableWidget)
        
    def updateInsertAndPrice(self):
        
        if not self._query_with_identifiers:
            return False
            
        self.insertNewSecurities(self._query_with_identifiers)
        
        identifiers = [identifier[1] for identifier in self._query_with_identifiers]
        self.priceNewSecurities(identifiers)
        
        QtGui.QMessageBox.information(self, 'Message', "Securities should be priced. Re-Price Portfolio and/or BMK")
    
    def updatePricePortfolio(self):
        
        self.pricePortfolio()
        
        if self._parent is not None:
            self._parent.updatePortfolioFromTradesWidget()
        
        self.updateUnpricedPositions()
        
    def updatePriceBMK(self):
        
        self.priceBMK()
        
        if self._parent is not None:
            self._parent.updatePortfolioFromTradesWidget()
        
        self.updateUnpricedPositions()
        
### Use and/or get information from objects
#==============================================================================
# Functions for getting information to be used on widgets
#==============================================================================    
    def getUnpricedPositions(self):
        
        checkUnpricedPositionsPort = self._portfolio.DBcheckUnpricedPositions(self._portfolioName, date = self._date, DBtype = 'portfolios')
        checkUnpricedPositionsBMK = self._portfolio.DBcheckUnpricedPositions(self._portfolioName, date = self._date, DBtype = 'BMK')
        unpricedPositions = list(set(checkUnpricedPositionsPort).union(set(checkUnpricedPositionsBMK)))
        
        if not unpricedPositions:
            return unpricedPositions
            
        query_with_identifiers = self._portfolio.getBBGQueryFromIdentifiers(unpricedPositions)
        
        return query_with_identifiers
        
    def insertNewSecurities(self, query_with_identifiers):
        
        self._portfolio.requestInsertNewSecurities(query_with_identifiers)
        
    def priceNewSecurities(self, identifiers):
        
        self._portfolio.requestPriceNewSecurities(identifiers = identifiers, date = self._date, OverWrite = True)
                    
    def pricePortfolio(self):
        
        self._portfolio.DBupdateNominalAndPricePortfolio(self._portfolioName, date = self._date)

    def priceBMK(self):
        
        self._portfolio.priceBMK(self._portfolioName, date = self._date)    
        
class importPortfolio(QtGui.QWidget):
    
    def __init__(self, parent = None):
        
        super(importPortfolio, self).__init__()
        
        try:
            pathname = os.path.join(os.path.dirname(__file__),"ui Files\\importPortfolio.ui")
        except NameError:  # We are the main py2exe script, not a module
            pathname = os.path.join(os.path.dirname(sys.argv[0]),"ui Files\\importPortfolio.ui")
        
        self._parent = parent
        uic.loadUi(pathname, self)
        self.initUI()
        
    def initUI(self):  
        
        self.setWidgetsPropertiesAndActions()
        
    def setWidgetsPropertiesAndActions(self):
        
        self._portfolio = port.portfolio()
        self.dateEdit.setDate(port.dt.today())
        self.updateAvailablePortfoliosList()
        
        self.pushButtonCreate.clicked.connect(self.updateCreatePortfolio)
        self.pushButtonImport.clicked.connect(self.importPositions)
        self.pushButtonPrice.clicked.connect(self.openPrice)
        
        self.comboBoxPortfolio.activated[str].connect(self.updateUnpricedPositions)
    
### Update widgets
#==============================================================================
# Functions for updating information on embedded widgets
#==============================================================================
    def importPositions(self):
        
        if self.comboBoxPortfolio.currentIndex() == 0:
            return False
            
        importData = self.getImportData()
        
        if not importData[3]:
            QtGui.QMessageBox.information(self, 'Message', "Please add positions to import")
            return False
            
        self.uploadPositions(*importData)
        self.pricePositions(*importData[0:-1])
        self.updateUnpricedPositions()
            
        return False
        
    def updateCreatePortfolio(self):
        
        text, ok = QtGui.QInputDialog.getText(self, 'Create Portfolio Dialog', 
            'Enter new portfolio name (only ASCII):')
        
        if not all(ord(str(c)) < 128 for c in text):
            self.updateCreatePortfolio()
            return None
            
        if ok:
            portfolio_name = str(text)
            self.createPortfolio(portfolio_name)
            self.updateAvailablePortfoliosList()
        
    def updateAvailablePortfoliosList(self):        
        
        availablePorts = self._portfolio.DBgetAvailablePortfolios()
        self.comboBoxPortfolio.clear() 
        self.comboBoxPortfolio.addItems([''] + availablePorts)
        
    def updateUnpricedPositions(self):
        
        unpricedPositions = self.checkUnpricedPositions()
        
        if not unpricedPositions:
            self.checkBoxUnpricedPositions.setChecked(False)
        else:
            self.checkBoxUnpricedPositions.setChecked(True)

### Open and Connect Widgets
#==============================================================================
# Functions for opening and connecting complementary widgets for portfolio managing

    def openPrice(self):
        importData = self.getImportData()
        portfolio_name = importData[0]
        date = importData[2]
        
        self._price = price(portfolio_name, date) #No le agregamos parent, ya que no es necesario tener un portafolio cargado para abrir el import.
        self._price.tableWidget.itemChanged.connect(self.updateUnpricedPositions) #Esta conexion no funciona bien. Por alguna razón no se emite el itemChanged se cambia el rowCount
        
        self._price.show()
        
    
### Use and/or get information from objects
#==============================================================================
# Functions for getting information to be used on widgets
#==============================================================================    
    def createPortfolio(self, portfolio_name):
        
        self._portfolio.DBcreatePortfolio(portfolio_name)
        
    def uploadPositions(self, portfolio_name, portfolio_type, date, positions):
        
        if portfolio_type == 'Portfolio':
            self._portfolio.DBuploadPositionsPortfolio(positions, portfolio_name, date = date)
        elif portfolio_type == 'Benchmark':
            pass
            #Deprecated function
#            self._portfolio.DBuploadPositionsBMK(positions, portfolio_name, date = date)
            
    def pricePositions(self, portfolio_name, portfolio_type, date):
        
        if portfolio_type == 'Portfolio':
            self._portfolio.DBupdateNominalAndPricePortfolio(portfolio_name, date = date)
            
        elif portfolio_type == 'Benchmark':
            self._portfolio.priceBMK(portfolio_name, date = date)
        
        
    def checkUnpricedPositions(self):
        
        importData = self.getImportData()
        portfolio_name = importData[0]
        date = importData[2]
        
        checkUnpricedPositionsPort = self._portfolio.DBcheckUnpricedPositions(portfolio_name, date, DBtype = 'portfolios')
        checkUnpricedPositionsBMK = self._portfolio.DBcheckUnpricedPositions(portfolio_name, date, DBtype = 'BMK')
        checkUnpricedPositions = list(set(checkUnpricedPositionsPort).union(set(checkUnpricedPositionsBMK)))
        
        return checkUnpricedPositions
            
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
    def closeEvent(self, event):        
        if self._parent is not None:            
            QtGui.QMessageBox.information(self, 'Information', "Portfolio list updated")            
            self._parent.updateAvailablePortfoliosList()
            
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
    
    portManager = portfolioManager()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()