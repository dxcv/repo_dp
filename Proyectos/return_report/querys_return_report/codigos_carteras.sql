SELECT fondos_benchmark.codigo_fdo, 
       master_fondos.nombre, 
       benchmarks_estatica.nombre_benchmark, 
       benchmarks_estatica.benchmark_id 
FROM   benchmarks_estatica, 
       fondos_benchmark 
       LEFT OUTER JOIN master_fondos 
                    ON master_fondos.codigo_fdo COLLATE 
                       sql_latin1_general_cp1_ci_as = 
                       fondos_benchmark.codigo_fdo 
WHERE  fondos_benchmark.benchmark_id = benchmarks_estatica.benchmark_id 
       AND fondos_benchmark.codigo_fdo NOT IN (SELECT DISTINCT codigo_fdo 
                                               FROM   fondosir) 
       AND master_fondos.estado = 'A' 
ORDER  BY benchmarks_estatica.nombre_benchmark