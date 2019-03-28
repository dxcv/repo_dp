select ltrim(rtrim(codigo_fdo)) as codigo_fdo, SUM(monto) as AUM
from ZHIS_Carteras_Main
where fecha ='AUTODATE' and codigo_fdo in ('DEUDA 360','DEUDA CORP','IMT E-PLUS','ARGENTIN','MACRO 1.5','MACRO CLP3','RENTA','SPREADCORP')
GROUP BY  codigo_fdo 