select fecha, valor
from zhis_ars_clp
where fecha >= 'autodate1' and fecha <= 'autodate2'
order by fecha desc