from dtk.utils.analyzers import TimeseriesAnalyzer, sample_selection
from dtk.utils.analyzers import VectorSpeciesAnalyzer
from dtk.utils.analyzers.download import DownloadAnalyzer
from dtk.utils.analyzers.group  import group_by_name
from dtk.utils.analyzers.plot   import plot_grouped_lines
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# For example only -- Force the selected block to be EXAMPLE
sp = SetupParser("EXAMPLE")

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
configure_site(cb, 'Namawala')
cb.set_param('Simulation_Duration',365)


analyzers = (TimeseriesAnalyzer(select_function=sample_selection(),
                                group_function=group_by_name('_site_'),
                                plot_function=plot_grouped_lines),

             VectorSpeciesAnalyzer(select_function=sample_selection(),
                                   group_function=group_by_name('_site_')),
             )


builder = GenericSweepBuilder.from_dict({'Run_Number': range(10)})

run_sim_args =  {'config_builder': cb,
                 'exp_name': 'testrunandanalyze',
                 'exp_builder': builder,
                 'analyzers':analyzers}


if __name__ == "__main__":
    sm = ExperimentManagerFactory.from_setup(sp)
    sm.create_simulations(cb,run_sim_args['exp_name'],builder, analyzers)
    sm.commission_simulations()
