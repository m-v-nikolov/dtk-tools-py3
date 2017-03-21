import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import logging
import os
import math
import core.utils.stats as stats

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer
from enum import Enum

class RelationshipType(Enum):
    TRANSITORY = 0
    INFORMAL = 1
    MARITAL = 2
REL_NAMES = {RelationshipType.TRANSITORY: 'Transitory', RelationshipType.INFORMAL: 'Informal', RelationshipType.MARITAL: 'Marital'}
DAYS_PER_YEAR = 365

logger = logging.getLogger(__name__)

def default_plot_fn(df, ax):
    grouped = df.groupby(level=['group'], axis=1)
    m = grouped.mean()
    m.plot(ax=ax, legend=True)


# a class to analyze relationship durations
class RelationshipDurationAnalyzer(BaseAnalyzer):

    def __init__(self,
                 filter_function=lambda md: True,
                 select_function=lambda ts: pd.Series(ts),
                 group_function=lambda k, v: k,
                 alpha=1e-3, verbose=True, output_dir='output'):
        super(RelationshipDurationAnalyzer, self).__init__()
        self.alpha = alpha
        self.verbose = verbose
        self.output_dir = output_dir
        self.filenames = [os.path.join( self.output_dir, 'RelationshipStart.csv'), 'config.json', '../input/PFA_overlay.json']
        self.group_function = group_function
        self.filter_function = filter_function
        self.select_function = select_function

        self.data = {}  # observed relationship duration data by type
        self.fun = {}   # truth function by type
        self.results = {} # Place to store the boolean validity and other statistics of sub-tests

        for reltype in [RelationshipType.TRANSITORY, RelationshipType.INFORMAL, RelationshipType.MARITAL]:
            relname = REL_NAMES[reltype]
            self.results[relname] = {}

    def filter(self, sim_metadata):
        return self.filter_function(sim_metadata)

    def apply(self, parser):
        emit_data = {}

        print parser
        rel_start = parser.raw_data[ self.filenames[0] ]    # CSV, has 'data' and 'colMap'

        # Extract parameters from config
        config_json = parser.raw_data[ self.filenames[1] ]
        cp = config_json['parameters']
        pfa_overlay_json = parser.raw_data[ self.filenames[2] ]
        pfap = pfa_overlay_json['Defaults']['Society']
        scale = {r: pfap[REL_NAMES[r].upper()]['Relationship_Parameters']['Duration_Weibull_Scale'] for r in RelationshipType}
        heterogeneity = {r: pfap[REL_NAMES[r].upper()]['Relationship_Parameters']['Duration_Weibull_Heterogeneity'] for
                         r in RelationshipType}
        kapv = {k: 1 / v for k, v in heterogeneity.iteritems()}
        muv = {k: scale[k] * math.gamma(1+1/v) for k, v in kapv.iteritems()}

        for reltype in [RelationshipType.TRANSITORY, RelationshipType.INFORMAL, RelationshipType.MARITAL]:
            relname = REL_NAMES[reltype]

            # Choose rows corresponding to this relationship type
            type_rows = rel_start[rel_start['Rel_type'] == reltype.value]

            # Get relationship duration for each type_row
            duration = type_rows['Rel_scheduled_end_time'].apply(float, True) - type_rows['Rel_start_time'].apply(float, True)

            mu = DAYS_PER_YEAR * muv[reltype]
            kap = kapv[reltype]
            lam = mu / math.gamma(1+1/kap)

            if self.verbose:
                print "Rel type: " + relname + ": lam=" + str(lam/DAYS_PER_YEAR) + " kap=" + str(kap) + " mu=" + str(mu/DAYS_PER_YEAR)

            key = ( id(self), reltype, lam, kap )
            emit_data[key] = {'Duration': duration}

        return emit_data

    def combine(self, parsers):
        # Accumulate grouped data over parsers
        for k,p in parsers.items():
            # my_items = [ (key,val) for (key,val) in p.emit_data.items() if key[0] == id(self) ]
            my_items = p.selected_data[id(self)].items()

            for (key, val) in my_items:
                if key not in self.data:
                    self.data[key] = np.array(val['Duration'])
                # else:
                #     self.data[key] = np.hstack( self.data[relname], np.array(val['Duration']) )

        # Now do the stat analysis
        for (key, duration) in self.data.items():
            (reltype, lam, kap) = key[1:4]
            relname = REL_NAMES[reltype]

            # Note dummy parameters in the lambda below kapp necessary variable (lam, kap) in scope
            self.fun[relname] = lambda x, lam=lam, kap=kap: stats.weib_cdf(x, lam, kap)

            self.results[relname] = stats.kstest(duration, self.fun[relname], self.alpha, )

            if self.verbose:
                if self.results[relname]['Valid']:
                    print "Sub-test for " + relname + " passed."
                    print self.results[relname]
                else:
                    print "Sub-test for " + relname + " failed."
                    print self.results[relname]


    def plot_figure(self):
        fig = plt.figure('Relationship Duration', figsize=(10, 5))
        ncols = len(REL_NAMES)

        idx = 0
        for key, duration in self.data.items():
            (reltype, lam, kap) = key[1:4]
            relname = REL_NAMES[reltype]

            plt.subplot(1, ncols, idx + 1)

            x = sorted(duration)
            y = [i / float(len(duration)) for i in range(0, len(duration))]

            plt.plot(x, y)

            y_true = self.fun[relname](x)
            plt.plot(x, y_true, linestyle="dashed")

            valid_str = {}
            valid_str[True] = "PASS"
            valid_str[False] = "FAIL"
            plt.title("%s: %s (p=%0.2f)" % (
            relname, valid_str[self.results[relname]['Valid']], self.results[relname]['P_Value']))
            idx = idx + 1

        fig.tight_layout()
        print "[ DONE ]"


    def finalize(self):
        self.plot_figure()


