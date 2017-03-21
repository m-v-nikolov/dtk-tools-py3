import json
import struct
from collections import OrderedDict


def extract_data_from_climate_bin_for_node(node, binary_file):
    """
    This function returns the data for a particular node in the provided binary_file.
    Works for climate binaries
    """
    meta = json.load(open(binary_file+'.json','rb'))
    tsteps = meta['Metadata']['DatavalueCount']
    offsets = meta['NodeOffsets']
    offsets_nodes = OrderedDict()
    i=0
    while i <len(offsets):
        nodeid = int(offsets[i:i+8],16)
        offset = int(offsets[i+9:i+16], 16)
        offsets_nodes[nodeid] = offset
        i+=16

    series = []
    with open(binary_file, 'rb') as bin_file:
        bin_file.seek(offsets_nodes[node.id])

        # Read the data
        for i in range(tsteps):
            series.append(struct.unpack('f', bin_file.read(4))[0])
    return series