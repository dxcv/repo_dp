/*
Created on Tue Feb 07 16:38:00 2017      
@author: Fernando Suarez      
Consulta para obtener el portfolio de los distintos fondos
*/ 
-- INSTRUMENTOS
SELECT Ltrim(Rtrim(zc.codigo_fdo)) COLLATE database_default AS codigo_fdo,
       '1900-01-01'											AS fec_op,
	   Ltrim(Rtrim(zc.codigo_emi)) COLLATE database_default AS codigo_emi, 
       Ltrim(Rtrim(zc.codigo_ins)) COLLATE database_default AS codigo_ins, 
       zc.fec_vcto as fec_vcto, 
       Ltrim(Rtrim(zc.moneda))                              AS moneda, 
       Ltrim(Rtrim(zc.tipo_instrumento))                    AS tipo_instrumento, 
       zc.monto, 
       zc.duration, 
       zc.tasa / 100                                        AS tasa,
       zc.precio_dirty         								AS precio, 
       Ltrim(Rtrim(zc.riesgo))                              AS riesgo
FROM   zhis_carteras_recursive zc 
WHERE  fecha = 'autodate' 
       AND codigo_fdo = 'autofund' 
       AND tipo_instrumento <> 'FX' 
UNION ALL 
-- FORWARDS
SELECT Ltrim(Rtrim(fwd.codigo_fdo)) AS codigo_fdo,
       fwd.fecha_op         AS fec_op,
       Ltrim(Rtrim(fwd.codigo_emi)) AS codigo_emi, 
       Ltrim(Rtrim(fwd.codigo_ins)) AS codigo_ins, 
       fwd.fecha_vcto               AS fec_vcto, 
       CASE
          WHEN f.moneda = '$' THEN 
          CASE
          WHEN fwd.moneda_compra = 'USD' OR fwd.moneda_venta = 'USD' THEN 'US$'
          WHEN fwd.moneda_compra = 'EUR' OR fwd.moneda_venta = 'EUR' THEN 'EU'
          WHEN fwd.moneda_compra = 'UF' OR fwd.moneda_venta = 'UF' THEN 'UF'   
          END 
      END                          AS moneda, 
       'FX Forward'                 AS tipo_instrumento, 
       CASE 
       WHEN fwd.moneda_compra = 'CLP' THEN -1 * nominal_compra
     ELSE nominal_venta END AS monto, 
       0.0                          AS duration, 
       0.0                          AS tasa,
       0.0              AS precio, 
       'N/A'                        AS riesgo
FROM   fwd_monedas_estatica fwd 
       LEFT OUTER JOIN fondosir f 
                    ON fwd.codigo_fdo = f.codigo_fdo 
WHERE  fwd.fecha_op <= 'autodate' 
       AND fwd.fecha_vcto >= 'autodate' 
       AND fwd.codigo_fdo = 'autofund' 