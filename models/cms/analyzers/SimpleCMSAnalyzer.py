from StringIO import StringIO

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer


class SimpleCMSAnalyzer(BaseAnalyzer):
    filenames = ['trajectories.csv']

    def apply(self, parser):
        import pandas as pd

        # Transform the data into a normal data frame
        data = pd.read_csv(StringIO(parser.raw_data[self.filenames[0]]), skiprows=1, header=None).transpose()
        data.columns = data.iloc[0]
        data = data.reindex(data.index.drop(0))

        # Store
        self.data = data

    def plot(self):
        import matplotlib.pyplot as plt
        self.data.plot(x='sampletimes')
        plt.show()

    def __init__(self):
        super(SimpleCMSAnalyzer, self).__init__()
        self.data = None
        self.parse = False

