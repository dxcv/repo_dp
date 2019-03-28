SELECT Rtrim(Ltrim(codigo_fdo)), 
       periodo, 
       Ltrim(Rtrim(codigo_cta)), 
       Ltrim(Rtrim(nombre_cta)), 
       estado, 
       moneda, 
       CASE 
         WHEN debe > haber THEN [debe] - [haber] 
         ELSE [haber] - [debe] 
       END AS SALDO 
FROM   (SELECT codigo_fdo, 
               periodo, 
               codigo_cta, 
               nombre_cta, 
               estado, 
               moneda, 
               [debe_01] + [debe_02] + [debe_03] + [debe_04] 
               + [debe_05] + [debe_06] + [debe_07] + [debe_08] 
               + [debe_09] + [debe_10] + [debe_11] + [debe_12]     AS DEBE, 
               [haber_01] + [haber_02] + [haber_03] + [haber_04] 
               + [haber_05] + [haber_06] + [haber_07] + [haber_08] 
               + [haber_09] + [haber_10] + [haber_11] + [haber_12] AS HABER 
        FROM   [BCS11384].[BDPFM2].dbo.fm_plan_cuentas 
        WHERE  periodo = '2017' 
               AND codigo_fdo IN ( 'IMT E-PLUS', 'MACRO CLP3', 'SPREADCORP', 
                                   'DEUDA CORP' ) 
               AND codigo_cta IN ( '101001001001', '101001001002', 
                                   '101001002002', 
                                   '101001001004', 
                                   '101001001005', '101001001008', 
                                   '101003001001', 
                                   '101003001002', 
                                   '101003001008', '101003001003', 
                                   '201001001002', 
                                   '201001001003', 
                                   '201001001006', '101001001003', 
                                   '101001002001', 
                                   '101001002003', 
                                   '201001001003', '101001002004', '201010100', 
                                   '201001001005', 
                                   '201010070', '201010020', '201010060', 
                                   '201 010080', 
                                   '201010090', '201001001004', '201001001001' ) 
       ) a1 
UNION ALL 
SELECT Rtrim(Ltrim(codigo_fdo)), 
       periodo, 
       Ltrim(Rtrim(codigo_cta)), 
       Ltrim(Rtrim(nombre_cta)), 
       estado, 
       moneda, 
       CASE 
         WHEN debe > haber THEN [debe] - [haber] 
         ELSE [haber] - [debe] 
       END AS SALDO 
FROM   (SELECT codigo_fdo, 
               periodo, 
               codigo_cta, 
               nombre_cta, 
               estado, 
               moneda, 
               [debe_01] + [debe_02] + [debe_03] + [debe_04] 
               + [debe_05] + [debe_06] + [debe_07] + [debe_08] 
               + [debe_09] + [debe_10] + [debe_11] + [debe_12]     AS DEBE, 
               [haber_01] + [haber_02] + [haber_03] + [haber_04] 
               + [haber_05] + [haber_06] + [haber_07] + [haber_08] 
               + [haber_09] + [haber_10] + [haber_11] + [haber_12] AS HABER 
        FROM   [BCS11384].[BDPFM1].dbo.fm_plan_cuentas 
        WHERE  periodo = '2017' 
               AND codigo_fdo IN ( 'RENTA', 'DEUDA 360', 'Liquidez', 'M_MARKET', 
                                   'DSMULTI', 'MACRO 1.5' ) 
               AND codigo_cta IN ( '101001001001', '101001001002', 
                                   '101001001004', 
                                   '101001001005', 
                                   '101001001008', '101003001001', 
                                   '101003001003', 
                                   '101003001008', 
                                   '201001001002', '201001001003', 
                                   '101001001003', 
                                   '101001002001', 
                                   '101001002003', '101001002002', 
                                   '101001002004', 
                                   '201010100', 
                                   '2010100 60', '201010070', '201010080', '201010090' )) 
       a1 