from dtk.tools.climate.BinaryFilesHelpers import extract_data_from_climate_bin_for_node
from dtk.tools.demographics.Node import Node


class WeatherNode(Node):
    def __init__(self, lat=None, lon=None, pop=None, name=None, area=None, forced_id=None):
        Node.__init__(self, lat, lon, pop, name, area, forced_id)
        self.air_temperature = []
        self.land_temperature = []
        self.rainfall = []
        self.humidity = []

    def data_from_files(self, air_temperature=None, land_temperature=None, humidity=None, rainfall=None):
        if air_temperature:
            self.air_temperature = extract_data_from_climate_bin_for_node(self, air_temperature)

        if land_temperature:
            self.air_temperature = extract_data_from_climate_bin_for_node(self, land_temperature)

        if humidity:
            self.humidity = extract_data_from_climate_bin_for_node(self, humidity)

        if rainfall:
            self.rainfall = extract_data_from_climate_bin_for_node(self, rainfall)

