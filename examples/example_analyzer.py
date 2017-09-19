from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager


class PopulationAnalyzer(BaseAnalyzer):
    # Defines which filenames we want to retrieve
    filenames = ['output\\InsetChart.json']

    def __init__(self):
        super(PopulationAnalyzer, self).__init__()
        # The pop_data will hold the population mapped to the simulation id
        self.pop_data = {}

    def apply(self, parser):
        # Apply is called for every simulations included into the experiment
        # We are simply storing the population data in the pop_data dictionary
        self.pop_data[parser.sim_id] = parser.raw_data[self.filenames[0]]["Channels"]["Statistical Population"]["Data"]

    def plot(self):
        import matplotlib.pyplot as plt
        map(plt.plot, self.pop_data.values())
        plt.legend(self.pop_data.keys())
        plt.show()


# This code will analyze the latest experiment ran with the PopulationAnalyzer
if __name__ == "__main__":
    am = AnalyzeManager('latest', analyzers=PopulationAnalyzer())
    am.analyze()