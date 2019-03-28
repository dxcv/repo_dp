Select CONVERT(varchar(5),Year_Bucket) as bucket, CASE WHEN moneda='CLP' then '$' Else RTRIM(LTRIM(moneda)) END as moneda, 
SUM(Weight_fondo*duration)/SUM(Weight_fondo) as dur_w, SUM(weight_fondo)/100 as weight
from Cartera_Gob_AFP_E where fecha=(Select MAX(Fecha) from Cartera_Gob_AFP_E)
group by Year_Bucket, Moneda

