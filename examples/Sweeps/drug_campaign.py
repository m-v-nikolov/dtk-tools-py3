from malaria.interventions.malaria_drugs import add_drug_campaign

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from malaria.reports.MalariaReport import add_patient_report

from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser


SetupParser.default_block = 'HPC'
exp_name = 'DrugCampaign'

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
configure_site(cb, 'Namawala')
cb.update_params({'Num_Cores': 1,
                  'Base_Population_Scale_Factor': 0.1,
                  'x_Temporary_Larval_Habitat': 0.05,
                  'Simulation_Duration': 365})

add_drug_campaign(cb, 'ALP', start_days=[10])
add_patient_report(cb)

run_sim_args = {'config_builder': cb,
                'exp_name': exp_name}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())