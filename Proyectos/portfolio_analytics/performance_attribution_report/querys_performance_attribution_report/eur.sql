select fecha, valor
from zhis_eur_clp
where fecha >= 'autodate1' and fecha <= 'autodate2'
order by fecha desc