select ltrim(rtrim(c.moneda)) as moneda
from ZHIS_Carteras_Recursive as c
INNER JOIN fondosir as f
ON f.Codigo_fdo = c.codigo_fdo collate database_default 
where  fecha ='AUTODATE' and Tipo_instrumento in ('Bono Corporativo', 'Bono de Gobierno', 'Deposito') and f.shore= 'onshore' and f.estrategia in ('renta fija' , 'credito', 'retorno absoluto')
GROUP BY c.moneda
