## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'

# Core class for configuring DTK simulations
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder

# An experiment builder function that sweeps over random-number seed
from dtk.utils.builders.RunNumberSweepBuilder import RunNumberSweepBuilder

# Configures site-specific climate and demographics files
# Configures vector species and larval habitat availability
from dtk.vector.study_sites import configure_site

sim_type  = 'MALARIA_SIM' 
geography = 'Namawala' 
exp_name  = 'ExampleSweep'
site      = 'Namawala'
habitat   = 0.1
builder   = RunNumberSweepBuilder(3)

# Load default config for sim_type
cb = DTKConfigBuilder.from_defaults(sim_type)

# Modify the config for the geography of interest
configure_site(cb.config, site)
cb.update_params({
                'Enable_Demographics_Other' : 0,
                'Config_Name': site + '_x_' + str(habitat),
                'x_Temporary_Larval_Habitat': habitat,
                'Geography': geography,
                'Num_Cores': 1,
                'Base_Population_Scale_Factor' : 0.1,
                'Simulation_Duration' : 365*5
                })

# Dictionary of keyword-arguments for DTKSimulationManager.RunSimulations
run_sim_args =  { 'config_builder' : cb,
                  'exp_name'       : exp_name,
                  'exp_builder'    : builder,
                  'show_progress'  : True }

# The following is only for when running directly from the command-line
if __name__ == "__main__":

    from dtk.utils.core.DTKSetupParser import DTKSetupParser
    from dtk.utils.simulation.SimulationManager import SimulationManagerFactory

    # run the simulation locally
    sm = SimulationManagerFactory.from_exe(DTKSetupParser().get('BINARIES','exe_path'),'LOCAL')
    sm.RunSimulations(**run_sim_args)