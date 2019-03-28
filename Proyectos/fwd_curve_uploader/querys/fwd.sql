SELECT fecha, 
       [0.0833333] AS [0.0833333], 
       [0.25] AS [0.25], 
       [0.5]  AS [0.5], 
       [0.75] AS [0.75], 
       [1]    AS [1], 
       [1.5]  AS [1.5], 
       [2]    AS [2] 
FROM   zhis_curva_fwd 
WHERE  fecha = 'autodate'