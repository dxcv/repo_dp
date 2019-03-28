Select Transacciones.Fecha, Transacciones.Instrumento, Transacciones.Compra, Transacciones.Vende, Transacciones.Moneda, Transacciones.Monto, Transacciones.Liq, Carteras.Fec_Vcto
from (Select * from TransaccionesIRF where fecha='AUTODATE_SPOT' and Liq not like '%PH%') Transacciones
left join
(Select DISTINCT codigo_ins as codigo_ins, CAST(fec_vcto as datetime) as fec_vcto from ZHIS_CARTERAS_Main Carteras 
where fecha= 'AUTODATE_YEST' and fec_vcto is not null) Carteras
on Transacciones.Instrumento COLLATE DATABASE_DEFAULT = Carteras.codigo_Ins COLLATE DATABASE_DEFAULT