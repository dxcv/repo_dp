SELECT Fecha, rtrim(ltrim(Tipo_mvto)) as "Tipo Movimiento", Cantidad, Monto
FROM MesaInversiones.dbo.Zhis_mvtoParticipes_Main
WHERE codigo_fdo = %s and fecha >= %s and fecha <= %s
ORDER BY fecha DESC
