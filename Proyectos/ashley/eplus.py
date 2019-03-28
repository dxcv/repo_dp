"""
Created on Tue Aug 22 11:00:00 2017

@author: Ashley Mac Gregor
"""

import sys
sys.path.insert(0, '../libreria/')
import libreria_fdo as fs
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup




f = open("cartera_agregada201710.xml", encoding="utf8")
cartera_xml = f.read()
f.close()
y = BeautifulSoup(cartera_xml, "html.parser")


'''
Cuadro 2: CARTERA AGREGADA DE LOS FONDOS DE PENSIONES TIPO E POR AFP
'''
columnas = y.find_all("listado")[1].find_all("tipofondo")[4].find_all("fila")[0].find_all("afp")


nombre_columnas = ["",]
for t in columnas:
    nombre_afp = t.find("nombre").text
    nombre_columnas.append(nombre_afp)
    if nombre_afp == "PROVIDA":
        nombre_columnas.append("Total(monto)")
        nombre_columnas.append("Total(porcentaje)")




fila = y.find_all("listado")[1].find_all("tipofondo")[4].find_all("fila")

total_filas = []
for filas in fila:
    datos_fila = [filas.find("glosa").text,]
    afp_fila = filas.find_all("afp")
    for t in afp_fila:
        monto_dolares = t.find("monto_dolares").text
        datos_fila.append(monto_dolares)
        
    total_fila = filas.find_all("total")
    for t in total_fila:
        total_monto = t.find("monto_dolares").text
        total_porcentaje = t.find("porcentaje").text
        datos_fila.append(total_monto)
        datos_fila.append(total_porcentaje)
    total_filas.append(datos_fila)


cuadro_2 = pd.DataFrame(total_filas, columns=nombre_columnas)

cuadro_2 = cuadro_2.convert_objects(convert_numeric=True).fillna(0)
cuadro_2["CAPITAL"] = cuadro_2["CAPITAL"].astype(float)
cuadro_2["CUPRUM"] = cuadro_2["CUPRUM"].astype(float)
cuadro_2["HABITAT"] = cuadro_2["HABITAT"].astype(float)
cuadro_2["MODELO"] = cuadro_2["MODELO"].astype(float)
cuadro_2["PLANVITAL"] = cuadro_2["PLANVITAL"].astype(float)
cuadro_2["PROVIDA"] = cuadro_2["PROVIDA"].astype(float)
cuadro_2["Total(monto)"] = cuadro_2["Total(monto)"].astype(float)
cuadro_2["Total(porcentaje)"] = cuadro_2["Total(porcentaje)"].astype(float)
print(cuadro_2)

'''
Cuadro 3.a: ACTIVOS DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO, DIVERSIFICACIÓN POR INSTRUMENTOS FINANCIEROS (por tipo de fondo, valores en %fondo)
'''

columnas_3_a = y.find_all("listado")[2].find_all("fila")[0].find_all("tipofondo")


nombre_columnas_3_a = ["",]
for t in columnas_3_a:
    tipo_fondo = t["codigo"]
    nombre_columnas_3_a.append(tipo_fondo)



fila_3_a = y.find_all("listado")[2].find_all("fila")
print(len(fila_3_a))

total_filas_3_a = []
for filas in fila_3_a:
    datos_fila_3_a = [filas.find("glosa").text,]
    tipofondo_fila = filas.find_all("tipofondo")
    for t in tipofondo_fila:
        datos = t.find(True).text
        datos_fila_3_a.append(datos)
    total_filas_3_a.append(datos_fila_3_a)


cuadro_3_a = pd.DataFrame(total_filas_3_a, columns=nombre_columnas_3_a)

print(cuadro_3_a)


'''
Cuadro 3.b: ACTIVOS DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO, DIVERSIFICACIÓN POR INSTRUMENTOS FINANCIEROS (total)
'''


nombre_columnas_3_b = ["","MM$","MMUS$","%Fondo"]


fila_3_b = y.find_all("listado")[2].find_all("fila")


