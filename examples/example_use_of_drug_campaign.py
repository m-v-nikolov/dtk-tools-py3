## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'

import os
from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.vector.study_sites import configure_site
from dtk.utils.reports.report_manager import add_reports
from dtk.interventions.malaria_drugs import add_drug_campaign

setup = DTKSetupParser()
dll_root = setup.get('BINARIES', 'dll_path')

exp_name  = 'ExampleSweep'
builder   = GenericSweepBuilder.from_dict({'Run_Number': range(1),
                                           'x_Temporary_Larval_Habitat': [0.05],
                                           '_site_'    : ['Namawala']})

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
cb.update_params({ 
                'Num_Cores': 1,
                'Base_Population_Scale_Factor' : 0.01,
                'Simulation_Duration' : 365
                })

add_drug_campaign(cb, 'MSAT_AL', start_days=[10])

dlls = add_reports(cb, dll_root, reports={'MalariaPatientJSONReport' : {}
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
