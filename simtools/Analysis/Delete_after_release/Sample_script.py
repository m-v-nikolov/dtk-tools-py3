from simtools.Analysis.AnalyzeManager import AnalyzeManager as am
from simtools.Analysis.Delete_after_release.MyAnalyzer import MyAnalyzer, MyAnalyzer2, MyDataAnalyzer
from simtools.SetupParser import SetupParser

if __name__ == "__main__":
    SetupParser.init('HPC')
    exp_ids = ['d715ab3a-effa-e711-80c6-f0921c167864']
    analyzers = [MyAnalyzer(), MyAnalyzer(), MyAnalyzer2(),MyDataAnalyzer()]

    a = am(exp_list=exp_ids, analyzers=analyzers)
    a.add_simulation('19ff7fd8-41fd-e711-80c6-f0921c167864')
    a.analyze()
