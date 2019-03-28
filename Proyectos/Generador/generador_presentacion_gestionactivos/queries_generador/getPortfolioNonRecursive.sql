SELECT rtrim(ltrim([Codigo_Ins])) as "Codigo_Ins",
       rtrim(ltrim([Codigo_Emi])) as "Codigo_Emi", SUM([Monto]) as "Monto", SUM([Weight]) as "Weight",
       rtrim(ltrim([Moneda])) as "Moneda", [Duration], [Tasa],
       rtrim(ltrim([Riesgo])) as "Riesgo",
       rtrim(ltrim([Tipo_Instrumento])) as "Tipo_Instrumento",
       rtrim(ltrim([Sector])) as "Sector",
       rtrim(ltrim([Nombre_Instrumento])) as "Nombre_Instrumento",
       rtrim(ltrim([Nombre_Emisor])) as "Nombre_Emisor", SUM([Cantidad]) as "Cantidad",
       rtrim(ltrim([Pais_Emisor])) as "Pais_Emisor",
       rtrim(ltrim([Zona])) as "Zona", [Precio], [Renta], 'Clasificacion_Riesgo' =
    CASE
        WHEN Riesgo = 'AAA+' THEN 'Bajo Riesgo'
        WHEN Riesgo = 'AAA'  THEN 'Bajo Riesgo'
        WHEN Riesgo = 'AAA-' THEN 'Bajo Riesgo'
        WHEN Riesgo = 'AA+'  THEN 'Bajo Riesgo'
        WHEN Riesgo = 'AA'   THEN 'Bajo Riesgo'
        WHEN Riesgo = 'AA-'  THEN 'Bajo Riesgo'
        ELSE 'Alto Riesgo'
    END
FROM [MesaInversiones].[dbo].[ZHIS_CARTERAS_Main]
WHERE codigo_fdo = %s and fecha = 'AUTODATE'
GROUP BY Codigo_Ins, Nombre_Emisor, Codigo_Emi, Moneda, Duration, Tasa, Riesgo,
Tipo_Instrumento, Sector, Nombre_Instrumento, Pais_Emisor, Zona, Precio, Renta
