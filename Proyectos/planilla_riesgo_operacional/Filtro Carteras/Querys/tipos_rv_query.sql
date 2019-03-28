SELECT ZS_TipoInstrumento_Aux.TipoInstr as "Tipo Instrumento", CASE WHEN R.weight IS NULL THEN 0 ELSE R.weight END as weight
FROM dbo.ZS_TipoInstrumento_Aux LEFT OUTER JOIN
(SELECT CASE WHEN TipoInstr IS NULL THEN 'No Definido' ELSE TipoInstr END AS TipoInstr, SUM(porc) as weight
FROM dbo.ZHIS_CARTERAS
WHERE Fecha='AUTODATE' AND Codigo_Fdo='AUTOFONDO'
GROUP BY TipoInstr)R
ON ZS_TipoInstrumento_Aux.TipoInstr=R.TipoInstr
ORDER BY weight DESC