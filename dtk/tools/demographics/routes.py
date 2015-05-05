import json
from functools import partial
from itertools import combinations
import urllib2

from polyline.codec import PolylineCodec
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# https://github.com/Project-OSRM/osrm-backend/wiki/Server-api
# https://github.com/Project-OSRM/osrm-backend/wiki/Api-usage-policy
server = 'router.project-osrm.org'

def osrm_query(service,params,parse_fns=[]):
    try:
        search_query = 'http://' + server + '/' + service + '?' + params
        print(search_query)
        sf = urllib2.urlopen(search_query)
        #print(sf.read())
        response = json.loads(sf.read())
        for parse_fn in parse_fns:
            parse_fn(response)
    except urllib2.URLError, err:
        print(err.reason)
    finally:
        try:
            sf.close()
        except NameError:
            pass

def format_latlon_list(latlons):
    return '&'.join(['loc=' + '%0.3f,%0.3f' % ll for ll in latlons if all(np.isfinite(ll))])

def find_route(latlons,parse_fns=[]):
    osrm_query('viaroute',format_latlon_list(latlons),parse_fns)

def route_table(latlons,parse_fns=[]):
    osrm_query('table',format_latlon_list(latlons),parse_fns)

def dump_response(r):
    print(json.dumps(r,sort_keys=True,indent=2))

def format_seconds(seconds,drop_seconds=True):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if drop_seconds:
        return "%dh%02d" % (h,m)
    else:
        return "%d:%02d:%02d" % (h, m, s)

def route_time(r):
    route_in_seconds = r['route_summary']['total_time']
    print('Route time is %s' % format_seconds(route_in_seconds))
    return route_in_seconds

def distance_table(r,save_array=False):
    # API returns in 10th of seconds
    array_in_seconds=np.array(r['distance_table'])/10.
    print('Route time matrix:')
    np.set_printoptions(formatter={'float_kind':format_seconds})
    print(array_in_seconds)
    if save_array:
        np.save('cache/distance_table.npy',array_in_seconds)
    return array_in_seconds

def plot_route(r):
    points = PolylineCodec().decode(r['route_geometry'])
    lats,lons = zip(*points)
    def fix(values):
        # OSRM API uses 6 digits precision, rather than Google/OpenLayers default of 5
        # so the codec spits out lat,lon=19.9,-73.2 as (199,-732)
        return [v / 10. for v in values]
    plt.figure('RouteTrace')
    plt.plot(fix(lons),fix(lats),'-',color='gray')
    plt.gca().set(aspect='equal')
    plt.tight_layout()

def plot_table(r,latlonpops,label_edges):
    table=distance_table(r)
    lats,lons,pops=zip(*latlonpops)
    positions=zip(lons,lats)
    G=nx.Graph()
    for i,j in combinations(range(table.shape[0]), 2):
        G.add_edge(i,j,weight=table[i][j])
    plt.figure('DistanceMap')
    nx.draw_networkx_edges(G,positions,alpha=0.1,width=0.2,
                           edge_color=[d['weight'] for u,v,d in G.edges(data=True)],edge_cmap=cm.gray)
    if label_edges:
        edge_labels={(u,v):format_seconds(d['weight']) for u,v,d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G,positions,edge_labels=edge_labels,alpha=0.2)
    nx.draw_networkx_nodes(G,positions,node_size=[min(300,30*p/1e3) for p in pops],node_color='navy',alpha=0.5)
    plt.gca().set(aspect='equal')

def get_raster_nodes(node_file,N=5):
    # The first few nodes clustered from WorldPop raster for Haiti
    with open(node_file) as f:
        node_json = json.loads(f.read())[:N]
    return node_json

def test_viaroute():
    # A few nodes in NW Haiti
    nodes = [(19.9047,-73.1953), (19.7993,-73.2576)]
    find_route(nodes,[route_time,plot_route])

def test_table(node_file='cache/raster_nodes_Haiti.json',N=5,label_edges=False):
    node_json = get_raster_nodes(node_file,N)
    nodes = [(n['Latitude'],n['Longitude']) for n in node_json]
    latlonpops = [(n['Latitude'],n['Longitude'],n['InitialPopulation']) for n in node_json]
    route_table(nodes,[partial(plot_table,latlonpops=latlonpops,label_edges=label_edges)])

def dump_distance_table(node_file='cache/raster_nodes_Haiti.json',N=5):
    node_json = get_raster_nodes(node_file,N)
    nodes = [(n['Latitude'],n['Longitude']) for n in node_json]
    route_table(nodes,[partial(distance_table,save_array=True)])

#test_viaroute()
#dump_distance_table(N=200) # URI size limit reached if N much greater than 300
test_table(N=30,label_edges=False)
plt.show()

