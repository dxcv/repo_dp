
    SELECT ltrim(rtrim(pc.codigo_fdo)) as codigo_fdo,
               SUM(CASE 
                 WHEN LEFT(pc.codigo_cta, 1) = 1 THEN 
                 pc.[debe_01] + pc.[debe_02] + pc.[debe_03] 
               + pc.[debe_04] + pc.[debe_05] + pc.[debe_06] 
               + pc.[debe_07] + pc.[debe_08] + pc.[debe_09] 
               + pc.[debe_10] + pc.[debe_11] + pc.[debe_12] - pc.[haber_01] - 
                 pc.[haber_02] 
                                                      - pc.[haber_03] - 
                 pc.[haber_04] - 
                 pc.[haber_05] - pc.[haber_06] - pc.[haber_07] - pc.[haber_08] - 
                 pc.[haber_09] 
               - pc.[haber_10] - pc.[haber_11] - pc.[haber_12] 
                 ELSE pc.[haber_01] + pc.[haber_02] + pc.[haber_03] 
                      + pc.[haber_04] + pc.[haber_05] + pc.[haber_06] 
                      + pc.[haber_07] + pc.[haber_08] + pc.[haber_09] 
                      + pc.[haber_10] + pc.[haber_11] + pc.[haber_12] - 
                      pc.[debe_01] - 
                      pc.[debe_02] 
                             - pc.[debe_03] - pc.[debe_04] - pc.[debe_05] - 
                      pc.[debe_06] - 
                             pc.[debe_07] - pc.[debe_08] - pc.[debe_09] - 
                      pc.[debe_10] 
                      - 
                      pc.[debe_11] - pc.[debe_12] 
               END) AS balance 
        FROM   [BCS11384].[BDPFM2].dbo.fm_plan_cuentas pc, 
               fondosir f 
        WHERE  periodo = LEFT('2018-01-30', 4) 
               AND f.codigo_fdo = pc.codigo_fdo COLLATE database_default 
               AND f.codigo_fdo IN ('MACRO CLP3', 'MACRO 1.5', 'IMT E-PLUS', 'RENTA')
               AND F.info_invest = 1 
               AND pc.codigo_cta IN (  '201010100','201010060')
		group by pc.codigo_fdo		
													
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				
																				