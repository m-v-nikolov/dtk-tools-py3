import sys, os, re
import logging
import pandas as pd
import numpy as np      # for finfo tiny
import copy
import shelve

# Plotting
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import gridspec

from calibtool import LL_calculators
from dtk.Typhoid.ReportTyphoidByAgeAndGenderAnalyzer import ReportTyphoidByAgeAndGenderAnalyzer

logger = logging.getLogger(__name__)

class CasesByAgeAnalyzer(ReportTyphoidByAgeAndGenderAnalyzer):

    def __init__(self, 
                    name,
                    age_bins,
                    year_bins,

                    max_sims_to_process = -1,
                    pop_scaling_year = 1975.997,
                    pop_scaling_pop = 3782716,
                    pop_scaling_age_min = 0,
                    pop_scaling_age_max = 100,
                    force_apply = False,
                    force_combine = False,
                    basedir = 'Work',
                    fig_format = 'png',
                    fig_dpi = 600,
                    verbose = False):

        super(CasesByAgeAnalyzer, self).__init__( max_sims_to_process, pop_scaling_year, pop_scaling_pop, pop_scaling_age_min, pop_scaling_age_max, force_apply, force_combine, basedir, fig_format, fig_dpi, verbose)

        self.name = name
        self.year_bins = year_bins
        self.age_bins = age_bins

        self.cache_data = {}

    """
    def set_reference(self, reference_data):
        self.reference = reference_data[self.reference_key]

        self.reference.set_index('Year', inplace=True)
        self.reference_years = sorted( self.reference.index.unique() )

        self.reference['Age'] = self.reference['Age'].astype('category', categories=sorted( list(set(self.reference['Age'])), key=self.lower_age), ordered=False)

        self.reference = self.reference.reset_index().groupby('Age').sum()
        self.reference.drop('Year', axis=1, inplace=True)

        self.reference = self.reference.rename(columns={'Cases':'Ref.Cases', 'Population':'Ref.Population'})

        self.cache_data['reference'] = self.reference.reset_index().to_dict(orient='list')
        self.cache_data['reference_years'] = self.reference_years
    """

    def filter(self, sim_metadata):
        return super(CasesByAgeAnalyzer, self).filter(sim_metadata)

    def lower_age(self, agebin):
        return [int(s) for s in re.findall(r'\b\d+\b', agebin)][0]

    def apply(self, parser):
        '''
        Extract data from output data and accumulate in same bins as reference.
        '''
        sim = super(CasesByAgeAnalyzer, self).apply(parser)
        if self.verbose:
            print 'Population scaling factor is', self.pop_scaling

        sim_age_bins = sorted( list(set(sim['Age'].tolist())) )

        keep_cols = ['Year', 'Population', 'Age', 'Acute (Inc)', 'Sub-Clinical (Inc)']
        drop_cols = list( set(sim.columns.values) - set(keep_cols) )
        sim.drop(drop_cols, axis=1, inplace=True)

        # Select years, assuming sequential
        first_year = self.reference_years[0]
        last_year = self.reference_years[-1]+1
        sim = sim.query('Year > @first_year & Year <= @last_year')
        tmp = sim.set_index('Year')
        if len(tmp.index.unique()) != len(self.reference_years):
            raise Exception( "[%s] Failed to find all data years (%s) in simulation output (%s)." % (self.name, self.reference_years, tmp.index.unique()) )

        ref_age_bins = self.reference.index.unique()
        sim_output = pd.DataFrame()
        for ref_bin in ref_age_bins:
            ref_edges = [int(s) for s in re.findall(r'\b\d+\b', ref_bin)]

            agebin_begin = ref_edges[0]
            agebin_end = ref_edges[1]

            assert( agebin_begin in sim_age_bins )
            assert( agebin_end in sim_age_bins or (agebin_end > sim_age_bins[-1] and agebin_end > 99) )

            #simbin = sim.query('Age >= @agebin_begin & Age < @agebin_end & Year > @first_year & Year <= @last_year').sum().to_frame() # [['Acute (Inc)', 'Sub-Clinical (Inc)', 'Population']]
            simbin = sim.query('Age >= @agebin_begin & Age < @agebin_end & Year > @first_year & Year <= @last_year').sum()
            simbin.loc['Age'] = ref_bin

            # Undo parent's pop scaling for beta-binomial likelihood
            simbin['Sim.Cases'] = (simbin['Acute (Inc)'] +simbin['Sub-Clinical (Inc)'])
            simbin['Sim.Cases.Unscaled'] = simbin['Sim.Cases'] / self.pop_scaling # Note: pop_scaling comes from parent
            simbin.rename(index={'Population':'Sim.Population'}, inplace=True)
            simbin['Sim.Population.Unscaled'] = simbin['Sim.Population'] / self.pop_scaling

            sim_output = pd.concat( [sim_output, simbin], axis=1 )

        sim_output = sim_output.transpose().reset_index(drop=True)
        sim_output['Age'] = sim_output['Age'].astype('category', categories=sorted( list(set(sim_output['Age'])), key=self.lower_age), ordered=False)
        sim_output = sim_output.set_index('Age').sort_index()
        sim_output.drop('Year', axis=1, inplace=True)

        merged = pd.merge( self.reference, sim_output, left_index=True, right_index=True)

        #merged.reset_index(inplace=True)
        #merged.dropna(axis=0, how='any', inplace=True)

        shelve_data = {
            'Data': merged,
            'Sim_Id': parser.sim_id,
            'Sample': parser.sim_data.get('__sample_index__'),
            'Pop_Scaling': self.pop_scaling # From base class
        }
        self.shelve_apply( parser.sim_id, shelve_data)

        if self.verbose:
            print "size (MB):", sys.getsizeof(shelve_data)/8.0/1024.0


    def combine(self, parsers):
        if self.verbose:
            print "combine"

        shelved_data = super(CasesByAgeAnalyzer, self).combine(parsers)

        if shelved_data is not None:
            # Get data from shelve
            self.data = shelved_data['Data']
        else:

            # Not in shelve, need to combine and store in shelve
            selected = [ self.shelve[str(sim_id)]['Data'] for sim_id in self.sim_ids ]
            keys = [ (self.shelve[str(sim_id)]['Sample'], self.shelve[str(sim_id)]['Sim_Id'])
                for sim_id in self.sim_ids ]

            self.data = pd.concat( selected, axis=0,
                                keys=keys,
                                names=['Sample', 'Sim_Id'] )

            # Inefficient, have to make a bunch of NaNs and then dropna.
            # Would be much better with a __replicate__ index
            #self.data = pcon.reset_index().groupby(['Sample', 'Sim_Id', 'Age']).sum()
            #self.data.dropna(axis=0, inplace=True)

            self.shelve_combine( { 'Data' : self.data } )

        #self.cache_data['Sim'] = self.data.reset_index().to_dict(orient='dict')
        d = self.data.reset_index()
        self.cache_data['Sim'] = d.where((pd.notnull(d)), None).to_dict(orient='list')

        logger.debug(self.data)

        if self.verbose:
            print "Done with combine!"

    def compare_age(self, sample):
        # Computation takes mean of log across data points
        LL = LL_calculators.beta_binomial(
            raw_nobs = sample['Ref.Population'].tolist(),           # raw_nobs
            sim_nobs = sample['Sim.Population.Unscaled'].tolist(),  # sim_nobs
            raw_data = sample['Ref.Cases'].tolist(),                # raw_data
            sim_data = sample['Sim.Cases.Unscaled'].tolist()        # sim_data
        )

        return LL


    def compare(self, sample):
        '''
        Assess the result per sample, in this case the likelihood
        comparison between simulation and reference data.
        '''

        LL = sample.reset_index().groupby(['Sim_Id']).apply(self.compare_age)
        return sum(LL.values)


    def finalize(self):
        '''
        Calculate the output result for each sample.
        '''

        super(CasesByAgeAnalyzer, self).finalize() # Closes the shelve file

        self.result = self.data.groupby(level='Sample').apply(self.compare)
        self.result.replace(-np.inf, -1e-6, inplace=True)
        print self.result
        self.cache_data['result'] = self.result.to_dict()

        logger.debug(self.result)

    def cache(self):
        '''
        Return a cache of the minimal data required for plotting sample comparisons
        to reference comparisons.
        '''

        return self.cache_data


    def uid(self):
        ''' A unique identifier of site-name and analyzer-name. '''
        return '_'.join([self.site.name, self.name])
