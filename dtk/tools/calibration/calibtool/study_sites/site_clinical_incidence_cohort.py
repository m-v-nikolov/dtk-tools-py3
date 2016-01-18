from site_setup_functions import *

fine_age_bins = [ 0.08333, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 
                  11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100 ]

setup_functions = [ config_setup_fn(duration=365),
                    summary_report_fn(age_bins=fine_age_bins, interval=21915),
                    lambda cb : cb.update_params({ "Geography": "Calibration",
                                                   "Demographics_Filenames": ["Calibration/birth_cohort_demographics.compiled.json"], 
                                                   'Base_Population_Scale_Factor' : 10,
                                                   'Enable_Vital_Dynamics' : 0, # No births/deaths.  Just following a birth cohort.
                                                   "Climate_Model" : "CLIMATE_CONSTANT"
                       })                    ]
reference_data = {}

analyzers = {   'clinical_incidence_by_age_cohort_analyzer' : { 'name' : 'analyze_clinical_incidence_by_age_cohort',
                                                               'reporter' : 'Annual Summary Report',
                                                               'fields_to_get' : ['Annual Clinical Incidence by Age Bin',
                                                                                  'Average Population by Age Bin',
                                                                                  'Age Bins'],
                                                               'LL_fn' : 'gamma_poisson'
                                                           }}

def get_setup_functions(site) :

    setup_functions.append(site_input_eir_fn(site))
    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]
