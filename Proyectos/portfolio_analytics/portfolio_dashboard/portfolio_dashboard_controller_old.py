













































































    
    
    
    
    
    
    
    
    
    
    
        
                                            database="MesaInversiones",
                                            password="Comercial1w",
                                            query=query_fund)
                                            username="usrConsultaComercial",
                                           benchmark_date=fund_date,
                                           fund_date=fund_date,
                                           funds=funds,
                                           inflation=0.03)
                                       ascending=[True])
                                       database="MesaInversiones",
                                       database="MesaInversiones",
                                       database="MesaInversiones",
                                       database="MesaInversiones",
                                       database="MesaInversiones",
                                       database="MesaInversiones",
                                       database="MesaInversiones",
                                       database="MesaInversiones",
                                       inplace=True,
                                       password="Comercial1w",
                                       password="Comercial1w",
                                       password="Comercial1w",
                                       password="Comercial1w",
                                       password="Comercial1w",
                                       password="Comercial1w",
                                       password="Comercial1w",
                                       password="Comercial1w",
                                       query=query_duration)
                                       query=query_ep)
                                       query=query_inv_extranjero)
                                       query=query_moneda)
                                       query=query_plazos)
                                       query=query_posicionamiento)
                                       query=query_re)
                                       query=query_RF_soberano)
                                       username="usrConsultaComercial",
                                       username="usrConsultaComercial",
                                       username="usrConsultaComercial",
                                       username="usrConsultaComercial",
                                       username="usrConsultaComercial",
                                       username="usrConsultaComercial",
                                       username="usrConsultaComercial",
                                       username="usrConsultaComercial",
                                      database="MesaInversiones",
                                      database="MesaInversiones",
                                      password="Comercial1w",
                                      password="Comercial1w",
                                      query=portfolio_query)
                                      query=query)
                                      username="usrConsultaComercial",
                                      username="usrConsultaComercial",
                                    data_end_date=data_end_date)
                              database="MesaInversiones",
                              database="MesaInversiones",
                              database="MesaInversiones",
                              password="Comercial1w",
                              password="Comercial1w",
                              password="Comercial1w",
                              query=query)
                              query=query)
                              query=query)
                              username="usrConsultaComercial",
                              username="usrConsultaComercial",
                              username="usrConsultaComercial",
                            forward["nominal"] = -1*forward["nominal_venta"]
                            forward["nominal"] = forward["nominal_compra"]
                        attachment_paths=paths)
                        body=body,
                        else:
                        forward["currency_pair"] = currencies[i]+ "-" +currencies[j]
                        grouped_forwards.loc[index] = forward
                        grouped_forwards.loc[index] = forward
                        if currencies[j] == forward["moneda_compra"]:
                        mails=mail_list,
                    "cantidad", "duration_x", "precio", "tipo_ra"]
                    "duration_x": "duration"}
                    "fec_vtco", "tipo_instrumento_x", "moneda_x",
                    "moneda_x": "moneda",
                    "weight_x", "monto", "ctd", "ctr", "pcr", 
                    "weight_x": "weight",
                    currency_pair = [currencies[i], currencies[j]]
                    if long_currency in currency_pair and short_currency in currency_pair:
                if i > j:
            for j in  range(len(currencies)):
        currency_pair = cash_flow["currency_pair"]
        for i in range(len(currencies)):
        forwards_portfolios.append(fx_forwards)
        fund_id = cash_flow["codigo_fdo"] 
        fx_forwards = fs.get_frame_sql_user(server="Puyehue",
        grouped_forwards_aux.loc[(maturity_date, currency_pair)][fund_id] += nominal
        grouped_forwards_aux[fund_id] = 0.0
        long_currency = forward["moneda_compra"]
        maturity_date = cash_flow["fec_vcto"]
        nominal = cash_flow["nominal"]
        query_fund = query.replace("autofund", fund_id)
        short_currency = forward["moneda_venta"]
    # Consolidamos todos los documentos en uno y luego los borramos
    # Consolidamos todos los documentos en uno y luego los borramos
    # Finalmente agrupamos y sumamos por fondo
    # Guardamos backup
    # Guardamos backup
    # Guardamos y cerramos el excel
    # Guardamos y cerramos el excel
    # Luego hacemos el display con columnas por fondo
    # notar quye usdclp y clpusd van al mismo tag
    # Por cada forward lo tageamos vamos a tagear con su cros respectivo
    # portfolio["weight"] = portfolio["valoriz_cierre"] / portfolio["Valoriz_Total_Portfolio"]# para weight por aum
    # Sacamos todas las monedas para armas las combinacione
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    '''
    (cartera_govt["duration"]<1.5),
    (cartera_govt["duration"]<12.5) & (cartera_govt["moneda"]=='$')]
    (cartera_govt["duration"]<15.5) & (cartera_govt["moneda"]=='UF'),
    (cartera_govt["duration"]<3),
    (cartera_govt["duration"]<5),
    (cartera_govt["duration"]<9),
    Agregamos al dataframe una columna Weight, que muestra el peso del instrumento 
    Agrupa los forwards para ver el total por dia a netear. 
    bmk_last_date = fs.get_val_sql_user(server="Puyehue",
    bmk_last_date = fs.get_val_sql_user(server="Puyehue",
    body = "Adjunto dashboard de tasas y monedas.\nSaludos,\nBot"
    buckets=[1,3,5,10,20,20]
    buy_currencies = buy_currencies.unique()
    buy_currencies = forwards_portfolios["moneda_compra"]
    cartera_afp_sob = ep_benchmark_RF_soberano.set_index(['code'])
    cartera_govt["bucket"]=np.select(conditions,buckets,default=30)
    clf = fs.get_val_sql_user(server="Puyehue",
    columns_dict = {"tipo_instrumento_x": "tipo_instrumento",
    conditions = [
    core_columns = ["codigo_fdo", "codigo_emi", "codigo_ins",
    currencies = list(set(buy_currencies).union(sell_currencies))
    currencies.sort()
    date_string = bmk_last_date.strftime('%Y-%m-%d')
    date_string = bmk_last_date.strftime('%Y-%m-%d')
    del portfolio["Valoriz_Total_Portfolio"]
    dst = "L:\\Rates & FX\\fsb\\reporting\\portfolio_dashboard_backup\\" + name
    dst = "L:\\Rates & FX\\fsb\\reporting\\portfolio_dashboard_backup\\" + name
    dur_w = eplus_gob.groupby(["code"]).apply( lambda x: np.average(x['duration'], weights=x['weight']))
    en el portafolio total (compuesto por todos los instrumentos de todos los competidores)
    Envia el mail a fernando suarez y JPA. 
    ep_benchmark_duration = fs.get_frame_sql_user(server="Puyehue",
    ep_benchmark_duration.set_index(["Fecha"], inplace=True)
    ep_benchmark_inv_extranjero = fs.get_frame_sql_user(server="Puyehue",
    ep_benchmark_inv_extranjero.set_index(["Fecha"], inplace=True)
    ep_benchmark_moneda = fs.get_frame_sql_user(server="Puyehue",
    ep_benchmark_moneda.set_index(["Fecha"], inplace=True)
    ep_benchmark_plazos = fs.get_frame_sql_user(server="Puyehue",
    ep_benchmark_plazos.set_index(["Fecha"], inplace=True)
    ep_benchmark_posicionamiento = fs.get_frame_sql_user(server="Puyehue",
    ep_benchmark_posicionamiento.set_index(["Fecha"], inplace=True)
    ep_benchmark_RF_soberano = fs.get_frame_sql_user(server="Puyehue",
    ep_benchmark_RF_soberano["code"] = ep_benchmark_RF_soberano["bucket"].astype(str)+ep_benchmark_RF_soberano["moneda"]
    eplus = pd.concat([dur_w, eplus_gob], axis=1)
    eplus.rename(columns={0: 'dur_w'}, inplace=True)
    eplus_gob = eplus_gob.groupby(["code","moneda"]).agg('sum').drop('duration',1).reset_index().set_index('code')
    eplus_gob = eplus_gob[['moneda', 'weight','duration']]
    eplus_gob = get_buckets_soberanos(eplus_gob)
    eplus_gob= eplus_gob[eplus_gob["moneda"].isin(['$','UF'])]
    eplus_gob= eplus_portfolio.loc[(eplus_portfolio["tipo_instrumento"] == 'Bono de Gobierno')]
    eplus_gob["code"] = eplus_gob["bucket"].astype(str)+eplus_gob["moneda"]
    eplus_portfolio=portfolios.loc["IMT E-PLUS"]
    for fund_id in fund_ids:
    for fund_id in fund_ids:
    for i, cash_flow in grouped_forwards.iterrows():
    for index, forward in grouped_forwards.iterrows():
    Formatea el dataframe para trabajarlo mas facil
    Formatea el dataframe para trabajarlo mas facil
    Formatea el dataframe para trabajarlo mas facil
    forwards_portfolios = []
    forwards_portfolios = []
    forwards_portfolios = pd.concat(forwards_portfolios, ignore_index=True)	
    forwards_portfolios.set_index(["codigo_fdo", "fecha_op", "codigo_emi", "codigo_ins"], inplace=True)
    forwards_portfolios.sort_values(["days_to_maturity"], inplace=True, ascending=[True])
    forwards_portfolios["days_to_maturity"] = (pd.to_datetime(forwards_portfolios["fec_vcto"] ) - fs.convert_string_to_date(spot_date)).astype('timedelta64[D]')
    fs.clear_sheet_xl(wb, "ep_benchmark_portfolio")
    fs.clear_sheet_xl(wb, "ep_subportfolio")
    fs.clear_sheet_xl(wb, "forwards_portfolios")
    fs.clear_sheet_xl(wb, "forwards_portfolios")
    fs.clear_sheet_xl(wb, "grouped_forwards")
    fs.clear_sheet_xl(wb, "grouped_forwards")
    fs.clear_sheet_xl(wb, "parameters")
    fs.clear_sheet_xl(wb, "parameters")
    fs.clear_sheet_xl(wb, "parameters")
    fs.clear_sheet_xl(wb, "parameters")
    fs.clear_sheet_xl(wb, "portfolios")
    fs.clear_sheet_xl(wb, "portfolios")
    fs.clear_sheet_xl(wb, "re_benchmark_portfolio")
    fs.clear_sheet_xl(wb, "re_benchmark_portfolio")
    fs.clear_sheet_xl(wb, "re_subportfolio")
    fs.clear_sheet_xl(wb, "spreads_portfolio_ep")
    fs.clear_sheet_xl(wb, "spreads_portfolio_ep")
    fs.clear_sheet_xl(wb, "spreads_portfolio_re")
    fs.clear_sheet_xl(wb, "spreads_portfolio_re")
    fs.close_excel(wb=wb)
    fs.close_excel(wb=wb)
    fs.copy_file(src, dst)
    fs.copy_file(src, dst)
    fs.delete_file(path)
    fs.delete_file(path_out_dashboard_ep)
    fs.delete_file(path_out_dashboard_macros)
    fs.delete_file(path_out_dashboard_re)
    fs.delete_file(path_out_dashboard_re)
    fs.delete_file(path_out_grouped_forwards)
    fs.delete_file(path_out_grouped_forwards)
    fs.delete_file(path_out_portfolios)
    fs.delete_file(path_out_portfolios)
    fs.delete_file(path_out_portfolios_forwards)
    fs.delete_file(path_out_portfolios_forwards)
    fs.delete_file(path_out_spreads_portfolios)
    fs.delete_file(path_out_spreads_portfolios)
    fs.export_sheet_pdf(sheet_index_dashboard_ep, ".", path_out_dashboard_ep)
    fs.export_sheet_pdf(sheet_index_dashboard_macros, ".", path_out_dashboard_macros)
    fs.export_sheet_pdf(sheet_index_dashboard_re, ".", path_out_dashboard_re)
    fs.export_sheet_pdf(sheet_index_dashboard_re, ".", path_out_dashboard_re)
    fs.export_sheet_pdf(sheet_index_grouped_forwards, ".", path_out_grouped_forwards)
    fs.export_sheet_pdf(sheet_index_grouped_forwards, ".", path_out_grouped_forwards)
    fs.export_sheet_pdf(sheet_index_portfolios, ".", path_out_portfolios)
    fs.export_sheet_pdf(sheet_index_portfolios, ".", path_out_portfolios)
    fs.export_sheet_pdf(sheet_index_portfolios_forwards, ".", path_out_portfolios_forwards)
    fs.export_sheet_pdf(sheet_index_portfolios_forwards, ".", path_out_portfolios_forwards)
    fs.export_sheet_pdf(sheet_index_spreads_portfolios, ".", path_out_spreads_portfolios)
    fs.export_sheet_pdf(sheet_index_spreads_portfolios, ".", path_out_spreads_portfolios)
    fs.merge_pdf(path=".\\output\\", output_name="dashboard_rates_fx.pdf")
    fs.merge_pdf(path=".\\output\\", output_name="dashboard_rates_fx.pdf")
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 1, ep_benchmark_posicionamiento)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 11, ep_benchmark_duration)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 16, ep_benchmark_plazos)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 21, ep_benchmark_inv_extranjero)
    fs.paste_val_xl(wb, "ep_benchmark_portfolio", 1, 6, ep_benchmark_moneda)
    fs.paste_val_xl(wb, "ep_subportfolio", 1, 1, ep_subportfolio)
    fs.paste_val_xl(wb, "forwards_portfolios", 1, 1, forwards_portfolios)
    fs.paste_val_xl(wb, "forwards_portfolios", 1, 1, forwards_portfolios)
    fs.paste_val_xl(wb, "grouped_forwards", 1, 1, grouped_forwards)
    fs.paste_val_xl(wb, "grouped_forwards", 1, 1, grouped_forwards)
    fs.paste_val_xl(wb, "parameters", 1, 1, clf)
    fs.paste_val_xl(wb, "parameters", 1, 1, clf)
    fs.paste_val_xl(wb, "portfolios", 1, 1, portfolios)
    fs.paste_val_xl(wb, "portfolios", 1, 1, portfolios)
    fs.paste_val_xl(wb, "re_benchmark_portfolio", 1, 1, re_benchmark_portfolio)
    fs.paste_val_xl(wb, "re_benchmark_portfolio", 1, 1, re_benchmark_portfolio)
    fs.paste_val_xl(wb, "re_subportfolio", 1, 1, re_subportfolio)
    fs.paste_val_xl(wb, "sovereign_comparison", 1, 1, table_soberanos)
    fs.paste_val_xl(wb, "spreads_portfolio_ep", 1, 1, spreads_ep)
    fs.paste_val_xl(wb, "spreads_portfolio_ep", 1, 1, spreads_ep)
    fs.paste_val_xl(wb, "spreads_portfolio_re", 1, 1, spreads_re)
    fs.paste_val_xl(wb, "spreads_portfolio_re", 1, 1, spreads_re)
    fs.save_workbook(wb=wb)
    fs.save_workbook(wb=wb)
    fs.send_mail_attach(subject=subject,
    grouped_forwards = forwards_portfolios
    grouped_forwards = grouped_forwards.groupby(["codigo_fdo", "fec_vcto", "currency_pair", "days_to_maturity"])["nominal"].sum()
    grouped_forwards = grouped_forwards.reset_index()
    grouped_forwards = grouped_forwards.reset_index()
    grouped_forwards = grouped_forwards_aux
    grouped_forwards["currency_pair"] = None
    grouped_forwards["nominal"] = None
    grouped_forwards_aux = grouped_forwards[["fec_vcto", "currency_pair", "days_to_maturity"]]
    grouped_forwards_aux = grouped_forwards_aux.drop_duplicates()
    grouped_forwards_aux = grouped_forwards_aux.set_index(["fec_vcto", "currency_pair"])
    grouped_forwards_aux.sort_values(["days_to_maturity"],
    Lee el query del portafolio de competidores, y lo transforma en dataframe
    mail_list = ["dposch@credicorpcapital.com"]
    mail_list = ["fsuarez@credicorpcapital.com", "fsuarez1@uc.cl"]#, "jparaujo@credicorpcapital.com"
    matrix_columns = ["fec_vcto", "days_to_maturity", "currency_pair"]
    matrix_columns = matrix_columns + list(fund_ids)
    name = "Dashboard_Rates_FX_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    name = "Dashboard_Rates_FX_" + fs.get_ndays_from_today(0).replace("-","") + ".pdf"
    path = ".\\querys_portfolio_dashboard\\clf.sql"
    path = ".\\querys_portfolio_dashboard\\ep_benchmark_last_date.sql"
    path = ".\\querys_portfolio_dashboard\\fx_forwards.sql"
    path = ".\\querys_portfolio_dashboard\\portfolio_spreads.sql"
    path = ".\\querys_portfolio_dashboard\\re_benchmark_last_date.sql"
    path = ".\\querys_portfolio_dashboard\\re_benchmark_portfolios.sql"
    path = fs.get_self_path() + "output\\dashboard_rates_fx.pdf"
    path_duration = ".\\querys_portfolio_dashboard\\ep_benchamrk_duracion.sql"
    path_inv_extranjero = ".\\querys_portfolio_dashboard\\ep_benchamrk_inv_extranjero.sql"
    path_moneda = ".\\querys_portfolio_dashboard\\ep_benchamrk_moneda.sql"
    path_out_dashboard_ep = fs.get_self_path()+"output\\6.pdf"
    path_out_dashboard_macros = fs.get_self_path()+"output\\7.pdf"
    path_out_dashboard_re = fs.get_self_path()+"output\\5.pdf"
    path_out_dashboard_re = fs.get_self_path()+"output\\5.pdf"
    path_out_grouped_forwards = fs.get_self_path()+"output\\3.pdf"
    path_out_grouped_forwards = fs.get_self_path()+"output\\3.pdf"
    path_out_portfolios = fs.get_self_path()+"output\\1.pdf"
    path_out_portfolios = fs.get_self_path()+"output\\1.pdf"
    path_out_portfolios_forwards = fs.get_self_path()+"output\\2.pdf"
    path_out_portfolios_forwards = fs.get_self_path()+"output\\2.pdf"
    path_out_spreads_portfolios = fs.get_self_path()+"output\\4.pdf"
    path_out_spreads_portfolios = fs.get_self_path()+"output\\4.pdf"
    path_plazos = ".\\querys_portfolio_dashboard\\ep_benchamrk_plazos.sql"
    path_posicionamiento = ".\\querys_portfolio_dashboard\\ep_benchamrk_posicionamiento.sql"
    path_RF_soberano = ".\\querys_portfolio_dashboard\\ep_benchmark_RF_soberano.sql"
    paths = [path]
    portfolio = fs.get_frame_sql_user(server="Puyehue",
    portfolio = fs.get_frame_sql_user(server="Puyehue",
    portfolio = rebalance_benchmark(portfolio)
    portfolio.set_index(["codigo_fdo"], inplace=True)
    portfolio.set_index(["fecha", "run_fondo", "codigo_ins"], inplace=True)
    portfolio["ctd"] = portfolio["weight"] * portfolio["duration"]
    portfolio["valoriz_cierre"] = portfolio["valoriz_cierre"].astype(float)
    portfolio["Valoriz_Total_Portfolio"] = portfolio.groupby("fecha")["valoriz_cierre"].transform(sum)
    portfolio["weight"] = portfolio["weight"] / portfolio["weight"].sum()
    portfolio_query = fs.read_file(path)
    portfolio_query = portfolio_query.replace("autodate", date)
    portfolios = portfolios.reindex()
    portfolios = portfolios[core_columns]
    portfolios.loc[portfolios["tipo_instrumento"] == "FX", "tipo_instrumento"] = "Cash"
    portfolios.rename(columns=columns_dict, inplace=True)
    portfolios.set_index(["codigo_fdo", "codigo_emi", "codigo_ins", "fec_vtco"], inplace=True)
    query = "select codigo_emi as codigo_fdo, cantidad, monto from zhis_carteras_main where fecha = '{}' and codigo_fdo = '{}' and tipo_instrumento = 'cuota de fondo' order by monto desc"
    query = fs.read_file(path=path)
    query = fs.read_file(path=path)
    query = fs.read_file(path=path)
    query = fs.read_file(path=path).replace("autodate", date)
    query = fs.read_file(path=path).replace("autodate", spot_date)
    query = query.format(date, fund_id)
    query_duration = fs.read_file(path=path_duration).replace("autodate", date)
    query_ep = query.replace("autofund", "IMT E-PLUS")
    query_inv_extranjero = fs.read_file(path=path_inv_extranjero).replace("autodate", date)
    query_moneda = fs.read_file(path=path_moneda).replace("autodate", date)
    query_plazos = fs.read_file(path=path_plazos).replace("autodate", date)
    query_posicionamiento = fs.read_file(path=path_posicionamiento).replace("autodate", date)
    query_re = query.replace("autofund", "RENTA")
    query_RF_soberano = fs.read_file(path=path_RF_soberano)
    Retorna el portfolio de cuotas de fondos.
    Retorna el portfolio de fx forwards.
    Retorna la fecha más reciente del portafolio del benchmark del renta
    Retorna la fecha más reciente del portafolio del fondo E de AFPs
    Retorna la uf spot en la base de datos.
    Retorna los cortes del portafolio del fondo E de AFPs
    Retorna los portafolios de los spreads.
    return cartera_govt
    return clf
    return date_string
    return date_string
    return ep_benchmark_duration, ep_benchmark_moneda, ep_benchmark_posicionamiento, ep_benchmark_plazos, ep_benchmark_inv_extranjero, ep_benchmark_RF_soberano
    return forwards_portfolios
    return grouped_forwards
    return portfolio
    return portfolio
    return portfolio
    return portfolios
    return spreads_re, spreads_ep
    return table_soberanos
    sell_currencies = forwards_portfolios["moneda_venta"]
    sell_currencies = sell_currencies.unique()
    sheet_index_dashboard_ep = fs.get_sheet_index(wb, "display_dashboard_ep") - 1
    sheet_index_dashboard_macros = fs.get_sheet_index(wb, "display_dashboard_macros") - 1
    sheet_index_dashboard_re = fs.get_sheet_index(wb, "display_dashboard_re") - 1
    sheet_index_dashboard_re = fs.get_sheet_index(wb, "display_dashboard_re") - 1
    sheet_index_grouped_forwards = fs.get_sheet_index(wb, "display_grouped_forwards") - 1
    sheet_index_grouped_forwards = fs.get_sheet_index(wb, "display_grouped_forwards") - 1
    sheet_index_portfolios = fs.get_sheet_index(wb, "display_portfolios") - 1
    sheet_index_portfolios = fs.get_sheet_index(wb, "display_portfolios") - 1
    sheet_index_portfolios_forwards = fs.get_sheet_index(wb, "display_portfolios_forwards") - 1
    sheet_index_portfolios_forwards = fs.get_sheet_index(wb, "display_portfolios_forwards") - 1
    sheet_index_spreads_portfolios = fs.get_sheet_index(wb, "display_spreads_portfolios") - 1
    sheet_index_spreads_portfolios = fs.get_sheet_index(wb, "display_spreads_portfolios") - 1
    spreads_ep = fs.get_frame_sql_user(server="Puyehue",
    spreads_ep.set_index(["codigo_fdo", "codigo_ins"], inplace=True)
    spreads_re = fs.get_frame_sql_user(server="Puyehue",
    spreads_re.set_index(["codigo_fdo", "codigo_ins"], inplace=True)
    src = ".\\output\\dashboard_rates_fx.pdf"
    src = ".\\output\\dashboard_rates_fx.pdf"
    subject = "Dashboard Portfolios Rates & FX"
    table_soberanos = pd.merge( eplus, cartera_afp_sob, how='outer', left_index=True, right_index=True, suffixes=('_eplus', '_afp'))
    table_soberanos = table_soberanos.sort_values(["moneda","bucket"], ascending=[True, True])
    table_soberanos = table_soberanos[["bucket","moneda","weight_eplus","weight_afp","dur_w_eplus", "dur_w_afp"]].reset_index(drop=True).set_index(table_soberanos["bucket"].astype(str) + "Y")
    table_soberanos.fillna(0.0,inplace=True)
    table_soberanos["ACT_DV01"] = table_soberanos["dur_w_eplus"] * table_soberanos["weight_eplus"] - table_soberanos["dur_w_afp"]*table_soberanos["weight_afp"]
    table_soberanos["bucket"] = np.where(table_soberanos["bucket_afp"] is None, table_soberanos["bucket_eplus"], table_soberanos["bucket_afp"])
    table_soberanos["bucket"] = table_soberanos["bucket"].apply(pd.to_numeric)
    table_soberanos["delta"] = table_soberanos["weight_eplus"] - table_soberanos["weight_afp"]
    table_soberanos["moneda"] = np.where(table_soberanos["moneda_afp"] is None, table_soberanos["moneda_eplus"], table_soberanos["moneda_afp"])
    wb = fs.open_workbook("portfolio_dashboard.xlsx", True, True)
    wb = fs.open_workbook("portfolio_dashboard.xlsx", True, True)
"""
"""
# benchmark date e inflation son dummy values porque para
# Cerramos posibles instancias de Excel abiertas
# Contruimos una matriz de varianza-covarianza
# de la matriz de varianza covarianza
# Descargamos los portfolios de forwards
# el ultimo dato para la matriz de varianza-covarianza
# el vector de weights de los portafolios
# Enviamos el dashboard por mail
# este monitor y fondos no aplican
# exponentially weighted en base al dataset
# Fijamos la fecha en la que empieza el dataset
# Fijamos la fecha para la cual se tomara
# Fijamos la fecha para la cual se tomara
# Formateamos los portfolios para el display
# fs.kill_excel()
# Imprimimos dashboards en excel
# Obtenemos el dataset con toda la informacion historica
# Obtenemos la cartera del benchmark del e-plus
# Obtenemos la cartera del benchmark del renta
# Obtenemos la lista de los fondos con su {-informacion basica
# Obtenemos la uf
# Obtenemos las cuotas de fondos en nuestros portfolios
# Obtenemos los forwards agrupados
# Obtenemos los spreads
# Para desabilitar warnings
# y obtenemos todos los portafolios activos con sus metricas de riesgo
#exit()
#Fijamos la fecha del benchmark como la más reciente disponible
#print(10000*np.sum(portfolios[portfolios["codigo_fdo"]=="MACRO 1.5"]["ctr"]))
#print(portfolios[portfolios["codigo_fdo"]=="MACRO 1.5"].loc[49])
@author: Fernando Suarez
clf = get_clf()
compute_dashboards(portfolios, forwards_portfolios, grouped_forwards, spreads_re, spreads_ep, re_benchmark_portfolio, clf, ep_benchmark_posicionamiento, ep_benchmark_moneda, ep_benchmark_duration, ep_benchmark_plazos, ep_benchmark_inv_extranjero, re_subportfolio, ep_subportfolio, table_soberanos)
Created on Thu Aug 10 11:00:00 2017
data_end_date = fs.get_prev_weekday(fund_date)
data_start_date = fs.get_ndays_from_date(365, spot_date)
dataset = rk.get_historical_dataset(data_start_date=data_start_date,
def compute_dashboards(portfolios, forwards_portfolios, grouped_forwards, spreads_re, spreads_ep, re_benchmark_portfolio, clf, ep_benchmark_posicionamiento, ep_benchmark_moneda, ep_benchmark_duration, ep_benchmark_plazos, ep_benchmark_inv_extranjero, re_subportfolio, ep_subportfolio, table_soberanos):
def compute_dashboardsANTIGUO(portfolios, forwards_portfolios, grouped_forwards, spreads_re, spreads_ep, re_benchmark_portfolio, clf):
def compute_grouped_forwards(forwards_portfolios, fund_ids):
def compute_table_soberanos(portfolios, ep_benchmark_RF_soberano):
def get_buckets_soberanos(cartera_govt):
def get_clf():
def get_ep_benchmark(date):
def get_ep_benchmark_last_date():
def get_forwards_portfolios(spot_date, fund_ids):
def get_re_benchmark(date):
def get_re_benchmark_last_date():
def get_spreads_portfolios(date):
def get_subportfolios(date, fund_id):
def rebalance_benchmark(portfolio):
def reshape_portfolios(portfolios):
def send_mail_report():
ep_benchmark_duration, ep_benchmark_moneda, ep_benchmark_posicionamiento, ep_benchmark_plazos, ep_benchmark_inv_extranjero, ep_benchmark_RF_soberano = get_ep_benchmark(ep_bmk_date)
ep_bmk_date = get_ep_benchmark_last_date()
ep_subportfolio = get_subportfolios(fund_date, "IMT E-PLUS")
forwards_portfolios = get_forwards_portfolios(spot_date, fund_ids)
fund_date = fs.get_prev_weekday(spot_date)
fund_ids = ("RENTA", "IMT E-PLUS", "MACRO 1.5", "MACRO CLP3")
funds = funds[funds["codigo_fdo"].isin(fund_ids)]
funds = rk.get_funds()
grouped_forwards = compute_grouped_forwards(forwards_portfolios, fund_ids)
import libreria_fdo as fs
import numpy as np
import os
import pandas as pd
import risk as rk
import sys
import warnings
matrix = rk.get_ewma_cov_matrix(data=dataset, landa=0.94)
pd.options.mode.chained_assignment = None 
portfolios = reshape_portfolios(portfolios)
portfolios = rk.get_full_portfolio_metrics(matrix=matrix,
print("Computing benchmark portfolios...")
print("Computing display...")
print("Computing ex ante volatility...")
print("Computing exponentially weighted covariance matrix...")
print("Computing grouped forwards...")
print("Computing portfolios spreads...")
print("Computing subportfolios...")
print("Fetching clf spot...")
print("Fetching forwards portfolios...")
print("Fetching historical dataset...")
print("Printing dashboard...")
print("Sending mail...")
re_benchmark_portfolio = get_re_benchmark(re_bmk_date)
re_bmk_date = get_re_benchmark_last_date()
re_subportfolio = get_subportfolios(fund_date, "RENTA")
send_mail_report()
spot_date = fs.get_ndays_from_today(0)
spreads_re, spreads_ep = get_spreads_portfolios(data_end_date)
sys.path.insert(0, '../../libreria/')
sys.path.insert(1, '../risk_library/')
table_soberanos = compute_table_soberanos(portfolios, ep_benchmark_RF_soberano)
warnings.filterwarnings("ignore") 