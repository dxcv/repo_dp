"""
Created on Wed Dec 07 11:00:00 2016

@author: Fernando Suarez
"""

import sys
sys.path.insert(0, '../libreria/')
from libreria_fdo import *
pd.set_option("display.max_columns", 3)
pd.set_option("display.max_rows", 4)


def getEWCOVMatrix(data, landa = 1):
	'''
	Funcion para calcular la matriz de varianza-covarianza suavizada exponencialmente,
	recibe una matriz (numpy o pandas dataframe) en que cada columna es una serie de retornos.
	Es importante que las series no tengan NaN. Lambda por defecto es 1 se puede modificar (0<landa<1)
	'''
	#sacamos el promedio de cada serie y normalizamos los datos
	avg = data.mean(axis = 0)
	data_mwb = data - avg
	#sacamos el vector de landas dandole mas peso a los primeros elementos(datos mas nuevos)
	powers = np.arange(len(data_mwb))
	landavect = np.empty(len(data_mwb))
	landavect.fill(landa)
	landavect = np.power(landavect, powers)
	#multiplicamos el vector por la matriz de datos normalizada, el vector landa tambien se normaliza con la raiz
	landavectSQRT=np.sqrt(landavect)
	data_tilde = data_mwb.T
	data_tilde = data_tilde*landavectSQRT
	data_tilde = data_tilde.T
	#multiplicamos la suma de todos los landas con la multiplicacion de la matriz compuesta con ella misma
	sumlanda = np.sum(landavect)
	cov_ewma=(1/(sumlanda-1))*(data_tilde.T.dot(data_tilde))
	#para obtener la covarianza/varianza de dos/un indices
	#print(cov_ewma[73].loc[168])
	#para obtener la matriz descorrelacionada
	#cov_ewma = pd.DataFrame(np.diag(np.diag(cov_ewma)),index = cov_ewma.index, columns = cov_ewma.columns)
	return cov_ewma

def getPortfolioMetrics(portfolio, matrix):
	'''
	En base a la cartera de fondos, el codigo de un fondo y la matriz de varianza-covarianza, obtiene un dataframe con el fondo
	junto sus metricas de reisgo calculadas.
	'''
	w_p = portfolio["weight_p"]
	w_b = portfolio["weight_b"]
	w_a = w_p-w_b
	w_marginal = matrix.dot(w_a)
	sigma = np.sqrt(w_a.T.dot(w_marginal))
	global volatility 
	volatility = np.sqrt(w_p.T.dot(matrix.dot(w_p))*252)
	print("TE: " + str(math.sqrt(252)*sigma))
	print("Volatility: " + str(volatility))
	
	mcr = (((w_marginal)*math.sqrt(252))/sigma).to_frame(name = "mcr") 
	portfolio = pd.merge(portfolio, mcr, how = "left", left_index = True, right_index = True)

	w_a = w_a.to_frame(name = "weight_a")
	portfolio = pd.merge(portfolio, w_a, how = "left", left_index = True, right_index = True)
	portfolio["ctr"] = portfolio["mcr"]*portfolio["weight_a"]

	sigma_ag = np.sum(portfolio["ctr"])
	portfolio["pcr"] = portfolio["ctr"]/sigma_ag

	portfolio = portfolio.sort_values(by ="weight_p", ascending = False)

	return portfolio


try:
	deleteFile(".\\output\\portfolio_management_onp.pdf")
except:
	pass

wb = openWorkbook(path = "Dataset.xlsx", screen_updating = True, visible = False)
schema_portfolio = getTableXl(wb = wb, sheet = "portfolio", row = 1, column = 1)[0]
portfolio_raw = getTableXl(wb = wb, sheet = "portfolio", row = 2, column = 1)
schema_hist_data = getTableXl(wb = wb, sheet = "data", row = 1, column = 1)[0]
hist_data_raw = getTableXl(wb = wb, sheet = "data", row = 2, column = 1)
closeExcel(wb = wb)


hist_data = pd.DataFrame(data = hist_data_raw, columns = schema_hist_data)
hist_data.set_index(["date"], inplace=True)
hist_data = hist_data[hist_data.index.dayofweek < 5]
hist_data = -1*hist_data.pct_change().fillna(0)[1:]
print(hist_data)

matrix = getEWCOVMatrix(data = hist_data, landa = 0.94)
print(matrix)



portfolio = pd.DataFrame(data = portfolio_raw, columns = schema_portfolio)
portfolio["weight_p"] = portfolio["weight_p"]/100
portfolio["weight_b"] = portfolio["weight_b"]/100
portfolio.set_index(["ticker"], inplace=True)
portfolio = getPortfolioMetrics(portfolio = portfolio, matrix = matrix)

wb = openWorkbook(path = "Report.xlsx", screen_updating = True, visible = False)
clearSheetXl(wb = wb, sheet = "portfolio")
pasteValXl(wb = wb, sheet = "portfolio", row = 1, column = 1, value = portfolio)
dia_spot = getNDaysFromToday(0)
pasteValXl(wb = wb, sheet = "portfolio", row = 1, column = 12, value = dia_spot)
pasteValXl(wb = wb, sheet = "portfolio", row = 1, column = 13, value = volatility)
ubicacion_pdf_views = getSelfPath() + "output\\1.pdf"
exportSheetPDF(sheet_index = getSheetIndex(wb, "views") - 1, path_in = ".", path_out = ubicacion_pdf_views)
ubicacion_pdf_holdings = getSelfPath() + "output\\2.pdf"
exportSheetPDF(sheet_index = getSheetIndex(wb, "holdings") - 1, path_in = ".", path_out = ubicacion_pdf_holdings)
saveWorkbook(wb = wb)
closeExcel(wb = wb)
mergePDF(path = ".\\output\\", output_name = "portfolio_management_onp.pdf")
deleteFile(ubicacion_pdf_holdings)
deleteFile(ubicacion_pdf_views)
