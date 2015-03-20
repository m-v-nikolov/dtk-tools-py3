import psycopg2
import matplotlib.pyplot as plt
from node import Node
from plotting import plot_nodes

class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)

def query_DB_for_shape_data(parent_alias,relative_admin_level):

    try:
        cnxn = psycopg2.connect(host='ivlabsdssql01.na.corp.intven.com', port=5432, dbname='idm_db')
    except pycopg2.Error:
        raise Exception("Failed connection to %s." % server_name)

    cursor = cnxn.cursor()
    data = (parent_alias,relative_admin_level)
    SQL  =  """SELECT a.hid_id as hid, a.hname, a.dt_name, a.shape_id as node_id, 
                       b.country_continent_id as iso_number, 
                       c.iso, c.iso3, c.fips,
                       d.area_len, d.geogcenterlat as centerlat, d.geogcenterlon as centerlon, 
                       e.calc_pop_total as totalpop
                FROM sd.get_hierarchy_children_at_level_with_shape_id_alt(%s, null, null, %s) a
                INNER JOIN sd.hierarchy_name_table b
                    ON a.hid_id = b.id
                INNER JOIN sd.country_information c
                    ON b.country_continent_id = c.iso_number
                INNER JOIN sd.shape_table d
                    ON d.id = a.shape_id
                INNER JOIN sd.shape_population_totals e
                    ON a.shape_id = e.shape_id
                WHERE e.reference_year = 2010
                ORDER BY a.shape_id;"""

    cursor.execute(SQL, data)
    nodes = []
    for row in cursor:
        r=reg(cursor,row)
        n=Node(r.centerlat, r.centerlon, r.totalpop, name=r.hname, area=r.area_len)
        nodes.append(n)
    cnxn.close()

    return nodes

if __name__ == '__main__':

    parent_alias='Nigeria' # only works for no ambiguity, e.g. Kano State or LGA
    relative_admin_level=2 # this is relative to the parent_alias admin level

    nodes = query_DB_for_shape_data(parent_alias,relative_admin_level)
    print('There are %d shapes %d admin level(s) below %s' % (len(nodes),relative_admin_level,parent_alias))

    plt.figure(parent_alias,facecolor='w',figsize=(7,6))
    plot_nodes(nodes, title=parent_alias)
    plt.show()


