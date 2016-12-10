import os
import json
import unittest
import copy
from abc import ABCMeta, abstractmethod

import numpy as np
import pandas as pd

from dtk.utils.parsers.malaria_summary import \
    summary_channel_to_pandas, get_grouping_for_summary_channel, get_bins_for_summary_grouping

from calibtool.analyzers.Helpers import \
    convert_annualized, convert_to_counts, age_from_birth_cohort, season_from_time

from calibtool.study_sites.LayeCalibSite import LayeCalibSite
from calibtool.study_sites.DielmoCalibSite import DielmoCalibSite
from calibtool.study_sites.MatsariCalibSite import MatsariCalibSite

from calibtool.LL_calculators import dirichlet_multinomial, gamma_poisson, beta_binomial


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


class BaseCalibSiteTest(object):
    """
    A class to hold functions common to all CalibSite test functions,
    but which will not run in the base class as it doesn't inherit from TestCase.
    Using multiple inheritance in derived classes to pick up TestCase functions,
    this class first so its definitions aren't overridden by unittest.TestCase.
    """

    __metaclass__ = ABCMeta

    filename = None

    @abstractmethod
    def setUp(self):
        filepath = os.path.join('input', 'test_malaria_summary_report.json')
        self.parser = DummyParser(self.filename, filepath)
        self.data = self.parser.raw_data[self.filename]

    def get_dummy_parsers(self, sim_data, analyzer_id, n_sims=8, n_samples=4):
        parsers = {i: copy.deepcopy(self.parser) for i in range(n_sims)}
        tmp_sim_data = [None] * n_sims
        for i, p in parsers.items():
            p.sim_id = 'sim_%d' % i
            p.sim_data['__sample_index__'] = i % n_samples
            tmp_sim_data[i] = copy.deepcopy(sim_data) * (i + 1)  # so we have different values to verify averaging
            tmp_sim_data[i].sample = p.sim_data.get('__sample_index__')
            tmp_sim_data[i].sim_id = p.sim_id
            p.selected_data[analyzer_id] = tmp_sim_data[i]
        return parsers


class TestLayeCalibSite(BaseCalibSiteTest, unittest.TestCase):

    site_name = 'Laye'
    analyzer_name = 'ChannelBySeasonAgeDensityCohortAnalyzer'
    filename = 'output/MalariaSummaryReport_Monthly_Report.json'

    def setUp(self):
        super(TestLayeCalibSite, self).setUp()
        self.site = LayeCalibSite()
        self.assertEqual(self.site.name, self.site_name)

    def test_site_analyzer(self):

        analyzers = self.site.analyzers
        self.assertTrue(len(analyzers), 1)

        analyzer = analyzers[0]
        self.assertTrue(analyzer.name, self.analyzer_name)

        reference = analyzer.reference
        self.assertIsInstance(reference, pd.DataFrame)

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

        # Make multiple dummy copies of the same parser
        # with unique sim_id and subset of different sample points
        n_sims, n_samples = 8, 4
        parsers = self.get_dummy_parsers(sim_data, id(analyzer), n_sims=n_sims, n_samples=n_samples)

        #############
        # TEST COMBINE
        analyzer.combine(parsers)

        # Verify averaging of sim_id by sample_index is done correctly
        # e.g. sample0 = (id0, id2) = (1x, 3x) => avg0 = 2
        avg = [np.arange(i + 1, n_sims + 1, n_samples).mean() for i in range(n_samples)]
        for ix, row in analyzer.data.iterrows():
            for isample in range(1, n_samples):
                self.assertAlmostEqual(row[0, 'Counts'] / avg[0], row[i, 'Counts'] / avg[i])

        #############
        # TEST COMPARE
        analyzer.finalize()  # applies compare_fn to each sample setting self.result

        # Reshape vectorized version to test nested-for-loop version
        def compare_with_nested_loops(x):
            x = pd.concat({'sim': x, 'ref': reference}, axis=1).dropna()
            x = x.unstack('PfPR Bin')
            return dirichlet_multinomial(x.ref.values, x.sim.values)

        for i in range(n_samples):
            sample_data = analyzer.data.xs(i, level='sample', axis=1)
            self.assertAlmostEqual(analyzer.result[i], compare_with_nested_loops(sample_data))

        #############
        # TEST CACHE
        cache = analyzer.cache()  # concats reference to columns of simulation outcomes by sample-point index
        self.assertListEqual(range(n_samples) + ['ref'], cache.columns.levels[0].tolist())

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
        self.assertEqual(reference.loc[('PfPR by Gametocytemia and Age Bin', 'start_wet', 15, 50), 'Counts'], 9)


