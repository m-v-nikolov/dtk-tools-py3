from dtk.tools.calibration.calibtool.study_sites.site_setup_functions import config_setup_fn, site_input_eir_fn, \
    summary_report_fn

setup_functions = [ config_setup_fn(duration=365),
                    summary_report_fn(interval=360),
                    lambda cb : cb.update_params({ "Geography": "Calibration",
                                "Demographics_Filenames": ["Calibration/birth_cohort_demographics.compiled.json"], 
                                'Base_Population_Scale_Factor' : 10,
                                'Enable_Vital_Dynamics' : 0, # No births/deaths.  Just following a birth cohort.
                                "Climate_Model" : "CLIMATE_CONSTANT"
                       })]
reference_data = {}

analyzers = {    'prevalence_by_age_cohort_analyzer' : { 'name' : 'analyze_prevalence_by_age_cohort',
                                                         'reporter' : 'Annual Summary Report',
                                                         'fields_to_get' : ['PfPR by Age Bin',
                                                                            'Average Population by Age Bin'],
                                                         'LL_fn' : 'beta_binomial'
                                          }}

def get_setup_functions(site) :

    setup_functions.append(site_input_eir_fn(site))
    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]
