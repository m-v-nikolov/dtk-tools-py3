import json
import math

def get_node_id(lat, lon, res_in_degrees = 2.5/60):
    xpix = int(math.floor((lon + 180.0) / res_in_degrees))
    ypix = int(math.floor((lat + 90.0) / res_in_degrees))
    nodeid = (xpix << 16) + ypix + 1
    return nodeid

class Node:

    default_density=200   # people/km^2
    res_in_degrees=2.5/60 # 2.5 arcmin

    def __init__(self, lat, lon, pop, name='', area=None):
        self.name=name
        self.lat=lat
        self.lon=lon
        self.pop=pop
        if area:
            self.density=pop/area
        else:
            self.density=self.default_density

    def __str__(self):
        return '%s: (%0.3f,%0.2f), pop=%s, per km^2=%d' % (self.name, self.lat, self.lon, "{:,}".format(self.pop), self.density)

    def toDict(self):
        d={ 'Latitude':self.lat,
            'Longitude':self.lon,
            'InitialPopulation':self.pop }
        if self.name:
            d.update({'Name':self.name})
        return d

    def toTuple(self):
        return self.lat,self.lon,self.pop

    @property
    def id(self):
        return get_node_id(self.lat,self.lon,self.res_in_degrees)

def nodes_for_DTK(filename,nodes):
    with open(filename,'w') as f:
        json.dump({'Nodes':[{'NodeID':n.id,
                             'NodeAttributes':n.toDict()} for n in nodes]},f,indent=4)