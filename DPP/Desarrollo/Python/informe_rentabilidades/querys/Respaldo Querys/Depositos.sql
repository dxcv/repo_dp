select c.fec_vcto,  ltrim(rtrim(c.codigo_emi)) as codigo_emi , ltrim(rtrim(c.codigo_fdo)) as codigo_fdo, SUM(c.weight) as weight, ltrim(rtrim(c.moneda)) as Moneda, ltrim(rtrim(c.tipo_instrumento)) as tipo_instrumento
from ZHIS_Carteras_Recursive as c
INNER JOIN fondosir as f
ON f.Codigo_fdo = c.codigo_fdo collate database_default 
where fecha ='AUTODATE' and Tipo_instrumento ='Deposito' and f.shore= 'onshore' and f.estrategia in ('renta fija' , 'credito', 'retorno absoluto') 
GROUP BY codigo_ins, c.codigo_fdo, codigo_emi, fec_vcto, c.moneda ,tipo_instrumento