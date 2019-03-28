import sys
sys.path.insert(0,'../libreria/')
sys.path.insert(0,'../portfolio_analytics/utiles')
import libreria_fdo as fs
import utiles as utiles

def get_carry(fondos, date, plazo_dias=30):
    """
    Función que dada una lista de fondos, retorna la sumaproducto de sus columnas [weight]*[duration] y [weight]*[tasa] por fondo
    """
    # Seleccionamos todos los fondos en la fecha especificada
    query = "SELECT rtrim(ltrim(Codigo_Fdo)) as Fondo, codigo_ins, weight, duration, tasa, rtrim(ltrim(moneda)) as moneda FROM ZHIS_Carteras_Recursive WHERE Codigo_Fdo in ( {} )  and fecha = '{}'".format(fondos, date)
    df_carteras_full = fs.get_frame_sql('Puyehue', 'MesaInversiones', query)

    df_rezagados = df_carteras_full[df_carteras_full['tasa']==0]
    df_carteras = df_carteras_full[~df_carteras_full['codigo_ins'].isin(df_rezagados['codigo_ins'])]

    query_monedas = "SELECT distinct(rtrim(ltrim(moneda))) as moneda from ZHIS_Carteras_Recursive WHERE Codigo_Fdo in ({}) and fecha = '{}'".format(fondos, date)
    
    # Creamos una lista con todas las monedas diferentes dentro de la cartera
    monedas = fs.get_frame_sql('Puyehue', 'MesaInversiones', query_monedas)
    monedas_lista = monedas['moneda'].tolist()

    # Cambiamos las monedas a float
    df_carteras['weight'] = df_carteras['weight'].astype(float)
    df_carteras['tasa'] = df_carteras['tasa'].astype(float)/100
    
    UF_period_return = utiles.get_yield_UF(date, plazo_dias)
    
    factor = plazo_dias/360
    df_carteras['tasa_final'] = 0

    for i in monedas_lista:
        tasa = 'tasa_' + i
        df_carteras[tasa] = df_carteras[df_carteras['moneda'] == i]['tasa']
        df_carteras.fillna(0, inplace=True)
        # Hacemos r_$_mensual = (r_ins/12) + rufmensual par las tasas en UF y r_$_mernsual = r_ins/12 para todo lo demás
        if tasa == 'tasa UF':
            df_carteras[tasa] = df_carteras[tasa] * factor + UF_period_return
        else:
            df_carteras[tasa] = df_carteras[tasa] * factor
        
        df_carteras['tasa_final'] += df_carteras[tasa]
    
    df_carteras['Devengo'] = round(df_carteras['weight'] * df_carteras['tasa_final'], 6)
    df_carteras['Duration'] = round(df_carteras['weight'] * df_carteras['duration'], 6)
    
    df_carry = df_carteras.groupby(by=['Fondo']).sum()[['Devengo', 'Duration']]
    
    return df_carry