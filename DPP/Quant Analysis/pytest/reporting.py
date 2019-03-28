# -*- coding: utf-8 -*-
"""
Created on Tue Sep 06 18:24:06 2016

@author: ngoldbergerr
"""

import sys
sys.path.append("L:\Rates & FX\Quant Analysis\portfolioManager\Portfolios")
from highway import portClas

import tia.rlab as rlab
import matplotlib.pyplot as plt
import datetime
from tia.rlab.table import PercentFormatter, MillionsFormatter, FloatFormatter, Style
import pandas as pd
import sqlite3
import matplotlib

# - Generate a pdf path
# - define a cover page
# - Create a Pdf Builder
# - Define the templates and register with the builder
#
#        TEMPLATE_1
#  |-------------------------|
#  |        HEADER           | 
#  |-------------------------|
#  |            |            |
#  |            |            |
#  |            |            |
#  |   IMG_1    |    IMG_2   |
#  |            |            |
#  |            |            |
#  |            |            |
#  |-------------------------|
#
#        TEMPLATE_2
#  |-------------------------|
#  |        HEADER           | 
#  |-------------------------|
#  |            |            |
#  |            |    TBL_2   |
#  |            |            |
#  |   TBL_1    |------------|
#  |            |            |
#  |            |    TBL_3   |
#  |            |            |
#  |-------------------------|
#
#        TEMPLATE_3
#  |-------------------------|
#  |        HEADER           | 
#  |-------------------------|
#  |            |            |
#  |   TBL_1    |            |
#  |            |            |
#  |------------|   TBL_3    |
#  |            |            |
#  |   TBL_2    |            |
#  |            |            |
#  |-------------------------|
pdfpath = 'rlab_usage.pdf'
now = datetime.datetime.now().strftime("%d-%m-%Y")
x = 'Reporte del ' + now
coverpage = rlab.CoverPage('Resumen Posicionamiento Fondos Renta Fija', x)
pdf = rlab.PdfBuilder(pdfpath, coverpage=coverpage, showBoundary=0)

# Define TEMPLATE_1
template = rlab.GridTemplate('TEMPLATE_1', nrows=100, ncols=100)
# uses numpy style slicing to define the dimensions
template.define_frames({
    'HEADER': template[:10, :],
    'IMG_1': template[15:, 3:48],
    'IMG_2': template[15:, 52:97]
})
template.register(pdf)

# Define TEMPLATE_2
template = rlab.GridTemplate('TEMPLATE_2', nrows=100, ncols=100)
template.define_frames({
    'HEADER': template[:10, :],
    'TBL_1': template[10:, :50],
    'TBL_2': template[10:55, 50:],
    'TBL_3': template[55:, 50:]
})
template.register(pdf)

# Define TEMPLATE_3
template = rlab.GridTemplate('TEMPLATE_3', nrows=100, ncols=100)
template.define_frames({
    'HEADER': template[:10, :],
    'TBL_1': template[8:60, :50],
    'TBL_2': template[60:95, :50],
    'TBL_3': template[8:, 50:]
})
template.register(pdf)

# Define a style and method for building a header

from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, TA_CENTER

# Add a stylesheet to the pdf
tb = ParagraphStyle('TitleBar', parent=pdf.stylesheet['Normal'], fontName='Helvetica-Bold', fontSize=14, 
                    leading=14, alignment=TA_CENTER)


'TitleBar' not in pdf.stylesheet and pdf.stylesheet.add(tb)


def title_bar(pdf, title):
    # Build a title bar for top of page
#    w, t, c = '100%', 2, HexColor('#404040')
    w, t, c = '100%', 1.5, HexColor('#597b7c')
    title = '<b>{0}</b>'.format(title)    
    return [HRFlowable(width=w, thickness=t, color=c, spaceAfter=5, vAlign='MIDDLE', lineCap='square'),
            pdf.new_paragraph(title, 'TitleBar'),
            HRFlowable(width=w, thickness=t, color=c, spaceBefore=5, vAlign='MIDDLE', lineCap='square')]
            

# Define method to convert a dataframe to a formatted pdf table object

def port_to_pdf_table(frame):
    table =  pdf.table_formatter(frame, inc_header=1, inc_index=1)
    # use the default style to add a bit of color
    table.apply_basic_style(cmap=rlab.Style.Cyan)
