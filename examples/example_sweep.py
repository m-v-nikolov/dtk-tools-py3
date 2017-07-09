## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'EXAMPLE'

exp_name  = 'ExampleSweep'
builder = GenericSweepBuilder.from_dict({'Run_Number': range(3),
                                         '_site_': ['Namawala', 'Matsari']})

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM',
                                    Num_Cores=1,
                                    Base_Population_Scale_Factor=0.1,
                                    x_Temporary_Larval_Habitat=0.05,
                                    Simulation_Duration=365*20)
configure_site(cb,'Namawala')

run_sim_args = {
    'exp_name': exp_name,
    'exp_builder': builder,
    'config_builder':cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
