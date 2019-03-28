SELECT zs.fecha, ltrim(rtrim(zs.codigo_fdo)) as codigo_fdo, valor_cuota_ajustado 
FROM   fondosir f left outer join zhis_series_ajustado zs
ON f.codigo_fdo = zs.codigo_fdo and f.serie = zs.codigo_ser
WHERE  zs.fecha >= 'autodate1' and zs.fecha <= 'autodate2' and info_attribution = 1