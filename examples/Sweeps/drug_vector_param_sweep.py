from malaria.interventions.malaria_drugs import set_drug_param, add_drug_campaign

from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModFn, ModBuilder

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from malaria.reports.MalariaReport import add_patient_report
from dtk.vector.study_sites import configure_site
from dtk.vector.species import set_species_param
from simtools.SetupParser import SetupParser

SetupParser.default_block = 'HPC'
exp_name = 'DrugCampaignVectorParamSweep'

builder = ModBuilder.from_combos(
    [ModFn(DTKConfigBuilder.set_param, 'x_Temporary_Larval_Habitat', h) for h in [0.05]],
    [ModFn(configure_site, 'Namawala')],
    [ModFn(set_species_param, 'gambiae', 'Required_Habitat_Factor', value=v) for v in [(100, 50), (200, 100)]],
    [ModFn(set_drug_param, 'Artemether', 'Max_Drug_IRBC_Kill', value=v) for v in [4, 2]])

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
cb.update_params({'Num_Cores': 1,
                  'Base_Population_Scale_Factor': 0.01,
                  'Simulation_Duration': 30})

add_drug_campaign(cb, 'DHA', start_days=[10])
add_patient_report(cb)

run_sim_args = {'config_builder': cb,
                'exp_name': exp_name,
                'exp_builder': builder}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())
