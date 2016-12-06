import os
import json
import unittest
from collections import OrderedDict

import pandas as pd

from calibtool.analyzers.Helpers import json_to_pandas
from calibtool.study_sites.site_Laye import LayeCalibSite


class DummyParser:
    """
    A class to hold what would usually be in OutputParser.rawdata
    allowing testing of analyzer apply() functions that bypasses ExperimentManager.
    """
    def __init__(self, filename, filepath):
        """
        :param filename: Dummy filename needs to match value expected by analyzer, e.g. filenames[0]
        :param filepath: Actual path to the test file
        """
        with open(filepath, 'r') as json_file:
            self.rawdata = {filename: json.load(json_file)}


class TestLayeCalibSite(unittest.TestCase):

    def setUp(self):
        filepath = os.path.join('input', 'test_malaria_summary_report.json')
        self.filename = 'MalariaSummaryReport_Monthly_Report.json'
        self.parser = DummyParser(self.filename, filepath)
        self.site = LayeCalibSite()

    def test_site(self):
        self.assertEqual(self.site.name, 'Laye')

    def test_parser(self):
        data = self.parser.rawdata[self.filename]
        metadata = data['Metadata']
        time = data['DataByTime']['Time Of Report']

        pop_bins = OrderedDict([
            ('Time', time),
            ('Age Bins', metadata['Age Bins'])
        ])

        pop_channel = 'Average Population by Age Bin'
        pop_grouping = 'DataByTimeAndAgeBins'
        population = json_to_pandas(data[pop_grouping][pop_channel], pop_bins, pop_channel)

        self.assertListEqual(population.index.names, ['Time', 'Age Bins'])
        self.assertAlmostEqual(population.loc[31, 80], 16.602738, places=5)

        # TODO: MSR.json helper to extract grouping and bins from channel
        parasite_channel = 'PfPR by Parasitemia and Age Bin'
        parasite_grouping = 'DataByTimeAndPfPRBinsAndAgeBins'

        parasite_bins = OrderedDict([
            ('Time', time),
            ('Age Bins', metadata['Age Bins']),
            ('PfPR bins', metadata['Parasitemia Bins'])
        ])

        parasites = json_to_pandas(data[parasite_grouping][parasite_channel], parasite_bins, parasite_channel)

        self.assertEqual(parasites.name, parasite_channel)
        self.assertListEqual(parasite_bins.keys(), parasites.index.names)
        self.assertAlmostEqual(parasites.loc[1095, 100, 500], 0.008418, places=5)
        for x, y in zip(parasites.loc[31, 20].values, [0.031877, 0.031228, 0.030612, 0.038961, 0.026351, 0.029814, 0.035644]):
            self.assertAlmostEqual(x, y, places=5)

    def test_analyzer(self):

        analyzers = self.site.analyzers
        self.assertTrue(len(analyzers), 1)

        analyzer = analyzers[0]
        self.assertTrue(analyzer.name, 'PrevalenceByAgeSeasonAnalyzer')

        reference = analyzer.reference
        self.assertIsInstance(reference, pd.Series)

    def test_bad_reference_type(self):
        self.assertRaises(lambda: self.site.get_reference_data('unknown_type'))

    def test_get_reference(self):
        reference = self.site.get_reference_data('density_by_age_and_season')
        self.assertListEqual(reference.index.names, ['PfPR Type', 'Seasons', 'Age Bins', 'PfPR bins'])
        self.assertEqual(reference.loc['PfPR by Gametocytemia and Age Bin', 'start_wet', 15, 50], 9)


if __name__ == '__main__':
    unittest.main()
