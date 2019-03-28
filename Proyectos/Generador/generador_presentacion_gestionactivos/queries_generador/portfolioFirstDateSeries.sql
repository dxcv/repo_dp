SELECT min(fecha)
FROM MesaInversiones.dbo.ZHIS_Series_Ajustado
WHERE Codigo_Fdo = 'FONDO' AND Codigo_Ser = 'PLACESERIE' AND Valor_Cuota <> 0
