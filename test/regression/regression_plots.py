from dtk.utils.analyzers import name_match_filter, group_by_name, plot_grouped_lines, \
                                TimeseriesAnalyzer, RegressionTestAnalyzer

analyzers = [ 
              TimeseriesAnalyzer(
                group_function=group_by_name('Config_Name'),
                plot_function=plot_grouped_lines
                ),
              RegressionTestAnalyzer(
                filter_function=name_match_filter('Vector'),
                channels=['Statistical Population', 
                          'Rainfall', 'Adult Vectors', 
                          'Daily EIR', 'Infected', 
                          'Parasite Prevalence' ],
                onlyPlotFailed=False
                )
            ]