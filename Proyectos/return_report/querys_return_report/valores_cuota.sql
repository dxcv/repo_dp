SELECT valor_cuota_ajustado
FROM   zhis_series_ajustado
WHERE  codigo_fdo = 'AUTOFONDO' 
       AND codigo_ser = 'AUTOSERIE' 
       AND fecha >= 'AUTODATE1'
       AND fecha <= 'AUTODATE2'
       AND ((DATEPART(dw, fecha) + @@DATEFIRST) % 7) NOT IN (0, 1)
ORDER  BY fecha ASC 