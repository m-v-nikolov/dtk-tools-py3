import os
import json
import unittest
import copy

import pandas as pd

from calibtool.analyzers.Helpers import \
    summary_channel_to_pandas, get_grouping_for_summary_channel, get_bins_for_summary_grouping, \
    convert_to_counts, age_from_birth_cohort, season_from_time
from calibtool.study_sites.site_Laye import LayeCalibSite

from calibtool.LL_calculators import dirichlet_multinomial, dirichlet_multinomial_pandas


class DummyParser:
    """
    A class to hold what would usually be in OutputParser.rawdata
    allowing testing of analyzer apply() functions that bypasses ExperimentManager.
    """
    def __init__(self, filename, filepath, sim_id='dummy_id', index='dummy_index'):
        """
        :param filename: Dummy filename needs to match value expected by analyzer, e.g. filenames[0]
        :param filepath: Actual path to the test file
        """
        with open(filepath, 'r') as json_file:
            self.raw_data = {filename: json.load(json_file)}

        self.sim_id = sim_id
        self.sim_data = {'__sample_index__': index}

        self.selected_data = {}


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

        #############
        # TEST APPLY
        sim_data = analyzer.apply(self.parser)
        self.assertListEqual(reference.index.names, sim_data.index.names)
        for i, level in enumerate(reference.index.levels):
            # N.B. sim_data.index keeps empty values from dropna, e.g. unpopulated age bins
            self.assertSetEqual(set(level.values), set(sim_data.index.levels[i].values))

        # Population by age and season is the same and captured in one of parasite/gametocyte density bins
        df = sim_data.unstack('Channel')
        df = df.sum(level=['Season', 'Age Bin'])
        for ix, row in df.iterrows():
            self.assertAlmostEqual(row[0], row[1])

        self.assertEqual(self.parser.sim_id, 'dummy_id')
        self.assertEqual(self.parser.sim_data.get('__sample_index__'), 'dummy_index')

        # Make four dummy copies of the same parser with unique sim_id and two different sample points
        parsers = {i: copy.deepcopy(self.parser) for i in range(4)}
        tmp_sim_data = [None] * 4
        for i, p in parsers.items():
            p.sim_id = 'sim_%d' % i
            p.sim_data['__sample_index__'] = i % 2
            tmp_sim_data[i] = copy.deepcopy(sim_data) * (i + 1)  # so we have different values to verify averaging
            tmp_sim_data[i].sample = p.sim_data.get('__sample_index__')
            tmp_sim_data[i].sim_id = p.sim_id
            p.selected_data[id(analyzer)] = tmp_sim_data[i]

        #############
        # TEST COMBINE
        analyzer.combine(parsers)

        # Verify averaging of sim_id by sample_index is done correctly
        # sample0 = (id0, id2) = (1x, 3x) => avg = 2
        # sample1 = (id1, id3) = (2x, 4x) => avg = 3
        for ix, row in analyzer.data.iterrows():
            self.assertAlmostEqual(1.5 * row[0], row[1])

        #############
        # TEST COMPARE
        analyzer.finalize()  # applies compare_fn to each sample setting self.result

        # Reshape vectorized version to test nested-for-loop version
        def compare_with_nested_loops(x):
            x = pd.concat([x.rename('sim'), reference.rename('ref')], axis=1).dropna()
            x = x.unstack('PfPR Bin')
            return dirichlet_multinomial(x.ref.values, x.sim.values)

        self.assertAlmostEqual(analyzer.result[0], compare_with_nested_loops(analyzer.data[0]))

    def test_grouping(self):
        group = get_grouping_for_summary_channel(self.data, 'Average Population by Age Bin')
        self.assertEqual(group, 'DataByTimeAndAgeBins')
        self.assertRaises(lambda: get_grouping_for_summary_channel(self.data, 'unknown_channel'))

    def test_binning(self):
        group = 'DataByTimeAndAgeBins'
        bins = get_bins_for_summary_grouping(self.data, group)
        self.assertListEqual(bins.keys(), ['Time', 'Age Bin'])
        self.assertListEqual(bins['Age Bin'], range(0, 101, 10) + [1000])
        self.assertEqual(bins['Time'][-1], 1095)
        self.assertRaises(lambda: get_bins_for_summary_grouping(self.data, 'unknown_group'))

    def test_parser(self):
        population = summary_channel_to_pandas(self.data, 'Average Population by Age Bin')
        self.assertListEqual(population.index.names, ['Time', 'Age Bin'])
        self.assertAlmostEqual(population.loc[31, 80], 16.602738, places=5)

        parasite_channel = 'PfPR by Parasitemia and Age Bin'
        parasites = summary_channel_to_pandas(self.data, parasite_channel)
        self.assertEqual(parasites.name, parasite_channel)
        self.assertAlmostEqual(parasites.loc[1095, 500, 100], 0.026666, places=5)
        self.assertAlmostEqual(parasites.loc[31, :, 20].sum(), 1)  # on given day + age, density-bin fractions sum to 1

        counts = convert_to_counts(parasites, population)
        self.assertEqual(counts.name, parasites.name)
        self.assertListEqual(counts.index.names, parasites.index.names)
        self.assertListEqual(counts.iloc[7:13].astype(int).tolist(), [281, 13, 19, 7, 9, 6])

        df = parasites.reset_index()

        df = age_from_birth_cohort(df)
        self.assertListEqual((df.Time / 365.0).tolist(), df['Age Bin'].tolist())

        months_df = season_from_time(df)
        months = months_df.Month.unique()
        self.assertEqual(len(months), 12)
        self.assertEqual(months_df.Month.iloc[0], 'February')

        seasons = {'fall': ['September', 'October'], 'winter': ['January']}
        seasons_by_month = {}
        for s, mm in seasons.items():
            for m in mm:
                seasons_by_month[m] = s
        seasons_df = season_from_time(df, seasons=seasons_by_month)
        months = seasons_df.Month.unique()
        self.assertEqual(len(months), 3)
        self.assertEqual(seasons_df.Month.iloc[0], 'September')
        self.assertEqual(seasons_df.Season.iloc[0], 'fall')

    def test_bad_reference_type(self):
        self.assertRaises(lambda: self.site.get_reference_data('unknown_type'))

    def test_get_reference(self):
        reference = self.site.get_reference_data('density_by_age_and_season')
        self.assertListEqual(reference.index.names, ['Channel', 'Season', 'Age Bin', 'PfPR Bin'])
        self.assertEqual(reference.loc['PfPR by Gametocytemia and Age Bin', 'start_wet', 15, 50], 9)


if __name__ == '__main__':
    unittest.main()
