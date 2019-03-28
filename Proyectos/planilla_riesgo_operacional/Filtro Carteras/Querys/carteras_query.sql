SELECT CAST(fecha AS DATETIME) AS fecha, 
       LTRIM(RTRIM(codigo_fdo)) COLLATE database_default AS codigo_fdo, 
       LTRIM(RTRIM(codigo_emi)) COLLATE database_default as codigo_emi, 
       LTRIM(RTRIM(codigo_ins)) COLLATE database_default AS codigo_ins, 
       tipo_instrumento, 
       LTRIM(RTRIM(moneda)) COLLATE database_default AS moneda, 
       sector, 
       monto, 
       nominal, 
       cantidad, 
       precio, 
       duration, 
       tasa, 
       riesgo, 
       nombre_emisor, 
       nombre_instrumento, 
       CAST(fec_vcto AS DATETIME) AS fec_vcto, 
       pais_emisor, 
       estrategia, 
       zona, 
       renta, 
       riesgo_internacional, 
       tasa_compra 
FROM   dbo.zhis_carteras_main 
WHERE  fecha = 'AUTODATE' 
       AND codigo_fdo LIKE ( '%AUTOFONDO%' ) 
       AND moneda LIKE ( '%AUTOMONEDA%' ) 
       AND codigo_ins LIKE ( '%AUTOINSTRUMENTO%' ) 
       AND codigo_emi LIKE ( '%AUTOEMISOR%' ) 

