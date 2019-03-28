SELECT Zona, Renta, SUM(Weight) as Weight FROM indices_estatica AS Indices
JOIN Benchmarks_Composicion AS Benchmarks
ON Indices.Index_Id = Benchmarks.Index_Id
WHERE Benchmark_Id =  (SELECT Benchmark_Id
											 FROM MesaInversiones.dbo.Fondos_Benchmark
											 WHERE Codigo_Fdo = 'FONDO'
											)
GROUP BY Zona, Renta
