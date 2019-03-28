SELECT LTRIM(RTRIM(fondosir.codigo_fdo)) AS codigo_fdo,
	   Fondos_Benchmark.benchmark_id,
	   alpha_seeker,
	   risk_budget,
	   nombre_benchmark
FROM   fondosir, Fondos_Benchmark, Benchmarks_Estatica
WHERE  active = 1 
	   AND fondosir.Info_Alpha = 1
	   AND FondosIR.Codigo_Fdo = Fondos_Benchmark.Codigo_Fdo
	   AND Benchmarks_Estatica.Benchmark_Id = Fondos_Benchmark.Benchmark_Id
ORDER BY display_portfolio desc, FondosIR.Codigo_Largo