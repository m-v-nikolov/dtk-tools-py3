from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from malaria.reports.MalariaReport import add_summary_report,add_immunity_report,add_survey_report

exp_name  = 'CustomReports'
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
configure_site(cb, 'Namawala')

nyears=2
cb.update_params({'Num_Cores': 1,
                  'Base_Population_Scale_Factor' : 0.1,
                  'x_Temporary_Larval_Habitat': 0.05,
                  'Simulation_Duration' : 365*nyears})

add_summary_report(cb,description='Monthly',interval=30)
add_summary_report(cb,description='Annual',interval=365)
add_immunity_report(cb,start=365*(nyears-1),interval=365,nreports=1,description = "FinalYearAverage")
add_survey_report(cb,survey_days=[100,200],reporting_interval=21,nreports=1)

run_sim_args =  { 'config_builder' : cb,
                  'exp_name'       : exp_name }