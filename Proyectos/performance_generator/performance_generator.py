"""
Created on Thu Jan 31 11:00:00 2018

@author: Fernando Suarez & Francisca Martinez
"""

import sys
sys.path.insert(0, "../libreria/")
import libreria_fdo as fs
import libreria_fdo as fs
import pandas as pd
import datetime as dt


def rentabilidad(date, dic_afp, serie_macro15, serie_macro3, tacs, ranking_renta, serie_eplus, icp, date_eplus):
    '''
    Entrega las rentabilidades de los fondos eplus, macro15, macro3 y renta
    '''
    eplus_yld, afp_yld = compute_rent_eplus(dic_afp, date, date_eplus, serie_eplus, tacs, ytd=True)
    eplus_yld_12m, afp_yld_12m = compute_rent_eplus(dic_afp, date, date_eplus, serie_eplus, tacs, ytd=False)
    m15_yld, m15_yld_month = compute_rent_m15(date, serie_macro15, icp)
    m3_yld, m3_yld_month = compute_rent_m3(date, serie_macro3, icp, tacs)
    renta_yld = compute_rent_renta(ranking_renta, 'ytd')
    renta_yld_1y = compute_rent_renta(ranking_renta, '1A (%)')
    print_report_pdf(eplus_yld=eplus_yld, afp_yld=afp_yld,eplus_yld_12m=eplus_yld_12m, afp_yld_12m=afp_yld_12m, m15_yld=m15_yld,
                     m15_yld_month=m15_yld_month, m3_yld=m3_yld, m3_yld_month=m3_yld_month, renta_yld=renta_yld, renta_yld_1y=renta_yld_1y)
    #print_report_macros(m15_yld=m15_yld, m15_yld_month=m15_yld_month, m3_yld=m3_yld, m3_yld_month=m3_yld_month)
    
    
def compute_rent_eplus(dic_afp, date, date_eplus ,serie_eplus, tacs, ytd=False):
    '''
    Generamos las rentabilidades para el eplus
    '''
    if ytd is True:
        date_inic = date_eplus+ dt.timedelta(days=1) #dt.datetime(date.year, 1, 1)

    else:
        date_inic = dt.datetime(date.year-1, date.month, date.day)
        #print(date_inic)

    # movemos el eplus y eliminamos filas vacias

    #fs.print_full(serie_eplus)
    
    serie_eplus['FDIMEPS CI Equity'] = serie_eplus['FDIMEPS CI Equity'].shift(-1)
    #fs.print_full(serie_eplus)
    
    serie_eplus = serie_eplus.dropna(axis=0, how='any')
    # generamos las rentabilidades
    yld_eplus = compute_yld_eplus(date, date_inic, serie_eplus, tacs)
    # obtenemos la serie con el prom, min y max del benchmark
    df_yld = compute_max_min(yld_eplus, 'FDIMEPS CI Equity')
    df_yld = df_yld.join(yld_eplus['FDIMEPS CI Equity'])
    # obtenemos las rentabilidades del ultimo dia
    df_afp = yld_eplus.loc[[date]].sort_values(by=date, ascending=False, axis=1).rename(dic_afp, axis='columns')

    return df_yld, df_afp


def compute_yld_eplus(date, date_inic, serie_eplus, tacs, ):
    '''
    Generamos el dataframe de las rentabilidades
    '''
    
    days_betwwen = fs.get_dates_between(date_inic+dt.timedelta(days=+1), date)
    df_yld = pd.DataFrame(index=days_betwwen, columns=serie_eplus.columns)
    for afp in serie_eplus.columns:
        rent_list = []
        aux_rent = 0
        aux=0
        serie = serie_eplus[afp]
        #fs.print_full(serie)
        for day in days_betwwen:

            aux_rent =compute_rent_afp(serie, day, tacs, afp)
            rent_list.append(1+aux_rent)
            

        df_yld[afp] = pd.Series(rent_list, index=days_betwwen)
        #fs.print_full(df_yld)
        df_yld[afp] = df_yld[afp].cumprod()*100
        
        
    fs.print_full(df_yld)  
    df_yld.loc[date_inic-dt.timedelta(days=1)] = [100 for k in range(len(serie_eplus.columns))]

    fs.print_full(df_yld)
    
    return df_yld


def compute_rent_afp(serie, date, tacs, afp=None):
    '''
    entrega el retorno para una afp entre dos fechas
    '''
    date_ant = date+dt.timedelta(days=-1)
    rent = (serie[date]/serie[date_ant])-1
    if afp=='FDIMEPS CI Equity':
    	rent = rent + compute_tacs(tacs, date,  'IMT E-PLUS')
    print(str(date)+" "+str(rent))

    return rent


