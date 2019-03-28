SELECT zc.fecha, 
       zc.run_fondo, 
       zc.codigo_ins, 
       zc.nombre_emisor, 
       zc.nombre_fondo, 
       zc.pais_emisor, 
       zc.fec_vcto, 
       zc.situacion_inst, 
       zc.clasif_riesgo, 
       zc.cod_grupo_empresarial, 
       zc.cant_unidades, 
       zc.tipo_unidades, 
       zc.tir, 
       zc.valor_par, 
       zc.valor_relevante, 
       zc.cod_valoriz, 
       zc.base_tasa, 
       zc.tipo_interes, 
       zc.valoriz_cierre, 
       zc.moneda_liquidacion, 
       zc.pais_transaccion, 
       zc.porcentaje_capital_emisor, 
       zc.porcentaje_activos_emisor, 
       zc.porcentaje_activos_fondo, 
       zc.weight, 
       zc.tipo_instrumento, 
       zc.moneda, 
       CASE 
         WHEN cv.riesgo_ra IS NOT NULL THEN cv.riesgo_ra 
         ELSE 'AAA' 
       END AS riesgo, 
       CASE 
         WHEN cv.duration IS NOT NULL THEN cv.duration / 365 
         WHEN cv.duration IS NULL 
              AND zc.tipo_instrumento IN ( 'Deposito', 'Bono Corporativo', 
                                           'Bono de Gobierno' ) THEN Cast( 
         Datediff(day, zc.Fecha, CONVERT(DATETIME, Replace(fec_vcto, '/', '-'), 
                                  103 
                                  ))AS 
         FLOAT) / 365 
         ELSE 0 
       END AS Duration 
FROM   zhis_carteras_pg_renta zc 
       LEFT OUTER JOIN cinta_valorizacion cv 
                    ON zc.codigo_ins = cv.codigo_ins 
                       AND cv.fecha = (SELECT TOP 1 fecha 
                                       FROM   cinta_valorizacion 
                                       ORDER  BY fecha DESC) 
WHERE  zc.fecha = 'autodate' 