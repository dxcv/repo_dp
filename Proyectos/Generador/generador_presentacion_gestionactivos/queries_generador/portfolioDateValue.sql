SELECT Valor_Cuota_Ajustado
FROM MesaInversiones.dbo.ZHIS_Series_Ajustado
WHERE Codigo_Fdo = 'FONDO' AND Fecha = %s
