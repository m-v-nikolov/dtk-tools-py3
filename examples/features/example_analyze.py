from dtk.utils.analyzers import TimeseriesAnalyzer
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.Utilities.Experiments import retrieve_experiment

# Retrieve a couple of test experiments
experiment1 = retrieve_experiment('cf9e9fb9-5c0e-e711-9400-f0921c16849c')
experiment2 = retrieve_experiment('d9d1ecea-5c0e-e711-9400-f0921c16849c')

# Create an analyze manager
# Note that we are adding the experiments that we want to analyze
am = AnalyzeManager(exp_list=[experiment1, experiment2])

# Add the TimeSeriesAnalyzer to the manager
am.add_analyzer(TimeseriesAnalyzer())

# Analyze
am.analyze()
