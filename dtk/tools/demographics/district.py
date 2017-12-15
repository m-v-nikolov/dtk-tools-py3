import os

import matplotlib.pyplot as plt

from . Node import Node, nodes_for_DTK
from . plotting import plot_nodes
from . db import *


def query_DB_for_shape_data(parent_alias, relative_admin_level, shape_set='EMED'):

    cnxn = idm_DB_connection()
    cursor = cnxn.cursor()
    data = (parent_alias, '%sNames' % shape_set, '%sShapes' % shape_set, relative_admin_level)
    SQL = """SELECT a.hid_id as hid, a.hname, a.dt_name, a.shape_id as node_id,
                 b.country_continent_id as iso_number,
                 c.iso, c.iso3, c.fips,
                 d.area_len, d.geogcenterlat as centerlat, d.geogcenterlon as centerlon,
                 e.calc_pop_total as totalpop
             FROM sd.get_hierarchy_children_at_level_with_shape_id_alt(%s, %s, %s, %s) a
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
        r = reg(cursor,row)
        n = Node(r.centerlat, r.centerlon, r.totalpop, name=r.hname, area=r.area_len)
        print(n.to_dict())
        nodes.append(n)
    cnxn.close()

    return nodes

if __name__ == '__main__':

    parent_alias = 'Pakistan'  # only works for no ambiguity, e.g. Kano State or LGA
    relative_admin_level = 3  # this is relative to the parent_alias admin level

    # parent_alias = 'Haiti'
    # relative_admin_level = 2
    # shape_set = 'GADM'  # Haiti not included in 'EMED'

    nodes = query_DB_for_shape_data(parent_alias, relative_admin_level)
    print('There are %d shapes %d admin level(s) below %s' % (len(nodes), relative_admin_level, parent_alias))

    Node.res_in_degrees = 2.5/60

    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    node_output_file = os.path.join(cache_dir, '%s_admin%d_demographics.json' % (parent_alias, relative_admin_level))
    nodes_for_DTK(node_output_file, nodes)

    plt.figure(parent_alias, facecolor='w', figsize=(7,6))
    plot_nodes(nodes, title=parent_alias)
    plt.show()