total_filas_3_b = []
for filas in fila_3_b:
    datos_fila_3_b = [filas.find("glosa").text,]
    monto_pesos = filas.find("total").find("monto_pesos").text
    monto_dolares = filas.find("total").find("monto_dolares").text
    porcentaje = filas.find("total").find("porcentaje").text
    datos_fila_3_b.append(monto_pesos)
    datos_fila_3_b.append(monto_dolares)
    datos_fila_3_b.append(porcentaje)
    total_filas_3_b.append(datos_fila_3_b)


cuadro_3_b = pd.DataFrame(total_filas_3_b, columns=nombre_columnas_3_b)

print(cuadro_3_b)


'''
CUADRO Nº 4_a: TASAS DE VALORACIÓN POR TIPO DE INSTRUMENTO FINANCIERO DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO (Tasa de Interes)
'''

columnas_4_a = y.find_all("listado")[3].find_all("fila")[0].find_all("tipofondo")


nombre_columnas_4_a = ["Tipo de instrumento","Unidad de Indexación",]
for t in columnas_4_a:
    tipo_fondo = t["codigo"]
    nombre_columnas_4_a.append(tipo_fondo)
    if tipo_fondo == "E":
        nombre_columnas_4_a.append("Total")

print(nombre_columnas_4_a)



fila_4_a = y.find_all("listado")[3].find_all("fila")


total_filas_4_a = []
for filas in fila_4_a:
    datos_fila_4_a = [filas.find("glosa").text,filas.find("unidad_indexada").text,]
    tipofondo_fila = filas.find_all("tipofondo")
    for t in tipofondo_fila:
        datos = t.find("tasa_interes").text
        datos_fila_4_a.append(datos)
    total_fila = filas.find_all("total")
    for t in total_fila:
        datos = t.find("tasa_interes").text
        datos_fila_4_a.append(datos)
    total_filas_4_a.append(datos_fila_4_a)


cuadro_4_a = pd.DataFrame(total_filas_4_a, columns=nombre_columnas_4_a)

print(cuadro_4_a)


'''
CUADRO Nº 4_b: TASAS DE VALORACIÓN POR TIPO DE INSTRUMENTO FINANCIERO DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO (% Invertido)
'''

columnas_4_b = y.find_all("listado")[3].find_all("fila")[0].find_all("tipofondo")

nombre_columnas_4_b = ["Tipo de instrumento","Unidad de Indexación",]
for t in columnas_4_b:
    tipo_fondo = t["codigo"]
    nombre_columnas_4_b.append(tipo_fondo)
    if tipo_fondo == "E":
        nombre_columnas_4_b.append("Total")



fila_4_b = y.find_all("listado")[3].find_all("fila")

total_filas_4_b = []
for filas in fila_4_b:
    datos_fila_4_b = [filas.find("glosa").text,filas.find("unidad_indexada").text,]
    tipofondo_fila = filas.find_all("tipofondo")
    for t in tipofondo_fila:
        datos = t.find("porcentaje").text
        datos_fila_4_b.append(datos)
    total_fila = filas.find_all("total")
    for t in total_fila:
        datos = t.find("porcentaje").text
        datos_fila_4_b.append(datos)
    total_filas_4_b.append(datos_fila_4_b)


cuadro_4_b = pd.DataFrame(total_filas_4_b, columns=nombre_columnas_4_b)
cuadro_4_b = cuadro_4_b.convert_objects(convert_numeric=True).fillna(0)
cuadro_4_b["E"] = cuadro_4_b["E"].astype(float)


print(cuadro_4_b)

'''
CUADRO Nº 7: PLAZO PROMEDIO DE LAS INVERSIONES DE LOS FONDOS DE PENSIONES POR TIPO DE FONDO E INSTRUMENTO (1)
'''

columnas_7 = y.find_all("listado")[6].find_all("fila")[0].find_all("tipofondo")

nombre_columnas_7 = ["Instituciones",]
for t in columnas_7:
    tipo_fondo = t["codigo"]
    nombre_columnas_7.append(tipo_fondo)
    if tipo_fondo == "E":
        nombre_columnas_7.append("Sistema")



