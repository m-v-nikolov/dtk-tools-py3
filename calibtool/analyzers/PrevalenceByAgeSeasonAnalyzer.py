import logging
from collections import OrderedDict

from calibtool import LL_calculators
from calibtool.analyzers.Helpers import *
from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class PrevalenceByAgeSeasonAnalyzer(BaseAnalyzer):

    required_reference_types = ['density_by_age_and_season']
    filenames = ['output/MalariaSummaryReport_Monthly_Report.json']

    x = 'age_bins'
    y = 'PfPR by Parasitemia and Age Bin'
    z = 'PfPR by Gametocytemia and Age Bin'

    data_group_names = ['sample', 'sim_id', 'channel']

    def __init__(self, name, weight):
        self.name = name
        self.weight = weight
        self.site = None
        self.reference = None

    def set_site(self, site):
        """
        Get the reference data that this analyzer needs from the specified site.
        """

        self.site = site
        self.reference = self.site.reference_data[self.required_reference_types[0]]

    def filter(self, sim_metadata):
        """
        This analyzer only needs to analyze simulations for the site it is linked to.
        N.B. another instance of the same analyzer may exist with a different site
             and correspondingly different reference data.
        """
        return sim_metadata.get('__site__', False) == self.site.name

    def apply(self, parser):
        """
        Extract data from output simulation data and accumulate in same bins as reference.
        """

        # Reference dataframe
        channel = 'PfPR by Parasitemia and Age Bin'
        bins = OrderedDict([('PfPR Type', ['Parasitemia', 'Gametocytemia']),
                            ('Seasons', self.reference['Seasons'].keys()),
                            ('Age Bins', self.reference['Metadata']['age_bins']),
                            ('PfPR bins', self.reference['Metadata']['parasitemia_bins'])])
        self.ref_data = ref_json_to_pandas(self.reference, self.required_reference_types[0], bins, channel)  # Ref data converted to Pandas

        # Load data from simulations
        data = parser.raw_data[self.filenames[0]]

        # Population dataframe
        population = data['TimeXAgeBin']['Average Population by Age Bin']
        bins = OrderedDict([('Time', [i for i in range(13)]), ('Age Bins', [1000])])
        bin_tuples = list(itertools.product(*bins.values()))
        multi_index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())
        channel_pop = 'Population by Age Bin'
        population = pd.Series(np.array(population).flatten(), index=multi_index, name=channel_pop)

        # Simulation dataframe
        months = self.reference['Metadata']['months']
        bins = OrderedDict([('Time', [i * 1 for i, _ in enumerate(data['Time']['Annual EIR'])]), ('Age Bins', data['Metadata']['Age Bins']),
                            ('PfPR bins', data['Metadata']['Parasitemia Bins'])])
        simdata1 = [data[type][self.y] for type in data.keys() if self.y in data[type].keys()]
        simdata2 = [data[type][self.z] for type in data.keys() if self.z in data[type].keys()]
        temp_data1 = json_to_pandas(simdata1[0], bins, channel)  # Sim data converted to Pandas
        temp_data1 = reorder_sim_data(temp_data1, self.ref_data, months, self.y, population)
        temp_data2 = json_to_pandas(simdata2[0], bins, channel)  # Sim data converted to Pandas
        temp_data2 = reorder_sim_data(temp_data2, self.ref_data, months, self.z, population)
        sim_data = pd.concat([temp_data1, temp_data2])

        sim_data.sample = parser.sim_data.get('__sample_index__')
        sim_data.sim_id = parser.sim_id

        return sim_data

    def combine(self, parsers):
        """
        Combine the simulation data into a single table for all analyzed simulations.
        """

        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected, axis=0,
                         keys=[(d.sim_id, d.sample) for d in selected],
                             names=self.data_group_names)
        combined = combined.reset_index()
        groupByColumns = list(combined.keys()[1:-1])          # Only taking sim_id, Age_Bins, Seasons (if available), PfPR Bins (if available), PfPR Type (if available)
        combined = pd.DataFrame.dropna(combined.groupby(groupByColumns).mean().reset_index())
        del combined['channel']
        self.data = pd.pivot_table(combined, values=combined.keys()[-1], index=list(combined.keys()[1:-1]), columns=combined.keys()[0])
        logger.debug(self.data)

    def compare(self, sample):
        """
        Assess the result per sample, in this case the likelihood
        comparison between simulation and reference data.
        """

        sample = sample.reset_index()
        sample.rename(columns={sample.keys()[-1]: 'sim'}, inplace=True)
        sample['ref'] = self.ref_data.reset_index()['PfPR by Parasitemia and Age Bin']
        sample = sample[sample['sim'] > 0]
        sample = sample[sample['ref'] > 0]


        # TODO: vectorize LL_calculators?!
        return LL_calculators.dirichlet_multinomial_pandas(sample)

    def finalize(self):
        """
        Calculate the output result for each sample.
        """
        self.result = self.data.apply(self.compare)
        logger.debug(self.result)

    def cache(self):
        """
        Return a cache of the minimal data required for plotting sample comparisons
        to reference comparisons.
        """

        cache = self.data.copy()
        sample_dicts = [{self.y:[cache[i][j] for j in range(len(cache[i])) ]} for i in range(len(cache.keys()))] # i cycles through simulation id, y cycles through sim values
        ref_dicts = {self.y:[self.ref_data[i] for i in range(len(self.ref_data))]}
        logger.debug(sample_dicts)

        return {'sims': sample_dicts, 'reference': ref_dicts, 'axis_names': [self.x, self.y]}

    def uid(self):
        """ A unique identifier of site-name and analyzer-name. """
        return '_'.join([self.site.name, self.name])
