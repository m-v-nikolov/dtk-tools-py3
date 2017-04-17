import json
from struct import pack

from dtk.tools.climate.BaseInputFile import BaseInputFile


class MigrationFile(BaseInputFile):
    def __init__(self, idref, matrix):
        """
        Initialize a MigrationFile.
        :param idref: 
        :param matrix: The matrix needs to be of the format:
            {
               node_source1: {
                  node_destination_1: rate,
                  node_destination_2: rate
                }
            }
        """
        super(MigrationFile, self).__init__(idref)
        self.idref = idref
        self.matrix = matrix

    def generate_file(self, name):
        # Before generating, transform the matrix
        matrix_id = self.nodes_to_id()

        offset = 0
        offset_str = ""

        # Make sure we have the same destinations size everywhere
        # First find the max size
        max_size = max([len(dest) for dest in matrix_id.values()])

        # Add a fake node destinations in nodes to make sure the destinations are all same size
        for source, dests in self.matrix.iteritems():
            self.get_filler_nodes(source, dests, max_size, matrix_id.keys())

        with open(name, 'wb') as migration_file:
            for nodeid, destinations in matrix_id.iteritems():
                destinations_id = pack('I' * len(destinations.keys()), *destinations.keys())
                destinations_rate = pack('d' * len(destinations.values()), *destinations.values())

                # Write
                migration_file.write(destinations_id)
                migration_file.write(destinations_rate)

                # Write offset
                offset_str = "%s%s%s" % (offset_str, "{0:08x}".format(nodeid), "{0:08x}".format(offset))

                # Increment offset
                offset += 12 * len(destinations)

        # Write the headers
        meta = self.generate_headers({"NodeCount": len(matrix_id), "DatavalueCount": len(matrix_id.itervalues().next()) })
        headers = {
            "Metadata": meta,
            "NodeOffsets": offset_str
        }
        json.dump(headers, open("%s.json" % name, 'wb'), indent=3)

    def get_filler_nodes(self, source, dests, n, available_nodes):
        """
        Fills the destinations with n filler nodes.
        Makes sure the nodes ids chosen are not the source, not the destinations and come from the available_nodes
        """
        while len(dests) < n:
            for node in available_nodes:
                if node not in dests and node != source:
                    dests[node] = 0

    def nodes_to_id(self):
        """
        Transform the matrix of {node:{destination:rate}} into {node.id: {dest.id:rate}}
        :return: 
        """
        return {
            node.id:{
                dest.id:v for dest, v in dests.iteritems()
            } for node, dests in self.matrix.iteritems()
        }

