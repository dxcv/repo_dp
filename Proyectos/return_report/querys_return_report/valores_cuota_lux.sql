SELECT valor_cuota
FROM   zhis_series_lux
WHERE  ticker = 'AUTOTICKER' 
       AND fecha >= 'AUTODATE1'
       AND fecha <= 'AUTODATE2' 
       AND ((DATEPART(dw, fecha) + @@DATEFIRST) % 7) NOT IN (0, 1)
ORDER  BY fecha ASC 