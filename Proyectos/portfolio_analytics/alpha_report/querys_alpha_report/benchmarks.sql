SELECT bd.fecha, bd.benchmark_id, bd.valor
FROM   fondosir f 
left outer join fondos_benchmark fb ON fb.codigo_fdo = f.codigo_fdo 
left outer join benchmarks_dinamica bd ON fb.benchmark_id = bd.benchmark_Id 
WHERE  bd.fecha >= 'autodate1' and bd.fecha <= 'autodate2' and info_alpha = 1
