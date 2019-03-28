----------------CONSULTAS ALIMENTADORAS DEL REPORTE
-----Movimientos
select CAST(Fecha AS smalldatetime) as Fecha, Zhis_mvtoParticipes_main.Codigo_Fdo, tipo_mvto, case when Zhis_mvtoParticipes_main.codigo_fdo in ('LATAM IG', 'M_MARKET', 'US_ALPHA', 'EQUITIES-L') THEN sum(monto)*660 ELSE sum(monto) END as Monto, Canal
from Zhis_mvtoParticipes_main, fondosir
where fecha>=DATEADD(yy, DATEDIFF(yy,0,getdate()), -1) and fecha<=DATEADD(mm, DATEDIFF(mm,0,getdate()), -1) and Zhis_mvtoParticipes_main.codigo_fdo =fondosir.Codigo_Fdo and  ltrim(rtrim(codigo_ser))<>'IM'
group by Fecha, Zhis_mvtoParticipes_main.Codigo_Fdo, tipo_mvto,  Canal
order by fecha asc

-----Patrimonios
select Fecha, Fondosir.Codigo_Fdo, case when Fondosir.codigo_fdo in ('LATAM IG', 'M_MARKET', 'US_ALPHA', 'EQUITIES-L') THEN sum(patrimonio)*660 ELSE sum(patrimonio) END AS Patrimonio
from Zhis_series_main, fondosir
where fecha>=DATEADD(yy, DATEDIFF(yy,0,getdate()), -1) and fecha<=DATEADD(mm, DATEDIFF(mm,0,getdate()), -1) and Zhis_series_main.codigo_fdo =fondosir.Codigo_Fdo and ltrim(rtrim(codigo_ser))<>'IM'
group by Fecha, Fondosir.Codigo_Fdo
order by fecha asc

-----Fondos
select distinct estrategia, Codigo_Largo, Codigo_Fdo
from fondosir
where active=1
order by estrategia, Codigo_Largo