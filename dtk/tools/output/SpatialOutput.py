import struct

import numpy as np


class SpatialOutput:

    def __init__(self):
        self.n_nodes = 0
        self.n_tstep = 0
        self.nodeids = []
        self.data = None

    @classmethod
    def from_bytes(cls, bytes):
        so = cls()

        so.n_nodes, = struct.unpack('i', bytes[0:4])
        so.n_tstep, = struct.unpack('i', bytes[4:8])
        # print( "There are %d nodes and %d time steps" % (n_nodes, n_tstep) )

        so.nodeids = struct.unpack(str(so.n_nodes) + 'I', bytes[8:8 + so.n_nodes * 4])
        so.nodeids = np.asarray(so.nodeids)

        so.data = struct.unpack(str(so.n_nodes * so.n_tstep) + 'f',
                                bytes[8 + so.n_nodes * 4:8 + so.n_nodes * 4 + so.n_nodes * so.n_tstep * 4])
        so.data = np.asarray(so.data)
        so.data = so.data.reshape(so.n_tstep, so.n_nodes)

        return so

    def to_dict(self):
        return {'n_nodes': self.n_nodes,
                'n_tstep': self.n_tstep,
                'nodeids': self.nodeids,
                'data': self.data}

