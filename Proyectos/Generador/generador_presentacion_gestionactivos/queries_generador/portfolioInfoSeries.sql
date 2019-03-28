SELECT DISTINCT Nombre_fdo, Run, Secuencia, Sub_categoria, Tipo, Perfil, SUM(Patrimonio) OVER() as Patrimonio
FROM [MesaInversiones].[dbo].Master_Composicion AS mc
LEFT OUTER JOIN [MesaInversiones].[dbo].[Fondos] AS f ON
  mc.Codigo_Fdo = f.Codigo_Fdo
LEFT OUTER JOIN [MesaInversiones].[dbo].ZHIS_SERIES_MAIN AS series ON
  mc.Codigo_Fdo = series.Codigo_Fdo
LEFT OUTER JOIN [MesaInversiones].[dbo].MantenedorBenchmarks AS mb ON
  mb.bmk_nombre = mc.Nombre_Benchmark
WHERE mc.Codigo_Fdo = %s and fecha = 'AUTODATE'
