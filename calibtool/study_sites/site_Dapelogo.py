from site_setup_functions import *
import site_BFdensity

setup_functions = site_BFdensity.get_setup_functions('Dapelogo')

reference_data = {        "density_by_age_and_season" : {
            "parasitemia_bins" : [0, 50, 500, 5000, 50000, 500000],
            "age_bins" : [5, 15, 100],
            "start_wet" : {
                "PfPR by Parasitemia and Age Bin" : [[1, 0, 0, 2, 2, 3], [2, 1, 0, 2, 0, 4], [9, 5, 4, 4, 2, 3]],
                "PfPR by Gametocytemia and Age Bin" : [[0, 1, 4, 2, 2, 0], [0, 1, 4, 6, 0, 0], [12, 8, 3, 4, 0, 0]]
            },
            "peak_wet" : {
                "PfPR by Parasitemia and Age Bin" : [[1, 2, 0, 1, 3, 1], [2, 5, 2, 3, 1, 1], [6, 8, 4, 4, 0, 2]],
                "PfPR by Gametocytemia and Age Bin" : [[1, 3, 2, 2, 0, 0], [0, 8, 0, 3, 0, 0], [11, 10, 2, 2, 0, 0]]
            },
            "end_wet" : {
                "PfPR by Parasitemia and Age Bin" : [[1, 1, 0, 4, 3, 1], [4, 1, 2, 4, 2, 1], [6, 9, 6, 2, 2, 0]],
                "PfPR by Gametocytemia and Age Bin" : [[2, 3, 2, 2, 1, 0], [2, 5, 4, 2, 1, 0], [14, 7, 4, 0, 0, 0]]
            }
        }
                  }

def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return site_BFdensity.get_analyzers(analyzer)