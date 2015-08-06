from dtk.utils.analyzers.select import example_selection
from dtk.utils.analyzers.group  import no_grouping, group_by_name, group_all
from dtk.utils.analyzers.plot   import plot_grouped_lines, plot_std_bands

from dtk.utils.analyzers import TimeseriesAnalyzer, VectorSpeciesAnalyzer

analyzers = [ TimeseriesAnalyzer(
                select_function=example_selection(),
                group_function=group_by_name('_site_'),
                plot_function=plot_grouped_lines
                ),
              VectorSpeciesAnalyzer(
                select_function=example_selection(),
                group_function=group_by_name('_site_'),
                )
            ]