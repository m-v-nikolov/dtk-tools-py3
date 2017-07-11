from dtk.utils.analyzers import TimeseriesAnalyzer
from dtk.utils.analyzers import VectorSpeciesAnalyzer
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'LOCAL'

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
configure_site(cb, 'Namawala')
cb.set_param('Simulation_Duration',365)


analyzers = (TimeseriesAnalyzer(),
             VectorSpeciesAnalyzer())


builder = GenericSweepBuilder.from_dict({'Run_Number': range(5)})

run_sim_args =  {
    'exp_name': 'testrunandanalyze',
    'exp_builder': builder,
    'config_builder':cb
}

if __name__ == "__main__":
    SetupParser.init(selected_block=SetupParser.default_block)
    exp_manager = ExperimentManagerFactory.from_cb(config_builder=cb)
    exp_manager.run_simulations(**run_sim_args)
    exp_manager.wait_for_finished(verbose=True)

    am = AnalyzeManager('latest')
    map(am.add_analyzer, analyzers)
    am.analyze()
