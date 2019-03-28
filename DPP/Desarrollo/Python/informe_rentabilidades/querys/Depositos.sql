select fec_vcto,  ltrim(rtrim(codigo_emi)) as codigo_emi , ltrim(rtrim(codigo_fdo)) as codigo_fdo, SUM(weight) as weight, ltrim(rtrim(moneda)) as Moneda, ltrim(rtrim(tipo_instrumento)) as tipo_instrumento
from ZHIS_Carteras_Recursive
where fecha ='AUTODATE' and Tipo_instrumento ='Deposito' and codigo_fdo in ('DEUDA 360','DEUDA CORP','IMT E-PLUS','ARGENTIN','MACRO 1.5','MACRO CLP3','RENTA','SPREADCORP')
GROUP BY codigo_ins, codigo_fdo, codigo_emi, fec_vcto, moneda ,tipo_instrumento