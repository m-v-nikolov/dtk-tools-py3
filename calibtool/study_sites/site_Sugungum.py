from site_setup_functions import *
import site_prevalence_cohort

setup_functions = site_prevalence_cohort.get_setup_functions('Sugungum')
reference_data = {        "prevalence_by_age" : {
            "n_obs" : [79, 79, 114, 229, 114, 669, 314, 324, 733, 829, 582, 418],
            "age_bins" : [0.5, 1, 2, 4, 5, 10, 15, 20, 30, 40, 50, 60],
            "PfPR by Age Bin" : [0.3, 0.68, 0.75, 0.82, 0.88, 0.76, 0.6, 0.42, 0.27, 0.22, 0.25, 0.32]
        }
}


def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return site_prevalence_cohort.get_analyzers(analyzer)
