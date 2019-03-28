SELECT FondosLux.Codigo_Fdo, Codigo_Largo, Ticker, Benchmark_Id
FROM FondosLux, Fondos_Benchmark, FondosIR
WHERE FondosLux.Codigo_Fdo=Fondos_Benchmark.Codigo_Fdo AND FondosIR.Codigo_Fdo=FondosLux.Codigo_Fdo