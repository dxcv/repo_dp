SELECT zs.fecha                            AS date, 
       Ltrim(Rtrim(zs.codigo_fdo))         AS fund_id, 
       'CL'                                AS country_id, 
       CASE 
         WHEN codigo_ser = '1' THEN 'U' 
         ELSE Ltrim(Rtrim(codigo_ser)) 
       END                                 AS fund_serie, 
       Cast(valor_cuota_ajustado AS FLOAT) AS nav, 
       Cast(patrimonio AS FLOAT)           AS aum_native_curren, 
       CASE 
         WHEN f.moneda = '$' THEN Cast(usd.valor * Cast(patrimonio AS FLOAT)AS 
                                       FLOAT) 
         ELSE Cast(patrimonio AS FLOAT) 
       END                                 AS aum_foreign_currency 
FROM   fondosir f 
       LEFT OUTER JOIN zhis_series_ajustado zs 
                    ON f.codigo_fdo = zs.codigo_fdo 
       INNER JOIN zhis_usd_clp usd 
               ON zs.fecha = usd.fecha 
WHERE  zs.fecha >= '2015-01-01' 