class TestDielmoCalibSite(BaseCalibSiteTest, unittest.TestCase):

    site_name = 'Dielmo'
    analyzer_name = 'IncidenceByAgeCohortAnalyzer'
    filename = 'output/MalariaSummaryReport_Annual_Report.json'

    def setUp(self):
        super(TestDielmoCalibSite, self).setUp()
        self.site = DielmoCalibSite()
        self.assertEqual(self.site.name, self.site_name)

    def test_get_reference(self):
        reference = self.site.get_reference_data('annual_clinical_incidence_by_age')
        self.assertListEqual(reference.index.names, ['Age Bin'])
        self.assertSetEqual(set(reference.columns.tolist()),
                            {'Average Population by Age Bin', 'Annual Clinical Incidence by Age Bin'})
        self.assertEqual(reference.loc[3, 'Annual Clinical Incidence by Age Bin'], 6.1)

    @classmethod
    def compare_with_nested_loops(cls, sim, ref):
        """
        Reshape vectorized version to test nested-for-loop version
        """
        x = pd.concat({'sim': sim, 'ref': ref}, axis=1).dropna()
        return gamma_poisson(x.ref['Person Years'].values, x.sim['Person Years'].values,
                             x.ref.Incidents.values, x.sim.Incidents.values)

    def test_site_analyzer(self):

        analyzers = self.site.analyzers
        self.assertTrue(len(analyzers), 1)

        analyzer = analyzers[0]
        self.assertTrue(analyzer.name, self.analyzer_name)

        reference = analyzer.reference
        self.assertIsInstance(reference, pd.DataFrame)

        #############
        # Test annualized functions
        channel_data = pd.concat([summary_channel_to_pandas(self.data, c)
                                  for c in (analyzer.channel, analyzer.population_channel)], axis=1)
        person_years = convert_annualized(channel_data[analyzer.population_channel])
        channel_data['Person Years'] = person_years
        channel_data['Incidents'] = convert_to_counts(channel_data[analyzer.channel], channel_data['Person Years'])
        for ix, row in channel_data.loc[31].iterrows():
            self.assertAlmostEqual(row['Person Years'], row[analyzer.population_channel] * 31 / 365.0)
            self.assertAlmostEqual(row['Incidents'], row[analyzer.channel] * row['Person Years'])

        #############
        # TEST APPLY
        sim_data = analyzer.apply(self.parser)
        self.assertListEqual(reference.index.names, sim_data.index.names)
        self.assertSetEqual(set(sim_data.columns.tolist()), {'Incidents', 'Person Years'})

        self.assertEqual(self.parser.sim_id, 'dummy_id')
        self.assertEqual(self.parser.sim_data.get('__sample_index__'), 'dummy_index')

        # Make multiple dummy copies of the same parser
        # with unique sim_id and subset of different sample points
        n_sims, n_samples = 8, 4
        parsers = self.get_dummy_parsers(sim_data, id(analyzer), n_sims=n_sims, n_samples=n_samples)

        #############
        # TEST COMBINE
        analyzer.combine(parsers)

        # Verify averaging of sim_id by sample_index is done correctly
        # e.g. sample0 = (id0, id2) = (1x, 3x) => avg0 = 2
        avg = [np.arange(i + 1, n_sims + 1, n_samples).mean() for i in range(n_samples)]
        for ix, row in analyzer.data.iterrows():
            for isample in range(1, n_samples):
                self.assertAlmostEqual(row[0, 'Incidents'] / avg[0], row[i, 'Incidents'] / avg[i])
                self.assertAlmostEqual(row[0, 'Person Years'] / avg[0], row[i, 'Person Years'] / avg[i])

        #############
        # TEST COMPARE
        analyzer.finalize()  # applies compare_fn to each sample setting self.result

        for i in range(n_samples):
            sample_data = analyzer.data.xs(i, level='sample', axis=1)
            self.assertAlmostEqual(analyzer.result[i], self.compare_with_nested_loops(sample_data, reference))

        #############
        # TEST CACHE
        cache = analyzer.cache()  # concats reference to columns of simulation outcomes by sample-point index
        self.assertListEqual(range(n_samples) + ['ref'], cache.columns.levels[0].tolist())


class TestMatsariCalibSite(TestDielmoCalibSite, unittest.TestCase):
    """
    This is similar enough to the Dielmo incidence calibration test that we can just derive from that
    """

    site_name = 'Matsari'
    analyzer_name = 'PrevalenceByAgeCohortAnalyzer'
    filename = 'output/MalariaSummaryReport_Annual_Report.json'

    def setUp(self):
        BaseCalibSiteTest.setUp(self)
        self.site = MatsariCalibSite()
        self.assertEqual(self.site.name, self.site_name)

    def test_get_reference(self):
        reference = self.site.get_reference_data('analyze_prevalence_by_age_cohort')
        self.assertListEqual(reference.index.names, ['Age Bin'])
        self.assertSetEqual(set(reference.columns.tolist()),
                            {'Average Population by Age Bin', 'PfPR by Age Bin'})
        self.assertEqual(reference.loc[2, 'PfPR by Age Bin'], 0.7)

    @classmethod
    def compare_with_nested_loops(cls, sim, ref):
        """
        Reshape vectorized version to test nested-for-loop version
        """
        x = pd.concat({'sim': sim, 'ref': ref}, axis=1).dropna()
        return beta_binomial(x.ref['Person Years'].values, x.sim['Person Years'].values,
                             x.ref.Incidents.values, x.sim.Incidents.values)


if __name__ == '__main__':
    unittest.main()
