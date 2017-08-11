import os
import json
import osm2nx
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from urllib import urlopen

import collections
import psycopg2
import json


geographies = {
    'Seattle': dict(
        bbox=(-122.35, 47.59, -122.32, 47.62)),

    'Kano': dict(
        bbox=(7.4020, 10.9385, 9.6130, 12.8627)),  # region

    'Garki': dict(
        bbox=(8.66, 12.1, 9.7, 12.7)),

    'Senegal': dict(
        bbox=(-17.496, 12.077, -10.712, 16.852),
        demographics_countries=['Senegal']),

    'Thies': dict(
        bbox=(-17.2451, 14.5537, -16.8256, 14.9912),  # area around Thies, Senegal
        residential=True),

    'Ebola': dict(
        demographics_countries=['Guinee', 'Sierra_Leone', 'Liberia'],
        bbox=(-15.392, 3.941, -6.614, 12.823)),

    'Haiti': dict(bbox=(-74.4846, 17.9787, -71.6226, 20.0972))
}


def get_geography(geography, overwrite=False):

    settings = geographies[geography]
    bbox = settings['bbox']

    dir_path = os.path.dirname(os.path.realpath(__file__))
    roads_file = os.path.join(dir_path, 'cache', 'all_roads_%s.osm' % geography)

    # Configure geography-specific resolution of road types to download
    highway_types = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']
    if settings.get('residential', False):
        highway_types.append('residential')
    if settings.get('unclassified', True):
        highway_types.append('unclassified')
    types_str = '|'.join(highway_types)

    # Query Overpass API for OSM highway objects within bounding box
    if overwrite or not os.path.exists(roads_file):
        fp = urlopen("http://www.overpass-api.de/api/xapi?*[highway=%s][bbox=%f,%f,%f,%f]"
                     % tuple([types_str] + list(bbox)))
        with open(roads_file, 'w') as f:
            f.write(fp.read())

    # Read edges into networkx Graph
    G = osm2nx.read_osm(roads_file, only_roads=False)

    G.position = {}
    for n_id in G.nodes_iter():
        na = G.node[n_id]['data']
        G.position[n_id] = (na.lon, na.lat)

    # Set colors according to highway types
    G.edge_colors = []
    # TODO: vary the line widths also depending on the edge types?
    for ii, (n1, n2, way) in enumerate(G.edges_iter(data=True)):
        tt = way['data'].tags
        if 'highway' in tt:
            if 'motorway' in tt['highway']:
                G.edge_colors.append('#7994b8')
            elif 'trunk' in tt['highway']:
                G.edge_colors.append('#84c484')
            elif 'primary' in tt['highway']:
                G.edge_colors.append('#cc8e8e')
            elif 'secondary' in tt['highway']:
                G.edge_colors.append('#e8c599')
            elif 'tertiary' in tt['highway']:
                G.edge_colors.append('#d8d88a')
            else:
                G.edge_colors.append('lightgrey')

    return G


def draw_geography(G, ax):

    nx.draw(G, G.position, with_labels=False, ax=ax,
            node_size=0, node_color='gray', alpha=0.4,
            edge_color=G.edge_colors)


###########
# min_pop=10 # was 1e3
# if not demographics_countries:
#     demographics_countries=[geography]
# cmaps=['Blues','Greens','Reds']
# for i,country in enumerate(demographics_countries):
#     with open('cache/raster_nodes_%s.json' % country,'r') as fjson:
#         gis_nodes=json.loads(fjson.read())
#     lats,lons,pops=[],[],[]
#     for n in gis_nodes:
#         pop=n['InitialPopulation']
#         if pop<min_pop:
#             continue
#         lats.append(n['Latitude'])
#         lons.append(n['Longitude'])
#         pops.append(pop)
#     sizes=[min(3e3,5+p/250.) for p in pops]
#
#     plt.scatter(lons,lats,s=sizes, c=np.log10(pops), cmap=cmaps[i%len(cmaps)], vmin=1, vmax=4, alpha=0.3)

# make nodes for all the scatter population points

# find closest walking-distance road node and connect

# throw away disconnected parts not belonging to giant component

# trim all order-2 nodes and reassign distance weights of neighbor connections to new larger edge
# or a more minimal trimming with reasonable fidelity in plotting via Ramer-Douglas-Peucker
# trim dead-end roads, i.e. non-population nodes with order=1 all the way back to either a population or an intersection

# confirm by replotting more angular connected edge map

# shortest paths on population node pairs.
# need to think about sparse road connections, e.g. shortest walk to all bounding roads?

# truncate big pairwise matrix to sparser representation of most-connected neighbors

# refactor this whole thing into a sensible set of modules and functions :)


# def get_country_shape(country):
#     try:
#         server_name = 'ivlabsdssql01.na.corp.intven.com'
#         cnxn = psycopg2.connect(host=server_name, port=5432, dbname='idm_db')
#     except psycopg2.Error:
#         raise Exception("Failed connection to %s." % server_name)
#     cursor = cnxn.cursor()
#     SQL = ("SELECT ST_AsGeoJSON(d.geom) as geom "
#             "FROM sd.shape_table d "
#             "WHERE d.id = %s; ")
#     params=(country,)
#     cursor.execute(SQL,params)
#     geojson = json.loads(cursor.fetchone()[0])
#     return geojson['coordinates']
#
#
# def plot_geojson_shape(coords):
#     if isinstance(coords[0][0], collections.Iterable):
#         for c in coords:
#             plot_geojson_shape(c)
#     else:
#         x = [i for i,j in coords]
#         y = [j for i,j in coords]
#         plt.plot(x,y,'darkgray')

if __name__ == '__main__':

    geography = 'Thies'
    sources = ['WorldPop', 'OpenStreetMap']

    fig = plt.figure('%s_%s' % (geography,'_'.join(sources)), figsize=(9, 8))
    ax = fig.add_subplot(111, aspect='equal')

    G = get_geography(geography)
    draw_geography(G, ax)

    if geography == 'Senegal':
        sources.append('D4D')

    ax.set_title('%s (%s)' % (geography,' + '.join(sources)))
    fig.set_tight_layout(True)

    ###########
    # if geography == 'Ebola':
    #     #country_names=['Guinea','Sierra Leone','Africa:Liberia']
    #     shape_ids=[230,41,151]
    #     for shape_id in shape_ids:
    #         country_shape=get_country_shape(shape_id)
    #         plot_geojson_shape(country_shape)

    ###########
    # if geography == 'Senegal':
    #     import csv
    #     with open(os.path.join('\\\\peebles.intvenlab.com\\shared\\EMOD\\Data\\D4D Senegal\\ContextData','SITE_ARR_LONLAT.CSV'),'r') as towers_f:
    #         reader = csv.reader(towers_f)
    #         header=reader.next()
    #         tower_lons,tower_lats=[],[]
    #         for line in reader:
    #             tower_lons.append(line[2])
    #             tower_lats.append(line[3])
    #         print(len(tower_lons))
    #     plt.scatter(tower_lons, tower_lats, s=2, c='k')
    ###########

    plt.show()
