import psycopg2

class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)

try:
    cnxn = psycopg2.connect(host='ivlabsdssql01.na.corp.intven.com', port=5432, dbname='idm_db')
except pycopg2.Error:
    raise Exception("Failed connection to %s." % server_name)

#SQL="""SELECT * FROM sd.alias2hierarchynamealt('Africa',sd.default_hierarchy_nameset())"""
SQL="""SELECT * FROM sd.get_hierarchy_id_children_at_level(5,1)"""

cursor = cnxn.cursor()
cursor.execute(SQL)
rows=cursor.fetchall()
#print(rows)
for row in rows:
    if any([l in row[1] for l in ['Liberia','Guinea','Sierra Leone']]):
        print(row)
cnxn.close()
