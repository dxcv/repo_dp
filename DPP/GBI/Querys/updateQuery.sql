/* borrar instrumentos_diego*/

update instrumentos_diego
set Codigo_Ins=LEFT(Codigo_Ins, LEN(Codigo_Ins)-1)
where Codigo_Ins in( 'QZ7003432','QZ8845377','QZ8845385','EK6900568','EJ5013655','AL9338982','AF1807128',
'AO2615059','JV5290624','LW8106244','EI1383294','AO2615067','EJ0602940','EK0169285','JV5341526','105756BL3',
'105756BT6','105756BN9','168863AU2','EK0291089','EF0376436','EJ1922511','EH7652033','EI8220614','EJ5096460',
'EK6999263','AM1281642','EI2021109','EJ3668765','EG5593306','EH7175118','EI7361336','EI1588082','EJ0234298',
'ED2028832','QJ1649335','EG1116375','EK1693424','EH6944449','AM7523740','EF0252694','EK5799607','QZ7445096',
'EH3330816','AO4008642','AN9574152','AP0760557')


