import csv
import json
import re
from struct import pack

import createmigrationheader
import dtk.tools.demographics.compiledemog as compiledemog
import visualize_routes
from GeoGraphGenerator import GeoGraphGenerator
from GravityModelRatesGenerator import GravityModelRatesGenerator


class MigrationGenerator:
    """
    Generate migration headers and binary files for DTK input;

    In a follow up refactor perhaps we should go further and decouple from demographics file;
    only supply the input relevant for migration; currently done in process_input(self)
    """

    def __init__(self, demographics_file_path, migration_network_file_path, graph_topo_type='rhumba',
                 link_rates_model_type='tango'):

        self.demographics_file_path = demographics_file_path
        self.migration_network_file_path = migration_network_file_path  # network structure provided in json adjacency list format or csv format

        self.adjacency_list = None  # migration adjacency list; supplied as an input file and compiled in the required format by process_input(self)

        self.node_properties = None  # node properties relevant for migration graph topology generation

        self.graph_topo_type = graph_topo_type

        self.link_rates_model_type = link_rates_model_type

        self.graph_topo = None
        self.link_rates = None

        # graph topology instance
        self.gt = None

        # link rates model instance
        self.lrm = None

    def set_graph_topo_type(self, graph_topo_type):
        self.graph_topo_type = graph_topo_type

    def set_link_rates_model_type(self, link_rates_model_type):
        self.link_rates_model_type = link_rates_model_type

    def process_input(self):
        """
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
        """

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

            with open(self.demographics_file_path, 'r') as demo_f:
                demographics = json.load(demo_f)
                node_label_2_id = {}
                nodes = demographics['Nodes']
                self.node_properties = {}
                for node in nodes:
                    node_attributes = node['NodeAttributes']
                    self.node_properties[int(node['NodeID'])] = [float(node_attributes['Longitude']),
                                                                 float(node_attributes['Latitude']),
                                                                 int(node_attributes['InitialPopulation']),
                                                                 node_attributes['FacilityName']]
                    node_label_2_id[node_attributes['FacilityName']] = int(node['NodeID'])

                # convert the adjacency list node labels to the corresponding dtk ids from the demographics file, so that the adjacency list can be consumed downstream (e.g. see class GeoGraphGenerator)
                adjacency_list_node_ids = {}
                for node_label, node_links in self.adjacency_list.iteritems():
                    adjacency_list_node_ids[node_label_2_id[node_label]] = {}
                    for node_link_label, w in node_links.iteritems():
                        adjacency_list_node_ids[node_label_2_id[node_label]] = {node_label_2_id[node_link_label]: w}

                self.adjacency_list = adjacency_list_node_ids

    def generate_graph_topology(self):

        self.process_input()

        if self.graph_topo_type == 'geo-graph':
            # generate geo graph with default link radius (in km)
            self.gt = GeoGraphGenerator(self.adjacency_list, self.node_properties, migration_radius=8.5)
        else:
            raise ValueError('Unsupported topology type!')

        if (self.gt):
            self.graph_topo = self.gt.generate_graph()  # assume all graphs types implement the generate_graph() method

    def generate_link_rates(self):

        self.process_input()  # refactor so that gnereate_graph_topology and generate_link_rates call process_input only once

        if self.graph_topo_type == 'geo-graph':
            # generate geo graph with default link radius (in km)
            self.gt = GeoGraphGenerator(self.adjacency_list, self.node_properties, migration_radius=8.5)
            print self.gt
        else:
            raise ValueError('Unsupported topology type!')

        if (self.gt):
            self.graph_topo = self.gt.generate_graph()  # assume all graphs types implement the generate_graph() method

        if self.link_rates_model_type == 'gravity':
            # generate link rates following the graivty link rates model with default parameters
            self.lrm = GravityModelRatesGenerator(
                self.gt.get_shortest_paths(),  # assume all graph topologies implement the get_shortest_paths() method
                self.graph_topo,
                coeff=1e-4
            )
        else:
            raise ValueError('Unsupported link rates mode type!')

        if self.lrm:
            self.link_rates = self.lrm.generate_migration_links_rates()  # assume all link rates models implement generate_migration_links_re

    '''
    save link rates to a human readable file;
    the txt file is consumable by link_rates_txt_2_bin(self) like function to generate DTK migration binary
    '''

    def save_link_rates_to_txt(self, rates_txt_file_path):
        with open(rates_txt_file_path, 'w') as fout:
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

        MAX_DESTINATIONS_BY_ROUTE = {'local': 8,
                                     'regional': 30,
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
                dest_rates = zip(net[ID], net_rate[ID])
                dest_rates.sort(key=lambda tup: tup[1], reverse=True)
                trimmed_rates = dest_rates[:MAX_DESTINATIONS_BY_ROUTE[route]]
                # print(len(trimmed_rates))
                (net[ID], net_rate[ID]) = zip(*trimmed_rates)
                # print(net[ID], net_rate[ID])

            for i in xrange(MAX_DESTINATIONS_BY_ROUTE[route]):
                ID_write.append(0)
                ID_rate_write.append(0)
            for i in xrange(len(net[ID])):
                ID_write[i] = net[ID][i]
                ID_rate_write[i] = net_rate[ID][i]
            s_write = pack('L' * len(ID_write), *ID_write)
            s_rate_write = pack('d' * len(ID_rate_write), *ID_rate_write)
            fout.write(s_write)
            fout.write(s_rate_write)

        fopen.close()
        fout.close()

    @staticmethod
    def save_migration_header(demographics_file_path):

        # generate migration header for DTK consumption
        # todo: the script below needs to be refactored/rewritten
        # in its current form it requires compiled demographisc file (that's not the only problem with its design)
        # to compile the demographics file need to know about compiledemog file here, which is unnecessary
        # compiledemog.py too could be refactored towards object-orientedness
        # the demographics_file_path supplied here may be different from self.demographics_file_path)
        compiledemog.main(demographics_file_path)
        createmigrationheader.main('dtk-tools', re.sub('\.json$', '.compiled.json', demographics_file_path), 'local')

    @staticmethod
    def save_migration_visualization(demographics_file_path, migration_header_binary_path, output_dir):
        # visualize nodes and migration routes and save the figure
        # todo: the script below needs to be refactored

        visualize_routes.main(demographics_file_path, migration_header_binary_path, output_dir)
