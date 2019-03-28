select min(fecha) from MesaInversiones.dbo.Benchmarks_Dinamica
where Benchmark_Id = (select Benchmark_Id
					  from MesaInversiones.dbo.Fondos_Benchmark
					  where Codigo_Fdo = 'FONDO'
					  )
