import os
import networkx as nx
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
from math import radians, cos, sin, asin, sqrt, pow
import random
import numpy as np
import itertools


class SmallWorldGridGraphGenerator(object):
	
	
	'''
	A geographical graph generator (connectivity depends on the distance between nodes);
	a future refactor may have a number graph generator types implementing a generic interface GraphTopoGenerator 
	'''

	def __init__(self, adjacency_list, node_properties):

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
			node_id1: [lon, lat, pop, node_label1, ...], # optional properties after node_label;
			node_id2: [lon, lat, pop, node_label2, ...], # optional properties after node_label;
			...
		}
		
		for all nodes in the adjacency list;
		
		this is not the best form; better have labeled properties, instead of depending on list order
	    '''
		self.node_properties = node_properties

		#networkx based geograph
		self.graph = None
	
	'''
	Generate a small world networx graph on a 2d grid:
	- assume nodes occupy a subset of points on a regular square 2d grid
	- assume adjacency_list is provided specifying the *local* grid connections of nodes; the long range links will be automatically added
	
	Notes: we let the user specify their own local neighborhood per node instead of using related networkx graph implementations   
	- the networkx implementation of small-world graphs assume ring topology; but instead we're interested in a grid in realistic scenarios
	- the networkx implementation of 2d grid graphs assumes no diagonal edges, whereas we'd like to have the ability to get neighbors from a (sub)set of the full neighborhood (of 8 nodes aside from boundary, corner or missing nodes)
	- since the user has likely already generated their lat/lon grid, we transfer the burden of neighborhood generation to them for now
	- we assume that the grid small-world network's non-local/long-range edges are wired for optimal decentralized efficiency, which coincides with most of the real-world small-world network examples
	- that is, the probability p((u,v)) of a an edge from node u to v is given by p(u,v) ~ d(u,v)^-2, where d(u,v) is the topological shortest path length (i.e. hop length) between u and v *on the grid*     
	'''
	def generate_graph(self):
		
		G=nx.Graph()
		G.position={}
		G.population={}
		G.name={}
		
		# add nodes 
		for node_id,properties in self.node_properties.iteritems():
			G.add_node(node_id)
			G.name[properties[3]] = node_id
			G.population[node_id] = properties[2]
			G.position[node_id]=(properties[0], properties[1]) # (x,y) for matplotlib
		
		
		# add provided local links
		nodes = G.nodes()
		if self.adjacency_list:
			for node_id, node_links in self.adjacency_list.iteritems():
				for node_link_id, w in node_links.iteritems():
					if node_id in nodes and node_link_id in nodes: # only add an edge between existing nodes  
						G.add_edge(int(node_id), int(node_link_id), weight = w)
		else:
			raise ValueError('SmallWorldGridGraphGenerator requires an adjacency list input!')
		
		print("Populated small world graph nodes and local edges.")
		
		# add long range links
		#calculate shortest hops paths and create an edge between two nodes w/ probability proportional to the inverse square of the distance between the two nodes
		shortest_path_lengths = nx.shortest_path_length(G, weight = 'weight').iteritems()
		for src_id, dst_records in shortest_path_lengths:
			for dst_id, dist in dst_records.iteritems():
				if dist > 0:
					if random.uniform(0,1) <= pow(dist, -2): # need to calculate normalization constant!
						G.add_edge(src_id, dst_id) 
		
		# go over isolated nodes and add edges to a random node; can be more realistic and add edges based on distance; but for now that should suffice to get a connected network
		# note that this does not create a fully connected network but a set of connected components with no isolated nodes 
		for iso_node in nx.isolates(G):
			G.add_edge(iso_node, nodes[int(len(nodes)*random.uniform(0,1))])
		
		print("Generated long links' connections.")
		
		self.graph = G
		
		return G
	
	
	def get_topo(self):
		return self.graph
	
	
	'''
	get shortest paths based on link weights
	'''
	def get_shortest_paths(self):
		return nx.shortest_path_length(self.graph, weight='weight')