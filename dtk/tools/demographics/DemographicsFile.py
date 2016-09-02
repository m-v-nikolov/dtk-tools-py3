import json


class DemographicsFile:

    def __init__(self, nodes, idref="Gridded world grump2.5arcmin"):
        self.nodes = nodes
        self.idref = idref


    def generate_file(self, name):
        content = {
            "Metadata": {
                "DateCreated": "7/26",
                "Tool": "dtk-tools",
                "Author": "braybaud",
                "IdReference": self.idref,
                "NodeCount": 1
            },
            "Nodes": [
            ],
            "Defaults": {
            }
        }

        content['Defaults']['NodeAttributes'] = {
            "Airport": 0,
            "Region": 0,
            "Seaport": 0,
            "AbovePoverty": 1,
            "Urban": 0,
            "Altitude": 0
        }

        content['Defaults']['IndividualAttributes'] = {
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

        for node in self.nodes:
            content['Nodes'].append({
                'NodeID': node.id,
                'NodeAttributes': node.toDict()
            })

        # Update node count
        content['Metadata']['NodeCount'] = len(self.nodes)
        with open(name, 'wb') as output:
            json.dump(content, output, indent=3)

        self.content = content
