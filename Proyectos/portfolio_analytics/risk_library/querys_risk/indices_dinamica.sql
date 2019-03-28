select fecha, index_id, cast(valor as float) as valor 
from Indices_Dinamica 
where fecha >= 'AUTODATE1' and fecha <= 'AUTODATE2'