UNION ALL -- Se computa la posicion forward long leg   
SELECT CAST('AUTODATE' AS DATETIME) AS fecha, 
       Ltrim(Rtrim(fwm.codigo_fdo))         AS codigo_fdo, 
       Ltrim(Rtrim(fwm.codigo_emi))         AS codigo_emi, 
       Ltrim(Rtrim(fwm.codigo_ins))         AS codigo_ins, 
       'FX Forward'                         AS tipo_instrumento, 
       CASE --PASAMOS MONEDAS AL FORMATO CORRECTO    
         WHEN fwm.moneda_compra = 'USD' THEN 'US$' 
         WHEN fwm.moneda_compra = 'CLP' THEN '$' 
         WHEN fwm.moneda_compra = 'UF' THEN 'UF' 
         WHEN fwm.moneda_compra = 'EUR' THEN 'EU' 
       END                                  AS moneda, 
       'Forwards'                           AS sector,
       CASE 
         -- valorizamos los forward a precio spot para la posicion larga en pesos   
         WHEN f.moneda = '$' THEN -- valorizamos forwards en fondo en pesos 
           CASE 
             WHEN fwm.moneda_compra = 'CLP' THEN nominal_compra 
             WHEN fwm.moneda_compra = 'USD' THEN 
             nominal_compra * (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 66 
             AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_compra = 'MXN' THEN 
             nominal_compra * (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 85 
             AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_compra = 'EUR' THEN 
             nominal_compra * (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 73 
             AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_compra = 'UF' THEN 
             nominal_compra * (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 72 
             AND fecha = 'AUTODATE') 
           END 
         WHEN f.moneda = 'US$' THEN -- valorizamos forwards en fondo en dolares 
           CASE 
             WHEN fwm.moneda_compra = 'USD' THEN nominal_compra 
             WHEN fwm.moneda_compra = '$' THEN 
             nominal_compra / (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 66 
             AND fecha = 'AUTODATE') 
           END 
       END                                  AS monto, 
       0                                    AS nominal, 
       0                                    AS cantidad, 
       0                                    AS precio, 
       0                                    AS duration, 
       0                                    AS tasa, 
       'N/A'                                AS riesgo, 
       Ltrim(Rtrim(emisores.nombre_emisor)) AS nombre_emisor, 
       'Forward ' + ' ' + emisores.nombre_emisor 
       + ' long leg'                        AS nombre_instrumento, 
       CAST(fwm.Fecha_Vcto AS DATETIME) AS fec_vcto,
       'N/A'                                 AS pais_emisor, 
       fwm.estrategia					    AS  estrategia,
       'local' AS zona,
       'fx' AS renta,
       'N/A'                                AS riesgo_internacional,
       0.0 AS tasa_compra
FROM   fwd_monedas_estatica FWM 
       LEFT OUTER JOIN emisores 
                    ON fwm.codigo_emi = emisores.codigo_emi, 
       fondosir F 
WHERE  FWM.codigo_fdo = F.codigo_fdo 
       AND FWM.fecha_op <= 'AUTODATE' 
       AND FWM.fecha_vcto >= 'AUTODATE'
     AND FWM.codigo_fdo = 'AUTOFONDO'  
UNION ALL -- Se computa la posicion forward short leg   
SELECT CAST('AUTODATE' AS DATETIME) AS fecha, 
       Ltrim(Rtrim(fwm.codigo_fdo))         AS codigo_fdo, 
       Ltrim(Rtrim(fwm.codigo_emi))         AS codigo_emi, 
       Ltrim(Rtrim(fwm.codigo_ins))         AS codigo_ins, 
       'FX Forward'                         AS tipo_instrumento, 
       CASE --PASAMOS MONEDAS AL FORMATO CORRECTO    
         WHEN fwm.moneda_venta = 'USD' THEN 'US$' 
         WHEN fwm.moneda_venta = 'CLP' THEN '$' 
         WHEN fwm.moneda_venta = 'UF' THEN 'UF' 
         WHEN fwm.moneda_venta = 'EUR' THEN 'EU' 
       END                                  AS moneda, 
       'Forwards'                           AS sector,
       CASE 
         -- valorizamos los forward a precio spot para la posicion corta, es negativo ya que es una posicion pasiva
         WHEN f.moneda = '$' THEN -- valorizamos para fondo en pesos 
           CASE 
             WHEN fwm.moneda_venta = 'CLP' THEN -1 * nominal_venta 
             WHEN fwm.moneda_venta = 'USD' THEN 
             -1 * nominal_venta * (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 66 
                                          AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_venta = 'MXN' THEN 
             -1 * nominal_venta * (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 85 
                                          AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_venta = 'EUR' THEN 
             -1 * nominal_venta * (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 73 
                                          AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_venta = 'UF' THEN 
             -1 * nominal_venta * (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 72 
                                          AND fecha = 'AUTODATE') 
           END 
         WHEN f.moneda = 'US$' THEN --Valorizamos para fondo en dolares 
           CASE 
             WHEN fwm.moneda_venta = 'USD' THEN -1 * nominal_venta 
             WHEN fwm.moneda_venta = 'CLP' THEN 
             -1 * nominal_venta / (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 66 
                                          AND fecha = 'AUTODATE') 
           END 
       END                                  AS Monto, 
       0                                    AS nominal, 
       0                                    AS cantidad, 
       0                                    AS precio, 
       0                                    AS duration, 
       0                                    AS tasa, 
       'N/A'                                AS riesgo, 
       Ltrim(Rtrim(emisores.nombre_emisor)) AS nombre_emisor, 
       'Forward ' + ' ' + emisores.nombre_emisor 
       + ' short leg'                       AS nombre_instrumento, 
       CAST(fwm.Fecha_Vcto AS DATETIME) AS fec_vcto,
       'N/A'                                 AS pais_emisor, 
       fwm.estrategia					    AS  estrategia,
       'local' AS zona,
       'fx' AS renta,
       'N/A'                                AS riesgo_internacional,
       0.0 AS tasa_compra
FROM   fwd_monedas_estatica FWM 
       LEFT OUTER JOIN emisores 
                    ON fwm.codigo_emi = emisores.codigo_emi, 
       fondosir F 
WHERE  FWM.codigo_fdo = F.codigo_fdo 
       AND F.info_invest = 1 
       AND FWM.fecha_op <= 'AUTODATE' 
       AND FWM.fecha_vcto >= 'AUTODATE'
     AND FWM.codigo_fdo = 'AUTOFONDO' 