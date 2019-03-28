def update_flujos():
    # Busca los movimientos realizados el día de hoy y su vencimiento,
    # cruza las tablas Transacciones IIF (transacciones) y ZHIS_Carteras
    # (vencimientos)
    today = dt.date.today()
    yesterday = fs.get_ndays_from_today(1)
    path = ".\\Querys\\consulta_join.sql"
    query = fs.read_file(path=path).replace(
        "AUTODATE_SPOT", fs.convert_date_to_string(today)).replace("AUTODATE_YEST", yesterday)
    # print(query)
    df = fs.get_frame_sql_user(server='Puyehue', database='MesaInversiones',
                                query=query, username='usuario1', password='usuario1')
    df.fillna(value=0, inplace=True)
    # HAY QUE SEPARAR PARA VER CUALES PAGAN EN T+1, T+2 Y PONERLE SIGNO
    # NEGATIVO A LOS QUE COMPRAN

    df_cn_compra = df[(df['Liq'] == 'CN') & (
        df['Compra'] != 0)].reset_index(drop=True)
    df_cn_compra['Monto_Final'] = df_cn_compra['Monto'] * -1
    df_cn_compra['Fondo_Final'] = df_cn_compra['Compra']
    df_cn_compra['Fecha_Settle'] = df_cn_compra['Fecha'].apply(utiles.get_fecha_contado_normal)
    df_cn_compra = df_cn_compra[['Fecha', 'Instrumento', 'Moneda',
                                 'Liq', 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']]

    df_cn_vende = df[(df['Liq'] == 'CN') & (
        df['Vende'] != 0)].reset_index(drop=True)
    df_cn_vende['Monto_Final'] = df_cn_vende['Monto']
    df_cn_vende['Fondo_Final'] = df_cn_vende['Vende']
    df_cn_vende['Fecha_Settle'] = df_cn_vende[
        'Fecha'].apply(utiles.get_fecha_contado_normal)
    df_cn_vende = df_cn_vende[['Fecha', 'Instrumento', 'Moneda',
                               'Liq', 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']]

    df_pm_compra = df[(df['Liq'] == 'PM') & (
        df['Compra'] != 0)].reset_index(drop=True)
    df_pm_compra['Monto_Final'] = df_pm_compra['Monto'] * -1
    df_pm_compra['Fondo_Final'] = df_pm_compra['Compra']
    df_pm_compra['Fecha_Settle'] = df_pm_compra[
        'Fecha'].apply(utiles.get_fecha_habil_posterior)
    df_pm_compra = df_pm_compra[['Fecha', 'Instrumento', 'Moneda',
                                 'Liq', 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']]

    df_pm_vende = df[(df['Liq'] == 'PM') & (
        df['Vende'] != 0)].reset_index(drop=True)
    df_pm_vende['Monto_Final'] = df_pm_vende['Monto']
    df_pm_vende['Fondo_Final'] = df_pm_vende['Vende']
    df_pm_vende['Fecha_Settle'] = df_pm_vende[
        'Fecha'].apply(utiles.get_fecha_habil_posterior)
    df_pm_vende = df_pm_vende[['Fecha', 'Instrumento', 'Moneda',
                               'Liq', 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']]

    df_pmod = df[df['Liq'] == 'PMOD']
    # columns=['Fecha', 'Instrumento', 'Moneda', 'Liq', 'Fec_Vcto',
    # 'Monto_Final', 'Fondo_Final', 'Fecha_Settle'])
    df_pmod_final = pd.DataFrame()
    k = 0
    for i, j in df_pmod.iterrows():
        fecha = df_pmod.loc[i]['Fecha']
        instr = df_pmod.loc[i]['Instrumento']
        moneda = df_pmod.loc[i]['Moneda']
        liq = df_pmod.loc[i]['Liq']
        fec_vcto = df_pmod.loc[i]['Fec_Vcto']
        monto = df_pmod.loc[i]['Monto']
        fondo_compra = df_pmod.loc[i]['Compra']
        fondo_vende = df_pmod.loc[i]['Vende']
        fecha_settle = utiles.get_fecha_habil_posterior(df_pmod.loc[i]['Fecha'])
        row_compra = [[fecha, instr, moneda, liq, fec_vcto,
                       monto * (-1), fondo_compra, fecha_settle]]
        row_vende = [[fecha, instr, moneda, liq,
                      fec_vcto, monto, fondo_vende, fecha_settle]]
        df_pmod_final = df_pmod_final.append(row_compra, ignore_index=True)
        df_pmod_final = df_pmod_final.append(row_vende, ignore_index=True)
    try:
        df_pmod_final.columns = ['Fecha', 'Instrumento', 'Moneda', 'Liq',
                                 'Fec_Vcto', 'Monto_Final', 'Fondo_Final', 'Fecha_Settle']
    except:
        print('No existen transacciones "PMOD"')
    """
	with pd.option_context('display.max_rows', None, 'display.max_columns', None):
		print(df_cn_compra)
		print(df_cn_vende)
		print(df_pm_compra)
		print(df_pm_vende)
	"""
    df_final = pd.concat([df_cn_compra, df_cn_vende, df_pm_compra,
                          df_pm_vende, df_pmod_final], ignore_index=True)
    return df_final

vencimientos_portfolios