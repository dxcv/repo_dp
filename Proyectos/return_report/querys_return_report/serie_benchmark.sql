SELECT valor 
FROM   benchmarks_dinamica
WHERE  benchmark_id = 'AUTOBENCHMARK' 
AND fecha >= 'AUTODATE1' 
AND fecha <= 'AUTODATE2' 
AND ((DATEPART(dw, fecha) + @@DATEFIRST) % 7) NOT IN (0, 1)
ORDER  BY fecha ASC 