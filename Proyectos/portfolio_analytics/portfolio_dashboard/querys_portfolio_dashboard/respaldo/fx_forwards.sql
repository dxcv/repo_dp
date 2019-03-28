/*
Created on Tue Aug 18 16:38:00 2017      
@author: Fernando Suarez      
Consulta para obtener los forwards de los fondos
*/ 
SELECT Ltrim(Rtrim(fwd.codigo_fdo)) AS codigo_fdo,
       fwd.fecha_op         AS fecha_op,
       Ltrim(Rtrim(fwd.codigo_emi)) AS codigo_emi, 
       Ltrim(Rtrim(fwd.codigo_ins)) AS codigo_ins, 
       fwd.Fecha_Fix              AS fec_fix, 
       fwd.fecha_vcto               AS fec_vcto, 
          CASE
          WHEN fwd.moneda_compra = 'CLP'  THEN '$'
          WHEN fwd.moneda_compra = 'USD'  THEN 'US$'
          WHEN fwd.moneda_compra = 'EUR'  THEN 'EU'
          WHEN fwd.moneda_compra = 'UF'  THEN 'UF'
		  WHEN fwd.moneda_compra = 'ARS'  THEN 'ARS'     
          END                        AS moneda_compra,
       CASE
          WHEN fwd.moneda_venta = 'CLP'  THEN '$'
          WHEN fwd.moneda_venta = 'USD'  THEN 'US$'
          WHEN fwd.moneda_venta = 'EUR'  THEN 'EU'
          WHEN fwd.moneda_venta = 'UF'  THEN 'UF'
		  WHEN fwd.moneda_venta = 'ARS'  THEN 'ARS'     
      END                          AS moneda_venta,
    Nominal_Compra as nominal_compra,
    Nominal_Venta as nominal_venta,
    Precio_Pactado as precio,
    CASE
         WHEN tipo='C' THEN 'Compensacion'
         WHEN tipo='F' THEN 'Fisico'
    END AS tipo,
    CASE
         WHEN Instrumento_Sintetico is not null THEN Instrumento_Sintetico
         ELSE ''
    END AS instrumento_sintetico,
    CASE
         WHEN Estrategia is not null THEN Estrategia
         ELSE ''
    END AS estrategia
FROM   fwd_monedas_estatica fwd 
WHERE  fwd.fecha_op <= 'autodate' 
       AND fwd.fecha_vcto >= 'autodate' 
       AND fwd.codigo_fdo = 'autofund' 