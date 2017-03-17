from dtk.tools.demographics.node import Node


class WeatherNode(Node):
    def __init__(self, lat=None, lon=None, pop=None, name=None, area=None, forced_id=None, ):
        Node.__init__(self, lat, lon, pop, name, area, forced_id)
        self.air_temperature = []
        self.land_temperature = []
        self.rainfall = []
        self.humidity = []
