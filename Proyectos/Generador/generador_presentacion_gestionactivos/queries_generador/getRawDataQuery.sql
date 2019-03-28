SELECT Fondos.Fecha,
       valor_cuota_ajustado,
       %s * valor / %s as "Valor_Benchmark"
FROM
  (SELECT Fecha, Valor_Cuota_Ajustado
  FROM MesaInversiones.dbo.ZHIS_Series_Ajustado
  WHERE  Codigo_Fdo LIKE 'FONDO') AS Fondos,
  (SELECT Fecha, Valor FROM MesaInversiones.dbo.Benchmarks_Dinamica
   WHERE Benchmark_Id = (
    SELECT benchmark_id FROM MesaInversiones.dbo.Fondos_Benchmark
    WHERE codigo_fdo = 'FONDO'
    )
  ) AS Benchmarks
WHERE Fondos.fecha = Benchmarks.fecha AND Fondos.fecha >= %s
AND Fondos.fecha <= %s
ORDER BY fecha DESC
