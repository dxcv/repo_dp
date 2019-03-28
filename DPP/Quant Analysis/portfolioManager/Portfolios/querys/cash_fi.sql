select RTRIM(LTRIM(Codigo_Fdo)) as Name, Periodo as Year, ltrim(rtrim(Codigo_Cta)) as Account, ltrim(rtrim(Nombre_Cta)) as Account_Name, 
Case when DEBE>HABER then [DEBE]-[HABER] else [HABER]-[DEBE] end AS Balance from 
(
SELECT Codigo_Fdo, Periodo, Codigo_Cta, Nombre_Cta, Estado, Moneda,[Debe_01]+[Debe_02]+[Debe_03]+[Debe_04]+[Debe_05]+[Debe_06]+[Debe_07]+[Debe_08]+[Debe_09]+[Debe_10]+[Debe_11]+[Debe_12] AS DEBE, 
[Haber_01]+[Haber_02]+[Haber_03]+[Haber_04]+[Haber_05]+[Haber_06]+[Haber_07]+[Haber_08]+[Haber_09]+[Haber_10]+[Haber_11]+[Haber_12] AS HABER 
from [BCS11384].[BDPFM2].dbo.FM_PLAN_CUENTAS 
WHERE Periodo='2016' 
AND codigo_fdo in ('MACRO CLP3') AND Codigo_Cta in ('101001001001', '101001001002', '101001001004', '101001001005', '101001001008', '101003001001', '101003001003','201001001002', '201001001003', '101001001003', '101001002001', '101001002003', '101001002002', '101001002004','201010100','201010060','201010070','201010080','201010090')) a1

