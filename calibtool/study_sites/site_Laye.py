import site_BFdensity

setup_functions = site_BFdensity.get_setup_functions('Laye')

reference_data = {
    "density_by_age_and_season": {
        "Metadata": {
            "parasitemia_bins": [0, 50, 500, 5000, 50000, 500000],
            "age_bins": [5, 15, 100],
            "months": ['April','August','December']
            },
        "Seasons": {
            "start_wet": {
                "PfPR by Parasitemia and Age Bin": [[2, 0, 0, 0, 1, 1], [4, 1, 2, 3, 2, 6], [7, 9, 4, 2, 4, 1]],
                "PfPR by Gametocytemia and Age Bin": [[0, 0, 0, 5, 0, 0], [3, 9, 8, 1, 0, 0], [16, 4, 6, 1, 0, 0]]
            },
            "peak_wet": {
                "PfPR by Parasitemia and Age Bin": [[0, 1, 0, 1, 1, 0], [13, 1, 0, 3, 0, 1], [9, 12, 3, 0, 1, 0]],
                "PfPR by Gametocytemia and Age Bin": [[1, 0, 1, 1, 0, 0], [2, 4, 8, 4, 1, 0], [7, 10, 5, 3, 0, 0]]
            },
            "end_wet": {
                "PfPR by Parasitemia and Age Bin": [[1, 0, 0, 0, 1, 0], [8, 1, 1, 6, 3, 1], [10, 11, 4, 2, 0, 0]],
                "PfPR by Gametocytemia and Age Bin": [[1, 0, 0, 1, 0, 0], [7, 9, 3, 1, 0, 0], [14, 10, 3, 0, 0, 0]]
            }
        }
    }
}

analyzers = {}


def get_setup_functions():

    return setup_functions


def load_reference_data(datatype):

    return reference_data[datatype]


def get_analyzers(analyzer):

    return site_BFdensity.get_analyzers(analyzer)