import os
import json
from collections import OrderedDict
import unittest

from calibtool.analyzers.Helpers import json_to_pandas


class TestCalibHelpers(unittest.TestCase):

    def setUp(self):
        with open(os.path.join('input', 'test_malaria_summary_report.json'), 'r') as json_file:
            data = json.load(json_file)

        self.bins = OrderedDict([('Time', range(len(data['Annual EIR']))),
                                 ('Age Bins', data['Age Bins']),
                                 ('PfPR bins', data['Parasitemia Bins'])])

        self.channel = 'PfPR by Parasitemia and Age Bin'

        self.channel_series = json_to_pandas(data, self.bins, self.channel)

    def test_pandas_from_json(self):
        self.assertEqual(self.channel_series.name, self.channel)
        self.assertListEqual(self.bins.keys(), self.channel_series.index.names)
        self.assertEqual(self.channel_series.loc[714, 1000, 50], 0.652581)
        self.assertListEqual(self.channel_series.loc[0, 1000].values.tolist(),
                             [0.024, 0.0113333, 0.016, 0.023, 0.0173333])


if __name__ == '__main__':
    unittest.main()