SELECT zs.fecha as fecha, ltrim(rtrim(zs.codigo_fdo)) as codigo_fdo, tac
FROM   fondosir f left outer join  zhis_tac zs
ON f.codigo_fdo = zs.codigo_fdo collate database_default and f.serie = zs.codigo_ser collate database_default
WHERE  zs.fecha >= 'autodate1' and zs.fecha <= 'autodate2' and info_attribution = 1