def compute_tacs(tacs, date, fund):
    '''
    Genera el tacs para una fecha y una rentabilidad dada
    '''
    month = date.month
    aux = tacs[fund][month-1]
    tac = (aux)/(100*365)
    print(str(date)+" "+str(tac))
    return tac


def compute_max_min(df, name_eplus):
    '''
    entega el max min y promedio de las afp
    '''
    df_yld = pd.DataFrame(columns=['Max', 'Min', 'Avg'])
    index_list = df.index.tolist()
    lista = df.values.tolist()
    for i in range(len(lista)):
        max_value = max(lista[i][:-1])
        min_value = min(lista[i][:-1])
        avg_value = sum(lista[i][:-1])/len(lista[i][:-1])
        df_yld.loc[index_list[i]] = [max_value, min_value, avg_value]
    return df_yld


def compute_rent_m15(date, serie_macro, icp):
    '''
    Generamos las rentabilidades para el macro 1.5
    '''
    m15_yld = compute_rent_icp(icp, date,  0.015)
    col_m15 = compute_col_m15(serie_macro, date)
    m15_yld = m15_yld.join(col_m15)
    yld_month = compute_yld_month(date, serie_macro)
    return m15_yld, yld_month


def compute_rent_icp(icp, date, pp):
    '''
    Entrega el retorno acomulado del icp y del icp + pp
    '''
    ytd_m15 = pd.DataFrame(columns=['Indice ICP', 'ICP + '])
    days_betwwen = len(fs.get_dates_between(
        dt.datetime(date.year, 1, 1), date))
    rent = 0
    for i in range(days_betwwen):
        aux_1 = icp.loc[
            date-dt.timedelta(days=days_betwwen-i-1)]['CLICP Index']
        aux_2 = icp.loc[date-dt.timedelta(days=days_betwwen-i)]['CLICP Index']
        rent += ((aux_1/aux_2)-1)
        rent_pp = rent+((i+1)*pp/365)
        ytd_m15.loc[date-dt.timedelta(days=days_betwwen-i-1)] = [100 + (100*rent), 100 + (100*rent_pp)]
    ytd_m15.loc[dt.date(date.year-1, 12, 31)] = [100, 100]
    return ytd_m15


def compute_col_m15(serie_macro, date):
    '''
    creamos la columna de rentabilidades del macro 15
    '''
    col_m15 = pd.DataFrame(columns=['9310-FM CC MACRO CLP 1.5'])
    rent_total = 0
    days_betwwen = len(fs.get_dates_between(
        dt.datetime(date.year, 1, 1), date))
    for i in range(days_betwwen):
        aux_1 = serie_macro.loc[
            date-dt.timedelta(days=days_betwwen-i-1)]['9310-FM CC MACRO CLP 1.5']
        aux_2 = serie_macro.loc[
            date-dt.timedelta(days=days_betwwen-i)]['9310-FM CC MACRO CLP 1.5']
        rent_total += ((aux_1/aux_2)-1)
        col_m15.loc[
            date-dt.timedelta(days=days_betwwen-i-1)] = [100 + (100*rent_total)]
    col_m15.loc[dt.date(date.year-1, 12, 31)] = [100]
    return col_m15


def compute_yld_month(date, serie_macro, tacs=None, m3=False):
    '''
    Entrega la rentabilidad del macro por mes o año
    '''
    #yld_month = pd.DataFrame(index=[2017, 2018], columns=[
                            # 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 'Total'])

    yld_month = pd.DataFrame(index=[2018, 2019], columns=[
                             1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 'Total'])
    dates_between = fs.get_dates_between(dt.datetime(date.year-1, 1, 1), date)
    if m3 is True:
        name = 'CRMAC3I CI Equity'
    else:
        name = '9310-FM CC MACRO CLP 1.5'
    month = 1
    year = date.year-1
    aux_month = 0
    aux_year = 0
    for d in dates_between:
        if d.month != month:
            yld_month.loc[year][month] = aux_month
            month = d.month
            aux_year += aux_month
            aux_month = 0
        if d.year != year:
            yld_month.loc[year]['Total'] = aux_year
            year = d.year
            aux_year = 0
        
        rent = (serie_macro.loc[d][name] /
                serie_macro.loc[d+dt.timedelta(days=-1)][name])-1
        if m3 is True:
            rent = rent +compute_tacs(tacs, d, 'MACRO CLP3')
        aux_month += rent
        if  d == dates_between[-1]:
            yld_month.loc[year][month] = aux_month
            yld_month.loc[year]['Total'] = aux_year

    return yld_month