#    table.apply_default_style()
    # apply a percent formatter to the return column
    table.cells.match_column_labels('Weight').apply_number_format(PercentFormatter)
    table.cells.match_column_labels('CTR').apply_number_format(PercentFormatter)
    table.cells.match_column_labels('PCTR').apply_number_format(PercentFormatter)
    table.cells.match_column_labels('Duration').apply_number_format(FloatFormatter)
    table.cells.match_column_labels('CTD').apply_number_format(FloatFormatter)
    table.cells.match_column_labels('YTM').apply_number_format(FloatFormatter)
    # apply a millions formatter to volumn column
    table.cells.match_column_labels('Market Value').apply_number_format(MillionsFormatter)
#    table.index.apply_format(mdYFormatter)
    return table.build(vAlign='MIDDLE', hAlign = 'LEFT')


# Define a matplotlib helper to store images by key
from tia.util.mplot import FigureHelper
figures = FigureHelper()

#def add_security_to_report(sid, pxframe):
#    # build the images
#    with plt.style.context('fivethirtyeight'):
#        plt.rcParams['lines.linewidth'] = 1.5
#        img1_key = '{0}_open_pxs'.format(sid)
#        img2_key = '{0}_close_pxs'.format(sid)
#        pxframe['Open'].plot(title='{0} Open Price'.format(sid))    
#        figures.savefig(key=img1_key)
#        pxframe['Close'].plot(title='{0} Close Price'.format(sid))
#        figures.savefig(key=img2_key)
#        # build the tables
#        pxframe['return'] = pxframe.Close.pct_change()
#        tbl1 = to_pdf_table(pxframe[['Open', 'High', 'Low', 'Close']].tail(40))
#        tbl2 = to_pdf_table(pxframe.iloc[:10])
#        tbl3 = to_pdf_table(pxframe.iloc[-10:])
#    
#        # Marry the template with the components
#        pdf.build_page('TEMPLATE_1', {
#            'HEADER': title_bar(pdf, '{0} Images'.format(sid)),
#            'IMG_1': rlab.DynamicPdfImage(figures[img1_key]),
#            'IMG_2': rlab.DynamicPdfImage(figures[img2_key]),        
#        })
#    
#        pdf.build_page('TEMPLATE_2', {
#            'HEADER': title_bar(pdf, '{0} Tables'.format(sid)),
#            'TBL_1': tbl1,
#            'TBL_2': tbl2,
#            'TBL_3': tbl3,
#        })

def add_portfolio_to_report(port, portFrame, portSummary):
    # build the images
#    with plt.style.context('ggplot'):
        plt.rcParams['lines.linewidth'] = 1.5
        graphDurationCTR(port)
        img1 = '{0}_open_pxs'.format(port)
        figures.savefig(key=img1)
        # build the tables
        tbl1 = port_to_pdf_table(portFrame)
#        tbl2 = graphDurationCTR()
        tbl3 = port_to_pdf_table(view)
    
        pdf.build_page('TEMPLATE_3', {
            'HEADER': title_bar(pdf, 'POSICIONAMIENTO Y RIESGO FONDO {0}'.format(port)),
            'TBL_1': tbl3,
            'TBL_2': rlab.DynamicPdfImage(figures[img1]),
            'TBL_3': tbl1,
        })

dbPath = 'L:\Rates & FX\Quant Analysis\portfolioManager\Portfolios\DB\\historicalPort.db'

