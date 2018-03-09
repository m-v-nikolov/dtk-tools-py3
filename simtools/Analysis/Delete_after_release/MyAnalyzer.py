from simtools.Analysis.BaseAnalyzers.BaseAnalyzer import BaseAnalyzer
from simtools.Analysis.BaseAnalyzers.BaseCacheAnalyzer import BaseCacheAnalyzer


class MyAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(need_dir_map=False)
        self.filenames = ['output\\InsetChart.json', 'Assets\\Calibration\\birth_cohort_demographics.compiled.json']

    def select_simulation_data(self, data, simulation):
        # print(type(data[self.filenames[0]]))
        # print(simulation.get_path())
        ichart = data[self.filenames[0]]
        pop = ichart['Channels']['Statistical Population']['Data']

        demog = data[self.filenames[1]]

        return {"population":pop[0], "test":demog["Metadata"]["Author"]}

    def finalize(self, all_data):
        for sim, data in all_data.items():
            print("{} = {}".format(sim,data))

            pass

class MyAnalyzer2(MyAnalyzer):
    def __init__(self):
        super().__init__()
        self.parse = False


    def select_simulation_data(self, data, simulation):
        # print(type(data[self.filenames[0]]))
        pass


class MyDataAnalyzer(BaseCacheAnalyzer):
    def __init__(self):
        super().__init__()
        self.filenames = ['output\\InsetChart.json']
        self.force = False

    def select_simulation_data(self, data, simulation):
        ichart = data[self.filenames[0]]
        pop = ichart['Channels']['Statistical Population']['Data']
        self.to_cache(simulation.id, {"population": pop[0]})

    def finalize(self, all_data):
        for sim,data in all_data.items():
            print(sim)
            print(data)

        for sim in all_data:
            print(self.from_cache(sim.id))

