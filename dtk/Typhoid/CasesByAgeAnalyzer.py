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
                    reference_sheet,

                    basedir = 'Work',

                    max_sims_to_process = -1,
                    force_apply = False,
                    force_combine = False,

                    pop_scaling_year = 1975.997,
                    pop_scaling_pop = 3782716,
                    pop_scaling_age_min = 0,
                    pop_scaling_age_max = 100,

                    fig_format = 'png',
                    fig_dpi = 600,
                    verbose = False):

        super(CasesByAgeAnalyzer, self).__init__( max_sims_to_process, pop_scaling_year, pop_scaling_pop, pop_scaling_age_min, pop_scaling_age_max, force_apply, force_combine, basedir, fig_format, fig_dpi, verbose)

        self.name = name
        self.reference_sheet = reference_sheet

        self.cache_data = {}

    def set_site(self, site):

        years = site.reference_data[self.reference_sheet]['Year'].unique()
        self.reference = site.reference_data[self.reference_sheet].groupby(['AgeBin']).sum().reset_index()
        self.reference['Year'] = '[%d, %d)'%(years[0], years[-1]+1)
        self.reference['AgeBin'] = self.reference['AgeBin'].astype('category', categories=sorted(list(set(self.reference['AgeBin'])), key=self.lower_value), ordered=True)
        #self.reference.drop('Age', axis=1, inplace=True)
        self.reference = self.reference.set_index('AgeBin').sort_index()

        self.year_bins = ['[%d, %d)'%(years[0], years[-1]+1)]
        self.age_bins = self.reference.index.get_level_values('AgeBin').unique()

        self.cache_data['reference'] = self.reference.reset_index().to_dict(orient='list')


    def filter(self, sim_metadata):
        return super(CasesByAgeAnalyzer, self).filter(sim_metadata)

    def lower_value(self, agebin): # For age-bin sorting
        return [int(s) for s in re.findall(r'\b\d+\b', agebin)][0]

    def apply(self, parser):
        '''
        Extract data from output data and accumulate in same bins as reference.
        '''
        (sim, pop_scaling) = super(CasesByAgeAnalyzer, self).apply(parser)

        sim_age_bins = sorted( list(set(sim['Age'].tolist())) )

        keep_cols = ['Year', 'Population', 'Age', 'Acute (Inc)', 'Sub-Clinical (Inc)']
        drop_cols = list( set(sim.columns.values) - set(keep_cols) )
        sim.drop(drop_cols, axis=1, inplace=True)

        sim_output = pd.DataFrame()
        for year_bin in self.year_bins:
            year_edges = [int(s) for s in re.findall(r'\b\d+\b', year_bin)]
            # Select years, assuming sequential
            sim_by_year = sim.query('Year >= @year_edges[0] & Year < @year_edges[1]').set_index('Year')

            for age_bin in self.age_bins:
                age_edges = [int(s) for s in re.findall(r'\b\d+\b', age_bin)]

                assert( age_edges[0] in sim_age_bins )
                assert( age_edges[1] in sim_age_bins or (age_edges[1] > sim_age_bins[-1] and age_edges[1] > 99) )

                simbin = sim_by_year.query('Age >= @age_edges[0] & Age < @age_edges[1]').sum()
                simbin.loc['AgeBin'] = age_bin
                simbin.loc['YearBin'] = year_bin

                # Undo parent's pop scaling for beta-binomial likelihood
                simbin['Sim_Cases'] = simbin['Acute (Inc)']
                simbin['Sim_Cases_With_Subclinical'] = simbin['Sim_Cases'] + simbin['Sub-Clinical (Inc)']

                simbin['Sim_Cases_Unscaled'] = simbin['Sim_Cases'] / pop_scaling # Note: pop_scaling comes from parent
                simbin['Sim_Cases_With_Subclinical_Unscaled'] = simbin['Sim_Cases_With_Subclinical'] / pop_scaling
                simbin.rename(index={'Population':'Sim_Population'}, inplace=True)
                simbin['Sim_Population_Unscaled'] = simbin['Sim_Population'] / pop_scaling

                sim_output = pd.concat( [sim_output, simbin], axis=1 )

        sim_output = sim_output.transpose().reset_index(drop=True)
        sim_output['AgeBin'] = sim_output['AgeBin'].astype('category', categories=sorted( list(set(sim_output['AgeBin'])), key=self.lower_value), ordered=False)
        sim_output['YearBin'] = sim_output['YearBin'].astype('category', categories=sorted( list(set(sim_output['YearBin'])), key=self.lower_value), ordered=False)

        sim_output = sim_output.set_index(['YearBin', 'AgeBin']).sort_index()
        sim_output.drop('Age', axis=1, inplace=True)

        merged = pd.merge(sim_output, self.reference, left_index=True, right_index=True)

        shelve_data = {
            'Data': merged,
            'Sim_Id': parser.sim_id,
            'Sample': parser.sim_data.get('__sample_index__'),
            #'Replicate': parser.sim_data.get('__replicate_index__'),
            'Pop_Scaling': pop_scaling # From base class
        }
        self.shelve_apply( parser.sim_id, shelve_data)

        #if self.verbose:
        #    print "size (MB):", sys.getsizeof(shelve_data)/8.0/1024.0

    def combine(self, parsers):
        shelved_data = super(CasesByAgeAnalyzer, self).combine(parsers)

        if shelved_data is not None:
            # Get data from shelve
            self.data = shelved_data['Data']
        else:

            # Not all sim_ids work, perhaps due to a failed job
            failed_sids = [sid for sid in self.sim_ids if str(sid) not in self.shelve]
            if failed_sids:
                print('WARNING ' * 5)
                print('The following (%d) sim ids were not in the shelve, perhaps the jobs failed?' % len(failed_sids))
                print('\n'.join(failed_sids))
                print('-(%d)' % len(failed_sids), '-' * 75)
            self.sim_ids = [sid for sid in self.sim_ids if str(sid) in self.shelve]


            # Not in shelve, need to combine and store in shelve
            selected = [ self.shelve[str(sim_id)]['Data'] for sim_id in self.sim_ids ]
            keys = [ (self.shelve[str(sim_id)]['Sample'], self.shelve[str(sim_id)]['Sim_Id'])
                for sim_id in self.sim_ids ]

            self.data = pd.concat( selected, axis=0,
                                keys=keys,
                                names=['Sample', 'Sim_Id'] )

            self.shelve_combine( { 'Data' : self.data } )

        d = self.data.reset_index()
        self.cache_data['Sim'] = d.where((pd.notnull(d)), None).to_dict(orient='list')

        self.data.sort_index(level='Sample', inplace=True, sort_remaining=True)

        #logger.debug(self.data)


    def compare_age(self, sample):
        # Computation takes mean of log across data points
        LL = 0
        '''
        LL = LL_calculators.beta_binomial(
            raw_nobs = sample['Population'].tolist(),           # raw_nobs
            sim_nobs = sample['Sim_Population_Unscaled'].tolist(),  # sim_nobs
            raw_data = sample['Cases'].tolist(),                # raw_data
            sim_data = sample['Sim_Cases_Unscaled'].tolist()        # sim_data
        )
        '''

        return LL


    def compare(self, sample):
        '''
        Assess the result per sample, in this case the likelihood
        comparison between simulation and reference data.
        '''

        LL = sample.reset_index().groupby(['Sim_Id']).apply(self.compare_age)
        return sum(LL.values)


    def finalize(self):
        super(CasesByAgeAnalyzer, self).finalize() # Closes the shelve file

        '''
        self.result = self.data.groupby(level='Sample').apply(self.compare)
        #self.result.replace(-np.inf, -1e-6, inplace=True)
        self.cache_data['result'] = self.result.to_dict()
        '''

        fn = os.path.join(self.workdir,'Results_%s.xlsx'%self.__class__.__name__)

        writer = pd.ExcelWriter(fn)
        #self.result.to_frame().sort_index().to_excel(writer, sheet_name='Result')
        self.data.to_excel(writer, sheet_name=self.__class__.__name__, merge_cells=False)
        writer.save()

        '''
        f, axes = plt.subplots(1, 1, figsize=(12, 8), sharex=False)
        #sns.despine(left=True)

        d = self.data.reset_index()
        d_by_sample = self.data.reset_index().set_index('Sample')
        n_samples = len(d_by_sample.index.unique())
        #self.result.name = 'LogLikelihood'
        #merged = pd.merge(d_by_sample, self.result.to_frame(), left_index=True, right_index=True).reset_index()

        axes.plot( self.reference['Cases'].values*[1,1], [0,n_samples], 'r-') # , axes=axes[0,0]

        sim_cases_range = self.data.reset_index().groupby('Sample')['Sim_Cases'].agg({'Min':np.min, 'Max':np.max})
        for idx,s in sim_cases_range.iterrows():
            axes.plot( [s['Min'], s['Max']], [idx,idx], 'b-', linewidth=0.5 )
        axes.scatter(d['Sim_Cases'], d['Sample'], c='k', marker='|', alpha=1, linewidths=1)

        plt.autoscale()
        #axes.set_xlim(xmin=-1)
        axes.set_ylim(ymin=0, ymax=n_samples)


        plt.savefig(os.path.join(self.workdir, 'CasesByAge.'+self.fig_format)); plt.close()

        return


        axes[0,1].scatter(merged['LogLikelihood'].values, merged['Sample'].astype(float), c='k', marker='|')

        sns.distplot(d['Sim_Cases'], hist=False, rug=True, color="k", ax=axes[1,0]) #axes[0,1]
        yl = axes[1,0].get_ylim()
        axes[1,0].plot( self.reference['Cases'].values*[1,1], yl, 'r-')
        axes[1,0].set_xlim(xmin=0)

        plt.savefig(os.path.join(self.workdir, 'CasesByAge.'+self.fig_format)); plt.close()
        '''


    def plot(self):
        super(CasesByAgeAnalyzer, self).plot() # plt.show()

    def cache(self):
        return self.cache_data

    def uid(self):
        ''' A unique identifier of site-name and analyzer-name. '''
        return '_'.join([self.site.name, self.name])
