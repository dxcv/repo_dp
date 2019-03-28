/*
Created on Tue Dec 19 16:38:00 2017      
@author: Ashley Mac Gregor     
Consulta para obtener la duracion por tipo de instrumento de la cartera del fondo E de AFP
*/ 
select  Fecha, Tipo_Instrumento, Total_porcentaje, Total_monto
from ZHIS_AFPs_cuadro_2
where fecha = 'autodate'
and tipo_fondo='E'
