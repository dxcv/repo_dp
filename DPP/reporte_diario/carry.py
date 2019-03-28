import libreria_fdo as fs

def frame_fondo(fondos, date, plazo_dias=30):
    """
    Función que dada una lista de fondos, retorna la sumaproducto de sus columnas [weight]*[duration] y [weight]*[tasa] por fondo
    """
    # Seleccionamos todos los fondos en la fecha especificada
    query = "SELECT rtrim(ltrim(Codigo_Fdo)) as Fondo, weight, duration, tasa, rtrim(ltrim(moneda)) as moneda FROM ZHIS_Carteras_Recursive WHERE Codigo_Fdo in {}  and fecha = '{}'".format(fondos, date)
    df_carteras_fondos = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)
    query_monedas = "SELECT distinct(rtrim(ltrim(moneda))) as moneda from ZHIS_Carteras_Recursive WHERE Codigo_Fdo in {} and fecha = '{}'".format(fondos, date)
    
    # Creamos una lista con todas las monedas diferentes dentro de la cartera
    monedas = fs.get_frame_sql('Puyehue', 'MesaInversiones', query_monedas)
    monedas_lista = monedas['moneda'].tolist()

    # Cambiamos las monedas a float
    df_carteras_fondos['weight'] = df_carteras_fondos['weight'].astype(float)
    df_carteras_fondos['tasa'] = df_carteras_fondos['tasa'].astype(float)/100
    
    # Revisamos si queremos la yield anual o el devengo mensual
    """
    if mensual:
        UF_period_return = get_yield_UF(date, 30)
        factor = 1/12
    else:
        print('Se está calculando la yield anual de cada fondo...')
        UF_period_return = get_yield_UF(date, 365)
        factor = 1
    """
    UF_period_return = get_yield_UF(date, plazo_dias)
    
    factor = plazo_dias/360
    

    df_carteras_fondos['Tasa Final'] = 0
    for i in monedas_lista:
        tasa = 'tasa ' + i
        df_carteras_fondos[tasa] = df_carteras_fondos[df_carteras_fondos['moneda'] == i]['tasa']
        df_carteras_fondos.fillna(0, inplace=True)
        # Hacemos r_$_mensual = (r_ins/12) + rufmensual par las tasas en UF y r_$_mernsual = r_ins/12 para todo lo demás
        if tasa == 'tasa UF':
            df_carteras_fondos[tasa] = df_carteras_fondos[tasa] * factor + UF_period_return
        else:
            df_carteras_fondos[tasa] = df_carteras_fondos[tasa] * factor
        
        df_carteras_fondos['Tasa Final'] += df_carteras_fondos[tasa]
    
    df_carteras_fondos['Devengo'] = round(df_carteras_fondos['weight'] * df_carteras_fondos['Tasa Final'], 6)
    df_carteras_fondos['Duration'] = round(df_carteras_fondos['weight'] * df_carteras_fondos['duration'], 6)
    
    df_carteras_grouped = df_carteras_fondos.groupby(by=['Fondo']).sum()[['Devengo', 'Duration']]
    
    
    return df_carteras_grouped, df_carteras_fondos


def get_yield_UF(date, periodo):
    """
    Entrega la Yield de la UF para el periodo pedido
    """
    UF_fwd = get_UF_fwd(date, periodo)
    UF_spot = get_UF_spot(date)
    UF_return = (UF_fwd/UF_spot) - 1

    return UF_return


def get_UF_fwd(date, periodo):
    """
    Entrega la UF fwd al plazo pedido
    """
    query = "SELECT Yield FROM ZHIS_RA_Curves WHERE Curve_name = 'NDF UF/CLP' AND date = '{}' AND tenor = {}".format(date, periodo)
    # ojo que modifiqué le función get_val pq no funcionaba, tiene que correr con la libreria_fdo que está en esta carpeta
    UF_fwd = fs.get_val_sql('Puyehue', 'MesaInversiones', query)
    return UF_fwd


def get_UF_spot(date):
    """
    Entrega el valor de la UF spot
    """
    query = "SELECT Valor FROM Indices_Dinamica WHERE Index_Id = 23 AND Fecha = '{}'".format(date)
    UF_spot = fs.get_val_sql('Puyehue', 'MesaInversiones', query)
    return UF_spot


def output(date, workbook, fondos):
    
    # Calculamos ambas yield
    df_devengos_grouped, df_devengos_total = frame_fondo(fondos, date)
    df_yield_anual_grouped, df_yield_total = frame_fondo(fondos, date, 360)

    sht = workbook.sheets['Resumen']
    sht.range('B6').value = df_devengos_grouped
    sht.range('G6').value = df_yield_anual_grouped

    sht2 = workbook.sheets['Devengo']
    sht2.range('B7').value = df_devengos_total

    sht2 = workbook.sheets['Devengo Anual']
    sht2.range('B7').value = df_yield_total    

    # Seleccionamos los fondos (están en una lista pero así se le dan menos parámetros a la función)
    fondos = df_devengos_total['Fondo'].unique().tolist()

    for fondo in fondos:
        sht = workbook.sheets[fondo]
        df_fondo = df_devengos_total[df_devengos_total['Fondo'] == fondo].reset_index(drop=True)
        sht.range('A1').value = df_fondo
        print('Actualizados Devengos de ' + fondo)


print(frame_fondo(('DEUDA 360', 'LIQUIDEZ', 'RENTA', 'DEUDA CORP', 'SPREADCORP', 'IMT E-PLUS', 'MACRO 1.5', 'MACRO CLP3'), '2018-12-06', 365)[1])