fila_7 = y.find_all("listado")[6].find_all("fila")

total_filas_7 = []
for filas in fila_7:
    datos_fila_7 = [filas.find("glosa").text,]
    tipofondo_fila = filas.find_all("tipofondo")
    for t in tipofondo_fila:
        datos = t.find("plazo").text
        datos_fila_7.append(datos)
    total_fila = filas.find_all("total")
    for t in total_fila:
        datos = t.find("plazo").text
        datos_fila_7.append(datos)
    total_filas_7.append(datos_fila_7)


cuadro_7 = pd.DataFrame(total_filas_7, columns=nombre_columnas_7)

print(cuadro_7)

'''
CUADRO Nº 22: INVERSIÓN EN EL EXTRANJERO DE LOS FONDOS DE PENSIONES, DIVERSIFICACIÓN POR TIPO DE FONDO Y MONEDA
'''

columnas_22 = y.find_all("listado")[21].find_all("fila")[0].find_all("tipofondo")

nombre_columnas_22 = ["Moneda",]
for t in columnas_22:
    tipo_fondo = t["codigo"]
    nombre_columnas_22.append(tipo_fondo)
    if tipo_fondo == "E":
        nombre_columnas_22.append("Total")
        nombre_columnas_22.append("% sobre el total del Fondo de Pensiones")
        nombre_columnas_22.append("% sobre inversion total extranjero")



fila_22 = y.find_all("listado")[21].find_all("fila")

total_filas_22 = []
for filas in fila_22:
    datos_fila_22 = [filas.find("glosa").text,]
    tipofondo_fila = filas.find_all("tipofondo")
    for t in tipofondo_fila:
        datos = t.find("monto_dolares").text
        datos_fila_22.append(datos)
    total_fila = filas.find_all("total")
    for t in total_fila:
        datos_monto = t.find("monto_dolares").text
        datos_porcentaje = t.find("porcentaje").text
        datos_porcentaje_sobre_extranjero = t.find("porcentaje_sobre_extranjero").text
        datos_fila_22.append(datos_monto)
        datos_fila_22.append(datos_porcentaje)
        datos_fila_22.append(datos_porcentaje_sobre_extranjero)
    total_filas_22.append(datos_fila_22)


cuadro_22 = pd.DataFrame(total_filas_22, columns=nombre_columnas_22)

print(cuadro_22)

'''
CUADRO Nº 27 y 28: CARTERA DE LOS FONDOS DE PENSIONES EN INSTRUMENTOS FORWARD NACIONALES Y EXTRANJEROS EN FUNCION DEL ACTIVO OBJETO MONEDA, 
MONEDA CONTRAPARTE Y POR TIPO DE FONDO (1)
'''

columnas_27_28 = y.find_all("listado")[26].find_all("fila")[0].find_all("tipofondo")

nombre_columnas_27_28 = [y.find_all("listado")[26].find_all("fondos_por_moneda_objeto")[0].find("fondos_por_agrupacion")["agrupacion_instrumentos"],
"Nac/Internac", "Moneda Objeto",]
for t in columnas_27_28:
    tipo_fondo = t["codigo"]
    nombre_columnas_27_28.append(tipo_fondo)
    if tipo_fondo == "E":
        nombre_columnas_27_28.append("Total")



moneda_objeto_27 = y.find_all("listado")[26].find_all("fondos_por_moneda_objeto")

total_filas_27 = []
for i in moneda_objeto_27:
    fila_27 = i.find_all("fila")
    for filas in fila_27:
        datos_fila_27 = [filas.find("glosa").text,"Nacional",i["moneda_objeto"],]
        tipofondo_fila = filas.find_all("tipofondo")
        for t in tipofondo_fila:
            datos = t.find("monto_dolares").text
            datos_fila_27.append(datos)
        total_fila = filas.find_all("total")
        for t in total_fila:
            datos_monto = t.find("monto_dolares").text
            datos_fila_27.append(datos_monto)

        total_filas_27.append(datos_fila_27)


moneda_objeto_28 = y.find_all("listado")[27].find_all("fondos_por_moneda_objeto")

