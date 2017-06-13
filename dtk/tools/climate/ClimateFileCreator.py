import json
import os
import struct
import time
import logging
from collections import OrderedDict

import itertools

logger = logging.getLogger(__name__)
logging.basicConfig(filename='ClimateFileCreator_Log.log', level=logging.DEBUG)


class ClimateFileCreator:
    def __init__(self, nodes, prefix, suffix, original_data_years, idref="Gridded world grump2.5arcmin"):
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
        self.idReference = idref
        self.nodes = nodes
        self.prefix = prefix
        self.suffix = suffix
        self.original_data_years = original_data_years

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
        for data_set in ('air_temperature', 'land_temperature', 'humidity', 'rainfall'):
            data = OrderedDict()
            offset = 0
            offset_string = ""

            for node in self.nodes:
                key = tuple(getattr(node, data_set))

                if not key in data:
                    data[key] = offset
                    offset += len(key)*4

                offset_string = "%s%08x%08x" % (offset_string, node.id, data[key])

            if len(data) > 0:
                self.write_files(output_path, len(data.keys()[0]), offset_string, len(data), list(itertools.chain.from_iterable(data.keys())), data_set)

    def write_files(self, output_path, count, offset_string, available_nodes_count, data_to_save, data_name):
        dump = lambda content: json.dumps(content, sort_keys=True, indent=4).strip('"')
        metadata = {
            "Metadata": {
                "Author": "IDM",
                "DataProvenance": "",
                "DatavalueCount": count,
                "DateCreated": time.strftime("%m/%d/%Y"),
                "IdReference": self.idReference,
                "NodeCount": available_nodes_count,
                "NumberDTKNodes": len(self.nodes),
                "OriginalDataYears": self.original_data_years,
                "StartDayOfYear": "January 1",
                "Tool": "Dtk-tools",
                "UpdateResolution": "CLIMATE_UPDATE_DAY"
            },
            "NodeOffsets": offset_string
        }

        file_name = self.prefix + "_" + data_name + "_" + self.suffix
        bin_file_name = file_name + ".bin"
        json_file_name = file_name + ".bin.json"

        with open(os.path.join(output_path, '%s' % bin_file_name), 'wb') as handle:
            a = struct.pack('f' * len(data_to_save), *data_to_save)
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