import json

from routes import get_raster_nodes
from node import get_node_id
from db import *

def query_PfPR_by_node(node_ids):
    cnxn = idm_DB_connection()
    cursor = cnxn.cursor()
    data = (node_ids,)

    SQL = """SELECT pr.nodeid, pr.q50 
             FROM malaria.pr as pr 
             WHERE pr.nodeid = ANY(%s);"""

    cursor.execute(SQL, data)
    rows=[]
    for row in cursor:
        r=reg(cursor,row)
        rows.append((r.nodeid,r.q50))
    cnxn.close()
    return rows

if __name__ == '__main__':
    nodes=get_raster_nodes('cache/raster_nodes_Haiti.json',N=-1)
    nodeids=[get_node_id(node['Latitude'],node['Longitude'],res_in_degrees=2.5/60) for node in nodes]
    PfPR_by_node=query_PfPR_by_node(nodeids)
    with open('cache/MAP_Haiti.json','w') as fp:
        json.dump(PfPR_by_node,fp,indent=4,sort_keys=True)