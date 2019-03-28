SELECT fecha, 
       ltrim(rtrim(zf.codigo_fdo)) as codigo_fdo, 
       ltrim(rtrim(zf.codigo_ser)) as codigo_ser, 
       CASE 
         WHEN zf.factor_ajuste = 0 THEN 1 
         ELSE zf.factor_ajuste
       END AS factor_ajuste 
FROM   lagunillas.pfmimt1.dbo.fm_factor_ajuste zf, 
       fondosir f 
WHERE  zf.codigo_fdo COLLATE database_default = f.codigo_fdo 
       AND zf.fecha >= 'AUTODATE1' 
       AND zf.fecha <= 'AUTODATE2'
       AND f.active = 1 