from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder, set_param
from dtk.utils.builders.sweep import Builder
from dtk.utils.reports.MalariaReport import add_patient_report
from dtk.interventions.malaria_drugs import add_drug_campaign
from dtk.vector.study_sites import configure_site
from dtk.vector.species import set_species_param
from dtk.interventions.malaria_drugs import set_drug_param

exp_name  = 'DrugCampaignVectorParamSweep'
builder = Builder.from_combos([Builder.ModFn(set_param, 'Run_Number', i) for i in range(1)],
                              [Builder.ModFn(set_param, 'x_Temporary_Larval_Habitat', h) for h in [0.05]],
                              [Builder.ModFn(configure_site, 'Namawala')],
                              [Builder.ModFn(set_species_param, 'gambiae', 'Required_Habitat_Factor', value=v) for v in [(100, 50), (200, 100)]],
                              [Builder.ModFn(set_drug_param, 'Artemether', 'Max_Drug_IRBC_Kill', value=v) for v in [4, 2]])

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
cb.update_params({'Num_Cores': 1,
                  'Base_Population_Scale_Factor': 0.01,
                  'Simulation_Duration': 30})

add_drug_campaign(cb, 'MDA_AL', start_days=[10])
add_patient_report(cb)

run_sim_args =  {'config_builder' : cb,
                 'exp_name'       : exp_name,
                 'exp_builder'    : builder}