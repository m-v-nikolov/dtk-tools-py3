import os
import sys
import logging

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from dtk.utils.analyzers.BaseShelveAnalyzer import BaseShelveAnalyzer

logger = logging.getLogger(__name__)

class ReportTyphoidByAgeAndGenderAnalyzer(BaseShelveAnalyzer):
    def __init__(self,
                max_sims_to_process = -1,
                pop_scaling_year = [1975, 1976], #1975.997,
                pop_scaling_pop = 3782716,
                pop_scaling_age_min = 0,
                pop_scaling_age_max = 100,
                force_apply = False,
                force_combine = False,
                basedir = 'Work',
                fig_format = 'png',
                fig_dpi = 600,
                verbose = False):

        super(ReportTyphoidByAgeAndGenderAnalyzer, self).__init__(force_apply, force_combine, verbose)

        # For pop scaling - would rather get from PopulationScalingAnalyzer!
        self.pop_scaling_year = pop_scaling_year
        self.pop_scaling_pop = pop_scaling_pop
        self.pop_scaling_age_min = pop_scaling_age_min
        self.pop_scaling_age_max = pop_scaling_age_max

        # Set to -1 to process all:
        self.max_sims_to_process = max_sims_to_process

        self.filenames = [ os.path.join('output', 'ReportTyphoidByAgeAndGender.csv') ]
        self.basedir = basedir
        self.fig_format = fig_format
        self.fig_dpi = fig_dpi
        self.verbose = verbose

        self.sim_ids = []
        self.count = 0

        self.num_outstanding = 0

        if not os.path.isdir(self.basedir):
            os.makedirs(self.basedir)

    def filter(self, sim_metadata):
        self.workdir = os.path.join(self.basedir, self.exp_id)
        if not os.path.isdir(self.workdir):
            os.makedirs(self.workdir)

        self.figdir = os.path.join(self.workdir, self.__class__.__name__)
        if not os.path.isdir(self.figdir):
            os.makedirs(self.figdir)

        # SELECT A LIMITED NUMBER #############################################
        if self.max_sims_to_process > 0 and self.count >= self.max_sims_to_process: # Take only a few of each scenario
            return False
        self.count += 1
        #######################################################################

        sim_id = sim_metadata['sim_id']
        self.sim_ids.append(sim_id)
        self.num_outstanding += 1

        if not self.shelve_file:    # Want this in the base class, but don't know exp_id at __init__
            self.shelve_file = os.path.join(self.workdir, '%s.db' % self.__class__.__name__) # USE ID instead?

        ret = super(ReportTyphoidByAgeAndGenderAnalyzer, self).filter(self.shelve_file, sim_metadata)

        if not ret and self.verbose:
            self.num_outstanding -= 1
            print('Skipping simulation %s because already in shelve' % str(sim_id))

        return ret

    def apply(self, parser):
        super(ReportTyphoidByAgeAndGenderAnalyzer, self).apply(parser)


        # Sum over age and other factors to make the data smaller
        raw = parser.raw_data[self.filenames[0]]
        pdata = raw.copy().rename(columns={'Time Of Report (Year)':'Year'})

        ### POP SCALING #######################################################
        ps = pdata.copy().query('Year >= @self.pop_scaling_year[0] & Year < @self.pop_scaling_year[1]').groupby('Age')[['Population']].sum()
        sim_pop = ps.loc[self.pop_scaling_age_min:self.pop_scaling_age_max].sum()

        pop_scaling = self.pop_scaling_pop / float(sim_pop)

        possible_scale_cols = ['Population', 'Infected', 'Newly Infected', 'Chronic (Prev)',
                        'Sub-Clinical (Prev)', 'Acute (Prev)', 'Pre-Patent (Prev)',
                        'Chronic (Inc) ', 'Sub-Clinical (Inc)', 'Acute (Inc)',
                        'Pre-Patent (Inc)']
        scale_cols = [ sc for sc in possible_scale_cols if sc in pdata.columns.values]
        pdata[scale_cols] *= pop_scaling
        #######################################################################

        self.num_outstanding -= 1
        if self.verbose:
            print('Progress: %d of %d (%.1f%%).  Pop scaling is %f' % (
            len(self.sim_ids) - self.num_outstanding, len(self.sim_ids),
            100 * (len(self.sim_ids) - self.num_outstanding) / float(len(self.sim_ids)), pop_scaling))

        pdata = pdata.reset_index(drop=True).set_index('Gender')
        pdata.rename({0:'Male', 1:'Female'}, inplace=True)
        pdata.reset_index(inplace=True)

        return (pdata, pop_scaling)

    def combine(self, parsers):
        return super(ReportTyphoidByAgeAndGenderAnalyzer, self).combine(parsers)

    def finalize(self):
        if self.verbose:
            print("finalize")

        super(ReportTyphoidByAgeAndGenderAnalyzer, self).finalize() # Closes the shelve file
        self.sim_ids = []
        self.count = 0

        sns.set_style("whitegrid")

    def plot(self):
        plt.show()
        print("[ DONE ]")
