from dtk.utils.analyzers import TimeseriesAnalyzer, sample_selection
from dtk.utils.analyzers import VectorSpeciesAnalyzer
from dtk.utils.analyzers.group  import group_by_name
from dtk.utils.analyzers.plot   import plot_grouped_lines
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'EXAMPLE'

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
configure_site(cb, 'Namawala')
cb.set_param('Simulation_Duration',365)


analyzers = (TimeseriesAnalyzer(select_function=sample_selection(),
                                group_function=group_by_name('_site_'),
                                plot_function=plot_grouped_lines),

             VectorSpeciesAnalyzer(select_function=sample_selection(),
                                   group_function=group_by_name('_site_')),
             )


builder = GenericSweepBuilder.from_dict({'Run_Number': range(5)})

run_sim_args =  {
    'exp_name': 'testrunandanalyze',
    'exp_builder': builder,
    'analyzers':analyzers,
}

if __name__ == "__main__":
    SetupParser.init(selected_block=SetupParser.default_block)
    exp_manager = ExperimentManagerFactory.from_setup(config_builder=cb)
    exp_manager.run_simulations(**run_sim_args)
