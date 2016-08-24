## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from simtools.SetupParser import SetupParser

# For example only -- Force the selected block to be EXAMPLE
SetupParser("EXAMPLE")

exp_name  = 'Puerto_Rico_First_Sweep'
builder = GenericSweepBuilder.from_dict({'Run_Number': range(3),
                                         '_site_': ['Namawala', 'Matsari']})

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM',
                                    Num_Cores=1,
                                    Base_Population_Scale_Factor=0.1,
                                    x_Temporary_Larval_Habitat=0.05,
                                    Simulation_Duration=365*20)

run_sim_args =  {'config_builder': cb,
                 'exp_name': exp_name,
                 'exp_builder': builder}


if __name__ == "__main__":

    from simtools.SetupParser import SetupParser
    from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

    sm = ExperimentManagerFactory.from_model(SetupParser().get('exe_path'), 'LOCAL')
    sm.run_simulations(**run_sim_args)
