from dtk.utils.analyzers.filter import example_filter
from dtk.utils.analyzers.select import example_selection
from dtk.utils.analyzers.group  import no_grouping, group_by_name, group_all
from dtk.utils.analyzers.plot   import no_plots, plot_with_tsplot, plot_CI_bands

from dtk.utils.analyzers.timeseries import TimeseriesAnalyzer

analyzers = [ TimeseriesAnalyzer(
                filter_function=example_filter,
                select_function=example_selection,
                group_function=group_all,
                plot_function=plot_CI_bands
                )
            ]