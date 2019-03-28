select A.Fecha, A.Compra as Fondo, A.Instrumento, A.Liq, A.Moneda, A.Cantidad, B.Tasa as TIR_Risk, A.Tir as TIR_Operacion
from TransaccionesIRF as A, Performance_nacionales as B
where A.fecha = 'AUTODATE' AND A.Vende is Null AND A.fecha = B.fecha AND A.Instrumento = B.Codigo_Ins
order by fecha desc