# from dtk.utils.analyzers import TimeseriesAnalyzer

from dtk.utils.analyzers.TimeSeriesAnalyzer import TimeseriesAnalyzer as ts
from dtk.utils.analyzers.VectorSpeciesAnalyzer import VectorSpeciesAnalyzer
from simtools.Analysis.AnalyzeManager import AnalyzeManager as am
from simtools.Analysis.Delete_after_release.MyAnalyzer import MyDataAnalyzer
from simtools.SetupParser import SetupParser

if __name__ == "__main__":
    SetupParser.init('HPC')
    # exp_ids = ['d715ab3a-effa-e711-80c6-f0921c167864']
    exp_ids = []
    # analyzers = [MyAnalyzer(), MyAnalyzer(), MyAnalyzer2(),MyDataAnalyzer()]
    analyzers = [ts(), VectorSpeciesAnalyzer()]
    analyzers = [MyDataAnalyzer()]

    a = am(exp_list=["e9396c96-e510-e811-9415-f0921c16b9e5"], analyzers=analyzers, verbose=True)
    # a = AnalyzeManager(exp_list=exp_ids, analyzers=analyzers)

    a.analyze()




    # t = time.time()
    # analyzers = [TimeseriesAnalyzer()]
    # a = AnalyzeManager(exp_list=exp_ids, analyzers=analyzers)
    # a.add_simulation('19ff7fd8-41fd-e711-80c6-f0921c167864')
    # a.analyze()
    # print("Took {}".format(time.time() - t))