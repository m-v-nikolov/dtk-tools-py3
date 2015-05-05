import json

import numpy as np
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt

from routes import *

with open('cache/raster_nodes_Haiti.json') as f:
    node_json = json.loads(f.read())

lonlats = np.array([(n['Longitude'],n['Latitude']) for n in node_json])
neighbor_tree=cKDTree(lonlats,leafsize=100)

for i,item in enumerate(lonlats[::50]): ##
    print(i,item)
    dists,idxs=neighbor_tree.query(item,k=3,distance_upper_bound=3)

    plt.scatter(*item,color='firebrick',alpha=0.5)
    neighbors=lonlats[idxs]
    plt.scatter(*zip(*neighbors),color='navy',alpha=0.5)

    for n in neighbors:
        latlons=[tuple(x[::-1]) for x in [item,n]]
        find_route(latlons,parse_fns=[route_time,plot_route])

plt.show()