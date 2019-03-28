SELECT fecha, 
       [0.0833333] / 100 AS [0.0833333], 
       [0.25] / 100 AS [0.25], 
       [0.5] / 100  AS [0.5], 
       [0.75] / 100 AS [0.75], 
       [1] / 100    AS [1], 
       [1.5] / 100  AS [1.5], 
       [2] / 100    AS [2] 
FROM   zhis_curva_swap_usd
WHERE  fecha >= 'autodate1' AND fecha <= 'autodate2'