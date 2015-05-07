from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.utils.reports.MalariaReport import add_patient_report
from dtk.interventions.malaria_drugs import add_drug_campaign

exp_name  = 'DrugCampaignVectorParamSweep'
builder   = GenericSweepBuilder.from_dict({'Run_Number': range(1),
                                           'x_Temporary_Larval_Habitat': [0.05],
                                           '_site_'    : ['Namawala'],
                                           'AntiMalDrug_Artemether_Adherence' : [0.5, 0.7],
                                           'VectorSpec_gambiae_Required_Habitat_Factor' : [[100, 50], [200,100]]})

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
cb.update_params({'Num_Cores': 1,
                  'Base_Population_Scale_Factor' : 0.01,
                  'Simulation_Duration' : 30})

add_drug_campaign(cb, 'MDA_AL', start_days=[10])
add_patient_report(cb)

run_sim_args =  { 'config_builder' : cb,
                  'exp_name'       : exp_name,
                  'exp_builder'    : builder }