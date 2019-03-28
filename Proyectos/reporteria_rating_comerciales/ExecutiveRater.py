"""
Created on Thu May 25 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
from libreria_fdo import *


'''MAIN'''

print("****************************************************************START****************************************************************")
path=getSelfPath()
wb = openWorkbook(path+"ExecutiveRater.xlsx")
eraseTableXl(sheet="Series",row=1,column=1)
yesterday_date=getYesterdayDate()
query_series=extractQuery(path+"querys_rater\\"+"full_stock_ejecutivos.sql").replace("AUTODATE", yesterday_date)
print("****************************************************************INSERTANDO Series****************************************************************")
pasteQueryXl(server="Puyehue", database="MesaInversiones", query=query_series, sheet="Series", row=1, column=1, with_schema=True)

#borrarDatosAntiguos()
#descargarDatosFondos(path)
#printFondosRentaFijaPDF(path)
#printFondosRentaVariablePDF(path)



#saveWorkbook(wb)
#closeWorkbook(wb)

print("****************************************************************END******************************************************************")


