import os
import json
from collections import OrderedDict
import unittest

from calibtool.analyzers.Helpers import json_to_pandas


class TestCalibHelpers(unittest.TestCase):

    def setUp(self):
        with open(os.path.join('input', 'test_malaria_summary_report.json'), 'r') as json_file:
            data = json.load(json_file)
            md = data['Metadata']

        self.channel = 'PfPR by Parasitemia and Age Bin'

        self.bins = OrderedDict([('Time', data['DataByTime']['Time Of Report']),
                                 ('Age Bins', md['Age Bins']),
                                 ('PfPR bins', md['Parasitemia Bins'])])

        grouping = 'DataByTimeAndPfPRBinsAndAgeBins'  # TODO: MSR.json helper to extract grouping and bins from channel

        self.channel_series = json_to_pandas(data[grouping][self.channel], self.bins, self.channel)

    def test_pandas_from_json(self):
        self.assertEqual(self.channel_series.name, self.channel)
        self.assertListEqual(self.bins.keys(), self.channel_series.index.names)
        self.assertAlmostEqual(self.channel_series.loc[1095, 100, 500], 0.008418, places=5)
        for x, y in zip(self.channel_series.loc[31, 20].values, [0.031877, 0.031228, 0.030612, 0.038961, 0.026351, 0.029814, 0.035644]):
            self.assertAlmostEqual(x, y, places=5)


if __name__ == '__main__':
    unittest.main()