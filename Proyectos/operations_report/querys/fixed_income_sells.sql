select vende as codigo_fdo, instrumento as codigo_ins, sum(cantidad) as nominal
from Transaccionesirf
where fecha = 'autodate' and vende is not null
group by vende, Instrumento