# -*- coding: utf-8 -*-
"""
Created on Tue Oct 04 09:52:09 2016

@author: ngoldbergerr
"""


import sys
sys.path.append("L:\Rates & FX\Quant Analysis\portfolioManager\Portfolios")
from highway import portClas

import tia.rlab as rlab
import matplotlib.pyplot as plt
import datetime
from tia.rlab.table import PercentFormatter, MillionsFormatter, FloatFormatter, Style, mdYFormatter, ThousandsFormatter, IntFormatter
import pandas as pd
import sqlite3
import matplotlib

# - Generate a pdf path
# - define a cover page
# - Create a Pdf Builder
# - Define the templates and register with the builder
#
#        TEMPLATE_0
#  |-------------------------|
#  |        HEADER           | 
#  |-------------------------|
#  |                         |
#  |                         |
#  |                         |
#  |          IMG_1          |
#  |                         |
#  |                         |
#  |                         |
#  |-------------------------|
#
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

now = datetime.datetime.now().strftime("%d%m%Y")
pdfpath = 'forwards' + ' ' + now + '.pdf'
x = 'Reporte del ' + now
pdf = rlab.PdfBuilder(pdfpath, showBoundary=0)

# Define TEMPLATE_0
template = rlab.GridTemplate('TEMPLATE_0', nrows=100, ncols=100)
# uses numpy style slicing to define the dimensions
template.define_frames({
    'HEADER': template[:8, :],
    'TBL_1': template[9:, 3:97],
})
template.register(pdf)

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
    'TBL_1': template[8:45, :50],
    'TBL_2': template[45:95, :50],
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

def fwd_to_pdf_table(frame):
    table =  pdf.table_formatter(frame, inc_header=1, inc_index=1)
    # use the default style to add a bit of color
    table.apply_basic_style(cmap=rlab.Style.Cyan)
    table.cells.match_column_labels('Trade Date').apply_format(mdYFormatter)
    table.cells.match_column_labels('Maturity').apply_format(mdYFormatter)
    table.cells.match_column_labels('Nominal Long').apply_number_format(ThousandsFormatter)
    table.cells.match_column_labels('Nominal Short').apply_number_format(ThousandsFormatter)
    table.cells.match_column_labels('MACRO 1.5').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('MACRO CLP3').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('SPREADCORP').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('DEUDA CORP').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('M_MARKET').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('LIQUIDEZ').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('RENTA').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('IMT E-PLUS').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('DEUDA 360').apply_format(ThousandsFormatter)
    table.cells.match_column_labels('TOTAL').apply_format(ThousandsFormatter)
    table.index.apply_format(mdYFormatter)
    return table.build(vAlign='MIDDLE', hAlign = 'RIGHT')

# Define a matplotlib helper to store images by key
from tia.util.mplot import FigureHelper
figures = FigureHelper()

def add_forwards_to_report(forwardsTable):
    # build the images
#    with plt.style.context('ggplot'):
        plt.rcParams['lines.linewidth'] = 1.5
        # build the tables
        tbl1 = fwd_to_pdf_table(forwardsTable)
    
        pdf.build_page('TEMPLATE_0', {
            'HEADER': title_bar(pdf, 'FORWARDS VIGENTES'),
            'TBL_1': tbl1
        })

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------
# For each portfolio, add to the pdf --------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------

port = portClas()

forward = port.getForwardsFromDB()
forward.columns = ['Trade Date','Name','Fixing','Maturity','Counterparty','Long','Short','Nominal Long','Nominal Short','Strike','Strategy Name','Type']
#forward.index = forward['Name']
#del forward['Name']
del forward['Fixing']
forward = forward[forward.Maturity > datetime.datetime.now()]
forward = forward.sort_values('Maturity')
#forward.index = range(1,len(forward)+1)

fwd = forward[['Maturity']]
fwd['Days'] = [int((forward['Maturity'].iloc[i] - datetime.datetime.now()).days) for i in range(0,len(forward))]
fwd['Currency'] = forward['Long']+forward['Short']
fwd['Type'] = forward['Type']

for portfolio in forward['Name'].unique():
    fwd[str(portfolio)] = 0
    for i in range(0,len(forward)):
        if str(forward['Name'].iloc[i]) == str(portfolio):
            if forward['Long'].iloc[i] == 'CLP':
                fwd[str(portfolio)].iloc[i] = -forward['Nominal Short'].iloc[i]
                fwd['Currency'].iloc[i] = forward['Short'].iloc[i]+forward['Long'].iloc[i]
            else:
                fwd[str(portfolio)].iloc[i] = forward['Nominal Long'].iloc[i]
        else:
            fwd[str(portfolio)].iloc[i] = 0

    x = fwd.groupby(['Maturity', 'Currency', 'Type', 'Days']).sum()
    x = x.reset_index()
    x.index = x['Maturity']
    del x['Maturity']

x['TOTAL'] = x['MACRO 1.5'] + x['MACRO CLP3'] + x['SPREADCORP'] + x['DEUDA CORP']
add_forwards_to_report(x.replace(0,'-'))

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