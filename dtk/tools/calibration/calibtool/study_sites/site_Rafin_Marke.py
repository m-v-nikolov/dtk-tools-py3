from site_setup_functions import *
import site_prevalence_cohort

setup_functions = site_prevalence_cohort.get_setup_functions('Rafin_Marke')
reference_data = {        "prevalence_by_age" : {
            "n_obs" : [45, 45,  66, 132,  66, 386, 182, 187, 424, 479, 336, 241],
            "age_bins" : [0.5, 1, 2, 4, 5, 10, 15, 20, 30, 40, 50, 60],
            "PfPR by Age Bin" : [0.44, 0.5, 0.55, 0.8, 0.85, 0.83, 0.68, 0.55, 0.35, 0.25, 0.2, 0.15]
        }
}


def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return site_prevalence_cohort.get_analyzers(analyzer)
