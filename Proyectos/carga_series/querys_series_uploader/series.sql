select Fecha, Codigo_Fdo, Codigo_Ser, Valor_Cuota, Patrimonio_Final
from FM_ZHIS_SERIES 
where Fecha>='AUTODATE1' AND Fecha <='AUTODATE2'