SELECT fondosir.codigo_fdo,
       serie,
       Codigo_Largo, 
       Benchmarks_Estatica.Benchmark_Id,
	   estrategia,
	   Benchmarks_Estatica.moneda 
FROM   fondosir, 
       fondos_benchmark, Benchmarks_Estatica 
WHERE  active = 1 
       AND fondosir.codigo_fdo = fondos_benchmark.codigo_fdo 
	   AND fondosir.info_ret = 1
	   AND Fondos_Benchmark.Benchmark_Id=Benchmarks_Estatica.Benchmark_Id
ORDER BY estrategia, FondosIR.Codigo_Largo