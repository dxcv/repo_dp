/*
Created on Tue Oct 03 16:38:00 2017      
@author: Fernando Suarez      
Consulta para obtener los bonos con sus respectivos sreads
*/ 
select  codigo_fdo, codigo_ins, moneda, nominal, riesgo, duration, spread, spread_carry
from ZHIS_Carteras_Main
where fecha = 'autodate' and codigo_fdo = 'autofund' and tipo_instrumento = 'bono corporativo'
order by spread_carry asc
