SELECT ltrim(rtrim(Codigo_Fdo)) as codigo_fdo, ltrim(rtrim(Moneda_Compra)) as moneda_compra, ltrim(rtrim(Moneda_Venta)) as moneda_venta, sum(Nominal_Compra) as Monto_Compra, sum(Nominal_Venta) as Monto_Venta
 FROM [MesaInversiones].[dbo].[FWD_Monedas_Estatica] 
 where (Fecha_Vcto > 'AUTODATE' And Fecha_Op<='AUTODATE')
 group by Moneda_Compra, Moneda_Venta, Codigo_Fdo
 order by Codigo_Fdo, moneda_compra, Moneda_Venta