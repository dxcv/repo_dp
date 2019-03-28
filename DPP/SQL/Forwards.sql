
SELECT Codigo_Fdo, Fecha_Vcto, Moneda_Compra, Moneda_Venta, sum(Nominal_Compra) as Monto_Compra, sum(Nominal_Venta) as Monto_Venta, AVG(Precio_Pactado) as Promedio_Precio_Pactado
 FROM [MesaInversiones].[dbo].[FWD_Monedas_Estatica] where Fecha_Vcto > SYSDATETIME() group by Moneda_Compra, Moneda_Venta, Codigo_Fdo, Fecha_Vcto 
 order by Codigo_Fdo, moneda_compra, Moneda_Venta, Fecha_Vcto

