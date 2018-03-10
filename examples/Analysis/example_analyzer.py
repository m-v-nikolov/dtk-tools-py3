from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.Analysis.BaseAnalyzers import BaseAnalyzer



class PopulationAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(filenames=['output\\InsetChart.json'])

    def select_simulation_data(self, data, simulation):
        # Apply is called for every simulations included into the experiment
        # We are simply storing the population data in the pop_data dictionary
        return data[self.filenames[0]]["Channels"]["Statistical Population"]["Data"]

    def finalize(self, all_data):
        import matplotlib.pyplot as plt
        for pop in list(all_data.values()):
            plt.plot(pop)
        plt.legend([s.id for s in all_data.keys()])
        plt.show()


# This code will analyze the latest experiment ran with the PopulationAnalyzer
if __name__ == "__main__":
    am = AnalyzeManager('latest', analyzers=PopulationAnalyzer())
    am.analyze()
