from diz6 import partner6_type
from diz8 import partner8_converter

f_sql = open('correct.sql', 'w')

for old6 in partner6_type:
    new8 = partner8_converter.get(old6, False)
    if not new8:
        print "Errore con ID old6: %s" % old6
        continue
    f_sql.write("UPDATE res_partner set type_id=%s where id= %s;\n" % (
        partner6_type[old6],
        new8,
        ))
        

