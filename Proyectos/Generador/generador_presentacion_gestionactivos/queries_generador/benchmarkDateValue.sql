SELECT Valor
FROM MesaInversiones.dbo.Benchmarks_Dinamica
WHERE Benchmark_Id = (SELECT Benchmark_Id
										  FROM MesaInversiones.dbo.Fondos_Benchmark
										  WHERE Codigo_Fdo = 'FONDO'
										  and Fecha = %s)
