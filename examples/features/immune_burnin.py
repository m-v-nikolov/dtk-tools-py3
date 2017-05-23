from dtk.interventions.outbreakindividual import recurring_outbreak
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports.MalariaReport import add_summary_report, add_immunity_report

exp_name  = 'burnin'
builder = GenericSweepBuilder.from_dict({
              'Run_Number': range(1),
              'x_Temporary_Larval_Habitat': (0.1,0.2,0.3,0.4,0.5),
              '_site_': ('Sinazongwe.static',)
              })

nyears=50 # for sim duration AND reporting interval

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
cb.update_params({ 'Num_Cores': 1,
                   'Simulation_Duration' : nyears*365,
                   'New_Diagnostic_Sensitivity': 0.025 # 40/uL
                })

# recurring outbreak to avoid fadeout
recurring_outbreak(cb, outbreak_fraction=0.001, tsteps_btwn=180)

# custom reporting
add_summary_report(cb, start=0, interval=365, nreports=nyears, description = "AnnualAverage")
add_immunity_report(cb, start=365*(nyears-1), interval=365, nreports=1, 
                    description = "FinalYearAverage",
                    age_bins = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                                 14, 15, 20, 25, 30, 40,  50,  60, 1000 ])

run_sim_args =  { 'config_builder': cb,
                  'exp_name': exp_name,
                  'exp_builder': builder}
