from site_setup_functions import *
import site_prevalence_cohort

setup_functions = site_prevalence_cohort.get_setup_functions('Namawala')
reference_data = {        "prevalence_by_age" : {
            "n_obs" : [150, 150, 626, 1252, 626, 2142, 1074, 1074, 605, 605, 489],
            "age_bins" : [0.5, 1, 2, 4, 5, 10, 15, 20, 30, 40, 50],
            "PfPR by Age Bin" : [0.55, 0.85, 0.9, 0.88, 0.85, 0.82, 0.75, 0.65, 0.45, 0.42, 0.4]
        }
}


def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return site_prevalence_cohort.get_analyzers(analyzer)
