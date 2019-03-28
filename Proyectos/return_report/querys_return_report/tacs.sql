select fecha, tac
from zhis_tac
where codigo_fdo = 'AUTOFUND' and codigo_ser = 'AUTOSERIE'
and fecha >= 'AUTODATE1'
and fecha <= 'AUTODATE2' 
order by fecha asc
