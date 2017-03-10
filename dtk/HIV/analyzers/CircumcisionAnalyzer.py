import pandas as pd
import os
import core.utils.stats as stats
from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

MALE = 0

class CircumcisionAnalyzer(BaseAnalyzer):

    def __init__(self,
                 filter_function=lambda md: True,
                 select_function=lambda ts: pd.Series(ts),
                 group_function=lambda k, v: k,
                 alpha=1e-3, verbose=True, output_dir='output'):
        super(CircumcisionAnalyzer, self).__init__()
        self.alpha = alpha
        self.verbose = verbose
        self.output_dir = output_dir
        self.filenames = ['campaign.json', os.path.join( self.output_dir, 'ReportHIVInfection.csv')]
        self.group_function = group_function
        self.filter_function = filter_function
        self.select_function = select_function
        self.data = {}  # observed circumcision
        self.fun = {}   # truth function
        self.results = {} # Place to store the boolean validity and other statistics of sub-tests


    def filter(self, sim_metadata):
        return self.filter_function(sim_metadata)


    def apply(self, parser):
        emit_data = {}

        hiv_infections = parser.raw_data[ self.filenames[1]]    # CSV, has 'data' and 'colMap'
        male_circumcision = hiv_infections[hiv_infections['Gender'] == MALE]['IsCircumcised'].apply(bool)

        # Get target MC from campaign
        campaign = parser.raw_data[ self.filenames[0]]
        circumcision_event_name = 'Male circumcision for initial population'
        target_mc_frac = 0
        found = False
        for e in campaign['Events']:
            if str(e['Event_Name']) == circumcision_event_name:
                target_mc_frac = e["Event_Coordinator_Config"]["Coverage"]
                found = True

        if not found:
            print "WARNING: Did not find campaign event with name '%s', assuming target male circumcision fraction is %f" % (circumcision_event_name, target_mc_frac)

        key = ( id(self), target_mc_frac )
        emit_data[key] = {'MC': male_circumcision}

        return emit_data

    def combine(self, parsers):
        # Accumulate grouped data over parsers
        for k,p in parsers.items():
            # my_items = [ (key,val) for (key,val) in p.emit_data.items() if key[0] == id(self) ]
            my_items = p.selected_data[id(self)].items()

            for (key, val) in my_items:
                target_mc_frac = key[1]

                if target_mc_frac not in self.data:
                    self.data[target_mc_frac] = val['MC']
                else:
                    self.data[target_mc_frac] += val['MC']

        for (target_mc_frac, is_circ) in self.data.items():
            # circ = [ c for c in is_circ if c is True ]
            circ = is_circ[is_circ == True]
            num_circ = len( circ )
            num_males = len( is_circ )

            # Underlying distribution is binomial.  Why using z-test?
# For large samples, can use Pearson's chi-squared test (and the G-test) / Wikipedia

            #self.results[target_mc_frac] = self.ztest( num_circ, num_males, target_mc_frac, self.alpha )
            self.results[target_mc_frac] = stats.binom_test( num_circ, num_males, target_mc_frac, self.alpha )

    def finalize(self):
        if self.verbose:
            print self.results

        each_valid = [y['Valid'] for y in [ self.results[x] for x in self.results]]
        all_valid = all( each_valid )
        print "[ DONE ]"

        return all_valid
