from site_setup_functions import *
import site_clinical_incidence_cohort

setup_functions = site_clinical_incidence_cohort.get_setup_functions('Ndiop')
reference_data = {        "annual_clinical_incidence_by_age" : {
            "n_obs" : [31, 34, 31, 28, 28, 21, 21, 21, 21, 21, 15, 15, 15, 15, 15, 62, 42, 42, 84, 39, 39, 50],
            "age_bins" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100],
            "Annual Clinical Incidence by Age Bin" : [1.9, 2.2, 2.6, 2.8, 2.9, 3.0, 2.8, 2.7, 2.6, 2.6, 2.5, 2.2, 2.1, 1.8, 1.5, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.4]
        }
}


def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return site_clinical_incidence_cohort.get_analyzers(analyzer)