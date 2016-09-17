from dtk.utils.analyzers import TimeseriesAnalyzer, VectorSpeciesAnalyzer, sample_selection
from dtk.utils.analyzers.group  import group_by_name
from dtk.utils.analyzers.plot   import plot_grouped_lines

analyzers = [ TimeseriesAnalyzer(
                select_function=sample_selection(),
                group_function=group_by_name('_site_'),
                plot_function=plot_grouped_lines
                ),
              VectorSpeciesAnalyzer(
                select_function=sample_selection(),
                group_function=group_by_name('_site_'),
                )
            ]