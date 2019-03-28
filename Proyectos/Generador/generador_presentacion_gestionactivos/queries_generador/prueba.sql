SELECT Fondos.Fecha,
       valor_cuota_ajustado /Dolar.valor as "valor_cuota_ajustado",
       %s * Benchmarks.valor /(Dolar.valor*%s) as "Valor_Benchmark"
FROM
  (SELECT Fecha, Valor_Cuota_Ajustado
  FROM MesaInversiones.dbo.ZHIS_Series_Ajustado
  WHERE  Codigo_Fdo LIKE 'FONDO') AS Fondos,
  (SELECT Fecha, Valor FROM MesaInversiones.dbo.Benchmarks_Dinamica
   WHERE Benchmark_Id = (
    SELECT benchmark_id FROM MesaInversiones.dbo.Fondos_Benchmark
    WHERE codigo_fdo = 'FONDO'
    )
  ) AS Benchmarks,
  (SELECT Fecha, Valor FROM [MesaInversiones].[dbo].[Indices_Dinamica] WHERE Index_Id = '66') as Dolar
WHERE Fondos.fecha = Benchmarks.fecha AND Dolar.Fecha = Fondos.Fecha + 1 AND Fondos.fecha >= '2014-01-01'
AND Fondos.fecha <= '2016-12-31'
ORDER BY fecha DESC
