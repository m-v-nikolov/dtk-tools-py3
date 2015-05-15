from dtk.utils.analyzers.filter import name_match_filter
from dtk.utils.analyzers.group  import group_by_name
from dtk.utils.analyzers.plot   import plot_CI_bands

from dtk.utils.analyzers.timeseries import TimeseriesAnalyzer
from dtk.utils.analyzers.regression import RegressionTestAnalyzer

analyzers = [ TimeseriesAnalyzer(
                group_function=group_by_name('Config_Name'),
                plot_function=plot_CI_bands
                ),
              RegressionTestAnalyzer(
                filter_function=name_match_filter('Vector'),
                channels=[ 'Statistical Population', 
                           'Rainfall', 'Adult Vectors', 
                           'Daily EIR', 'Infected', 
                           'Parasite Prevalence' ],
                onlyPlotFailed=False
                )
            ]