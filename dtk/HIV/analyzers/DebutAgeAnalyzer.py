import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import math
import scipy.stats as sps
import core.utils.stats as stats
from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

MALE = 0
FEMALE = 1
DAYS_PER_YEAR = 365.0
gendernames = ['Male', 'Female']

class DebutAgeAnalyzer(BaseAnalyzer):

    def __init__(self,
                 filter_function=lambda md: True,
                 select_function=lambda ts: pd.Series(ts),
                 group_function=lambda k, v: k,
                 alpha=1e-3, verbose=True, output_dir='output'):
        super(DebutAgeAnalyzer, self).__init__()
        self.alpha = alpha
        self.verbose = verbose
        self.output_dir = output_dir
        self.filenames = ['config.json', os.path.join(self.output_dir, 'ReportHIVInfection.csv')]
        self.group_function = group_function
        self.filter_function = filter_function
        self.select_function = select_function
        self.data = {}  # observed relationship debut_age data by type
        self.fun = {}   # truth function by type
        self.results = {} # Place to store the boolean validity and other statistics of sub-tests


    def apply(self, parser):
        emit_data = {}

        print parser
        hiv_infections = parser.raw_data[ self.filenames[1]]    # CSV, has 'data' and 'colMap'
        rows = hiv_infections[hiv_infections['Year'] == 2020.05481] # filter to year 1 only

        # Extract parameters from config
        config_json = parser.raw_data[ self.filenames[0]]
        cp = config_json['parameters']
        muv = {}
        kapv = {}
        heterogeneity = {}
        scale = {}
        scale[MALE]  = float(cp['Sexual_Debut_Age_Male_Weibull_Scale'])
        heterogeneity[MALE] = float(cp['Sexual_Debut_Age_Male_Weibull_Heterogeneity'])
        scale[FEMALE] = float(cp['Sexual_Debut_Age_Female_Weibull_Scale'])
        heterogeneity[FEMALE] = float(cp['Sexual_Debut_Age_Female_Weibull_Heterogeneity'])

        # kapv[MALE] = 1 / heterogeneity[MALE]
        # muv[MALE] = scale[MALE] * math.gamma(1+1/kapv[MALE])
        # kapv[FEMALE] = 1 / heterogeneity[FEMALE]
        # muv[FEMALE] = scale[FEMALE] * math.gamma(1+1/kapv[FEMALE])
        kapv = 1 / heterogeneity
        muv = scale * math.gamma(1 + 1/kapv)

        for gender in [MALE, FEMALE]:
            gendername = gendernames[gender]

            # Choose rows corresponding to this relationship type
            gender_rows = rows[rows['Gender'] == gender]

            # Get debut_age for each gender_row
            debut_age = gender_rows['DebutAge'].apply(float, True) / DAYS_PER_YEAR

            mu = float(muv[gender])
            kap = float(kapv[gender])
            lam = mu / math.gamma(1+1/kap)
            #z = 1.0+1.0/float(kap)
            #gamma_approx_sterling = math.sqrt(2*math.pi/z) * (1/math.e*(z + 1/(12*z - 1/(10*z))))**z
            #gamma_approx_winschitl = (2.5066282746310002 * math.sqrt(1.0/z) * ((z/math.e) * math.sqrt(z*math.sinh(1/z) + 1/(810*z**6)))**z)
            #lam = mu / gamma_approx_winschitl

            key = ( id(self), gender, lam, kap )
            emit_data[key] = {'DebutAge': debut_age}
            # print emit_data[MALE]
            # print emit_data[FEMALE]

            # Note dummy parameters in the lambda below kapp necessary variable (lam, kap) in scope
            if key not in self.fun:
                self.fun[key] = lambda x, lam=lam, kap=kap: \
                    sps.exponweib(1,kap).cdf([xx/lam for xx in x])

        return emit_data


    def combine(self, parsers):
        # Accumulate grouped data over parsers
        for k,p in parsers.items():
            my_items = p.selected_data[id(self)].items()

            for (key, val) in my_items:

                if key not in self.data:
                    self.data[key] = np.array(val['DebutAge'])
                else:
                    self.data[key] = np.hstack( self.data[key], np.array(val['DebutAge']) )

        # Now do the stat analysis
        for (key, debut_age) in self.data.items():
            # (gender, lam, kap) = key[1:4]

            self.results[key] = stats.kstest(debut_age, self.fun[key], self.alpha, )

            if self.verbose:
                if self.results[key]['Valid']:
                    print "Sub-test for " + str(key) + " passed."
                    print self.results[key]
                else:
                    print "Sub-test for " + str(key) + " failed."
                    print self.results[key]

    def plot_figure(self):
        fig = plt.figure(self.__class__.__name__, figsize=(10, 5))
        ncols = len(self.fun)

        idx = 0
        for key, debut_age in self.data.items():
            (gender, lam, kap) = key[1:4]
            gendername = gendernames[gender]

            plt.subplot(1, ncols, idx + 1)

            x = sorted(debut_age)
            y = [i / float(len(debut_age)) for i in range(0, len(debut_age))]

            plt.plot(x, y)

            y_true = self.fun[key](x)
            plt.plot(x, y_true, linestyle="dashed")

            valid_str = {True: "PASS", False: "FAIL"}
            plt.title(
                "%s: %s (p=%0.2f)" % (gendername, valid_str[self.results[key]['Valid']], self.results[key]['P_Value']))
            idx = idx + 1

        fig.tight_layout()
        print "[ DONE ]"

    def finalize(self):
        self.plot_figure()
        pass