total_filas_28 = []
for i in moneda_objeto_28:
    fila_28 = i.find_all("fila")
    for filas in fila_28:
        datos_fila_28 = [filas.find("glosa").text,"Internacional",i["moneda_objeto"],]
        tipofondo_fila = filas.find_all("tipofondo")
        for t in tipofondo_fila:
            datos = t.find("monto_dolares").text
            datos_fila_28.append(datos)
        total_fila = filas.find_all("total")
        for t in total_fila:
            datos_monto = t.find("monto_dolares").text
            datos_fila_28.append(datos_monto)

        total_filas_28.append(datos_fila_28)



total_filas_27_28 = total_filas_27 + total_filas_28


cuadro_27_28 = pd.DataFrame(total_filas_27_28, columns=nombre_columnas_27_28)

print(cuadro_27_28)


'''
CUADRO Nº 27 y 28 Ajustada: CARTERA DE LOS FONDOS DE PENSIONES EN INSTRUMENTOS FORWARD NACIONALES Y EXTRANJEROS EN FUNCION DEL ACTIVO OBJETO MONEDA, 
MONEDA CONTRAPARTE Y POR TIPO DE FONDO (1)
'''

columnas_27_28_ajus = y.find_all("listado")[26].find_all("fila")[0].find_all("tipofondo")

nombre_columnas_27_28_ajus = [y.find_all("listado")[26].find_all("fondos_por_moneda_objeto")[0].find("fondos_por_agrupacion")["agrupacion_instrumentos"],
"Nac/Internac", "Moneda Objeto",]
for t in columnas_27_28_ajus:
    tipo_fondo = t["codigo"]
    nombre_columnas_27_28_ajus.append(tipo_fondo)
    if tipo_fondo == "E":
        nombre_columnas_27_28_ajus.append("Total")
        nombre_columnas_27_28_ajus.append("V/C")



moneda_objeto_27_ajus = y.find_all("listado")[26].find_all("fondos_por_moneda_objeto")

total_filas_27_ajus = []
for i in moneda_objeto_27_ajus:
    fila_27_ajus = i.find_all("fila")
    for filas in fila_27_ajus:
        #sacamos los subtotales o subgrupos (compra o venta) de entremedio de la tabla:
        if filas.find("glosa").text.isupper()==False:
            datos_fila_27_ajus = [filas.find("glosa").text,"Nacional",i["moneda_objeto"],]
            tipofondo_fila = filas.find_all("tipofondo")
            for t in tipofondo_fila:
                datos = t.find("monto_dolares").text
                datos_fila_27_ajus.append(datos)
            total_fila = filas.find_all("total")
            for t in total_fila:
                datos_monto = t.find("monto_dolares").text
                datos_fila_27_ajus.append(datos_monto)
            #se asigna a cada fila la identificación si se trata de compra o venta:
            d=[]   
            for f in filas.find_previous_siblings(): 
                if f.find("glosa").text.isupper()==True: 
                    c_v = f.find("glosa").text
                    d.append(c_v)
                    break
            datos_fila_27_ajus.extend(d)


            total_filas_27_ajus.append(datos_fila_27_ajus)



moneda_objeto_28_ajus = y.find_all("listado")[27].find_all("fondos_por_moneda_objeto")

total_filas_28_ajus = []
for i in moneda_objeto_28_ajus:
    fila_28_ajus = i.find_all("fila")
    for filas in fila_28_ajus:
        if filas.find("glosa").text.isupper()==False:
            datos_fila_28_ajus = [filas.find("glosa").text,"Internacional",i["moneda_objeto"],]
            tipofondo_fila = filas.find_all("tipofondo")
            for t in tipofondo_fila:
                datos = t.find("monto_dolares").text
                datos_fila_28_ajus.append(datos)
            total_fila = filas.find_all("total")
            for t in total_fila:
                datos_monto = t.find("monto_dolares").text
                datos_fila_28_ajus.append(datos_monto)
            d=[]   
            for f in filas.find_previous_siblings(): 
                if f.find("glosa").text.isupper()==True: 
                    c_v = f.find("glosa").text
                    d.append(c_v)
                    break
            datos_fila_28_ajus.extend(d)

            total_filas_28_ajus.append(datos_fila_28_ajus)



