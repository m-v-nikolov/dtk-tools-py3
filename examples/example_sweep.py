## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.vector.study_sites import configure_site

exp_name  = 'ExampleSweep'
builder   = GenericSweepBuilder.from_dict({'Run_Number': range(3),
                                           'x_Temporary_Larval_Habitat': [0.05],
                                           '_site_'    : ['Namawala','Matsari']})

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
cb.update_params({
                'Num_Cores': 1,
                'Base_Population_Scale_Factor' : 0.1,
                'Simulation_Duration' : 365*5
                })

run_sim_args =  { 'config_builder' : cb,
                  'exp_name'       : exp_name,
                  'exp_builder'    : builder,
                  'show_progress'  : True }

if __name__ == "__main__":

    from dtk.utils.core.DTKSetupParser import DTKSetupParser
    from dtk.utils.simulation.SimulationManager import SimulationManagerFactory

    sm = SimulationManagerFactory.from_exe(DTKSetupParser().get('BINARIES','exe_path'),'LOCAL')
    sm.RunSimulations(**run_sim_args)
