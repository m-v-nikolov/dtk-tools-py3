import os
import networkx as nx
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
from math import radians, cos, sin, asin, sqrt
import numpy as np
import itertools

class GeoGraphGenerator(object):
	
	
	'''
	A geographical graph generator (connectivity depends on the distance between nodes);
	a future refactor may have a number graph generator types implementing a generic interface GraphTopoGenerator 
	'''

	def __init__(self, adjacency_list, node_properties, migration_radius = None):

		
		#how far would a person be able to travel in all cases (e.g. walkable distance); 
		#nodes distanced within that radius would be linked independent of adjacency list indication
		self.migration_radius = migration_radius
		
		
		'''
		adjacency_list of the form
		
		{
            node_id1: {
                            #key         # weight
                            node_id2: 0.5,
                            node_id4: 0.4,
                            node_id3: 0.4,
                            node_id5: 1,
                            ... 
                          },
                          
            node_id2: {
                            #key         # weight
                            node_id2: 0.4,
                            node_id3: 0.4,
                            node_id10: 1,
                            ... 
                          },
            ...
        }
		
		'''
		self.adjacency_list = adjacency_list
		
		
		
		'''
		node properties of the form
		
		{
			node_id1: [lon, lat, pop, node_label1],
			node_id2: [lon, lat, pop, node_label2],
			...
		}
		
		for all nodes in the adjacency list;
		
		this is not the best form; better have labeled properties, instead of depending on list order
	    '''
		self.node_properties = node_properties
		
		
		
		#networkx based geograph
		self.graph = None
	
	'''
	generate a networx graph based on distances between vertices
	'''
	def generate_graph(self):
		
		G=nx.Graph()
		G.position={}
		G.population={}
		G.name={}
		
		for node_id,properties in self.node_properties.iteritems():
			G.add_node(node_id)
			G.name[properties[3]] = node_id
			G.population[node_id] = properties[2]
			G.position[node_id]=(properties[0], properties[1]) # (x,y) for matplotlib
	
		# add an edge between any two nodes distanced less than max_kms away
		
		for n in itertools.combinations(G.nodes(),2):
			distance = self.get_haversine_distance(G.position[n[0]][0],G.position[n[0]][1],G.position[n[1]][0],G.position[n[1]][1])
			if not self.migration_radius or distance < self.migration_radius:
				G.add_edge(n[0], n[1], weight = distance)
		
	
		# add edge based on adjacency matrix
		for node_id, node_links in self.adjacency_list.iteritems():
			for node_link_id, w in node_links.iteritems():
				distance = self.get_haversine_distance(G.position[int(node_id)][0], G.position[int(node_id)][1], G.position[int(node_link_id)][0], G.position[int(node_link_id)][1])
				G.add_edge(int(node_id), int(node_link_id), weight = distance*w)
				
		self.graph = G
		
		return G
	
	
	'''
	get shortest paths based on link weights
	'''
	def get_shortest_paths(self):
		
		return nx.shortest_path_length(self.graph, weight='weight') 
	
		
	'''
	    Calculate the great circle distance between two points 
	    on the earth (specified in decimal degrees)
	'''
	def get_haversine_distance(self, lon1, lat1, lon2, lat2):


		# convert decimal degrees to radians 
		lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
		
		# haversine formula 
		dlon = lon2 - lon1 
		dlat = lat2 - lat1 
		a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
		c = 2 * asin(sqrt(a))
		
		# 6367 km is the radius of the Earth
		km = 6367 * c
		
		return km