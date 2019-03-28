SELECT ltrim(rtrim(Codigo_Fdo)) as codigo_fdo, ltrim(rtrim(Moneda_Compra)) as moneda_compra, ltrim(rtrim(Moneda_Venta)) as moneda_venta, sum(Nominal_Compra) as Monto_Compra, sum(Nominal_Venta) as Monto_Venta
 FROM [MesaInversiones].[dbo].[FWD_Monedas_Estatica] 
 where (Fecha_Vcto > 'AUTODATE' And Fecha_Op<='AUTODATE')
 and codigo_fdo in ('DEUDA 360','DEUDA CORP','IMT E-PLUS','ARGENTIN','MACRO 1.5','MACRO CLP3','RENTA','SPREADCORP')
 group by Moneda_Compra, Moneda_Venta, Codigo_Fdo
 order by Codigo_Fdo, moneda_compra, Moneda_Venta