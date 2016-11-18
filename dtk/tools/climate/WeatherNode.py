from dtk.tools.demographics.node import Node


class WeatherNode(Node):
    def __init__(self):
        self.air_temperature = []
        self.land_temperature = []
        self.rainfall = []
        self.humidity = []
        self.id = 0