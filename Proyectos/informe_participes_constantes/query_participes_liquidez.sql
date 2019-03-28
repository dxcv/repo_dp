----- CONSULTA CON CLIENTES CON POSICION PERMANENTE EN FONDO LIQUEDEZ DURANTE 3 MESES CON SU EJECUTIVO RESPECTIVO------
--VER DE ADENTRO PARA AFUERA (TOMA APROX 2 MINUTOS LA EJECUCION)
-- SERVIDOR ES LAGUNILLAS

SELECT FP.rut_par, 
       Max(Comerciales.NAME)               AS Nombre,     --JOIN ENTRE PERSONAS CON 33 APARICIONES Y LISTA DE EJECUTIVOS COMERCIALES (SE AGRUPA PORQUE HAY FOLIOS Y OPERACIONES)
       Cast(Sum(FP.monto) AS BIGINT)       AS Monto, 
       Max(FP.codigo_ser)                  AS Serie, 
       Max(Comerciales.owneridname)        AS Ejecutivo, 
       Max(Comerciales.businessunitidname) AS Area 
FROM                                                       
(SELECT rut_par,                                           -- ELIGE LOS RUTS QUE HAN ESTADO 33 FECHAS (EN LIQUIDEZ HABIAN 33 DIAS DE HISTORIA CON SALTOS) 
        Count(fecha) AS nFechas 
 FROM   (SELECT DISTINCT fecha,                            -- SACA TODOS LOS RUTS QUE HAN ESTADO CON TODAS SUS FECHAS
                         rut_par 
         FROM   [PFMIMT1].[dbo].[fm_zhis_fondos_participes] 
         WHERE  fecha >= '2016-05-31' 
                AND fecha <= '2016-09-29' 
                AND codigo_fdo = 'LIQUIDEZ') RF 
 GROUP  BY rut_par 
 HAVING Count(fecha) = 33) R, 
[PFMIMT1].[dbo].[fm_zhis_fondos_participes] FP 
LEFT OUTER JOIN 
[COLORADO].[IM_TRUST_S_A__CORREDORES_DE_BOLSA_MSCRM].[dbo].[im_vista_listaclientesconejecutivoscomerciales] Comerciales 
             ON Rtrim(Ltrim(FP.rut_par)) = Rtrim(Ltrim(comerciales.cfsrut)) 
                                           COLLATE 
                                           database_default 
WHERE  FP.rut_par = R.rut_par 
       AND fecha = '2016-09-29' 
       AND codigo_fdo = 'LIQUIDEZ' 
GROUP  BY FP.rut_par 
HAVING Sum(monto) >= 100000000 -- EN ESTE CASO SE QUERIA CLIENTES CON MAS DE 100MM
ORDER  BY Sum(FP.monto) DESC 