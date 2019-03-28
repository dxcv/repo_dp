SELECT DISTINCT Benchmarks_Estatica.Nombre_Benchmark
FROM Benchmarks_Estatica, Fondos_Benchmark
WHERE Fondos_Benchmark.Benchmark_Id=Benchmarks_Estatica.Benchmark_Id
AND Fondos_Benchmark.Codigo_Fdo NOT IN (SELECT DISTINCT Codigo_Fdo FROM FondosIR)
