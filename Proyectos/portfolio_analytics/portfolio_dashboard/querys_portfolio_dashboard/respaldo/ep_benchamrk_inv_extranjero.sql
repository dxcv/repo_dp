/*
Created on Tue Dec 19 16:38:00 2017      
@author: Ashley Mac Gregor     
Consulta para obtener la duracion por tipo de instrumento de la cartera del fondo E de AFP
*/ 


SELECT Fecha, 
       Clasificacion, 
       ''     AS Institucion, 
       Sum(e) AS 'MMUSD' 
FROM   zhis_afp_cuadro_25 
WHERE  fecha = 'autodate' 
       AND clasificacion <> 'ESTADOS EXTRANJEROS' 
GROUP  BY clasificacion, 
          fecha 
UNION 
SELECT Fecha, 
       Clasificacion, 
       Institucion, 
       Sum(e) AS 'MMUSD' 
FROM   zhis_afp_cuadro_25 
WHERE  fecha = 'autodate' 
       AND clasificacion = 'ESTADOS EXTRANJEROS' 
       AND e <> 0 
GROUP  BY institucion, 
          fecha, 
          clasificacion