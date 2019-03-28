/*
Created on Tue Dec 19 16:38:00 2017      
@author: Ashley Mac Gregor     
Consulta para obtener la duracion por tipo de instrumento de la cartera del fondo E de AFP
*/ 
select  *
from ZHIS_AFPE_moneda_final
where fecha = 'autodate'
