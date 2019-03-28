SELECT min(fecha)
FROM MesaInversiones.dbo.ZHIS_Series_Ajustado
WHERE Codigo_Fdo = 'FONDO' AND Valor_Cuota <> 0
