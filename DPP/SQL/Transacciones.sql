Select fecha, Instrumento, compra as fondo, 'C', SUM(Cantidad), SUM(Monto) as tipo_op from TransaccionesIRF where fecha>='2018-02-01'
and compra in ('RENTA')
group by fecha, compra,  Instrumento
UNION ALL
Select fecha, Instrumento, vende as fondo, 'V', SUM(Cantidad), SUM(monto) as tipo_op from TransaccionesIRF where fecha>='2018-03-01'
and vende in ('RENTA')
group by fecha, vende,  Instrumento
order by tipo_op, fecha


Select * from TransaccionesIRF where fecha>='2018-03-06' and vende='RENTA'

Select * from TransaccionesIRF where compra='RENTA' and fecha>='2018-02-09'

Select * from ZHIS_Carteras_Recursive