def compute_rent_m3(date, serie_macro, icp, tacs):
    '''
    Generamos las rentabilidades para el macro 3
    '''
    m3_yld = compute_rent_icp(icp, date,  0.03)
    #fs.print_full(serie_macro)
    col_m3 = compute_col_m3(serie_macro, date,  tacs)

    m3_yld = m3_yld.join(col_m3)
    yld_month = compute_yld_month(date, serie_macro, tacs, m3=True)
    return m3_yld, yld_month


def compute_col_m3(icp, date, tacs):
    '''
    creamos la columna de rentabilidades del macro 3
    '''
    col_df = pd.DataFrame(columns=['CRMAC3I CI Equity'])
    col_df.loc[dt.date(date.year-1, 12, 31)] = [100]
    rent_total = 0
    days_betwwen = len(fs.get_dates_between(
        dt.datetime(date.year, 1, 1), date))
    for i in range(days_betwwen):
        aux_1 = icp.loc[
            date-dt.timedelta(days=days_betwwen-i-1)]['CRMAC3I CI Equity']
        aux_2 = icp.loc[
            date-dt.timedelta(days=days_betwwen-i)]['CRMAC3I CI Equity']
        rent_total += (((aux_1/aux_2)-1) + compute_tacs(tacs,
                                                        date-dt.timedelta(days=days_betwwen-i-1), 'MACRO CLP3'))
        col_df.loc[
            date-dt.timedelta(days=days_betwwen-i-1)] = [100 + (100*rent_total)]
    return col_df


def compute_rent_renta(ranking_renta, period):
    '''
    Generamos las rentabilidades para el renta
    '''
    ranking_renta = ranking_renta[['Administradora', 'Fondo', period]]
    ranking_renta = ranking_renta.sort_values([period], ascending=False)
    ranking_renta['Ranking'] = [k+1 for k in range(len(ranking_renta.index))]
    # calculamos el benchamark y lo agregamos
    benchamark = ranking_renta[period].mean()
    ranking_renta.loc['b'] = ['Benchmark', 0, benchamark, 0]
    # ordenamos y ponemos el rnaking como index
    ranking_renta = ranking_renta.sort_values([period], ascending=False)
    ranking_renta.set_index(["Ranking"], inplace=True)
    return ranking_renta


def get_inputs(name):
    '''
    Obtenemos inputs para trabajar
    '''
    wb = fs.open_workbook(".\\{}".format(name), False, False)
    serie_macro = fs.get_frame_xl(wb, "serie_macro", 1, 1, [0])
    serie_macro3 = fs.get_frame_xl(wb, "serie_macro3", 1, 1, [0])
    tacs = fs.get_frame_xl(wb, "tacs", 1, 1, [0])
    ranking_renta = fs.get_frame_xl(wb, "ranking_renta", 1, 1, [0])
    serie_eplus = fs.get_frame_xl(wb, "serie_eplus", 1, 1, [0])
    icp = fs.get_frame_xl(wb, "icp", 1, 1, [0])
    return serie_macro, serie_macro3, tacs, ranking_renta, serie_eplus, icp


def print_report_pdf(eplus_yld, afp_yld, eplus_yld_12m, afp_yld_12m, m15_yld, m15_yld_month, m3_yld, m3_yld_month, renta_yld, renta_yld_1y):
    '''
    Exporta el reporte a un pdf consolidado.
    '''
    # Abrimos el workbook con el template del informe
    wb = fs.open_workbook(path=".\\output_performance.xlsx",
                          screen_updating=True,
                          visible=True)
    # Borramos datos anteriores
    fs.clear_sheet_xl(wb=wb, sheet="eplus_yld")
    fs.clear_sheet_xl(wb=wb, sheet="afp_yld")
    fs.clear_sheet_xl(wb=wb, sheet="eplus_yld_12m")
    fs.clear_sheet_xl(wb=wb, sheet="afp_yld_12m")
    fs.clear_sheet_xl(wb=wb, sheet="m15_yld")
    fs.clear_sheet_xl(wb=wb, sheet="m15_yld_month")
    fs.clear_sheet_xl(wb=wb, sheet="m3_yld_month")
    fs.clear_sheet_xl(wb=wb, sheet="m3_yld")
    fs.clear_sheet_xl(wb=wb, sheet="renta_yld")
    fs.clear_sheet_xl(wb=wb, sheet="renta_yld_1y")

    # Insertamos nueva data
    fs.paste_val_xl(wb, "eplus_yld", 1, 1, eplus_yld)
    fs.paste_val_xl(wb, "afp_yld", 1, 1, afp_yld)
    fs.paste_val_xl(wb, "eplus_yld_12m", 1, 1, eplus_yld_12m)
    fs.paste_val_xl(wb, "afp_yld_12m", 1, 1, afp_yld_12m)
    fs.paste_val_xl(wb, "m15_yld", 1, 1, m15_yld)
    fs.paste_val_xl(wb, "m15_yld_month", 1, 1, m15_yld_month)
    fs.paste_val_xl(wb, "m3_yld", 1, 1, m3_yld)
    fs.paste_val_xl(wb, "m3_yld_month", 1, 1, m3_yld_month)
    fs.paste_val_xl(wb, "renta_yld", 1, 1, renta_yld)
    fs.paste_val_xl(wb, "renta_yld_1y", 1, 1, renta_yld_1y)
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)

