SELECT fondosir.codigo_fdo                 AS codigo_fdo, 
       benchmarks_estatica.benchmark_id    AS benchmark_id, 
       benchmarks_estatica.fuente          AS fuente, 
       benchmarks_estatica.codigo_descarga AS codigo_descarga 
FROM   fondosir 
       LEFT OUTER JOIN fondos_benchmark 
                    ON fondosir.codigo_fdo = fondos_benchmark.codigo_fdo 
       LEFT OUTER JOIN benchmarks_estatica 
                    ON benchmarks_estatica.benchmark_id = 
                       fondos_benchmark.benchmark_id 
WHERE  alpha_seeker = 1 