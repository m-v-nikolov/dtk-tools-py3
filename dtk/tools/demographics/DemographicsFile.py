import json

from dtk.tools.climate.BaseInputFile import BaseInputFile
from dtk.tools.demographics.Node import Node


class DemographicsFile(BaseInputFile):

    @classmethod
    def from_file(cls, base_file):
        content = json.load(open(base_file, 'rb'))
        nodes = []

        # Load the nodes
        for node in content["Nodes"]:
            nodes.append(Node.from_data(node))

        # Load the idref
        idref = content['Metadata']['IdReference']

        # Create the file
        return cls(nodes, idref, base_file)

    def __init__(self, nodes, idref="Gridded world grump2.5arcmin", base_file=None):
        super(DemographicsFile, self).__init__(idref)
        self.nodes = {node.name: node for node in nodes}
        self.idref = idref
        self.content = None

        if base_file:
            self.content = json.load(open(base_file,'rb'))
        else:
            meta = self.generate_headers()
            self.content = {
                "Metadata": meta,
                "Defaults": {
                }
            }

            self.content['Defaults']['NodeAttributes'] = {
                "Airport": 0,
                "Region": 0,
                "Seaport": 0,
                "AbovePoverty": 1,
                "Urban": 0,
                "Altitude": 0
            }

            self.content['Defaults']['IndividualAttributes'] = {
                # Uniform prevalence between .1 and .3
                "PrevalenceDistributionFlag": 1,
                "PrevalenceDistribution1": 0.1,
                "PrevalenceDistribution2": 0.3,

                "ImmunityDistributionFlag": 0,
                "ImmunityDistribution1": 1,
                "ImmunityDistribution2": 0,

                "RiskDistributionFlag": 0,
                "RiskDistribution1": 1,
                "RiskDistribution2": 0,

                "AgeDistributionFlag": 1,
                "AgeDistribution1": 0,
                "AgeDistribution2": 18250
            }

    def generate_file(self, name):
        self.content['Nodes'] = []

        for node in self.nodes.values():
            self.content['Nodes'].append({
                'NodeID': node.id,
                'NodeAttributes': node.to_dict()
            })

        # Update node count
        self.content['Metadata']['NodeCount'] = len(self.nodes)
        with open(name, 'w') as output:
            json.dump(self.content, output, indent=3)

    @property
    def node_ids(self):
        return [node['NodeID'] for node in self.nodes]

    @property
    def node_count(self):
        return len(self.nodes)

    def get_node(self, nodeid):
        """
        Return the node idendified by nodeid. Search either name or actual id
        :param nodeid: 
        :return: 
        """
        if nodeid in self.nodes: return self.nodes[nodeid]
        for node in self.nodes.values():
            if node.name == nodeid: return node
        raise ValueError("No nodes available with the id: %s. Available nodes (%s)" % (nodeid, ", ".join(self.nodes.keys())))