def print_report_macros(m15_yld, m15_yld_month, m3_yld, m3_yld_month):
    '''
    Exporta el reporte a un pdf consolidado.
    '''
    # Abrimos el workbook con el template del informe
    wb = fs.open_workbook(path=".\\output_performance.xlsx",
                          screen_updating=True,
                          visible=True)
    # Borramos datos anteriores
   
    fs.clear_sheet_xl(wb=wb, sheet="m15_yld")
    fs.clear_sheet_xl(wb=wb, sheet="m15_yld_month")
    fs.clear_sheet_xl(wb=wb, sheet="m3_yld_month")
    fs.clear_sheet_xl(wb=wb, sheet="m3_yld")
    

    # Insertamos nueva data
    
    fs.paste_val_xl(wb, "m15_yld", 1, 1, m15_yld)
    fs.paste_val_xl(wb, "m15_yld_month", 1, 1, m15_yld_month)
    fs.paste_val_xl(wb, "m3_yld", 1, 1, m3_yld)
    fs.paste_val_xl(wb, "m3_yld_month", 1, 1, m3_yld_month)
   
    fs.save_workbook(wb=wb)
    fs.close_excel(wb=wb)


if __name__ == "__main__":
    serie_macro, serie_macro3, tacs, ranking_renta, serie_eplus, icp = get_inputs(
        'inputs.xlsx')
    date = dt.date(2019, 2, 28)
    dic_afp = {'AFPCAPE CI Equity': 'CAPITAL', 'AFPHABE CI Equity': 'HABITAT', 'AFPPLAE CI Equity': 'PLANVITAL',
               'AFPMODE CI Equity': 'MODELO', 'AFPCUPE CI Equity': 'CUPRUM', 'AFPPROE CI Equity': 'PROVIDA', 'FDIMEPS CI Equity': 'E Plus'}
    '''
    inic_afp = "2018-01-02" # para que la primera rentabilidad sea el 3 (fluctuacion del 2)
    inic_ep = "2017-12-31" #para que la primera rentabilidad sea la del 1
    dic_afp = {'AFPCAPE CI Equity': 'CAPITAL', 'AFPHABE CI Equity': 'HABITAT', 'AFPPLAE CI Equity': 'PLANVITAL',
               'AFPMODE CI Equity': 'MODELO', 'AFPCUPE CI Equity': 'CUPRUM', 'AFPPROE CI Equity': 'PROVIDA', 'FDIMEPS CI Equity': 'E Plus'}

    serie_ep = serie_eplus["FDIMEPS CI Equity"]
    serie_ep = serie_ep[serie_ep.index >= inic_ep]
    series_afp = serie_eplus.drop("FDIMEPS CI Equity", 1)
    series_afp = series_afp[series_afp.index >= inic_afp]
    serie_ep = serie_ep.sort_index(ascending=True)
    series_afp = series_afp.sort_index(ascending=True)
    serie_ep = serie_ep.pct_change()
    series_afp = series_afp.pct_change()
    print(series_afp)
    '''

    rentabilidad(date=date, 
                 dic_afp=dic_afp,
                 serie_macro15=serie_macro,
                 serie_macro3=serie_macro3,
                 tacs=tacs,
                 ranking_renta=ranking_renta,
                 serie_eplus=serie_eplus,
                 icp=icp,
                 date_eplus=dt.datetime(2019, 1, 1))#dt.datetime(2017, 12, 28)
