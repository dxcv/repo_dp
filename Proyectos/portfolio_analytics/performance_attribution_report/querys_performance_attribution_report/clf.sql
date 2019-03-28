select fecha, valor
from zhis_clf_clp
where fecha >= 'autodate1' and fecha <= 'autodate2'
order by fecha desc