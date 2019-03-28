select ltrim(rtrim(c.codigo_fdo)) as codigo_fdo, SUM(c.monto) as AUM
from ZHIS_Carteras_Main as c
INNER JOIN fondosir as f
ON f.Codigo_fdo = c.codigo_fdo collate database_default 
where fecha ='AUTODATE' and f.shore= 'onshore' and f.estrategia in ('renta fija' , 'credito', 'retorno absoluto') 
GROUP BY  c.codigo_fdo 