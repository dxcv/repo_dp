select vende as codigo_fdo, emisor as codigo_emi, instrumento as codigo_ins, dias as dias, sum(rescate) as nominal
from Transaccionesiif
where fecha = 'autodate' and vende is not null
group by vende, emisor, instrumento, dias