def openConnection():
    #Función que abre una conexión con el default path de la clase
    con = sqlite3.connect(dbPath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    con.text_factory = str
    return con

def getHistoricalPortData(port):
    con = openConnection()
    CTR = pd.read_sql(('SELECT DATE(Date),CTR,Duration FROM HistoricalAttributes WHERE PortfolioName = "AUTOPORT" AND AssetClass = "Total" ORDER BY Date').replace("AUTOPORT", port),con)
    CTR.index = CTR['DATE(Date)']
    del CTR['DATE(Date)']
    CTR['CTR'] = [float(CTR['CTR'][i]) for i in range(0,len(CTR))]
    CTR['Duration'] = [float(CTR['Duration'][i]) for i in range(0,len(CTR))]
    return CTR

def graphDurationCTR(port):
    matplotlib.rcParams.update(matplotlib.rcParamsDefault)
    CTR = getHistoricalPortData(port)
    CTR = CTR.tail(20)
    CTR['Period'] = [CTR.index[x][5:7] + '/' + CTR.index[x][8:10] for x in range(0,len(CTR))]
    CTR.index = CTR['Period']
    barcolor = '#d75b27'
    fig = plt.figure();
    ax = CTR['CTR'].plot(kind='bar', color = barcolor)
    plt.ylabel('Tracking Error (%)',fontsize = 16)
    plt.yticks(fontsize = 14)
    plt.xlabel('',fontsize = 18)
    
    linecolor = '#597b7c'
    ax2 = ax.twinx()
    ax2.plot(ax.get_xticks(),CTR['Duration'], linestyle  = '--', color = linecolor)
    plt.ylabel('Duracion',fontsize = 16)
    plt.yticks(fontsize = 14)    

    plt.title('Evolucion de Presupuesto de Riesgo y OAD',fontsize = 20)

    plt.xticks(fontsize = 14)
    plt.tight_layout()
    fig.set_size_inches(10, 8)

    for p in ax.patches:
        ax.annotate(str(round(p.get_height(),2)), (p.get_x() * 1.001, p.get_height() * 1.006), size=12)
    
    plt.legend(['OAD'])
    return True

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------
# For each portfolio, add to the pdf --------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------


port = portClas()
rates = ['MACRO 1.5', 'MACRO CLP3', 'RENTA', 'IMT E-PLUS']
for name in rates:
    view, portfolio = port.getBasicView(name)
    portFrame = portfolio[['instrument_name','market_value','maturity_date','w','CTR','PCTR']]
    portFrame.columns = ['Instrument Name','Market Value','Maturity Date','Weight','CTR','PCTR']
    portFrame.index = portFrame['Instrument Name']
    portFrame['PCTR'] = portFrame['PCTR']/100
    portFrame['CTR'] = portFrame['CTR']/100
    portFrame = portFrame.sort_values(['PCTR'], ascending = False)
    portFrame = portFrame.dropna()
    del portFrame['Instrument Name']
    portFrame = portFrame.head(31)
    view.columns = ['CTR','PCTR','Weight','Market Value','CTD','YTM','Duration']
    view['Market Value'] = view['Market Value']*1000000
    view = port.set_column_sequence(view,['Weight','Market Value','Duration','CTD','YTM','CTR','PCTR'])
    view['PCTR'] = view['PCTR']/100
    view['CTR'] = view['CTR']/100
    view['Weight'] = view['Weight']/100
    add_portfolio_to_report(name,portFrame,view)

#credit = ['DEUDA CORP', 'SPREADCORP']
#credit_bmk = {'DEUDA CORP':'IMT Corp Clas A+ To AAA Dur 0y9y Liquido', 'SPREADCORP': 'IMT Corp Clas BBB- To A+ Liquidez 30000UF'}
#for name in credit:
#    view, portfolio = port.getBasicView(name,credit_bmk[name])
#    portFrame = portfolio[['instrument_name','market_value','maturity_date','w','CTR','PCTR']]
#    portFrame.columns = ['Instrument Name','Market Value','Maturity Date','Weight','CTR','PCTR']
#    portFrame.index = portFrame['Instrument Name']
#    portFrame['PCTR'] = portFrame['PCTR']/100
#    portFrame['CTR'] = portFrame['CTR']/100
#    portFrame = portFrame.sort_values(['PCTR'], ascending = False)
#    portFrame = portFrame.dropna()
#    del portFrame['Instrument Name']
#    portFrame = portFrame.head(31)
#    view.columns = ['CTR','PCTR','Weight','Market Value','CTD','YTM','Duration']
#    view['Market Value'] = view['Market Value']*1000000
#    view = port.set_column_sequence(view,['Weight','Market Value','Duration','CTD','YTM','CTR','PCTR'])
#    view['PCTR'] = view['PCTR']/100
#    view['CTR'] = view['CTR']/100
#    view['Weight'] = view['Weight']/100
#    add_portfolio_to_report(name,portFrame,view)
    
pdf.save()