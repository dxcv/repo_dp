SELECT Ltrim(Rtrim(fecha))              AS date,
       Ltrim(Rtrim(indice))         	AS name, 
       Ltrim(Rtrim(nemo))         	AS instrument_code, 
       Ltrim(Rtrim(clasificacion))      AS risk,
       duracion				AS duration,
       plazoResidual			AS maturity_years,
       ponderacion 			AS weight,
       tirVal				AS yield
FROM   dbo.Indices_RAIM
WHERE  fecha = 'AUTODATE'