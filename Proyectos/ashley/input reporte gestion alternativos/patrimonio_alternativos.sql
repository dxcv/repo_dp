SELECT G.fecha, 
       G.codigo_fdo, 
       CASE 
         WHEN G.moneda = 3001 THEN G.patrimonio / 1000000 
         ELSE G.tipodecambio * G.patrimonio / 1000000 
       END AS PatrimonioCLPMM 
FROM   (SELECT F.fecha, 
               F.codigo_fdo, 
               F.patrimonio, 
               F.moneda, 
               D.valor, 
               CASE 
                 WHEN ( D.valor IS NULL 
                        AND F.moneda <> 3001 ) THEN (SELECT TOP 1 valor 
                                                     FROM 
                 mesainversiones.dbo.indices_dinamica 
                                                     WHERE  fecha >= F.fecha 
                                                            AND 
                                                    index_id = F.indice 
                                                     ORDER  BY fecha ASC) 
                 ELSE D.valor 
               END AS TipodeCambio 
        FROM   (SELECT A.fecha, 
                       A.codigo_fdo, 
                       A.patrimonio, 
                       B.moneda, 
                       B.nombre_fdo, 
                       CASE 
                         WHEN B.moneda = 3000 THEN 66 
                         WHEN B.moneda = 3002 THEN 262 
                         ELSE NULL 
                       END AS INDICE 
                FROM   (SELECT fecha, 
                               codigo_fdo, 
                               Patrimonio=Sum(patrimonio) 
                        FROM   [MesaInversiones].[dbo].zhis_series_main 
                        WHERE  fecha IN (SELECT fecha 
                                         FROM 
                               [MesaInversiones].[dbo].zhis_series_main 
                                         WHERE  fecha >= 'autodate'
                                                AND fecha <= 'autodate1'
                                                GROUP  BY fecha) 
                               AND codigo_fdo IN ( 'ACONCAG-I', 'ACONCA-II', 
                                                   'ESP-CORDOV', 
                                                   'FI PATIO I', 
                                                   'RAICES', 'RENTA INM', 
                                                   'PRIVA-APAX', 
                                                   'Private IC', 
                                                   'PRIVATE-EQ', 'FI PE AIX', 
                                                   'PG SEC II', 
                                                   'PGDIRECTII', 
                                                   'P EQ SEC I', 'TIERRASDS', 
                                                   'PE FULLY F', 
                                                   'DIRECT_III', 
                                                   'RENTA_RESI', 'PGRE SEC I', 
                                                   'FI PLAZA-E', 
                                                   'FI CC SLP' ) 
                        GROUP  BY fecha, 
                                  codigo_fdo) AS A 
                       LEFT JOIN mesainversiones.dbo.fondos AS B 
                              ON A.codigo_fdo = B.codigo_fdo) AS F 
               LEFT JOIN mesainversiones.dbo.indices_dinamica D 
                      ON D.fecha = F.fecha 
                         AND D.index_id = F.indice) G 
ORDER  BY G.codigo_fdo ASC, 
          G.fecha ASC 