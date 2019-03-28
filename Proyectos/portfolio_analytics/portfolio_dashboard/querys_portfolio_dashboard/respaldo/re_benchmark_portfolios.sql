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
         WHEN zc.codigo_ins IN ( 'CFMITADUIT', 'CFMITADCIT' ) THEN 3.0
         WHEN cv.duration IS NOT NULL THEN cv.duration / 365 
         WHEN cv.duration IS NULL 
              AND zc.tipo_instrumento IN ( 'Deposito', 'Bono Corporativo', 
                                           'Bono de Gobierno' ) THEN Cast( 
         Datediff(day, zc.Fecha, CONVERT(DATETIME, Replace(fec_vcto, '/', '-'), 
                                  103 
                                  ))AS 
         FLOAT) / 365 
         ELSE 0

       END AS duration,
        CASE
        WHEN cv.tipo = 'BCA'  THEN  'Bono Convertible Acciones'
        WHEN cv.tipo = 'BCP'  THEN  'Bono Central Peso'
        WHEN cv.tipo = 'BCS'  THEN  'Bono Securitizado'
        WHEN cv.tipo = 'BCU'  THEN  'Bono Central UF'
        WHEN cv.tipo = 'BEF'  THEN  'Bono Bancario'
        WHEN cv.tipo = 'BHM'  THEN  'Bono Hipotecario'
        WHEN cv.tipo = 'BRP'  THEN  'Bono Reconocimiento'
        WHEN cv.tipo = 'BSF'  THEN  'Bono Subordinado'
        WHEN cv.tipo = 'BTP'  THEN  'Bono Tesoro Peso'
        WHEN cv.tipo = 'BTU'  THEN  'Bono Tesoro UF'
        WHEN cv.tipo = 'BVL'  THEN  'Bono Vivienda'
        WHEN cv.tipo = 'CERO' THEN   'Bono Cero'
        WHEN cv.tipo = 'DEB'  THEN  'Bono Empresa'
        WHEN cv.tipo = 'DPF'  THEN  'Deposito'
        WHEN cv.tipo = 'ECO'  THEN  'Efecto Comercio'
        WHEN cv.tipo = 'LHF'  THEN  'Letra Hipotecaria'
        WHEN cv.tipo = 'PDC'  THEN  'PDBC Peso'
        WHEN cv.tipo = 'PRC'  THEN  'PDBC UF'
        ELSE 'Otros'
        END AS Tipo_Ra
FROM   zhis_carteras_pg_renta zc 
       LEFT OUTER JOIN cinta_valorizacion cv 
                    ON zc.codigo_ins = cv.codigo_ins 
                       AND cv.fecha = (SELECT TOP 1 fecha 
                                       FROM   cinta_valorizacion 
                                       ORDER  BY fecha DESC) 
WHERE  zc.fecha = 'autodate' 