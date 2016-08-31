import json
import os
import struct
import time
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='ClimateFileCreator_Log.log', level=logging.DEBUG)

class ClimateFileCreator:
    def __init__(self, nodes, prefix, suffix, original_data_years, is_slim=False):
        """
        :param nodes: format -
            node1 = WeatherNode()
            node1.id = 340461479
            node1.rainfall = [1,2,3,4,5]
            node1.temperature = [1,2,3,4,5]
            node1.land_temperature = [1,2,-3,3,4,5]
            node1.humidity = [1,2,-79,3,4,5]

            node2 = WeatherNode()
            node2.id = 12353654
            node2.rainfall = [1,2,3,4,5]
            node2.temperature = [1,2,3,4,5]
            node2.land_temperature = [1,2,5,3,4,5]
            node2.humidity = [1,2,-56,3,4,5]

            nodes = [node1, node2]
        """
        self.nodes = nodes
        self.prefix = prefix
        self.suffix = suffix
        self.original_data_years = original_data_years
        self.is_slim = is_slim

    def prepare_rainfall(self, invalid_handler=None, test_function=None):
        if not invalid_handler:
            invalid_handler = self.invalid_rainfall_handler
        if not test_function:
            test_function = self.valid_rainfall
        for i, node in enumerate(self.nodes):
            self.nodes[i].rainfall = self.prepare_data(node.rainfall, invalid_handler, test_function)

    def prepare_air_temperature(self, invalid_handler=None, test_function=None):
        if not invalid_handler:
            invalid_handler = self.invalid_air_temperature_handler
        if not test_function:
            test_function = self.valid_air_temperature

        for i, node in enumerate(self.nodes):
            self.nodes[i].air_temperature = self.prepare_data(node.air_temperature, invalid_handler, test_function)

    def prepare_land_temperature(self, invalid_handler=None, test_function=None):
        if not invalid_handler:
            invalid_handler = self.invalid_land_temperature_handler
        if not test_function:
            test_function = self.valid_land_temperature

        for i, node in enumerate(self.nodes):
            self.nodes[i].land_temperature = self.prepare_data(node.land_temperature, invalid_handler, test_function)

    def prepare_humidity(self, invalid_handler=None, test_function=None):
        if not invalid_handler:
            invalid_handler = self.invalid_humidity_handler
        if not test_function:
            test_function = self.valid_humidity

        for i, node in enumerate(self.nodes):
            self.nodes[i].humidity = self.prepare_data(node.humidity, invalid_handler, test_function)

    # Format climate data
    @staticmethod
    def prepare_data(data, invalid_handler=None, test_function=None):
        ret = []
        # Make sure all data is correct
        for i in range(len(data)):
            data_day = data[i]
            if test_function(data_day):
                # The weather value is correct
                ret.append(data_day)
            else:
                clean_value = invalid_handler(data_day, i, data)
                logger.warning("Bad value: %s, replaced by %s at index %s" % (data_day, clean_value, i), exc_info=1)
                ret.append(clean_value)

        return ret

    def generate_climate_files(self, output_path):
        node_offset, offset_string = 0, ""
        rainfall_count, air_temperature_count, land_temperature_count, humidity_count = 0, 0, 0, 0
        rainfall_data, air_temperature_data, land_temperature_data, humidity_data = [], [], [], []
        rainfall_dict, land_temperature_dict, air_temperature_dict, humidity_dict = {}, {}, {}, {}
        rainfall_node_offset, air_temperature_node_offset, land_temperature_node_offset, humidity_node_offset = 0, 0, 0, 0
        rainfall_offset_string, air_temperature_offset_string, land_temperature_offset_string, humidity_offset_string = "", "", "", ""

        for node in self.nodes:
            if self.is_slim:
                if len(node.rainfall) > 0:
                    if rainfall_count == 0:
                        rainfall_count = len(node.rainfall)

                    key = str(node.rainfall)
                    if key in rainfall_dict:
                        rainfall_offset_string = "%s%08x%08x" % (rainfall_offset_string, node.id, rainfall_dict[key])

                    else:
                        rainfall_data.extend(node.rainfall)
                        rainfall_offset_string = "%s%08x%08x" % (rainfall_offset_string, node.id, rainfall_node_offset)
                        rainfall_dict[key] = rainfall_node_offset
                        rainfall_node_offset = len(rainfall_data) * 4

                if len(node.air_temperature) > 0:
                    if air_temperature_count == 0:
                        air_temperature_count = len(node.air_temperature)

                    key = str(node.air_temperature)
                    if key in air_temperature_dict:
                        air_temperature_offset_string = "%s%08x%08x" % (air_temperature_offset_string, node.id,
                                                                        air_temperature_dict[key])
                    else:
                        air_temperature_data.extend(node.air_temperature)
                        air_temperature_offset_string = "%s%08x%08x" % (air_temperature_offset_string, node.id,
                                                                        air_temperature_node_offset)
                        air_temperature_dict[key] = air_temperature_node_offset
                        air_temperature_node_offset = len(air_temperature_data) * 4

                if len(node.land_temperature) > 0:
                    if land_temperature_count == 0:
                        land_temperature_count = len(node.land_temperature)

                    key = str(node.land_temperature)
                    if key in land_temperature_dict:
                        land_temperature_offset_string = "%s%08x%08x" % (land_temperature_offset_string, node.id,
                                                                         land_temperature_dict[key])
                    else:
                        land_temperature_data.extend(node.land_temperature)
                        land_temperature_offset_string = "%s%08x%08x" % (land_temperature_offset_string, node.id,
                                                                         land_temperature_node_offset)
                        land_temperature_dict[key] = land_temperature_node_offset
                        land_temperature_node_offset = land_temperature_count * 4

                if len(node.humidity) > 0:
                    if humidity_count == 0:
                        humidity_count = len(node.humidity)

                    key = str(node.humidity)
                    if key in humidity_dict:
                        humidity_offset_string = "%s%08x%08x" % (humidity_offset_string, node.id, humidity_dict[key])

                    else:
                        humidity_data.extend(node.humidity)
                        humidity_offset_string = "%s%08x%08x" % (humidity_offset_string, node.id, humidity_node_offset)
                        humidity_dict[key] = humidity_node_offset
                        humidity_node_offset = humidity_count * 4

            else:
                if len(node.rainfall) > 0:
                    if rainfall_count == 0:
                        rainfall_count = len(node.rainfall)
                    rainfall_data.extend(node.rainfall)

                if len(node.air_temperature) > 0:
                    if air_temperature_count == 0:
                        air_temperature_count = len(node.air_temperature)
                    air_temperature_data.extend(node.air_temperature)

                if len(node.land_temperature) > 0:
                    if land_temperature_count == 0:
                        land_temperature_count = len(node.land_temperature)
                    land_temperature_data.extend(node.land_temperature)

                if len(node.humidity) > 0:
                    if humidity_count == 0:
                        humidity_count = len(node.humidity)
                    humidity_data.extend(node.humidity)

                offset_string = "%s%08x%08x" % (offset_string, node.id, node_offset)

                if rainfall_count > 0:
                    node_offset = len(rainfall_data) * 4

                elif air_temperature_count > 0:
                    node_offset = len(air_temperature_data) * 4

                elif land_temperature_count > 0:
                    node_offset = len(land_temperature_data) * 4

                elif humidity_count > 0:
                    node_offset = len(humidity_data) * 4

        # Generate bin and json files
        if len(rainfall_data) > 0:
            self.write_files(output_path, rainfall_count, offset_string, rainfall_data, "rainfall")

        if len(air_temperature_data) > 0:
            self.write_files(output_path, air_temperature_count, offset_string, air_temperature_data, "air_temperature")

        if len(land_temperature_data) > 0:
            self.write_files(output_path, land_temperature_count, offset_string, land_temperature_data, "land_temperature")

        if len(humidity_data) > 0:
            self.write_files(output_path, humidity_count, offset_string, humidity_data, "humidity")

    def write_files(self, output_path, count, offset_string, data_to_save, data_name):
        dump = lambda content: json.dumps(content, sort_keys=True, indent=4).strip('"')
        metadata = {
            "Metadata": {
                "Author": "IDM",
                "DataProvenance": "",
                "DatavalueCount": count,
                "DateCreated": time.strftime("%m/%d/%Y"),
                "IdReference": "Gridded world grump2.5arcmin",
                "NodeCount": len(self.nodes),
                "OriginalDataYears": self.original_data_years,
                "StartDayOfYear": "January 1",
                "Tool": "Dtk-tools",
                "UpdateResolution": "CLIMATE_UPDATE_DAY"
            },
            "NodeOffsets": offset_string
        }

        file_name = self.prefix + "_" + data_name + "_" + self.suffix
        bin_file_name = file_name + ".bin"
        json_file_name = file_name + ".json"
        with open(os.path.join(output_path, '%s' % bin_file_name), 'wb') as handle:
            a = struct.pack('f' * count, *data_to_save)
            # Write it to the file
            handle.write(a)

        with open(os.path.join(output_path, '%s' % json_file_name), 'w') as f:
            f.write(dump(metadata))

    @staticmethod
    def invalid_rainfall_handler(current_value, index, data):
        return 0

    @staticmethod
    def valid_rainfall(current_value):
        return 0 <= current_value < 2493

    @staticmethod
    def invalid_air_temperature_handler(current_value, index, data):
        return 0

    @staticmethod
    def valid_air_temperature(current_value):
        return -89.2 <= current_value < 56.7

    @staticmethod
    def invalid_land_temperature_handler(current_value, index, data):
        return 0

    @staticmethod
    def valid_land_temperature(current_value):
        return -89.2 <= current_value < 56.77

    @staticmethod
    def invalid_humidity_handler(current_value, index, data):
        return 0

    @staticmethod
    def valid_humidity(current_value):
        return 0 <= current_value <= 100
