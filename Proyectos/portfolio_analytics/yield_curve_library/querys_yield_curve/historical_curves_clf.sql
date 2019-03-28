select fecha,[0.0027]/100 as [0.0027], [0.25]/100 as [0.25], [0.5]/100 as [0.5], [0.75]/100 as [0.75] , [1]/100 as [1], [2]/100 as [2], [5]/100 as [5], [7]/100 as [7], [10]/100 as [10], [20]/100 as [20]
from zhis_curva_clf
where fecha >= 'AUTODATE1' and fecha <= 'AUTODATE2' and ((DATEPART(dw, fecha) + @@DATEFIRST) % 7) NOT IN (0, 1)