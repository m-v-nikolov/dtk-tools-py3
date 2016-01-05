from site_setup_functions import *

setup_functions = [ config_setup_fn(duration=21915), 
                    summary_report_fn(interval=30,description='Monthly_Report'),
                    add_treatment_fn(),
                    lambda cb : cb.update_params({ "Geography": "Calibration",
                                                   "Demographics_Filenames": ["Calibration/birth_cohort_demographics.compiled.json"], 
                                                   'Base_Population_Scale_Factor' : 10,
                                                   'Enable_Vital_Dynamics' : 0, # No births/deaths.  Just following a birth cohort.
                                                   "Climate_Model" : "CLIMATE_CONSTANT"
                       })]
reference_data = {}

analyzers = {  'seasonal_monthly_density_cohort_analyzer' : { 'name' : 'analyze_seasonal_monthly_density_cohort',
                                                              'reporter' : 'Monthly Summary Report',
                                                              'seasons' : { 'start_wet' : 6, 'peak_wet' : 8, 'end_wet' : 0},
                                                              'fields_to_get' : ['PfPR by Parasitemia and Age Bin',
                                                                                 'PfPR by Gametocytemia and Age Bin',
                                                                                 'Average Population by Age Bin'],
                                                              'LL_fn' : 'dirichlet_multinomial'
                                                            }}

def get_setup_functions(site) :

    setup_functions.append(site_input_eir_fn(site))
    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]
