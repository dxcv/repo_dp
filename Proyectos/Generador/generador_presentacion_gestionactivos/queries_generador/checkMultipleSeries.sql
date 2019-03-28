SELECT ltrim(rtrim(Codigo_Fdo))
FROM zhis_series_ajustado
WHERE fecha = %s
GROUP BY Codigo_Fdo
HAVING count(*) > 1
