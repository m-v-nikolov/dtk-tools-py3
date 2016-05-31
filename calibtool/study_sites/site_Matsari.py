from site_setup_functions import *
import site_prevalence_cohort

setup_functions = site_prevalence_cohort.get_setup_functions('Matsari')
reference_data = {        "prevalence_by_age" : {
            "n_obs" : [52, 52, 76, 151, 76, 441, 207, 214, 484, 547, 384, 276],
            "age_bins" : [0.5, 1, 2, 4, 5, 10, 15, 20, 30, 40, 50, 60],
            "PfPR by Age Bin" : [0.2, 0.68, 0.7, 0.85, 0.8, 0.8, 0.78, 0.55, 0.35, 0.3, 0.25, 0.3]
        }
}


def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return site_prevalence_cohort.get_analyzers(analyzer)
