import csv
import json
import re
from struct import pack
import os
import matplotlib.pyplot as plt
import networkx as nx

import dtk.tools.demographics.compiledemog as compiledemog
from dtk.tools.migration import createmigrationheader
from dtk.tools.migration.SmallWorldGridGraphGenerator import SmallWorldGridGraphGenerator
from . import visualize_routes
from . GeoGraphGenerator import GeoGraphGenerator
from . GravityModelRatesGenerator import GravityModelRatesGenerator


class MigrationGenerator(object):
    '''
    Generate migration headers and binary files for DTK input;

    In a follow up refactor perhaps we should go further and decouple from demographics file;
    only supply the input relevant for migration; currently done in process_input(self)
    '''

    def __init__(self, demographics_file_path, migration_network_file_path, graph_topo_type='geo-graph',
                 link_rates_model_type='gravity'):

        self.demographics_file_path = demographics_file_path
        self.migration_network_file_path = migration_network_file_path  # network structure provided in json adjacency list format or csv format

        self.adjacency_list = None  # migration adjacency list; supplied as an input file and compiled in the required format by process_input(self)

        self.node_properties = None  # node properties relevant for migration graph topology generation
        self.node_label_2_id = None  # node labels to dtk ids

        self.graph_topo_type = graph_topo_type

        self.link_rates_model_type = link_rates_model_type

        self.graph_topo = None
        self.link_rates = None

        # graph topology instance
        self.gt = None

        # link rates model instance
        self.lrm = None

        self.process_input()

    def set_graph_topo_type(self, graph_topo_type):
        self.graph_topo_type = graph_topo_type

    def set_link_rates_model_type(self, link_rates_model_type):
        self.link_rates_model_type = link_rates_model_type

    def set_link_rates(self, link_rates):

        # assume link rates provided with node labels;
        # convert node labels to node dtk ids 

        dtk_node_ids_link_rates = {}

        # this kind of node label to node id conversion occurs in process_input function
        # could refactor in a separate function 
        for src_node_label, dst_record in link_rates.items():
            if not src_node_label in self.node_label_2_id:
                continue

            src_node_id = self.node_label_2_id[src_node_label]

            dtk_node_ids_link_rates[src_node_id] = {}

            for dst_node_label, rate in dst_record.items():
                if not dst_node_label in self.node_label_2_id:
                    continue

                dst_node_id = self.node_label_2_id[dst_node_label]
                dtk_node_ids_link_rates[src_node_id][dst_node_id] = rate

        self.link_rates = dtk_node_ids_link_rates

    def process_input(self):

        '''
        output an adjacency list here given as  a dictionary with format;
        adj. list could be directed
        {
            node_label1: {
                            #key         # weight
                            node_label2: 0.5,
                            node_label4: 0.4,
                            node_label3: 0.4,
                            node_label5: 1,
                            ... 
                          },

            node_label2: {
                            #key         # weight
                            node_label1: 0.4,
                            node_label3: 0.4,
                            node_label10: 1,
                            ... 
                          },
            ...
        }
        '''

        # if migration file path is not provided, the migration adjacency list remains None;
        # that is fine for the geo-graph topo type (in which case edges are placed only to neighbors within a given radius
        if self.migration_network_file_path:
            with open(self.migration_network_file_path, 'r') as mig_f:

                if 'csv' in self.migration_network_file_path:

                    '''        
                    if input file is a csv adjacency matrix of the form

                    node_label 1,  2,  3,  4,  5
                        1     w11 w12  w13 w14 w15
                        2     w21       ...    
                        3     w31       ...
                        4     w41       ...
                        5     w51       ...

                    process to adjacency list in the format above
                    '''

                    reader = csv.DictReader(mig_f)

                    # assume a node is not connected to itself

                    for row in reader:
                        node = row['node_label']
                        self.adjacency_list[node] = {}
                        node_connections = row.keys()[1:]

                        # if graph is undirected; csv matrix should be symmetric and this should work
                        for node_connection in node_connections:
                            self.adjacency_list[node][node_connection] = row[node_connection]

                elif 'json' in self.migration_network_file_path:
                    '''
                    if input file is json, assume it contains the adjacency list in the required form above 
                    '''
                    self.adjacency_list = json.load(mig_f)

                    self.generate_node_properties()

                    # convert the adjacency list node labels to the corresponding dtk ids from the demographics file, so that the adjacency list can be consumed downstream (e.g. see class GeoGraphGenerator)
                    # note that nodes that are in the adjacency list but not in the demographics will be filtered out
                    adj_list_dtk_node_ids = {}
                    for src_node_label, dst_records in self.adjacency_list.items():
                        if not src_node_label in self.node_label_2_id:
                            continue
                        src_node_id = self.node_label_2_id[src_node_label]

                        adj_list_dtk_node_ids[src_node_id] = {}
                        for dst_node_label, w in dst_records.items():
                            if not dst_node_label in self.node_label_2_id:
                                continue
                            dst_node_id = self.node_label_2_id[dst_node_label]
                            adj_list_dtk_node_ids[src_node_id][dst_node_id] = w

                    self.adjacency_list = adj_list_dtk_node_ids

        else:  # do not construct adjacency matrix if the relevant input file is provided; still try to extract node properties from demographics
            self.generate_node_properties()

    def generate_node_properties(self):
        with open(self.demographics_file_path, 'r') as demo_f:
            demographics = json.load(demo_f)
            self.node_label_2_id = {}
            nodes = demographics['Nodes']
            self.node_properties = {}
            for node in nodes:
                node_attributes = node['NodeAttributes']

                self.node_properties[int(node['NodeID'])] = [float(node_attributes['Longitude']),
                                                             float(node_attributes['Latitude']),
                                                             int(node_attributes['InitialPopulation']),
                                                             node_attributes['FacilityName']]

                self.node_label_2_id[node_attributes['FacilityName']] = int(node['NodeID'])

    def generate_graph_topology(self):

        if self.graph_topo_type == 'geo-graph':
            # generate geo graph with default link radius (in km); neede to expose that as a user-defined parameter via spatial manager
            self.gt = GeoGraphGenerator(self.adjacency_list, self.node_properties, migration_radius=2)
        elif self.graph_topo_type == 'small-world-grid':
            self.gt = SmallWorldGridGraphGenerator(self.adjacency_list, self.node_properties)
        else:
            raise ValueError('Unsupported topology type!')

        if (self.gt):
            self.graph_topo = self.gt.generate_graph()  # assume all graphs types implement the generate_graph() method

    def get_topo(self):
        return self.gt.get_topo()  # assume all topologies implement get_topo() returning graph topology (networkx graph)

    def generate_link_rates(self):

        self.process_input()  # refactor so that gnereate_graph_topology and generate_link_rates call process_input only once

        if self.graph_topo_type == 'geo-graph':
            # generate geo graph with default link radius (in km)
            self.gt = GeoGraphGenerator(self.adjacency_list, self.node_properties, migration_radius=2)
            # print self.gt
        elif self.graph_topo_type == 'small-world-grid':
            self.gt = SmallWorldGridGraphGenerator(self.adjacency_list, self.node_properties)
        elif self.graph_topo_type == 'custom':
            pass
        else:
            raise ValueError('Unsupported topology type!')

        if (self.gt):
            self.graph_topo = self.gt.generate_graph()  # assume all graphs types implement the generate_graph() method

        if self.link_rates_model_type == 'gravity':
            # generate link rates following the graivty link rates model with default parameters

            print ("Preparing link rates generation config...")

            self.lrm = GravityModelRatesGenerator(
                self.gt.get_shortest_paths(),
                # assume all graph topologies implement the get_shortest_paths() method; enforce via interface? in Python??
                self.graph_topo,
                coeff=1e-4
            )

        elif self.link_rates_model_type == 'custom':
            pass

        else:
            raise ValueError('Unsupported link rates mode type!')

        print ("Link rates generation config completed.")

        if self.lrm:
            self.link_rates = self.lrm.generate_migration_links_rates()  # assume all link rates models implement generate_migration_links_re

    def save_migration_graph_topo_visualization(self, output_dir):
        graph = self.get_topo()

        pos = {}
        node_sizes = []
        max_marker = 400

        # following loops are not most efficient given networx graph data struct

        # find max pop
        max_pop = 0.0
        for i, node_id in enumerate(graph.nodes(data=False)):
            pop = graph.population[node_id]
            if pop > max_pop:
                max_pop = pop

        # calculate node sizes for figure
        for i, node_id in enumerate(graph.nodes(data=False)):
            pos[node_id] = graph.position[node_id]  # assume a graph topo has nodes positions and populations
            node_sizes.append(max_marker * graph.population[node_id] / max_pop)

        nx.draw_networkx(graph, pos, with_labels=False, node_size=node_sizes, alpha=0.75, node_color='blue')

        plt.savefig(os.path.join(output_dir, "migration_network_topo.png"), bbox_inches="tight")
        plt.close()

    '''
    save link rates to a human readable file;
    the txt file is consumable by link_rates_txt_2_bin(self) like function to generate DTK migration binary
    '''

    def save_link_rates_to_txt(self, rates_txt_file_path):
        with open(rates_txt_file_path, 'w') as fout:
            if not self.link_rates:
                raise ValueError(
                    'Link rates were not generated or provided! Please provide link rates or indicate link rates generation algorithm.')
            for src, v in self.link_rates.items():
                for dest, mig in v.items():
                    fout.write('%d %d %0.1g\n' % (int(src), int(dest), mig))

    '''
    convert a txt links rates file (e.g. as generated by save_link_rates_to_txt(self...)) to DTK binary migration file 
    '''

    @staticmethod
    def link_rates_txt_2_bin(rates_txt_file_path, rates_bin_file_path, route="local"):

        fopen = open(rates_txt_file_path)

        fout = open(rates_bin_file_path, 'wb')

        net = {}
        net_rate = {}

        MAX_DESTINATIONS_BY_ROUTE = {'local': 90,
                                     'regional': 90,
                                     'sea': 5,
                                     'air': 60}

        for line in fopen:
            s = line.strip().split()
            ID1 = int(float(s[0]))
            ID2 = int(float(s[1]))
            rate = float(s[2])
            # print(ID1,ID2,rate)
            if ID1 not in net:
                net[ID1] = []
                net_rate[ID1] = []
            net[ID1].append(ID2)
            net_rate[ID1].append(rate)

        for ID in sorted(net.keys()):

            ID_write = []
            ID_rate_write = []

            if len(net[ID]) > MAX_DESTINATIONS_BY_ROUTE[route]:
                print('There are %d destinations from ID=%d.  Trimming to %d (%s migration max) with largest rates.' % (
                len(net[ID]), ID, MAX_DESTINATIONS_BY_ROUTE[route], route))
                dest_rates = sorted(zip(net[ID], net_rate[ID]), key=lambda tup: tup[1], reverse=True)
                # dest_rates.sort(key=lambda tup: tup[1], reverse=True)
                trimmed_rates = dest_rates[:MAX_DESTINATIONS_BY_ROUTE[route]]
                # print(len(trimmed_rates))
                (net[ID], net_rate[ID]) = zip(*trimmed_rates)
                # print(net[ID], net_rate[ID])

            for i in iter(range(MAX_DESTINATIONS_BY_ROUTE[route])):
                ID_write.append(0)
                ID_rate_write.append(0)
            for i in iter(range(len(net[ID]))):
                ID_write[i] = net[ID][i]
                ID_rate_write[i] = net_rate[ID][i]
            s_write = pack('L' * len(ID_write), *ID_write)
            s_rate_write = pack('d' * len(ID_rate_write), *ID_rate_write)
            fout.write(s_write)
            fout.write(s_rate_write)

        fopen.close()
        fout.close()

    @staticmethod
    def save_migration_header(demographics_file_path, migration_file_name):

        # generate migration header for DTK consumption
        # todo: the script below needs to be refactored/rewritten
        # in its current form it requires compiled demographisc file (that's not the only problem with its design)
        # to compile the demographics file need to know about compiledemog file here, which is unnecessary
        # compiledemog.py too could be refactored towards object-orientedness
        # the demographics_file_path supplied here may be different from self.demographics_file_path)
        compiledemog.main(demographics_file_path)
        createmigrationheader.main('dtk-tools', re.sub('\.json$', '.compiled.json', demographics_file_path),
                                   migration_file_name, 'local')

    @staticmethod
    def save_migration_visualization(demographics_file_path, migration_header_binary_path, output_dir):
        # visualize nodes and migration routes and save the figure
        # todo: the script below needs to be refactored
        visualize_routes.main(demographics_file_path, migration_header_binary_path, output_dir)