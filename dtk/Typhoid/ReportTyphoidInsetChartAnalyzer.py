import os
import sys
import logging

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from dtk.utils.analyzers.BaseShelveAnalyzer import BaseShelveAnalyzer

logger = logging.getLogger(__name__)

class ReportTyphoidInsetChartAnalyzer(BaseShelveAnalyzer):
    def __init__(self,
                max_sims_to_process = -1,
                pop_scaling_year = [1975, 1976], #1975.997,
                pop_scaling_pop = 3782716,
                force_apply = False,
                force_combine = False,
                basedir = 'Work',
                fig_format = 'png',
                fig_dpi = 600,
                verbose = False):

        super(ReportTyphoidInsetChartAnalyzer, self).__init__(force_apply, force_combine, verbose)

        # For pop scaling - would rather get from PopulationScalingAnalyzer!
        self.pop_scaling_year = pop_scaling_year
        self.pop_scaling_pop = pop_scaling_pop

        # Set to -1 to process all:
        self.max_sims_to_process = max_sims_to_process

        self.filenames = [ os.path.join('output', 'InsetChart.json') ]
        self.basedir = basedir
        self.fig_format = fig_format
        self.fig_dpi = fig_dpi
        self.verbose = verbose

        self.sim_ids = []
        self.count = 0
        self.num_outstanding = 0

    def initialize(self):
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

        ret = super(ReportTyphoidInsetChartAnalyzer, self).filter(self.shelve_file, sim_metadata)

        if not ret and self.verbose:
            self.num_outstanding -= 1
            print 'Skipping simulation %s because already in shelve' % str(sim_id)

        return ret

    def apply(self, parser):
        super(ReportTyphoidInsetChartAnalyzer, self).apply(parser)

        raw = parser.raw_data[self.filenames[0]]
        self.header = raw['Header']
        assert('Simulation_Timestep' and 'Start_Time' and 'Report_Start_Year' and 'Report_Stop_Year' and 'Timesteps' in self.header)

        import datetime as DT
        def t2dt(atime):
            """
            Convert atime (a float) to DT.datetime
            This is the inverse of dt2t.
            assert dt2t(t2dt(atime)) == atime
            """
            year = int(atime)
            remainder = atime - year
            boy = DT.datetime(year, 1, 1)
            eoy = DT.datetime(year + 1, 1, 1)
            seconds = remainder * (eoy - boy).total_seconds()
            t = boy + DT.timedelta(seconds=seconds)
            return t.strftime('%Y%m%d')

        icstart = t2dt(self.header['Report_Start_Year'])

        assert(self.header['Simulation_Timestep'] == 1)
        # Using real date:
        '''
        pdata = pd.DataFrame(index=pd.date_range(icstart,periods=self.header['Timesteps'],freq='D'))
        pdata.index.name = 'Date'
        pdata.reset_index(inplace=True)

        pdata['Month'] = pd.Categorical(pdata['Date'].map(lambda x: x.strftime('%B')).astype('category'), categories=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], ordered=True)

        pdata['Year'] = pdata['Date'].map(lambda x: x.strftime('%Y')).astype(int)
        pdata.set_index('Date', inplace=True)
        '''

        # Using simple day of year:
        pdata = pd.DataFrame(index=np.arange(self.header['Timesteps']))
        pdata.index.name = 'SimDay'
        pdata.reset_index(inplace=True)
        pdata['DayOfYear'] = pdata['SimDay'] % 365 # TODO: Assuming Start_Day is at beginning of year!
        pdata['Month'] = pd.cut(pdata['DayOfYear'], [d-1 for d in [0,31,59,90,120,151,181,212,243,273,304,334,365]],labels=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])

        assert(self.header['Report_Start_Year'] == np.floor(self.header['Report_Start_Year']))
        pdata['Year'] = np.floor(self.header['Report_Start_Year'] + pdata['SimDay']/365).astype(int)

        for ch in raw['Channels']:
            pdata[ch] = raw['Channels'][ch]['Data']

        ### POP SCALING #######################################################
        sim_pop  = pdata.query('Year >= @self.pop_scaling_year[0] & Year < @self.pop_scaling_year[1]')[['Statistical Population']].sum()/365

        pop_scaling = self.pop_scaling_pop / float(sim_pop)
        possible_scale_cols = ['Environmental Contagion Population',
                'Number of New Acute Infections',
                'Statistical Population',
                'Contact Contagion Population',
                'Infected',
                'Number of Chronic Carriers',
                'Number of New Sub-Clinical Infections',
                'New Infections By Route (CONTACT)',
                'New Infections By Route (ENVIRONMENT)']
        scale_cols = [ sc for sc in possible_scale_cols if sc in pdata.columns.values]
        pdata[scale_cols] *= pop_scaling
        #######################################################################

        self.num_outstanding -= 1
        if self.verbose:
            print 'Progress: %d of %d (%.1f%%).  Pop scaling is %f'%(len(self.sim_ids)-self.num_outstanding, len(self.sim_ids), 100*(len(self.sim_ids)-self.num_outstanding) / float(len(self.sim_ids)), pop_scaling)

        return (pdata, pop_scaling)

    def combine(self, parsers):
        return super(ReportTyphoidInsetChartAnalyzer, self).combine(parsers)

    def finalize(self):
        if self.verbose:
            print "finalize"

        super(ReportTyphoidInsetChartAnalyzer, self).finalize() # Closes the shelve file
        self.sim_ids = []
        self.count = 0

        sns.set_style("whitegrid")

    def plot(self):
        plt.show()
        print "[ DONE ]"
