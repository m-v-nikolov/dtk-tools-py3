import json
import math


class Node:
    default_density = 200  # people/km^2
    default_population = 1000
    res_in_degrees = 2.5 / 60

    def __init__(self, lat, lon, pop, name='', area=None, forced_id=None, extra_attributes={}):
        """
        Represent a Node
        :param lat: Latitude
        :param lon: Longitude
        :param pop: Population
        :param name:  Facility name
        :param area:  Area
        :param forced_id: Do we want a custom id instead of the normal ID based on lat/lon?
        :param extra_attributes: Extra node attributes
        """
        self.name = name
        self.lat = lat
        self.lon = lon
        self.pop = pop
        self.forced_id = forced_id
        self.extra_attributes = extra_attributes

        if area:
            self.density = pop / area
        else:
            self.density = self.default_density

    def __repr__(self):
        return '%s: (%0.3f,%0.2f), pop=%s, per km^2=%d' % (
        self.name, self.lat, self.lon, "{:,}".format(self.pop), self.density)

    def to_dict(self):
        d = {'Latitude': float(self.lat),
             'Longitude': float(self.lon),
             'InitialPopulation': int(self.pop)}
        if self.name:
            d.update({'FacilityName': self.name})

        d.update(self.extra_attributes)
        return d

    def to_tuple(self):
        return self.lat, self.lon, self.pop

    @property
    def id(self):
        return self.forced_id if self.forced_id is not None else nodeid_from_lat_lon(self.lat, self.lon, self.res_in_degrees)

    @classmethod
    def init_resolution_from_file(cls, fn):
        if '30arcsec' in fn:
            cls.res_in_degrees = 30 / 3600.
        elif '2_5arcmin' in fn:
            cls.res_in_degrees = 2.5 / 30
        else:
            raise Exception("Don't recognize resolution from demographics filename")

    @classmethod
    def from_data(cls, data):
        """
        Function used to create the node object from data (most likely coming from a demographics file)
        :param data: 
        :return: 
        """
        nodeid = data['NodeID']
        attributes = data['NodeAttributes']
        latitude = attributes.pop('Latitude')
        longitude = attributes.pop('Longitude')
        population = attributes.pop('InitialPopulation', Node.default_population)
        name = attributes.pop('FacilityName', nodeid)

        # Create the node
        return Node(lat=latitude, lon=longitude,
                    pop=population, name=name, extra_attributes=attributes, forced_id=nodeid)


def get_xpix_ypix(nodeid):
    ypix = (nodeid - 1) & 2 ** 16 - 1
    xpix = (nodeid - 1) >> 16
    return (xpix, ypix)


def lat_lon_from_nodeid(nodeid, res_in_deg=Node.res_in_degrees):
    xpix, ypix = get_xpix_ypix(nodeid)
    lat = (0.5 + ypix) * res_in_deg - 90.0
    lon = (0.5 + xpix) * res_in_deg - 180.0
    return (lat, lon)


def xpix_ypix_from_lat_lon(lat, lon, res_in_deg=Node.res_in_degrees):
    xpix = int(math.floor((lon + 180.0) / res_in_deg))
    ypix = int(math.floor((lat + 90.0) / res_in_deg))
    return xpix, ypix


def nodeid_from_lat_lon(lat, lon, res_in_deg=Node.res_in_degrees):
    xpix, ypix = xpix_ypix_from_lat_lon(lat, lon, res_in_deg)
    nodeid = (xpix << 16) + ypix + 1
    return nodeid


def nodes_for_DTK(filename, nodes):
    with open(filename, 'w') as f:
        json.dump({'Nodes': [{'NodeID': n.id,
                              'NodeAttributes': n.to_dict()} for n in nodes]}, f, indent=4)
