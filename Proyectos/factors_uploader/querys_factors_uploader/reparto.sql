SELECT fecha, 
       ltrim(rtrim(zf.codigo_fdo)) as codigo_fdo, 
       ltrim(rtrim(zf.codigo_ser)) as codigo_ser, 
       CASE 
         WHEN zf.factor_reparto = 0 THEN 1 
         ELSE zf.factor_reparto 
       END AS factor_reparto 
FROM   lagunillas.pfmimt1.dbo.fm_factor_ajuste zf, 
       fondosir f 
WHERE  zf.codigo_fdo COLLATE database_default = f.codigo_fdo 
       AND zf.fecha >= 'AUTODATE1' 
       AND zf.fecha <= 'AUTODATE2'
       AND f.active = 1
UNION ALL
select ze.fecha, ze.codigo_fdo collate database_default, ze.codigo_ser collate database_default, ze.factor_reparto
from factores_REPARTO_EXCEPCIONALES ze