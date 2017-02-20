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

class TotalCasesAnalyzer(ReportTyphoidByAgeAndGenderAnalyzer):

    def __init__(self,
                    name,
                    reference_sheet,

                    #iteration = 0,
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

        super(TotalCasesAnalyzer, self).__init__( max_sims_to_process, pop_scaling_year, pop_scaling_pop, pop_scaling_age_min, pop_scaling_age_max, force_apply, force_combine, basedir, fig_format, fig_dpi, verbose)

        self.name = name
        self.reference_sheet = reference_sheet

        #self.iteration = iteration

        self.cache_data = {}

    def set_site(self, site):
        self.reference = site.reference_data[self.reference_sheet].set_index(['YearBin', 'AgeBin'])

        self.year_bins = self.reference.index.get_level_values('YearBin').unique()
        self.age_bins = self.reference.index.get_level_values('AgeBin').unique()

        self.cache_data['reference'] = self.reference.reset_index().to_dict(orient='list')


    def filter(self, sim_metadata):
        return super(TotalCasesAnalyzer, self).filter(sim_metadata)

    def lower_value(self, agebin): # For age-bin sorting
        return [int(s) for s in re.findall(r'\b\d+\b', agebin)][0]

    def apply(self, parser):
        '''
        Extract data from output data and accumulate in same bins as reference.
        '''
        sim = super(TotalCasesAnalyzer, self).apply(parser)
        if self.verbose:
            print 'Population scaling factor is', self.pop_scaling

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
                simbin['Sim_Cases_Unscaled'] = simbin['Sim_Cases'] / self.pop_scaling # Note: pop_scaling comes from parent
                simbin.rename(index={'Population':'Sim_Population'}, inplace=True)
                simbin['Sim_Population_Unscaled'] = simbin['Sim_Population'] / self.pop_scaling

                err = simbin['Sim_Population']-self.pop_scaling_pop
                #if abs(err) > 1e-6:
                print parser.sim_id, 'RawPop =', simbin['Sim_Population_Unscaled'], 'PopScale =', self.pop_scaling, 'ScaledSimPop =', simbin['Sim_Population'], 'Err =', err

                #assert( abs(simbin['Sim_Population']-self.pop_scaling_pop)<1e-6 )

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
            'Pop_Scaling': self.pop_scaling # From base class
        }
        self.shelve_apply( parser.sim_id, shelve_data)

        if self.verbose:
            print "size (MB):", sys.getsizeof(shelve_data)/8.0/1024.0

    def combine(self, parsers):
        shelved_data = super(TotalCasesAnalyzer, self).combine(parsers)

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

            self.shelve_combine( { 'Data' : self.data } )

        d = self.data.reset_index()
        self.cache_data['Sim'] = d.where((pd.notnull(d)), None).to_dict(orient='list')

        logger.debug(self.data)


    def compare_age(self, sample):
        # Computation takes mean of log across data points
        LL = LL_calculators.beta_binomial(
            raw_nobs = sample['Ref_Population'].tolist(),           # raw_nobs
            sim_nobs = sample['Sim_Population_Unscaled'].tolist(),  # sim_nobs
            raw_data = sample['Ref_Cases'].tolist(),                # raw_data
            sim_data = sample['Sim_Cases_Unscaled'].tolist()        # sim_data
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
        super(TotalCasesAnalyzer, self).finalize() # Closes the shelve file

        self.result = self.data.groupby(level='Sample').apply(self.compare)
        #self.result.replace(-np.inf, -1e-6, inplace=True)
        self.cache_data['result'] = self.result.to_dict()

        writer = pd.ExcelWriter(os.path.join(self.workdir,'Results.xlsx'))
        #self.result.to_frame().sort_index().to_excel(writer, sheet_name='Result')
        self.data.to_excel(writer, sheet_name=self.__class__.__name__)
        writer.save()

        f, axes = plt.subplots(1, 1, figsize=(12, 8), sharex=False)
        #sns.despine(left=True)

        d = self.data.reset_index()
        d_by_sample = self.data.reset_index().set_index('Sample')
        n_samples = len(d_by_sample.index.unique())
        self.result.name = 'LogLikelihood'
        merged = pd.merge(d_by_sample, self.result.to_frame(), left_index=True, right_index=True).reset_index()

        axes.plot( self.reference['Ref_Cases'].values*[1,1], [0,n_samples], 'r-') # , axes=axes[0,0]

        sim_cases_range = self.data.reset_index().groupby('Sample')['Sim_Cases'].agg({'Min':np.min, 'Max':np.max})
        for idx,s in sim_cases_range.iterrows():
            axes.plot( [s['Min'], s['Max']], [idx,idx], 'b-', linewidth=0.5 )
        axes.scatter(d['Sim_Cases'], d['Sample'], c='k', marker='|', alpha=1, linewidths=1)

        # TODO: Vectorize
        '''
        for idx,s in d.iterrows():
            k = s['Ref_Cases']
            n = s['Ref_Population']
            a = s['Sim_Cases_Unscaled']+1
            b = s['Sim_Population_Unscaled']+1

            mean = n*a / (a+b)
            var = n*a*b*(a+b+n) / ((a+b)**2 * (a+b+1))

            axes[0].errorbar(s['Sim_Cases'], int(float(s['Sample'])), xerr=2*np.sqrt(var), marker='|', markersize=20, ecolor='k', mew=1)
        '''
        plt.autoscale()
        #axes.set_xlim(xmin=-1)
        axes.set_ylim(ymin=0, ymax=n_samples)


        plt.savefig(os.path.join(self.workdir, 'TotalCases.'+self.fig_format)); plt.close()

        return


        axes[0,1].scatter(merged['LogLikelihood'].values, merged['Sample'].astype(float), c='k', marker='|')

        sns.distplot(d['Sim_Cases'], hist=False, rug=True, color="k", ax=axes[1,0]) #axes[0,1]
        yl = axes[1,0].get_ylim()
        axes[1,0].plot( self.reference['Ref_Cases'].values*[1,1], yl, 'r-')
        axes[1,0].set_xlim(xmin=0)

        plt.savefig(os.path.join(self.workdir, 'TotalCases.'+self.fig_format)); plt.close()

        '''
        writer = pd.ExcelWriter('TotalCases.xlsx')
        self.data.to_excel(writer,'Data')
        self.result.to_frame(name='Result').to_excel(writer,'Result')
        writer.save()

        from Map import Map

        calib_manager = Map()
        calib_manager.iteration = self.iteration
        calib_manager.iteration_state = Map()
        calib_manager.iteration_state['analyzers'] = {}
        calib_manager.iteration_state.analyzers['Santiago_TotalCases'] = self.cache()

        p = TotalCasesPlotter(combine_sites=True)
        p.visualize(calib_manager)
        '''


    def plot(self):
        super(TotalCasesAnalyzer, self).plot() # plt.show()

    def cache(self):
        return self.cache_data

    def uid(self):
        ''' A unique identifier of site-name and analyzer-name. '''
        return '_'.join([self.site.name, self.name])
