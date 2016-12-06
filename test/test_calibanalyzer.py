import os
import json
import unittest

import pandas as pd

from calibtool.analyzers.Helpers import summary_channel_to_pandas, get_grouping_for_summary_channel, get_bins_for_summary_grouping
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
            self.raw_data = {filename: json.load(json_file)}


class TestLayeCalibSite(unittest.TestCase):

    def setUp(self):
        filepath = os.path.join('input', 'test_malaria_summary_report.json')
        self.filename = 'output/MalariaSummaryReport_Monthly_Report.json'
        self.parser = DummyParser(self.filename, filepath)
        self.data = self.parser.raw_data[self.filename]
        self.site = LayeCalibSite()

    def test_site_analyzer(self):
        self.assertEqual(self.site.name, 'Laye')

        analyzers = self.site.analyzers
        self.assertTrue(len(analyzers), 1)

        analyzer = analyzers[0]
        self.assertTrue(analyzer.name, 'PrevalenceByAgeSeasonAnalyzer')

        reference = analyzer.reference
        self.assertIsInstance(reference, pd.Series)

        sim_data = analyzer.apply(self.parser)

    def test_grouping(self):
        group = get_grouping_for_summary_channel(self.data, 'Average Population by Age Bin')
        self.assertEqual(group, 'DataByTimeAndAgeBins')
        self.assertRaises(lambda: get_grouping_for_summary_channel(self.data, 'unknown_channel'))

    def test_binning(self):
        group = 'DataByTimeAndAgeBins'
        bins = get_bins_for_summary_grouping(self.data, group)
        self.assertListEqual(bins.keys(), ['Time', 'Age Bins'])
        self.assertListEqual(bins['Age Bins'], range(0, 101, 10) + [1000])
        self.assertEqual(bins['Time'][-1], 1095)
        self.assertRaises(lambda: get_bins_for_summary_grouping(self.data, 'unknown_group'))

    def test_parser(self):
        population = summary_channel_to_pandas(self.data, 'Average Population by Age Bin')
        self.assertListEqual(population.index.names, ['Time', 'Age Bins'])
        self.assertAlmostEqual(population.loc[31, 80], 16.602738, places=5)

        parasite_channel = 'PfPR by Parasitemia and Age Bin'
        parasites = summary_channel_to_pandas(self.data, parasite_channel)
        self.assertEqual(parasites.name, parasite_channel)
        self.assertAlmostEqual(parasites.loc[1095, 100, 500], 0.008418, places=5)
        for x, y in zip(parasites.loc[31, 20].values, [0.031877, 0.031228, 0.030612, 0.038961, 0.026351, 0.029814, 0.035644]):
            self.assertAlmostEqual(x, y, places=5)

    def test_bad_reference_type(self):
        self.assertRaises(lambda: self.site.get_reference_data('unknown_type'))

    def test_get_reference(self):
        reference = self.site.get_reference_data('density_by_age_and_season')
        self.assertListEqual(reference.index.names, ['PfPR Type', 'Seasons', 'Age Bins', 'PfPR bins'])
        self.assertEqual(reference.loc['PfPR by Gametocytemia and Age Bin', 'start_wet', 15, 50], 9)


if __name__ == '__main__':
    unittest.main()
