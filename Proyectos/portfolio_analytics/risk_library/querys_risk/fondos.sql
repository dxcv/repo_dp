SELECT LTRIM(RTRIM(fondosir.codigo_fdo)) AS codigo_fdo,
       serie,
       codigo_largo, 
	   display_portfolio,
	   Fondos_Benchmark.benchmark_id,
	   alpha_seeker
FROM   fondosir, Fondos_Benchmark
WHERE  active = 1 
	   AND fondosir.Info_Invest = 1
	   AND FondosIR.Codigo_Fdo = Fondos_Benchmark.Codigo_Fdo
ORDER BY display_portfolio desc, FondosIR.Codigo_Largo