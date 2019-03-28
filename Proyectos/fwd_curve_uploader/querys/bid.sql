select fecha, [1M], [3M], [6M], [9M], [12M], [18M], [24M]
from zhis_fwd_usd_bid
where fecha = 'autodate'