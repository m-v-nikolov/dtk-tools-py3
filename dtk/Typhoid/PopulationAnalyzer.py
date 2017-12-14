import logging

import pandas as pd

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

# Plotting

logger = logging.getLogger(__name__)

class PopulationAnalyzer(BaseAnalyzer):

    required_reference_types = ['Population']
    filenames = ['output/ReportTyphoidByAgeAndGender.csv']


    def __init__(self, name, weight):
        self.name = name
        self.weight = weight
        self.site = None
        self.cache_data = {}


    @staticmethod
    def parse_range(d):
        '''
        Given data along the lines of 
            d = '[5, 7)'
        return a tuple of (5,7).
        Also handle the case in which d is a scalar.
        '''

        if ',' in d:
            tok = d.split(',')
            begin = int(float(tok[0][1:]))
            end = int(float(tok[1][:-1]))
        else:
            begin = int(float(d))
            end = begin+1

        return (begin,end)


    @staticmethod
    def parse_ranges(data):
        '''
        Call parse_range on each entry of data, if a list, or otherwise on the data directly.
        '''
        ranges = []
        if isinstance(data, basestring):
            ranges.append( self.parse_range(data) )
        else:
            for d in data:
                ranges.append( self.parse_range(d) )
        return ranges


    def set_site(self, site):
        '''
        Get the reference data that this analyzer needs from the specified site.
        '''

        self.site = site
        # Note: Reference data is not site-dependent for Santiago
        self.reference = {}
        self.cache_data['reference'] = {}


    def filter(self, sim_metadata):
        '''
        This analyzer only needs to analyze simulations for the site it is linked to.
        N.B. another instance of the same analyzer may exist with a different site
             and correspondingly different reference data.
        '''
        return sim_metadata.get('__site__', False) == self.site.name


    def apply(self, parser):
        '''
        Extract data from output data and accumulate in same bins as reference.
        '''

        data = parser.raw_data[self.filenames[0]]
        data.rename(columns={'Time Of Report (Year)':'Year'}, inplace=True)

        summary = data.groupby( ['Year'] ).sum()

        summary.drop(['Age', 'NodeId', 'Gender'], axis=1, inplace=True)

        # Add metadata
        summary.sim_id =  parser.sim_id
        summary.sample =  parser.sim_data['__sample_index__']

        return summary


    def combine(self, parsers):
        '''
        Combine the simulation data into a single table for all analyzed simulations.
        '''

        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]

        #print('Writing selected to csv')
        #[s.to_csv('selected_%d.csv' % i) for (i,s) in enumerate(selected)]

        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]

        combined = pd.concat( selected, axis=1,
                                keys=[(d.sample, d.sim_id) for d in selected],
                                names=['sample', 'sim_id', 'channel'] )
        print('Writing combined to csv')
        combined.to_csv('combined_pop.csv')
        #combined = pd.read_csv('combined.csv', skipinitialspace=True, low_memory=False, header=[0,1,2], index_col=[0,1]);

        del selected

        # Out of RAM without cross sectioning (xs) to just Binned_Cases
        #stacked = combined.stack(['sample', 'sim_id'])#.reorder_levels(['sample', 'sim_id', 'Year', 'Age'])
        stacked = combined.xs('Population', level='channel', axis=1, drop_level=False).stack(['sample', 'sim_id'])

        #self.fig = plt.figure(figsize=(8, 6)) 
        #gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
        #ax1 = plt.subplot(gs[0])
        #ax2 = plt.subplot(gs[1])
        #sns.pointplot(data=stacked.reset_index(), x="Age", y="Binned_Cases", hue="sample", ax=ax1)
        #ax1.plot(range(len(self.age_bins)), self.reference['Count'], 'k+', ms=10, lw=2, mew=1, zorder=10)

        self.data = stacked[['Population']]
        self.cache_data['stacked'] = stacked.reset_index().to_dict(orient='dict')
        logger.debug(self.data)


    def compare(self, sample):
        return 0

    def finalize(self):
        '''
        Calculate the output result for each sample.
        '''
        self.result = self.data.groupby(level='sample').apply(self.compare)
        self.cache_data['result'] = self.result.to_dict()

        #result_to_plot = copy.deepcopy(self.result).to_frame('LogLikelihood').reset_index()
        #ax2 = self.fig.get_axes()[1]
        #sns.pointplot(data=result_to_plot, y='LogLikelihood', x='sample', join=False, ax=ax2)
        #ax2.yaxis.grid(True)
        ##sns.plt.show() # <-- When lots of sims, "ICE default IO error handler doing an exit(), pid = 5044, errno = 32"
        #plt.savefig('U20Incidence.pdf')
        #plt.close()

        logger.debug(self.result)

    def cache(self):
        '''
        Return a cache of the minimal data required for plotting sample comparisons
        to reference comparisons.
        '''

        return self.cache_data

        #cache = self.data.copy()
        #cache = cache[cache['Person Years'] > 0]
        #cache['Annual Clinical Incidence by Age Bin'] = cache['Clinical Incidents'] / cache['Person Years']
        #cache = cache[['Annual Clinical Incidence by Age Bin']].reset_index(level='age_bins')
        #cache.age_bins = cache.age_bins.astype(int)  # numpy.int64 serialization problem with utils.NumpyEncoder
        #sample_dicts = [df.to_dict(orient='list') for idx, df in cache.groupby(level='sample', sort=True)]
        #logger.debug(sample_dicts)

        #return {'sims': sample_dicts, 'reference': self.reference, 'axis_names': [self.x, self.y]}

    def uid(self):
        ''' A unique identifier of site-name and analyzer-name. '''
        return '_'.join([self.site.name, self.name])
