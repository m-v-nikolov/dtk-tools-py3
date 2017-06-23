from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from malaria.reports.MalariaReport import add_patient_report
from dtk.interventions.malaria_drugs import add_drug_campaign

exp_name  = 'DrugCampaign'
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
configure_site(cb, 'Namawala')
cb.update_params({'Num_Cores': 1,
                  'Base_Population_Scale_Factor' : 0.1,
                  'x_Temporary_Larval_Habitat': 0.05,
                  'Simulation_Duration' : 365})

add_drug_campaign(cb, 'MSAT_AL', start_days=[10])
add_patient_report(cb)

run_sim_args =  { 'config_builder' : cb,
                  'exp_name'       : exp_name }