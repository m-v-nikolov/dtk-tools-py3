from dtk.utils.analyzers import TimeseriesAnalyzer, VectorSpeciesAnalyzer
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.Utilities.Experiments import retrieve_experiment

if __name__ == "__main__":
    # Retrieve a couple of test experiments
    experiment1 = retrieve_experiment('158cc530-780e-e711-9400-f0921c16849c')
    experiment2 = retrieve_experiment('c62aa746-780e-e711-9400-f0921c16849c')

    # Create an analyze manager
    # Note that we are adding the experiments that we want to analyze
    am = AnalyzeManager(exp_list=[experiment1, experiment2])

    # Add the TimeSeriesAnalyzer to the manager
    am.add_analyzer(TimeseriesAnalyzer())
    am.add_analyzer(VectorSpeciesAnalyzer())

    # Analyze
    am.analyze()
