SELECT LTRIM(RTRIM(t1.codigo_fdo)) as Fondo, t1.Valor as monto_pactado
  FROM LAGUNILLAS.PFMIMT2.dbo.FM_DMOVTOS_CONTABILIDAD t1
  LEFT JOIN
  LAGUNILLAS.PFMIMT2.dbo.FM_PLAN_CUENTAS t2
  on t1.codigo_fdo = t2.codigo_fdo and t1.Codigo_Cta = t2.Codigo_Cta and YEAR(t1.fecha) = t2.Periodo
  WHERE t1.Fecha = 'AUTODATE' and t1.Descripcion like 'DOCTOS POR PAGAR PACTOS%' 
  and t1.Ind_Saldo='H'
