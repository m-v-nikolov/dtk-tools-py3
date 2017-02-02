import os
import sys
import logging

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from dtk.utils.analyzers.BaseShelveAnalyzer import BaseShelveAnalyzer

logger = logging.getLogger(__name__)

class ReportHIVByAgeAndGenderAnalyzer(BaseShelveAnalyzer):
    count = {}
    skipped_interventions = []

    # For computing person-years, ASSUMING 6-monthly REPORTING INTERVAL! (Could read from config.json or elsewhere)
    report_timestep_in_years = 0.5
    prevalent_cols = ['Population', 'Infected', 'On_ART','HasIntervention(EffectivePrEP)']

    def __init__(self,
                max_sims_per_scenario = -1,
                reference_year = 2012.5,
                reference_population = 6269676,
                age_min = 15,
                age_max = 50,
                start_year = 2017,
                node_map = {},
                node_order = None,
                intervention_subset = None,
                force_apply = False,
                force_combine = False,
                basedir = 'Work',
                fig_format = 'png',
                fig_dpi = 600,
                verbose = False,
                parse = True,
                **kwargs):

        self.parse = parse

        super(ReportHIVByAgeAndGenderAnalyzer, self).__init__(force_apply, force_combine, verbose)

        # For pop scaling - would rather get from PopulationScalingAnalyzer!
        self.reference_year = reference_year
        self.reference_population = reference_population
        self.age_min = age_min
        self.age_max = age_max

        # Set to -1 to process all:
        self.max_sims_per_scenario = max_sims_per_scenario

        # Set to None to process all interventions, or pass a list of intervention names
        self.intervention_subset = intervention_subset

        self.start_year = start_year

        # Map from NodeId to Name - would rather get from a NodeListAnalyzer that reads Demographics.json for one simulation
        self.node_map = node_map

        self.node_order = node_order    # Can be None

        self.filenames = [ os.path.join('output', 'ReportHIVByAgeAndGender.csv') ]
        self.basedir = basedir
        self.fig_format = fig_format
        self.fig_dpi = fig_dpi
        self.verbose = verbose

        logger.info(self.__class__.__name__ + " writing to " + self.basedir) # TODO

        self.sim_ids = []

        if not os.path.isdir(self.basedir):
            os.makedirs(self.basedir)

    def filter(self, sim_metadata):
        self.workdir = os.path.join(self.basedir, self.exp_id)
        if not os.path.isdir(self.workdir):
            os.makedirs(self.workdir)

        self.figdir = os.path.join(self.workdir, self.__class__.__name__)
        if not os.path.isdir(self.figdir):
            os.makedirs(self.figdir)

        scenario = sim_metadata['Scenario']

        # SELECT BY SCENARIO ##################################################
        if self.intervention_subset is not None:
            if '_' in scenario:
                tok = scenario.split('_')
                intervention = '_'.join(tok[1:])

                if intervention != 'Baseline' and intervention not in self.intervention_subset:
                    if intervention not in self.skipped_interventions:
                        self.skipped_interventions.append( intervention )
                    if self.verbose:
                        print 'Skipping', scenario
                    return False
        #######################################################################

        # SELECT A LIMITED NUMBER #############################################
        if scenario not in self.count:
            self.count[scenario] = 1
        else:
            self.count[scenario] += 1

        if self.max_sims_per_scenario > 0 and self.count[scenario] > self.max_sims_per_scenario: # Take only a few of each scenario
            return False
        #######################################################################

        sim_id = sim_metadata['sim_id']
        self.sim_ids.append(sim_id)

        if not self.shelve_file:    # Want this in the base class, but don't know exp_id at __init__
            self.shelve_file = os.path.join(self.workdir, '%s.db' % self.__class__.__name__) # USE ID instead?

        ret = super(ReportHIVByAgeAndGenderAnalyzer, self).filter(self.shelve_file, sim_metadata)

        if not ret and self.verbose:
            print 'Skipping simulation %s because already in shelve' % str(sim_id)

        return ret

    def apply(self, parser, add_both_level_to_gender=True):
        super(ReportHIVByAgeAndGenderAnalyzer, self).apply(parser)

        # Sum over age and other factors to make the data smaller
        raw = parser.raw_data[self.filenames[0]]

        if 'HasIntervention:EffectivePrEP' in raw.columns.values:
            if self.verbose:
                print 'Computing HasIntervention(EffectivePrEP) from HasIntervention:EffectivePrEP'
            pdata_intv = raw.copy().groupby([ 'HasIntervention:EffectivePrEP', 'Year', 'NodeId', 'Age', 'Gender', 'IP_Key:Risk']).sum()
            pdata = raw.copy().groupby([ 'Year', 'NodeId', 'Age', 'Gender', 'IP_Key:Risk']).sum()
            pdata['HasIntervention(EffectivePrEP)'] = pdata_intv.loc[1]['Population']

            pdata.reset_index(inplace=True)
        else:
            pdata = raw.copy()

        ### POP SCALING #######################################################
        ps = pdata.copy().set_index('Year')#.query('Year == @self.reference_year')
        assert( self.reference_year in ps.index.unique() )

        sim_pop = pdata.copy().groupby(['Year', 'Age'])['Population'].sum().loc[self.reference_year].loc[self.age_min:self.age_max].sum()

        pop_scaling = self.reference_population / float(sim_pop)
        if self.verbose:
            print 'Population scaling is', pop_scaling
        scale_cols = [sc for sc in ['Population', 'Infected', 'Newly Infected', 'On_ART', 'Died', 'Died_from_HIV', 'Transmitters', 'HasIntervention(EffectivePrEP)', 'Received_PrEP'] if sc in pdata.columns]

        pdata[scale_cols] *= pop_scaling
        #######################################################################

        ### ANNUALIZATION #####################################################
        # Compute person-years
        prevalent_cols = [pc for pc in self.prevalent_cols if pc in pdata.columns]
        py_cols = [ col + ' (PY)' for col in prevalent_cols ]
        for col, py_col in zip(prevalent_cols, py_cols):
            pdata[py_col] = self.report_timestep_in_years * pdata[col]
        #######################################################################

        keep_cols = [kc for kc in ['Year', 'Gender', 'NodeId', 'IP_Key:Risk', 'Age', 'Population', 'Infected', 'Newly Infected', 'On_ART', 'Died', 'Died_from_HIV', 'Received_PrEP', 'Transmitters', 'HasIntervention(EffectivePrEP)', 'Diagnosed'] if kc in pdata.columns]
        keep_cols += py_cols
        drop_cols = list( set(pdata.columns.values) - set(keep_cols) )
        pdata.drop(drop_cols, axis=1, inplace=True)

        pdata.rename(columns={'IP_Key:Risk':'Risk', 'NodeId':'Province'}, inplace=True)

        pdata = pdata.reset_index(drop=True).set_index('Province')
        pdata.rename(self.node_map, inplace=True)
        pdata = pdata.reset_index().set_index('Gender')
        pdata.rename({0:'Male', 1:'Female'}, inplace=True)
        pdata.reset_index(inplace=True)

        # Make "Both" gender col in case data are not gender disaggregated
        if add_both_level_to_gender:
            pdata.set_index(['Gender', 'Province', 'Year', 'Risk', 'Age'], inplace=True)
            both = pdata.loc['Male'] + pdata.loc['Female']
            both['Gender'] = 'Both'
            both = both.reset_index().set_index(['Gender', 'Province', 'Year', 'Risk', 'Age'])
            pdata = pd.concat([pdata, both])
            pdata.reset_index(inplace=True)

        return {'Data':pdata, 'Pop_Scaling':pop_scaling}

    def combine(self, parsers):
        if self.verbose:
            print "combine"

        if self.verbose and self.skipped_interventions:
            print '*'*80
            print 'The following interventions were skipped:'
            print self.skipped_interventions
            print '*'*80

        return super(ReportHIVByAgeAndGenderAnalyzer, self).combine(parsers)

    def finalize(self):
        if self.verbose:
            print "finalize"

        super(ReportHIVByAgeAndGenderAnalyzer, self).finalize() # Closes the shelve file
        self.sim_ids = []

        sns.set_style("whitegrid")

    def plot(self):
        plt.show()
        print "[ DONE ]"
