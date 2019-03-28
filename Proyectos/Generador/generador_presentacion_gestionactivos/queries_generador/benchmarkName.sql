SELECT Nombre_Benchmark
FROM [MesaInversiones].[dbo].[Benchmarks_Estatica]
WHERE Benchmark_Id =
	(SELECT Benchmark_Id
	 FROM [MesaInversiones].[dbo].[Fondos_Benchmark]
	 WHERE Codigo_Fdo = %s)
