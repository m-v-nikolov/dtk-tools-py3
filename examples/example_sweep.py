## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import RunNumberSweepBuilder
from dtk.vector.study_sites import configure_site

sim_type  = 'MALARIA_SIM' 
exp_name  = 'ExampleSweep'
site      = 'Namawala'
habitat   = 0.1
builder   = RunNumberSweepBuilder(3)

cb = DTKConfigBuilder.from_defaults(sim_type)
configure_site(cb, site)
cb.update_params({
                'Enable_Demographics_Other' : 0,
                'Config_Name': site + '_x_' + str(habitat),
                'x_Temporary_Larval_Habitat': habitat,
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
