import json

import numpy as np
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
import networkx as nx

from routes import find_route,route_time,plot_route

with open('cache/raster_nodes_Haiti.json') as f:
    node_json = json.loads(f.read())

latlonpops = [(n['Latitude'],n['Longitude'],n['InitialPopulation']) for n in node_json]
lonlats=np.array([(lon,lat) for lat,lon,pop in latlonpops])
neighbor_tree=cKDTree(lonlats,leafsize=100)
print('There are %d selected nodes' % len(lonlats))

def query_neighbor_routes(max_srcs=20):
    for i,item in enumerate(lonlats[::50]): ##
        print(i,item)
        dists,idxs=neighbor_tree.query(item,k=5,distance_upper_bound=10)

        plt.scatter(*item,color='firebrick',alpha=0.5)
        neighbors=lonlats[idxs]
        plt.scatter(*zip(*neighbors),color='navy',alpha=0.5)

        for n in neighbors:
            latlons=[tuple(x[::-1]) for x in [item,n]]
            find_route(latlons,parse_fns=[route_time,plot_route])

        if max_srcs>0 and i>max_srcs:
            #Don't overuse the OSRM test server accidentally
            break

def adjacency_network():
    G=nx.Graph()
    for i,item in enumerate(latlonpops):
        lat,lon,pop=item
        G.add_node(i,lat=lat,lon=lon,pop=pop)
        dists,idxs=neighbor_tree.query((lon,lat),k=8,distance_upper_bound=0.15)
        for idx,dist in zip(idxs,dists):
            if i==idx or not np.isfinite(dist):
                continue
            G.add_edge(i,idx,weight=dist)
    print('%d adjacency edges' % G.number_of_edges())
    print('Connected components:',[len(c) for c in nx.connected_components(G)])
    return G

def plot_network(G,nc='navy',ec='darkgray',na=0.2,ea=0.2):
    plt.figure('AdjacencyNetwork',figsize=(10,8))
    nodes=G.nodes(data=True)
    positions=[(n[1]['lon'],n[1]['lat']) for n in nodes]
    sizes=[30*n[1]['pop']/1e4 for n in nodes]
    nx.draw_networkx_nodes(G,positions,with_labels=False,node_color=nc,alpha=na,node_size=sizes)
    nx.draw_networkx_edges(G,positions,with_labels=False,edge_color=ec,alpha=ea,edge_cmap=cm.gray,arrows=False)
    plt.gca().set(aspect='equal')
    plt.tight_layout()

def path_lengths(G,src=None):
    if src:
        D=nx.single_source_dijkstra_path_length(G,src)
        return {src:D}
    else:
        D = nx.all_pairs_dijkstra_path_length(G)
        return D

def gravity(mass,dist,const=0.01):
    if not dist > 0:
        raise Exception('Distance must be positive')
    return const * mass * pow(dist,-2)

max_connections={'local':8,'regional':30}

def gravity_network(G,D,mode='regional'):
    H=nx.DiGraph()
    H.add_nodes_from(G.nodes(data=True))
    for src,lengths in D.items():
        if mode=='local':
            dists,idxs=neighbor_tree.query((G.node[src]['lon'],G.node[src]['lat']),k=max_connections['local']+1) # for self
            for idx in idxs:
                if idx==src or idx not in lengths:
                    continue
                H.add_edge(src,idx,weight=gravity(G.node[idx]['pop'],lengths[idx]))
        elif mode=='regional':
            dest_weights=[(dest,gravity(G.node[dest]['pop'],dist)) for dest,dist in lengths.items() if dist>0]
            dest_weights.sort(key=lambda tup: tup[1], reverse=True)  # sorts by outgoing migration rate
            for dest,weight in dest_weights[:max_connections['regional']]:
                H.add_edge(src,dest,weight=weight)
        else:
            print('Not supporting mode=%s' % mode)
    return H

#query_neighbor_routes()

G=adjacency_network()
#plot_network(G)

D=path_lengths(G,src=100)
H=gravity_network(G,D,mode='local')
plot_network(H,ea=0.5,na=0.2,ec=[e[2]['weight'] for e in H.edges(data=True)])

plt.show()