#se unen ambos conjuntos de filas nacional e internacional
total_filas_27_28_ajus = total_filas_27_ajus + total_filas_28_ajus

#se crea el dataframe conjunto: nacional+internacional
cuadro_27_28_ajus = pd.DataFrame(total_filas_27_28_ajus, columns=nombre_columnas_27_28_ajus)
#se crea una nueva columna que sólo indica la letra "C"= compra o "V"= venta
cuadro_27_28_ajus["V_C"] = cuadro_27_28_ajus["V/C"].str[-1:]
#se llenan las celdas vacías de la tabla con ceros, para poder luego transformar la columna de string a float y poder así luego trabajar los numeros
cuadro_27_28_ajus = cuadro_27_28_ajus.convert_objects(convert_numeric=True).fillna(0)
cuadro_27_28_ajus["E"] = cuadro_27_28_ajus["E"].astype(float)


print(cuadro_27_28_ajus)






'''
PROYECTO E PLUS
'''

#calculamos el total de Activos Fondo E (suma de la fila TOTAL ACTIVOS del cuadro 2)

total_activos = cuadro_2.loc[cuadro_2[""] == "TOTAL ACTIVOS", "Total(monto)"].sum()
print("Total activos Fondo E=",total_activos)



'''
TABLA RESUMEN FORWARDS FONDO E
'''

columns = ["Moneda", "Compra", "Venta"]

list_moneda_obj = cuadro_27_28_ajus["Moneda Objeto"].unique()
list_moneda_forward = cuadro_27_28_ajus["Forward"].unique()
list_monedas = []
list_monedas.extend(list_moneda_obj)
list_monedas.extend(list_moneda_forward)

moneda_unique = []
for l in list_monedas:
    if l not in moneda_unique:
        moneda_unique.append(l)


datos = []
for moneda in moneda_unique:
    fila_i = [moneda,]
    compra_a = cuadro_27_28_ajus.loc[(cuadro_27_28_ajus["V_C"] == "C") & (cuadro_27_28_ajus["Moneda Objeto"] == moneda), "E"].sum()
    compra_b = cuadro_27_28_ajus.loc[(cuadro_27_28_ajus["V_C"] == "V") & (cuadro_27_28_ajus["Forward"] == moneda), "E"].sum()
    venta_a = cuadro_27_28_ajus.loc[(cuadro_27_28_ajus["V_C"] == "V") & (cuadro_27_28_ajus["Moneda Objeto"] == moneda), "E"].sum()
    venta_b = cuadro_27_28_ajus.loc[(cuadro_27_28_ajus["V_C"] == "C") & (cuadro_27_28_ajus["Forward"] == moneda), "E"].sum()
    compra = compra_a + compra_b
    venta = venta_a + venta_b
    fila_i.append(compra)
    fila_i.append(venta)
    datos.append(fila_i)


cuadro_resumen_forwards = pd.DataFrame(datos, columns=columns)
cuadro_resumen_forwards["Diferencia"] = cuadro_resumen_forwards["Compra"] - cuadro_resumen_forwards["Venta"]
cuadro_resumen_forwards["Porcentaje"] = (cuadro_resumen_forwards["Diferencia"]/total_activos)*100

print(cuadro_resumen_forwards)
print("Check=",cuadro_resumen_forwards["Compra"].sum()-cuadro_resumen_forwards["Venta"].sum())

'''
TABLA RESUMEN FÍSICO EXTRANJERO FONDO E (cuadro 22)
'''
cuadro_resumen_físico_extranjero = cuadro_22[["Moneda","E"]]
cuadro_resumen_físico_extranjero = cuadro_resumen_físico_extranjero.convert_objects(convert_numeric=True).fillna(0)
cuadro_resumen_físico_extranjero["E"] = cuadro_resumen_físico_extranjero["E"].astype(float)
cuadro_resumen_físico_extranjero["Porcentaje"] = (cuadro_resumen_físico_extranjero["E"]/total_activos)*100

