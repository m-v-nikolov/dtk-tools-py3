from dtk.utils.analyzers.select import example_selection
from dtk.utils.analyzers.group  import no_grouping, group_by_name, group_all
from dtk.utils.analyzers.plot   import no_plots, plot_grouped_lines, plot_std_bands, plot_CI_bands

from dtk.utils.analyzers.timeseries import TimeseriesAnalyzer
from dtk.utils.analyzers.vector import VectorSpeciesAnalyzer

analyzers = [ TimeseriesAnalyzer(
                select_function=example_selection(),
                group_function=group_by_name('_site_'),
                plot_function=plot_std_bands
                ),
              VectorSpeciesAnalyzer(
                select_function=example_selection(),
                group_function=group_by_name('_site_'),
                )
            ]