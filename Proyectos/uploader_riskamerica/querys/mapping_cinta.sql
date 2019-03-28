Select rtrim(Codigo_Ins) as Codigo_Ins, CASE
WHEN Tipo in ('DEB','BCA') THEN 'Bono Corporativo'
WHEN Tipo in ('BEF', 'BCS','BSF','BHM') THEN 'Bono Bancario'
WHEN Tipo in ('BCU','BTU','BCP','BTP','CERO','PRC','BVL') Then 'Bono de Gobierno'
WHEN Tipo = 'LHF' THEN 'Letra Hipotecaria'
WHEN Tipo in ('DPF','ECO','PDBC','PDC') THEN 'Deposito'
END as tipo_instrumento, 
CASE 
	WHEN Moneda='NO' Then '$'
	Else LTRIM(RTRIM(Moneda))
END as Moneda
from Cinta_Valorizacion where fecha='AUTODATE'