print(cuadro_resumen_físico_extranjero)

'''
TABLA RESUMEN FÍSICO LOCAL FONDO E (cuadro 4_b)
'''

#localizamos la fila a partir de la cual comienzan los datos extranjeros, y eliminamos las filas a partir de ella (filas extranjeras)
fila_EXTS = cuadro_4_b["Tipo de instrumento"].str.startswith('EXTS', na=False)
index_EXTS = cuadro_4_b.index[fila_EXTS==True].tolist()[0].astype(int)
#keep top filas (nacionales)
cuadro_resumen_fisico_local = cuadro_4_b[:index_EXTS] 
cuadro_resumen_fisico_local = cuadro_resumen_fisico_local[["Unidad de Indexación","E"]] 
cuadro_resumen_fisico_local = cuadro_resumen_fisico_local.groupby("Unidad de Indexación", as_index=False).sum()

moneda_dict = {"EUR":"Euro(EUR)",
   "IPC":"IPC",
   "NO":"Pesos",
   "UF":"Unidad de Fomento",
   "US$":"Dólar estadounidense(US$)"}

cuadro_resumen_fisico_local["Unidad de Indexación"] = cuadro_resumen_fisico_local["Unidad de Indexación"].map(moneda_dict)



#localizamos la fila a partir de la cual comienzan los datos extranjeros, y eliminamos las filas a partir de ella (filas extranjeras)
fila_inv_ext = cuadro_2[""].str.startswith('INVERSIÓN EXTRANJERA TOTAL', na=False)
index_inv_ext = cuadro_2.index[fila_inv_ext==True].tolist()[0].astype(int)
#keep top filas (nacionales)
cuadro_2_new = cuadro_2[:index_inv_ext] 
#sumamos los porcentajes en pesos (del cuadro 2) en Renta Variable,Fondos Mutuos y de Inversión,Disponible(1), DERIVADOS, OTROS NACIONALES(2) y (del cuadro 4_b) RF local 
pesos = cuadro_2_new.loc[cuadro_2_new[""]=="RENTA VARIABLE","Total(porcentaje)"].tolist()[0] + cuadro_2_new.loc[cuadro_2_new[""]=="Fondos Mutuos y de Inversión","Total(porcentaje)"].tolist()[0] + cuadro_2_new.loc[cuadro_2_new[""]=="Disponible(1)","Total(porcentaje)"].tolist()[0] + cuadro_2_new.loc[cuadro_2_new[""]=="DERIVADOS","Total(porcentaje)"].tolist()[0] + cuadro_2_new.loc[cuadro_2_new[""]=="OTROS NACIONALES(2)","Total(porcentaje)"].tolist()[0] + cuadro_resumen_fisico_local.loc[cuadro_resumen_fisico_local["Unidad de Indexación"]=="Pesos","E"].tolist()[0]

#reemplazamos el valor en pesos del cuadro_resumen_fisico_local (que solo toma RF local), por el monto total en pesos calculado en la línea anterior (que también incluye este)
cuadro_resumen_fisico_local.loc[cuadro_resumen_fisico_local['Unidad de Indexación'] == 'Pesos', 'E'] = pesos
#cambiamos el nombre de las columnas de la tabla, para que coincida con las otras dos, y luego poder concatenar los dataframes
cuadro_resumen_fisico_local.columns = ["Moneda","Porcentaje"]
print(cuadro_resumen_fisico_local)


'''
CUADRO MONEDA FINAL
'''

#concatenamos los 3 dataframes de moneda
cuadro_moneda_final = pd.concat([cuadro_resumen_forwards[["Moneda","Porcentaje"]],cuadro_resumen_físico_extranjero[["Moneda","Porcentaje"]][:-1],cuadro_resumen_fisico_local])
#usamos groupby para mostrar una sola fila por moneda y su porcentaje
cuadro_moneda_final = cuadro_moneda_final.groupby("Moneda", as_index=False).sum()

print(cuadro_moneda_final)
print("Total=",cuadro_moneda_final["Porcentaje"].sum())

