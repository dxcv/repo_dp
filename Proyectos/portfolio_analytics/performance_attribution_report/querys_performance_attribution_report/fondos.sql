select codigo_fdo, codigo_largo, serie
from fondosir
where info_attribution = 1 and active = 1
order by estrategia asc