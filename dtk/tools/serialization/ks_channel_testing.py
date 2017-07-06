import json
import os.path as path
from scipy import stats

debug=True
CHANNELS_KEY = "Channels"
DATA_KEY = "Data"
REFERENCE_CHART_KEY = "reference"
TEST_CHART_KEY = "test"

def ping():
    """
    Method to validate that this script has been imported and is accessible
    """
    print "file {0} is here!".format(__name__)

def hardcoded():
    """
    This is the script that served as a template for the code.
    Not supported.
    """
    first_report_filename="InsetChart.json"
    second_report_name="combined_insetchart.json"

    first_report_name = path.join("output",first_report_filename)
    chart_1 = None
    with open(first_report_name) as infile:
        chart_1 = json.load(infile)
    with open(second_report_name) as infile:
        chart_2 = json.load(infile)

    if debug:
        print "chart_1 keys: " + str(chart_1.keys())
        print "chart_2 keys: " + str(chart_2.keys())

    INFECTIONS_CHANNEL = "Cumulative Infections"

    cum_infections_1 = chart_1[CHANNELS_KEY][INFECTIONS_CHANNEL]["Data"]
    cum_infections_2 = chart_2[CHANNELS_KEY][INFECTIONS_CHANNEL]["Data"]

    print "cum_infections_1 sum: {0}".format(sum(cum_infections_1))
    print "cum_infections_2 sum: {0}".format(sum(cum_infections_2))

    stat, p_val = stats.ks_2samp(cum_infections_1, cum_infections_2)

    print "stat: {0}".format(stat)
    print "p_val: {0}".format(p_val)

class KsChannelTester:
    def __init__(self, ref_path, test_path, channel_list):
        """
        Creates the object and populates all of the channels to be tested

        :param ref_path: full path to reference chart, i.e., ./output/InsetChart.json
        :param test_path: full path to test chart, i.e., C:/test_output/combined_inset.json
        :param channel_list: array of channel names, i.e., ["New Infections","Births","Infected"]
        """
        self.channel_list = channel_list
        self.data = {}
        self.populate_data(ref_path, channel_list, REFERENCE_CHART_KEY)
        self.populate_data(test_path, channel_list, TEST_CHART_KEY)

    def populate_data(self, file_path, channel_list, key_name):
        with open (file_path) as infile:
            channel_data = json.load(infile)[CHANNELS_KEY]
        self.data[key_name] = {}
        ref_keys = channel_data.keys()
        for channel in self.channel_list:
            if channel not in ref_keys:
                raise ValueError("Channel {0} not found in ref data keys {1}\n".format(channel, ref_keys))
            else:
                self.data[key_name][channel] = channel_data[channel]

    def test_channel(self, channel_name, key_1=REFERENCE_CHART_KEY, key_2=TEST_CHART_KEY):
        """
        Runs a Kolmogorov Smirnov test of the channel in question. Uses scipy.stats
        https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.stats.kstest.html

        :param channel_name: Channel to be tested, i.e., "New Infections"
        :param key_1: key for reference data ("reference")
        :param key_2: key for data under test ("test")
        :return: ks_statistic, p_value
        """
        data_keys = self.data.keys()
        if not (key_1 in data_keys and key_2 in data_keys):
            raise KeyError("Keys {0} and {1} were not both populated in {2}.\n".format(
                key_1, key_2, data_keys
            ))
        channel_1 = self.data[key_1][channel_name][DATA_KEY]
        channel_2 = self.data[key_2][channel_name][DATA_KEY]
        stat, p_val = stats.ks_2samp(channel_1, channel_2)
        return stat, p_val
