import json

import pandas as pd

from calibtool.LL_calculators import euclidean_distance
from calibtool.analyzers.BaseComparisonAnalyzer import BaseComparisonAnalyzer


class CMSAnalyzer(BaseComparisonAnalyzer):
    filenames = ['trajectories.csv']

    def __init__(self, site):
        super().__init__(site)
        self.parse = False
        self.reference = self.site.get_reference_data()

    def initialize(self):
        self.result = None
        self.data = []

    def apply(self, parser):
        # Transform the data into a normal data frame
        data = pd.read_csv(parser.raw_data[self.filenames[0]], skiprows=1, header=None).transpose()
        data.columns = data.iloc[0]
        data = data.reindex(data.index.drop(0))

        # Calculate the ratios needed for comparison with the reference data
        ratio_SI_10 = 0 if data["smear-positive{0}"][10] == 0 else data["susceptible{0}"][10]/data["smear-positive{0}"][10]
        ratio_SI_100 = 0 if data["smear-positive{0}"][100] == 0 else data["susceptible{0}"][100]/data["smear-positive{0}"][100]

        # Returns the data needed for this simulation
        return {
            "sample_index": parser.sim_data.get('__sample_index__'),
            "sim_id": parser.sim_id,
            "ratio_SI_10": ratio_SI_10,
            "ratio_SI_100": ratio_SI_100
        }

    def combine(self, parsers):
        # Collect all the data for all the simulations
        for p in parsers.values():
            self.data.append(p.selected_data[id(self)])

        # Sort our data by sample_index
        # We need to preserve the order by sample_index
        self.data = sorted(self.data, key=lambda k: k['sample_index'])

    def finalize(self):
        lls = []

        # Calculate the Log Likelihood by comparing the simulated data with the reference data and computing the
        # euclidean distance
        for d in self.data:
            lls.append(euclidean_distance(list(self.reference.values()), [d[k] for k in self.reference.keys()]))

        # Result needs to be a series where the index is the sample_index and the value the likelihood for this sample
        self.result = pd.Series(lls)

    def cache(self):
        return json.dumps(self.data)
