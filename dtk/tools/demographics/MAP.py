import json
import time

from . Node import *
from . raster import *
from . routes import get_raster_nodes
from . db import *

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

def PfPR_from_file(geotiff_file, node_ids):
    A, transform_fn = raster.read(geotiff_file)
    lon,lat,alt = transform_fn(0,0) # upper-left corner of MAP
    xpixUL,ypixUL = Node.xpix_ypix_from_lat_lon(lat, lon, Node.Node.res_in_degrees) #default is 2.5arcmin
    
    # utility to map nodeid to raster index
    def raster_idx_from_nodeid(nodeid):
        xpix,ypix = Node.get_xpix_ypix(nodeid) # indexed to ll=(-90,-180)
        return ((xpix-xpixUL),(ypixUL-ypix))

    rows=[]
    for nid in node_ids:
        x,y = raster_idx_from_nodeid(nid)
        pfpr=float(A[y][x]) # tranposed?
        rows.append((nid,pfpr))
    return rows

if __name__ == '__main__':

    nodes = get_raster_nodes('cache/raster_nodes_Haiti.json', N=-1)
    nodeids = [Node.nodeid_from_lat_lon(n['Latitude'],
                                        n['Longitude'],
                                        res_in_deg=2.5/60) for n in nodes]

    begin = time.time()
    map_file = 'Q:/Malaria/MAP_cube_2000_2015/PfPR_cube_2000-2015_MEANS/MODEL42.2015.MEAN.PR.tif'
    PfPR_by_node = PfPR_from_file(map_file, nodeids)
    print('From file: elapsed time = %0.2f seconds' % (time.time() - begin))

    with open('cache/MAP_Haiti.json','w') as fp:
        json.dump(PfPR_by_node, fp, indent=4, sort_keys=True)

    begin = time.time()
    PfPR_by_node = query_PfPR_by_node(nodeids)
    print('From DB: elapsed time = %0.2f seconds' % (time.time() - begin))
