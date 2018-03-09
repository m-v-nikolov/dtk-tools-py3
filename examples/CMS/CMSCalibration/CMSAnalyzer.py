import io

import pandas as pd

from calibtool.LL_calculators import euclidean_distance
from simtools.Analysis.BaseAnalyzers import BaseCalibrationAnalyzer


class CMSAnalyzer(BaseCalibrationAnalyzer):

    def __init__(self, reference_data):
        super().__init__(filenames = ['trajectories.csv'], reference_data=reference_data, parse=False)

    def select_simulation_data(self, sim_data, simulation):
        # Transform the data into a normal data frame
        data = pd.read_csv(io.BytesIO(sim_data[self.filenames[0]]), skiprows=1, header=None).transpose()
        data.columns = data.iloc[0]
        data = data.reindex(data.index.drop(0))

        # Calculate the ratios needed for comparison with the reference data
        ratio_SI_10 = 0 if data["smear-positive{0}"][10] == 0 else data["susceptible{0}"][10]/data["smear-positive{0}"][10]
        ratio_SI_100 = 0 if data["smear-positive{0}"][100] == 0 else data["susceptible{0}"][100]/data["smear-positive{0}"][100]

        # Returns the data needed for this simulation
        return {
            "sample_index": simulation.tags.get('__sample_index__'),
            "ratio_SI_10": ratio_SI_10,
            "ratio_SI_100": ratio_SI_100
        }

    def finalize(self, all_data):
        lls = []
        # Sort our data by sample_index
        # We need to preserve the order by sample_index
        # Calculate the Log Likelihood by comparing the simulated data with the reference data and computing the
        # euclidean distance
        for d in sorted(all_data.values(), key=lambda k: k['sample_index']):
            lls.append(euclidean_distance(list(self.reference_data.values()), [d[k] for k in self.reference_data.keys()]))

        return pd.Series(lls)

