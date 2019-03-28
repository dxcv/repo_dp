select ltrim(rtrim(codigo_fdo)) as codigo_fdo,
       ltrim(rtrim(codigo_emi)) as codigo_emi,
	   ltrim(rtrim(codigo_ins)) as codigo_ins,
	   case 
	   when fec_vcto = '' then '1991-05-17'
	   else fec_vcto end as fec_vcto, 
	   nominal
from ZHIS_Carteras_Main
where fecha = 'autodate'