SELECT bd.fecha                   AS date, 
       Ltrim(Rtrim(f.codigo_fdo)) AS fund_id, 
       'CL'                       AS country_id, 
       Cast(bd.valor AS FLOAT)    AS benchmark_nav 
FROM   fondosir f 
       LEFT OUTER JOIN fondos_benchmark fb 
                    ON f.codigo_fdo = fb.codigo_fdo 
       LEFT OUTER JOIN benchmarks_dinamica bd 
                    ON fb.benchmark_id = bd.benchmark_id 
WHERE  bd.fecha >= '2015-01-01' 