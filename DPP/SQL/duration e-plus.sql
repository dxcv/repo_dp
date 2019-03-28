Select t1.Activos, t1.Activos-t1.Leverage as Patrimonio, t1.duration_fdo_sin_leverage, t1.duration_fdo_sin_leverage * t1.Activos/ (t1.Activos-t1.Leverage) as duration_fdo  from 
(
Select SUM(Monto) as Activos, 7020000000 as Leverage, SUM(weight*duration) as duration_fdo_sin_leverage from ZHIS_Carteras_Recursive
where fecha='2017-12-29' and codigo_fdo like '%E-PLUS%'


) t1









