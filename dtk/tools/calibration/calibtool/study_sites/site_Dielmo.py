from site_setup_functions import *
import site_clinical_incidence_cohort

setup_functions = site_clinical_incidence_cohort.get_setup_functions('Dielmo')
reference_data = {        "annual_clinical_incidence_by_age" : {
            "n_obs" : [55, 60, 55, 50, 50, 38, 38, 38, 38, 38, 26, 26, 26, 26, 26, 110, 75, 75, 150, 70, 70, 90],
            "age_bins" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100],
            "Annual Clinical Incidence by Age Bin" : [3.2, 5, 6.1, 4.75, 3.1, 2.75, 2.7, 1.9, 0.12, 0.8, 0.5, 0.25, 0.1, 0.2, 0.4, 0.3, 0.2, 0.2, 0.2, 0.15, 0.15, 0.15]
        }
}


def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return site_clinical_incidence_cohort.get_analyzers(analyzer)