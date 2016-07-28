
# TODO: Generalize this style of CalibAnalyzer as much as possible
#       to minimize repeated code in e.g. PrevalenceByAgeAnalyzer
import logging

import pandas as pd

from calibtool import LL_calculators
from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class PrevalenceByRoundAnalyzer(BaseAnalyzer):

    required_reference_types = ['prevalence_by_round']

    y = 'New Diagnostic Prevalence'

    data_group_names = ['sample', 'sim_id', 'channel']

    def __init__(self, name, weight):
        self.name = name
        self.weight = weight
        self.site = None
        self.setup = {}

    def set_site(self, site):
        '''
        Get the reference data that this analyzer needs from the specified site.

        Get survey collection dates and subregions, if present, from the specified site.
        '''
        self.site = site
        self.reference = self.site.reference_data['prevalence_by_round']
        try :
            self.testdays = self.setup['testdays']
        except KeyError :
            raise Exception('%s requires \'testdays\' input in site setup' % self.name)

        self.filenames = ['output/ReportMalariaFiltered.json']
        if 'regions' in self.setup :
            self.regions = self.setup['regions']
            filenames = ['output/ReportMalariaFiltered' + x + '.json' for x in self.regions if x != 'all']
            if 'all' in self.regions :
                self.filenames += filenames
                self.regions.insert(0, self.regions.pop(self.regions.index('all')))
            else :
                self.filenames = filenames
        else :
            self.regions = ['all']

    def filter(self, sim_metadata):
        '''
        This analyzer only needs to analyze simulations for the site it is linked to.
        N.B. another instance of the same analyzer may exist with a different site
             and correspondingly different reference data.
        '''
        return sim_metadata.get('__site__', False) == self.site.name

    def apply(self, parser):
        '''
        Extract data from output data
        '''
        dfs = []
        for i, region in enumerate(self.regions) :
            data = [parser.raw_data[self.filenames[i]]['Channels'][self.y]['Data'][x] for x in self.testdays]

            df = pd.DataFrame({ self.y: data},
                                index=self.testdays)
            df.region = region
            df.index.name = 'testdays'
            dfs.append(df)

        c = pd.concat(dfs, axis=1, keys=self.regions, names=['region'])
        channel_data = c.stack(['region'])
        channel_data.sample = parser.sim_data.get('__sample_index__')
        channel_data.sim_id = parser.sim_id

        return channel_data

    def combine(self, parsers):
        '''
        Combine the simulation data into a single table for all analyzed simulations.
        '''
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected, axis=1,
                             keys=[(d.sample, d.sim_id) for d in selected],
                             names=self.data_group_names)
        stacked = combined.stack(['sample', 'sim_id'])
        self.data = stacked.groupby(level=['sample', 'region', 'testdays']).mean()
        logger.debug(self.data)

    def compare(self, sample):
        '''
        Assess the result per sample, in this case the likelihood
        comparison between simulation and reference data.
        '''
        return sum([LL_calculators.euclidean_distance(self.reference[region], df[self.y].tolist()) for (region, df) in sample.groupby(level='region')])

    def finalize(self):
        '''
        Calculate the output result for each sample.
        '''
        self.result = self.data.groupby(level='sample').apply(self.compare)
        logger.debug(self.result)

    def cache(self):
        '''
        Return a cache of the minimal data required for plotting sample comparisons
        to reference comparisons.
        '''
        cache = self.data.copy()

        sample_dicts = []
        for idx, df in cache.groupby(level='sample', sort=True) :
            d = { 'region' : self.regions,
                   self.y : [sdf[self.y].values.tolist() for jdx, sdf in df.groupby(level='region') ] }
            sample_dicts.append(d)

        logger.debug(sample_dicts)

        return {'sims': sample_dicts, 'reference': self.reference, 'axis_names': ['region', self.y]}

    def uid(self):
        ''' A unique identifier of site-name and analyzer-name. '''
        return '_'.join([self.site.name, self.name])

    @staticmethod
    def plot_sim(fig, reference, simdata, x, y, style='-', color='#CB5FA4', alpha=1, linewidth=1) :
        numpoints = len(reference['all'])
        numregions = len(simdata['region'])
        for i, region in enumerate(simdata['region']) :
            ax = fig.add_subplot(max([1, (numregions+1)/2]), min([numregions, 2]), i+1)
            ax.plot(range(1, numpoints+1), simdata[y][i], style, color=color, alpha=alpha, linewidth=linewidth)

    @staticmethod
    def plot_reference(fig, reference, simdata, x, y, style='-o', color='#8DC63F', alpha=1, linewidth=1) :
        numpoints = len(reference['all'])
        numregions = len(simdata['region'])
        for i, region in enumerate(simdata['region']) :
            ax = fig.add_subplot(max([1, (numregions+1)/2]), min([numregions, 2]), i+1)
            ax.plot(range(1, numpoints+1), reference[region], style, color=color, alpha=alpha, linewidth=linewidth)
            ax.set_title(region)
            ax.set(xlabel='round', ylabel=y)