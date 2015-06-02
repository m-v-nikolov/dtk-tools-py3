import json
import math

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
        return nodeid_from_lat_lon(self.lat,self.lon,self.res_in_degrees)

    @classmethod
    def init_resolution_from_file(cls, fn):
        if '30arcsec' in fn:
            cls.res_in_degrees = 30/3600.
        elif '2_5arcmin' in fn:
            cls.res_in_degrees = 2.5/30
        else:
            raise Exception("Don't recognize resolution from demographics filename")

def get_xpix_ypix(nodeid):
    ypix = (nodeid-1) & 2**16-1
    xpix = (nodeid-1) >> 16
    return (xpix,ypix)

def lat_lon_from_nodeid(nodeid, res_in_deg=Node.res_in_degrees):
    xpix,ypix = get_xpix_ypix(nodeid)
    lat = (0.5+ypix)*res_in_deg - 90.0
    lon = (0.5+xpix)*res_in_deg - 180.0
    return (lat,lon)

def xpix_ypix_from_lat_lon(lat, lon, res_in_deg=Node.res_in_degrees):
    xpix = int(math.floor((lon + 180.0) / res_in_deg))
    ypix = int(math.floor((lat + 90.0) / res_in_deg))
    return xpix,ypix

def nodeid_from_lat_lon(lat, lon, res_in_deg=Node.res_in_degrees):
    xpix,ypix=xpix_ypix_from_lat_lon(lat, lon, res_in_deg)
    nodeid = (xpix << 16) + ypix + 1
    return nodeid

def nodes_for_DTK(filename,nodes):
    with open(filename,'w') as f:
        json.dump({'Nodes':[{'NodeID':n.id,
                             'NodeAttributes':n.toDict()} for n in nodes]}, f, indent=4)
