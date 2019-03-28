SELECT Fecha,
       RTRIM(LTRIM(PARTICIPES_EJECUTIVOS.Codigo_Fdo)) AS Codigo_Fdo,
       RTRIM(LTRIM(Codigo_Ser)) AS Codigo_Ser,
       RTRIM(LTRIM(Rut_Par)) AS Rut_Par,
       Num_Cuotas,
       Val_Cuota,
       Monto,
       CASE
           WHEN ejecutivo COLLATE DATABASE_DEFAULT IN
                  (SELECT ejecutivo
                   FROM ejecutivos) THEN RTRIM(LTRIM(PARTICIPES_EJECUTIVOS.ejecutivo))
           ELSE 'JAIME OCHAGAVIA ALLENDES'
       END AS nombre_ejecutivo,
       RTRIM(LTRIM(estrategia)) AS estrategica,
       RTRIM(LTRIM(shore)) AS shore
FROM PARTICIPES_EJECUTIVOS
LEFT OUTER JOIN FondosIR ON PARTICIPES_EJECUTIVOS.Codigo_Fdo COLLATE DATABASE_DEFAULT =FondosIR.Codigo_Fdo
WHERE Fecha ='AUTODATE'