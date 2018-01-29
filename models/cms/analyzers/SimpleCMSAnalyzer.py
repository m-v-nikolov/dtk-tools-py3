import pandas as pd
from io import BytesIO

from simtools.Analysis.BaseAnalyzers import BaseAnalyzer


class SimpleCMSAnalyzer(BaseAnalyzer):

    def __init__(self):
        super(SimpleCMSAnalyzer, self).__init__(filenames=['trajectories.csv'], parse=False)

    def select_simulation_data(self, data, simulation):
        # Transform the data into a normal data frame
        selected = pd.read_csv(BytesIO(data[self.filenames[0]]), skiprows=1, header=None).transpose()
        selected.columns = selected.iloc[0]
        selected = selected.reindex(selected.index.drop(0))
        return selected

    def finalize(self, all_data):
        import matplotlib.pyplot as plt
        for sim, data in all_data.items():
            f = plt.figure()
            a = f.add_subplot(111)
            data.plot(ax=a, x='sampletimes', title=sim.id)

        plt.show()
