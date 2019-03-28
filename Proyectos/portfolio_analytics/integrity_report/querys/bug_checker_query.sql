---------------------------------------------------------VALORES CUOTA 
SELECT '07:15' AS hora, 
      'Valores cuota' AS Script, 
       CASE 
         WHEN Count(*) >= 70 THEN 1 
         ELSE 0 
       END AS Checked 
FROM   zhis_series_main 
WHERE  fecha = 'autoyesterday' 
---------------------------------------------------------FACTORES 
UNION ALL 
SELECT '07:50' AS hora, 
      'Factores de ajuste' AS Script, 
       CASE 
         WHEN Count(*) >= 15 THEN 1 
         ELSE 0 
       END AS Checked 
FROM   factores 
WHERE  fecha = 'autoyesterday' 
---------------------------------------------------------VALORES CUOTA LUX 
UNION ALL 
SELECT '08:30' AS hora, 
      'Valores cuota lux' AS Script, 
       CASE 
         WHEN Count(*) >= 2 THEN 1 
         ELSE 0 
       END AS Checked 
FROM   zhis_series_lux 
WHERE  fecha = 'autoyesterday' 
--------------------------------------------------------INSTRUMENTOS 
UNION ALL 
SELECT '08:30' AS hora, 
      'Instrumentos' AS Script, 
       CASE 
         WHEN Count(*) < 1 THEN 1 
         ELSE 0 
       END AS Checked 
FROM   (select f.codigo_fdo, codigo_emi, codigo_ins
from ZHIS_Carteras_Main zc, fondosir f
where fecha = 'autoyesterday' and f.codigo_fdo = zc.codigo_fdo collate database_default and tipo_instrumento is null
 and (f.Info_invest = 1 or f.Info_Attribution = 1)) R 
--------------------------------------------------------Emisores
UNION ALL 
SELECT '08:30' AS hora, 
      'Emisores' AS Script, 
       CASE 
         WHEN Count(*) < 1 THEN 1 
         ELSE 0 
       END AS Checked 
FROM   (select f.codigo_fdo, codigo_emi, codigo_ins
from ZHIS_Carteras_Main zc, fondosir f
where fecha = 'autoyesterday' and f.codigo_fdo = zc.codigo_fdo collate database_default and sector is null
 and (f.Info_invest = 1 or f.Info_Attribution = 1)) R 
---------------------------------------------------------INDICES 
UNION ALL 
SELECT '11:00' AS hora, 
      'Indices' AS Script,  
       CASE 
         WHEN Count(*) = (SELECT Count(*) 
                          FROM   indices_estatica) THEN 1 
         ELSE 0 
       END AS Checked 
FROM   indices_dinamica 
WHERE  fecha = 'autotoday'  
---------------------------------------------------------BENCHMARKS 
UNION ALL 
SELECT '11:10' AS hora, 
      'Composicion Benchmarks' AS Script, 
       CASE 
         WHEN Count(*) = (SELECT Count(*) 
                          FROM   benchmarks_estatica) THEN 1 
         ELSE 0 
       END AS Checked 
FROM   benchmarks_dinamica 
WHERE  fecha = 'autoyesterday' 
---------------------------------------------------------CARTERA BMK 
UNION ALL 
SELECT '14:30' AS hora, 
      'Carteras benchmarks' AS Script, 
       CASE 
         WHEN Count(*) > 550 THEN 1 
         ELSE 0 
       END AS Checked 
FROM   zhis_carteras_bmk 
WHERE  fecha = 'autoyesterday' 
---------------------------------------------------------Curva punto forward
UNION ALL 
SELECT '16:00' AS hora, 
      'FWD Curve' AS Script,  
       CASE 
         WHEN 1 = (SELECT Count(*) 
                   FROM  zhis_curva_fwd
           WHERE fecha = 'autotoday'
           ) THEN 1 
         ELSE 0 
       END AS Checked
---------------------------------------------------------curvas cero
UNION ALL
SELECT '15:45' AS hora, 
       'RA Curves' AS Script,   
     CASE 
      WHEN 36500 =  (SELECT count(*) from ZHIS_RA_Curves where date = 'autotoday') THEN 1
      ELSE 0
     END AS Checked
---------------------------------------------------------dias puntos fwd
UNION ALL 
SELECT '16:00' AS hora, 
      'FWD Days' AS Script,  
       CASE 
         WHEN 1 = (SELECT Count(*) 
                   FROM  zhis_fwd_usd_days
           WHERE fecha = 'autotoday'
           ) THEN 1 
         ELSE 0 
       END AS Checked 
---------------------------------------------------------bid puntos fwd
UNION ALL 
SELECT '16:00' AS hora, 
      'FWD Bid' AS Script,  
       CASE 
         WHEN 1 = (SELECT Count(*) 
                   FROM  zhis_fwd_usd_bid
           WHERE fecha = 'autotoday'
           ) THEN 1 
         ELSE 0 
       END AS Checked 
---------------------------------------------------------ask puntos fwd
UNION ALL 
SELECT '16:00' AS hora, 
      'FWD Ask' AS Script,  
       CASE 
         WHEN 1 = (SELECT Count(*) 
                   FROM  zhis_fwd_usd_ask
           WHERE fecha = 'autotoday'
           ) THEN 1 
         ELSE 0 
       END AS Checked 
