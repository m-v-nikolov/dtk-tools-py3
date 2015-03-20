class Node:

    default_density=200 # people/km^2

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